"""
Aggregations behind the public analytics page.

The participant data arrives from the EiA MELIA API with the state and LGA
columns in two different shapes: readable names ("Benue", "Cross_River") and
GADM codes ("NG.BE", "NG.CR"). Roughly 40% of Nigerian records use the coded
form, so anything that groups on the raw column splits a single state across
two buckets and understates it. Everything here normalises first.

Results are cached — the full set of aggregations reads ~200k rows and takes
several seconds, which is far too slow to run per page view.
"""
import logging
import re

from django.core.cache import cache
from django.db.models import Count
from django.utils import timezone

logger = logging.getLogger(__name__)

CACHE_KEY = 'public_analytics_v1'
METRIC_TYPE = 'public_analytics'
CACHE_TTL = 60 * 60 * 6  # 6 hours; participant data syncs at most daily


# ─── Nigeria state normalisation ──────────────────────────────────────────────

#: GADM level-1 code → canonical state name.
STATE_CODE_TO_NAME = {
    'NG.AB': 'Abia',        'NG.AD': 'Adamawa',      'NG.AK': 'Akwa Ibom',
    'NG.AN': 'Anambra',     'NG.BA': 'Bauchi',       'NG.BY': 'Bayelsa',
    'NG.BE': 'Benue',       'NG.BO': 'Borno',        'NG.CR': 'Cross River',
    'NG.DE': 'Delta',       'NG.EB': 'Ebonyi',       'NG.ED': 'Edo',
    'NG.EK': 'Ekiti',       'NG.EN': 'Enugu',        'NG.FC': 'FCT (Abuja)',
    'NG.GO': 'Gombe',       'NG.IM': 'Imo',          'NG.JI': 'Jigawa',
    'NG.KD': 'Kaduna',      'NG.KN': 'Kano',         'NG.KT': 'Katsina',
    'NG.KE': 'Kebbi',       'NG.KO': 'Kogi',         'NG.KW': 'Kwara',
    'NG.LA': 'Lagos',       'NG.NA': 'Nasarawa',     'NG.NI': 'Niger',
    'NG.OG': 'Ogun',        'NG.ON': 'Ondo',         'NG.OS': 'Osun',
    'NG.OY': 'Oyo',         'NG.PL': 'Plateau',      'NG.RI': 'Rivers',
    'NG.SO': 'Sokoto',      'NG.TA': 'Taraba',       'NG.YO': 'Yobe',
    'NG.ZA': 'Zamfara',
}

#: Spelling variants seen in the source data → canonical state name.
STATE_NAME_ALIASES = {
    'cross river': 'Cross River',
    'crossriver': 'Cross River',
    'akwa ibom': 'Akwa Ibom',
    'akwaibom': 'Akwa Ibom',
    'abuja': 'FCT (Abuja)',
    'fct': 'FCT (Abuja)',
    'federal capital-abuja': 'FCT (Abuja)',
    'federal capital territory': 'FCT (Abuja)',
    'nassarawa': 'Nasarawa',
    'nasarawa': 'Nasarawa',
}

UNKNOWN = 'Not Specified'


def _clean(value):
    """Underscores → spaces, collapse whitespace, trim."""
    return re.sub(r'\s+', ' ', str(value).replace('_', ' ')).strip()


def normalize_state(value):
    """Map any state spelling or GADM code to one canonical state name."""
    if not value:
        return UNKNOWN

    raw = str(value).strip()
    code = raw.upper()
    if code in STATE_CODE_TO_NAME:
        return STATE_CODE_TO_NAME[code]

    cleaned = _clean(raw)
    alias = STATE_NAME_ALIASES.get(cleaned.lower())
    if alias:
        return alias

    return cleaned.title() if cleaned else UNKNOWN


def state_of_lga_code(value):
    """Return the state name implied by an ``NG.XX.YY`` LGA code, if any."""
    if value and str(value).upper().startswith('NG.'):
        parts = str(value).upper().split('.')
        if len(parts) >= 2:
            return STATE_CODE_TO_NAME.get('.'.join(parts[:2]))
    return None


def normalize_lga(value):
    """
    Best-effort readable label for an LGA.

    Unlike states, the source gives no readable name for coded LGAs, and there
    is no authoritative code→name table in this project. Rather than invent
    names, a coded LGA is shown as its own code qualified by the state it
    belongs to — e.g. ``NG.AB.IS`` becomes ``IS (Abia)``.
    """
    if not value:
        return UNKNOWN

    raw = str(value).strip()
    if raw.upper().startswith('NG.'):
        parts = raw.upper().split('.')
        state = state_of_lga_code(raw)
        suffix = parts[-1] if len(parts) >= 3 else raw
        return f"{suffix} ({state})" if state else raw

    return _clean(raw).title()


def normalize_gender(value):
    """Collapse gender spellings into Male / Female / Not Specified."""
    if not value:
        return UNKNOWN
    v = str(value).strip().lower()
    if v in ('m', 'male'):
        return 'Male'
    if v in ('f', 'female'):
        return 'Female'
    if v in ('not specified', 'unspecified', 'unknown', 'n/a', 'na', '-'):
        return UNKNOWN
    return _clean(value).title()


# ─── Aggregation helpers ──────────────────────────────────────────────────────

def _grouped(queryset, field, normalizer, limit=None, drop_unknown=False):
    """
    Group ``queryset`` by ``field``, normalise the labels, and merge the
    buckets that normalise to the same label.

    Returns a list of ``{'label': str, 'count': int}`` ordered by count desc.
    """
    merged = {}
    for row in queryset.values(field).annotate(n=Count('id')):
        label = normalizer(row[field])
        if drop_unknown and label == UNKNOWN:
            continue
        merged[label] = merged.get(label, 0) + row['n']

    ordered = sorted(merged.items(), key=lambda kv: (-kv[1], kv[0]))
    if limit:
        ordered = ordered[:limit]
    return [{'label': label, 'count': count} for label, count in ordered]


def build_analytics(country='nigeria'):
    """Compute the full public analytics payload. Slow — always cache this."""
    from .models import AkilimoParticipant, ANANigeriaPartner

    qs = AkilimoParticipant.objects.all()
    if country and country != 'all':
        qs = qs.filter(country__iexact=country)

    total = qs.count()

    by_gender = _grouped(qs, 'farmer_gender', normalize_gender)
    by_state = _grouped(qs, 'admin_level1', normalize_state, drop_unknown=True)
    # Grouped once in full: the total LGA count and the top-25 chart both come
    # from this, rather than paying for a second distinct scan.
    all_lgas = _grouped(qs, 'admin_level2', normalize_lga, drop_unknown=True)
    by_lga = all_lgas[:25]
    by_age = _grouped(qs, 'age_category', lambda v: _clean(v).title() if v else UNKNOWN)
    by_crop = _grouped(qs, 'crop', lambda v: _clean(v).title() if v else UNKNOWN, drop_unknown=True)
    by_event_type = _grouped(qs, 'event_type', lambda v: _clean(v).title() if v else UNKNOWN,
                             limit=12, drop_unknown=True)
    by_partner = _grouped(qs, 'partner', lambda v: _clean(v) if v else UNKNOWN,
                          limit=15, drop_unknown=True)

    # Reach over time, oldest first, ignoring rows with no event year.
    by_year = [
        {'label': str(row['event_year']), 'count': row['n']}
        for row in qs.exclude(event_year__isnull=True)
                     .values('event_year').annotate(n=Count('id')).order_by('event_year')
    ]

    female = next((r['count'] for r in by_gender if r['label'] == 'Female'), 0)
    male = next((r['count'] for r in by_gender if r['label'] == 'Male'), 0)
    gendered = female + male

    with_phone = qs.exclude(farmer_phone_no__isnull=True).exclude(farmer_phone_no='').count()
    events = (qs.exclude(event_type__isnull=True).exclude(event_type='')
                .values('event_date', 'event_type', 'event_venue').distinct().count())

    return {
        'country': country,
        'totals': {
            'farmers': total,
            'states': len(by_state),
            'lgas': len(all_lgas),
            'partners': ANANigeriaPartner.objects.filter(is_active=True).count(),
            'events': events,
            'farmers_with_phone': with_phone,
            'female': female,
            'male': male,
            'female_pct': round(female / gendered * 100, 1) if gendered else 0,
            'male_pct': round(male / gendered * 100, 1) if gendered else 0,
        },
        'by_gender': by_gender,
        'by_state': by_state,
        'by_lga': by_lga,
        'by_age': by_age,
        'by_crop': by_crop,
        'by_event_type': by_event_type,
        'by_partner': by_partner,
        'by_year': by_year,
    }


def save_snapshot(country='nigeria'):
    """
    Recompute the analytics and persist them as a DashboardMetrics snapshot.

    This is the slow path (~1 minute over 200k rows) and is meant to be run by
    the scheduled task after a data sync — never inside a web request.
    """
    from .models import DashboardMetrics

    data = build_analytics(country=country)

    snapshot = DashboardMetrics.objects.filter(
        metric_type=METRIC_TYPE, metric_name=country
    ).first()
    if snapshot:
        snapshot.metric_value = data
        snapshot.computed_at = timezone.now()
        snapshot.is_current = True
        snapshot.save(update_fields=['metric_value', 'computed_at', 'is_current'])
    else:
        snapshot = DashboardMetrics.objects.create(
            metric_type=METRIC_TYPE, metric_name=country,
            metric_value=data, is_current=True,
        )

    data['computed_at'] = snapshot.computed_at.isoformat()
    cache.set(f"{CACHE_KEY}:{country}", data, CACHE_TTL)
    logger.info("Public analytics snapshot saved for country=%s (%s farmers)",
                country, data['totals']['farmers'])
    return data


def _snapshot_from_db(country):
    """Read the stored snapshot, or None if one has never been computed."""
    from .models import DashboardMetrics

    snapshot = DashboardMetrics.objects.filter(
        metric_type=METRIC_TYPE, metric_name=country
    ).order_by('-computed_at').first()
    if not snapshot or not isinstance(snapshot.metric_value, dict):
        return None

    data = snapshot.metric_value
    data['computed_at'] = snapshot.computed_at.isoformat()
    return data


def get_analytics(country='nigeria', force_refresh=False):
    """
    Return the analytics payload for display.

    Order of preference: process cache → stored snapshot → compute now. The
    last step only ever runs before the first snapshot exists, so a visitor
    normally gets an instant response.
    """
    key = f"{CACHE_KEY}:{country}"

    if not force_refresh:
        cached = cache.get(key)
        if cached is not None:
            return cached

        data = _snapshot_from_db(country)
        if data is not None:
            cache.set(key, data, CACHE_TTL)
            return data

    logger.warning(
        "No analytics snapshot for country=%s — computing inline. "
        "Run 'manage.py refresh_analytics' on a schedule to avoid this.", country
    )
    return save_snapshot(country=country)


def clear_analytics_cache():
    """Drop every cached analytics payload (call after a data sync)."""
    for country in ('nigeria', 'all'):
        cache.delete(f"{CACHE_KEY}:{country}")


# ─── Per-partner analytics ────────────────────────────────────────────────────

PARTNER_CACHE_KEY = 'partner_analytics_v1'
PARTNER_CACHE_TTL = 60 * 60 * 6


def build_partner_analytics(partner_name, country='nigeria'):
    """
    Aggregate the participant records attributed to one partner organisation.

    ``AkilimoParticipant.partner`` is free text supplied by the source system,
    so it is matched case-insensitively against the organisation name — the
    same rule PartnerOrganization.total_farmers already uses.

    Scoped to Nigeria by default: several partners also appear in the wider
    AKILIMO dataset for other countries, and an AKILIMO *Nigeria* partner page
    showing Tanzanian districts among its states would simply be wrong.

    The partner filter is a substring match, which no index can serve, so the
    rows are read **once** and every breakdown is tallied from that single pass
    in Python. Running six separate GROUP BY queries instead meant six full
    scans and took roughly twenty seconds per partner.
    """
    from collections import Counter
    from .models import AkilimoParticipant

    qs = AkilimoParticipant.objects.filter(partner__icontains=partner_name)
    if country and country != 'all':
        qs = qs.filter(country__iexact=country)

    genders, states, lgas, years, event_types = (
        Counter(), Counter(), Counter(), Counter(), Counter()
    )
    events = set()
    total = 0

    rows = qs.values_list(
        'farmer_gender', 'admin_level1', 'admin_level2', 'event_year',
        'event_type', 'event_date', 'event_venue',
    ).iterator(chunk_size=5000)

    for gender, state, lga, year, event_type, event_date, venue in rows:
        total += 1
        genders[normalize_gender(gender)] += 1

        state_label = normalize_state(state)
        if state_label != UNKNOWN:
            states[state_label] += 1

        lga_label = normalize_lga(lga)
        if lga_label != UNKNOWN:
            lgas[lga_label] += 1

        if year:
            years[str(year)] += 1

        if event_type:
            event_types[_clean(event_type).title()] += 1
            events.add((event_date, event_type, venue))

    if not total:
        return {
            'partner': partner_name, 'has_data': False,
            'totals': {'farmers': 0, 'states': 0, 'lgas': 0, 'events': 0,
                       'female': 0, 'male': 0, 'female_pct': 0, 'male_pct': 0},
            'by_gender': [], 'by_state': [], 'by_year': [], 'by_event_type': [],
        }

    def ranked(counter, limit=None):
        ordered = sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))
        if limit:
            ordered = ordered[:limit]
        return [{'label': label, 'count': count} for label, count in ordered]

    female, male = genders.get('Female', 0), genders.get('Male', 0)
    gendered = female + male

    return {
        'partner': partner_name,
        'has_data': True,
        'totals': {
            'farmers': total,
            'states': len(states),
            'lgas': len(lgas),
            'events': len(events),
            'female': female,
            'male': male,
            'female_pct': round(female / gendered * 100, 1) if gendered else 0,
            'male_pct': round(male / gendered * 100, 1) if gendered else 0,
        },
        'by_gender': ranked(genders),
        'by_state': ranked(states, limit=15),
        # Oldest first — this one reads as a trend, not a ranking.
        'by_year': [{'label': y, 'count': years[y]} for y in sorted(years)],
        'by_event_type': ranked(event_types, limit=10),
    }


def _partner_cache_key(partner_name):
    """
    Build a safe cache key for a partner.

    Partner names contain spaces, ampersands and brackets, which are illegal in
    a memcached key — so the name is hashed rather than interpolated.
    """
    import hashlib
    digest = hashlib.sha1(partner_name.strip().lower().encode('utf-8')).hexdigest()[:16]
    return f"{PARTNER_CACHE_KEY}:{digest}"


def get_partner_analytics(partner_name, force_refresh=False):
    """Cached per-partner analytics. Far cheaper than the site-wide build."""
    key = _partner_cache_key(partner_name)
    if not force_refresh:
        cached = cache.get(key)
        if cached is not None:
            return cached

    data = build_partner_analytics(partner_name)
    cache.set(key, data, PARTNER_CACHE_TTL)
    return data
