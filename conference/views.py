import json
import uuid
import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.views.generic import TemplateView, FormView, DetailView
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse, Http404, HttpResponse, FileResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.conf import settings

from django.core import signing
from django.core.paginator import Paginator

from .models import (
    Conference, Speaker, AbstractSubmission, AbstractThematicArea,
    RegistrationCategory, Registration, ProgramDay, Sponsor, KeyMessage,
    ContentBlock, Exhibitor, ExhibitorPackage, ExhibitorShowcase,
    PaymentVerifier, AbstractReviewer,
)
from .forms import (
    AbstractSubmissionForm, RegistrationForm, StakeholderRegistrationForm,
    ExhibitorRegistrationForm, ExhibitorShowcaseForm,
)
from dashboard.paystack_service import PaystackService

logger = logging.getLogger(__name__)


def get_active_conference():
    """Helper: get the currently active conference"""
    return Conference.objects.filter(is_active=True).first()


def _no_conference_redirect():
    """Redirect to landing when no conference is configured"""
    return redirect('conference:landing')


# ─── Landing ──────────────────────────────────────────────────────────────────

class ConferenceLandingView(TemplateView):
    template_name = 'conference/landing.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        conference = get_active_conference()
        if not conference:
            context['conference'] = None
            return context

        context['conference'] = conference
        context['sub_themes'] = conference.sub_themes.filter(is_active=True)
        context['featured_speakers'] = conference.speakers.filter(is_active=True, is_featured=True).order_by('order')[:6]
        context['keynote_speakers'] = conference.speakers.filter(is_active=True, speaker_type='keynote')
        context['key_messages'] = conference.key_messages.filter(is_active=True)
        context['loc_members'] = conference.loc_members.filter(is_active=True)
        context['sponsors'] = conference.sponsors.filter(is_active=True)
        context['registration_categories'] = conference.registration_categories.filter(is_active=True)
        context['total_registrations'] = Registration.objects.filter(
            conference=conference, payment_status='confirmed'
        ).count()
        context['total_abstracts'] = AbstractSubmission.objects.filter(conference=conference).count()
        return context


# ─── Speakers ─────────────────────────────────────────────────────────────────

class SpeakersView(TemplateView):
    template_name = 'conference/speakers.html'

    def get(self, request, *args, **kwargs):
        if not get_active_conference():
            return _no_conference_redirect()
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        conference = get_active_conference()
        context['conference'] = conference
        context['keynote_speakers'] = conference.speakers.filter(is_active=True, speaker_type='keynote').order_by('order')
        context['invited_speakers'] = conference.speakers.filter(is_active=True, speaker_type='invited').order_by('order')
        context['panelists'] = conference.speakers.filter(is_active=True, speaker_type='panelist').order_by('order')
        return context


# ─── Abstract Submission ──────────────────────────────────────────────────────

class AbstractSubmissionView(FormView):
    template_name = 'conference/abstract_submission.html'

    def get_conference(self):
        return get_active_conference()

    def dispatch(self, request, *args, **kwargs):
        if not self.get_conference():
            return _no_conference_redirect()
        return super().dispatch(request, *args, **kwargs)

    def get_form(self, form_class=None):
        conference = self.get_conference()
        return AbstractSubmissionForm(conference, **self.get_form_kwargs())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        conference = self.get_conference()
        context['conference'] = conference
        context['abstract_structure'] = [
            'Title (centered)',
            'Author(s) & Affiliations',
            'Corresponding author email & phone (WhatsApp)',
            'Objectives',
            'Methodology',
            'Major Findings',
            'Conclusion',
        ]
        if not conference.abstract_submission_open:
            context['submission_closed'] = True
        return context

    def form_valid(self, form):
        conference = self.get_conference()
        if not conference.abstract_submission_open:
            messages.error(self.request, "Abstract submission is currently closed.")
            return redirect('conference:abstract_submit')

        abstract = form.save(commit=False)
        abstract.conference = conference
        abstract.save()

        self.request.session['abstract_ref'] = abstract.reference_number
        logger.info(f"Abstract submitted: {abstract.reference_number} by {abstract.author_name}")
        return redirect('conference:abstract_success')

    def form_invalid(self, form):
        messages.error(self.request, "Please correct the errors below.")
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse('conference:abstract_success')


class AbstractSuccessView(TemplateView):
    template_name = 'conference/abstract_success.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['reference'] = self.request.session.get('abstract_ref', '')
        context['conference'] = get_active_conference()
        return context


# ─── Registration ─────────────────────────────────────────────────────────────

class RegistrationView(FormView):
    template_name = 'conference/registration.html'

    def get_conference(self):
        return get_active_conference()

    def dispatch(self, request, *args, **kwargs):
        if not self.get_conference():
            return _no_conference_redirect()
        return super().dispatch(request, *args, **kwargs)

    def get_form(self, form_class=None):
        conference = self.get_conference()
        return RegistrationForm(conference, **self.get_form_kwargs())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        conference = self.get_conference()
        context['conference'] = conference
        context['categories'] = conference.registration_categories.filter(is_active=True)
        context['is_early_bird'] = (
            conference.early_bird_deadline and
            timezone.now().date() <= conference.early_bird_deadline
        )
        if not conference.registration_open:
            context['registration_closed'] = True
        return context

    def form_valid(self, form):
        conference = self.get_conference()
        if not conference.registration_open:
            messages.error(self.request, "Registration is currently closed.")
            return redirect('conference:register')

        registration = form.save(commit=False)
        registration.conference = conference
        # Set amount based on current fee (early bird or regular)
        category = form.cleaned_data['category']
        registration.amount = category.current_fee(conference)
        registration.save()

        # If fee is 0 (free / waived), confirm immediately
        if registration.amount == 0:
            registration.payment_status = 'confirmed'
            registration.payment_date = timezone.now()
            registration.save()
            self.request.session['ticket_id'] = registration.ticket_id
            return redirect('conference:registration_success')

        # Manual bank transfer — save pending, show instructions
        if registration.payment_method == 'manual':
            self.request.session['ticket_id'] = registration.ticket_id
            return redirect('conference:registration_success')

        # Initialize Paystack payment
        try:
            paystack = PaystackService()
            reference = f"ANC-REG-{registration.ticket_id}-{uuid.uuid4().hex[:8].upper()}"
            registration.paystack_reference = reference
            registration.save()

            callback_url = self.request.build_absolute_uri(
                reverse('conference:payment_verify', args=[registration.ticket_id])
            )
            response = paystack.initialize_transaction(
                email=registration.email,
                amount=float(registration.amount),
                reference=reference,
                callback_url=callback_url,
                metadata={
                    'ticket_id': registration.ticket_id,
                    'full_name': registration.full_name,
                    'category': category.name,
                    'conference': conference.name,
                }
            )

            if response.get('status'):
                return redirect(response['data']['authorization_url'])
            else:
                logger.error(f"Paystack init failed: {response}")
                messages.error(self.request, "Payment initialization failed. Please try again.")
                registration.delete()
                return redirect('conference:register')

        except Exception as e:
            logger.error(f"Payment error for {registration.ticket_id}: {e}")
            messages.error(self.request, "An error occurred. Please try again.")
            registration.delete()
            return redirect('conference:register')

    def form_invalid(self, form):
        messages.error(self.request, "Please correct the errors below.")
        return super().form_invalid(form)


class StakeholderRegistrationView(RegistrationView):
    """Private, fee-free registration for stakeholders.

    Reached only via /register/stakeholder/<token>/ where the token matches the
    active conference's ``stakeholder_access_token`` — the link is emailed
    directly to stakeholders and is not linked anywhere public. No fees are
    shown and no payment is taken; the registration is saved as a waived
    (complimentary) stakeholder registration and confirmed immediately.
    """
    template_name = 'conference/stakeholder_registration.html'

    def dispatch(self, request, *args, **kwargs):
        conference = self.get_conference()
        if conference and str(kwargs.get('token')) != str(conference.stakeholder_access_token):
            raise Http404("Invalid stakeholder registration link.")
        return super().dispatch(request, *args, **kwargs)

    def get_form(self, form_class=None):
        return StakeholderRegistrationForm(self.get_conference(), **self.get_form_kwargs())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_stakeholder'] = True
        return context

    def form_valid(self, form):
        conference = self.get_conference()
        stakeholder_url = reverse('conference:stakeholder_register', args=[conference.stakeholder_access_token])
        if not conference.registration_open:
            messages.error(self.request, "Registration is currently closed.")
            return redirect(stakeholder_url)

        registration = form.save(commit=False)
        registration.conference = conference
        registration.is_stakeholder = True
        registration.amount = 0
        registration.payment_status = 'waived'
        registration.payment_date = timezone.now()
        registration.save()

        # Stakeholders get the fee-free welcome email (not the payment receipt).
        try:
            from .emails import send_welcome
            send_welcome(registration)
        except Exception as exc:
            logger.error("Failed to send stakeholder welcome email for %s: %s",
                         registration.ticket_id, exc, exc_info=True)

        logger.info("Stakeholder registration captured: %s (%s)",
                    registration.ticket_id, registration.organization)
        self.request.session['ticket_id'] = registration.ticket_id
        return redirect('conference:registration_success')


def payment_verify(request, ticket_id):
    """Paystack callback: verify payment and confirm registration"""
    registration = get_object_or_404(Registration, ticket_id=ticket_id)
    reference = request.GET.get('reference') or registration.paystack_reference

    if registration.payment_status == 'confirmed':
        request.session['ticket_id'] = ticket_id
        return redirect('conference:registration_success')

    try:
        paystack = PaystackService()
        result = paystack.verify_transaction(reference)

        if result.get('status') and result['data']['status'] == 'success':
            registration.payment_status = 'confirmed'
            registration.paystack_transaction_id = str(result['data'].get('id', ''))
            registration.payment_date = timezone.now()
            registration.save()
            logger.info(f"Payment confirmed: {ticket_id}")
            request.session['ticket_id'] = ticket_id
            return redirect('conference:registration_success')
        else:
            registration.payment_status = 'failed'
            registration.save()
            messages.error(request, "Payment was not successful. Please try again.")
            return redirect('conference:register')

    except Exception as e:
        logger.error(f"Verification error for {ticket_id}: {e}")
        messages.error(request, "Could not verify payment. Contact support.")
        return redirect('conference:register')


class RegistrationSuccessView(TemplateView):
    template_name = 'conference/registration_success.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ticket_id = self.request.session.get('ticket_id')
        if ticket_id:
            context['registration'] = Registration.objects.filter(ticket_id=ticket_id).first()
        context['conference'] = get_active_conference()
        return context


def ticket_verify(request, ticket_id):
    """Public ticket verification"""
    registration = Registration.objects.filter(ticket_id=ticket_id.upper(), payment_status='confirmed').first()
    return render(request, 'conference/ticket_verify.html', {
        'registration': registration,
        'ticket_id': ticket_id.upper(),
        'conference': get_active_conference(),
    })


# ─── Programme ────────────────────────────────────────────────────────────────

class ProgramView(TemplateView):
    template_name = 'conference/program.html'

    def get(self, request, *args, **kwargs):
        if not get_active_conference():
            return _no_conference_redirect()
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        conference = get_active_conference()
        context['conference'] = conference
        context['program_days'] = conference.program_days.filter(
            is_active=True
        ).prefetch_related('sessions__speakers')
        return context


# ─── Exhibitors ───────────────────────────────────────────────────────────────

class ExhibitorsView(TemplateView):
    template_name = 'conference/exhibitors.html'

    def get(self, request, *args, **kwargs):
        if not get_active_conference():
            return _no_conference_redirect()
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        conference = get_active_conference()
        context['conference'] = conference
        context['packages'] = conference.exhibitor_packages.filter(is_active=True)
        context['showcase_items'] = ExhibitorShowcase.objects.filter(
            exhibitor__conference=conference,
            exhibitor__payment_status='confirmed',
            is_approved=True,
            is_active=True,
        ).select_related('exhibitor')
        return context


class ExhibitorRegistrationView(FormView):
    template_name = 'conference/exhibitor_register.html'

    def get_conference(self):
        return get_active_conference()

    def dispatch(self, request, *args, **kwargs):
        if not self.get_conference():
            return _no_conference_redirect()
        return super().dispatch(request, *args, **kwargs)

    def get_form(self, form_class=None):
        return ExhibitorRegistrationForm(self.get_conference(), **self.get_form_kwargs())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        conference = self.get_conference()
        context['conference'] = conference
        context['packages'] = conference.exhibitor_packages.filter(is_active=True)
        return context

    def form_valid(self, form):
        conference = self.get_conference()

        exhibitor = form.save(commit=False)
        exhibitor.conference = conference
        package = form.cleaned_data['package']
        exhibitor.amount = package.price
        exhibitor.save()

        # Free package — confirm immediately
        if exhibitor.amount == 0:
            exhibitor.payment_status = 'confirmed'
            exhibitor.payment_date = timezone.now()
            exhibitor.save()
            self.request.session['exhibitor_token'] = str(exhibitor.access_token)
            return redirect('conference:exhibitor_register_success')

        # Manual bank transfer — save pending, show instructions
        if exhibitor.payment_method == 'manual':
            self.request.session['exhibitor_token'] = str(exhibitor.access_token)
            return redirect('conference:exhibitor_register_success')

        # Initialize Paystack payment
        try:
            paystack = PaystackService()
            reference = f"ANC-EXH-{exhibitor.reference}-{uuid.uuid4().hex[:8].upper()}"
            exhibitor.paystack_reference = reference
            exhibitor.save()

            callback_url = self.request.build_absolute_uri(
                reverse('conference:exhibitor_payment_verify', args=[exhibitor.access_token])
            )
            response = paystack.initialize_transaction(
                email=exhibitor.email,
                amount=float(exhibitor.amount),
                reference=reference,
                callback_url=callback_url,
                metadata={
                    'reference': exhibitor.reference,
                    'company_name': exhibitor.company_name,
                    'package': package.name,
                    'conference': conference.name,
                }
            )

            if response.get('status'):
                return redirect(response['data']['authorization_url'])
            else:
                logger.error(f"Paystack init failed (exhibitor): {response}")
                messages.error(self.request, "Payment initialization failed. Please try again.")
                exhibitor.delete()
                return redirect('conference:exhibitor_register')

        except Exception as e:
            logger.error(f"Payment error for exhibitor {exhibitor.reference}: {e}")
            messages.error(self.request, "An error occurred. Please try again.")
            exhibitor.delete()
            return redirect('conference:exhibitor_register')

    def form_invalid(self, form):
        messages.error(self.request, "Please correct the errors below.")
        return super().form_invalid(form)


def exhibitor_payment_verify(request, token):
    """Paystack callback: verify payment and confirm exhibitor."""
    exhibitor = get_object_or_404(Exhibitor, access_token=token)
    reference = request.GET.get('reference') or exhibitor.paystack_reference

    if exhibitor.payment_status == 'confirmed':
        request.session['exhibitor_token'] = str(exhibitor.access_token)
        return redirect('conference:exhibitor_register_success')

    try:
        paystack = PaystackService()
        result = paystack.verify_transaction(reference)

        if result.get('status') and result['data']['status'] == 'success':
            exhibitor.payment_status = 'confirmed'
            exhibitor.paystack_transaction_id = str(result['data'].get('id', ''))
            exhibitor.payment_date = timezone.now()
            exhibitor.save()
            logger.info(f"Exhibitor payment confirmed: {exhibitor.reference}")
            request.session['exhibitor_token'] = str(exhibitor.access_token)
            return redirect('conference:exhibitor_register_success')
        else:
            exhibitor.payment_status = 'failed'
            exhibitor.save()
            messages.error(request, "Payment was not successful. Please try again.")
            return redirect('conference:exhibitor_register')

    except Exception as e:
        logger.error(f"Exhibitor verification error for {exhibitor.reference}: {e}")
        messages.error(request, "Could not verify payment. Contact support.")
        return redirect('conference:exhibitor_register')


class ExhibitorRegistrationSuccessView(TemplateView):
    template_name = 'conference/exhibitor_register_success.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        token = self.request.session.get('exhibitor_token')
        if token:
            context['exhibitor'] = Exhibitor.objects.filter(access_token=token).first()
        context['conference'] = get_active_conference()
        return context


class ExhibitorShowcaseView(View):
    """Private token portal for an exhibitor to manage their showcase items."""
    template_name = 'conference/exhibitor_showcase.html'

    def get_exhibitor(self, token):
        return get_object_or_404(Exhibitor, access_token=token)

    def get(self, request, token):
        exhibitor = self.get_exhibitor(token)
        return render(request, self.template_name, {
            'exhibitor': exhibitor,
            'conference': get_active_conference(),
            'items': exhibitor.showcase_items.all(),
            'form': ExhibitorShowcaseForm(),
        })

    def post(self, request, token):
        exhibitor = self.get_exhibitor(token)
        if not exhibitor.is_confirmed:
            messages.error(request, "Your payment must be confirmed before you can add showcase items.")
            return redirect('conference:exhibitor_showcase', token=token)

        form = ExhibitorShowcaseForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.exhibitor = exhibitor
            item.is_approved = False
            item.save()
            messages.success(request, "Item submitted! It will appear publicly once an admin approves it.")
            return redirect('conference:exhibitor_showcase', token=token)

        messages.error(request, "Please correct the errors below.")
        return render(request, self.template_name, {
            'exhibitor': exhibitor,
            'conference': get_active_conference(),
            'items': exhibitor.showcase_items.all(),
            'form': form,
        })


@require_POST
def exhibitor_showcase_delete(request, token, pk):
    """Let an exhibitor remove one of their own showcase items via their token."""
    exhibitor = get_object_or_404(Exhibitor, access_token=token)
    item = get_object_or_404(ExhibitorShowcase, pk=pk, exhibitor=exhibitor)
    item.delete()
    messages.success(request, "Item removed.")
    return redirect('conference:exhibitor_showcase', token=token)


# ─── Payment Verification ─────────────────────────────────────────────────────

# Magic-link signing config for non-staff verifiers.
PV_SALT = 'conference.payment_verification.magic-link'
PV_MAX_AGE = 60 * 60 * 2  # links valid for 2 hours
PV_SESSION_KEY = 'pv_verifier_email'


def _active_verifier_email(request):
    """Return the session's verifier email if it still maps to an active
    PaymentVerifier, else None (so revoking access ends the session too)."""
    email = request.session.get(PV_SESSION_KEY)
    if email and PaymentVerifier.objects.filter(email__iexact=email, is_active=True).exists():
        return email
    return None


def _is_pv_staff(request):
    """Only superadmins get account-based access; other staff do not."""
    return request.user.is_authenticated and request.user.is_superuser


def payment_verification_login(request, token):
    """Consume a magic link: validate the signed token and grant a session."""
    try:
        email = signing.loads(token, salt=PV_SALT, max_age=PV_MAX_AGE)
    except signing.SignatureExpired:
        messages.error(request, "That sign-in link has expired. Please request a new one.")
        return redirect('conference:payment_verification')
    except signing.BadSignature:
        messages.error(request, "That sign-in link is invalid.")
        return redirect('conference:payment_verification')

    verifier = PaymentVerifier.objects.filter(email__iexact=email, is_active=True).first()
    if not verifier:
        messages.error(request, "Access for this email is no longer active.")
        return redirect('conference:payment_verification')

    request.session[PV_SESSION_KEY] = verifier.email
    PaymentVerifier.objects.filter(pk=verifier.pk).update(last_login_at=timezone.now())
    messages.success(request, f"Welcome, {verifier.name or verifier.email}. You now have verification access.")
    return redirect('conference:payment_verification')


@require_POST
def payment_verification_logout(request):
    """End a verifier's session."""
    request.session.pop(PV_SESSION_KEY, None)
    messages.info(request, "You have been signed out of Payment Verification.")
    return redirect('conference:payment_verification')


def payment_verification(request):
    """
    Tool to verify and confirm payments for both registrations and exhibitors.

    Access is restricted to superadmins (Django superusers), or to people on
    the PaymentVerifier allowlist who sign in via a magic link emailed to them.
    Other staff accounts have no access.

    * Look up a record by its Ticket ID (registrations, e.g. ANC2026-T00001)
      or Reference (exhibitors, e.g. EXH2026-0001).
    * For Paystack payments still showing as pending, re-verify against the
      Paystack API in case the original callback never completed.
    * For bank transfers, confirm the payment manually once it has been
      checked against the bank that the holder of that Ticket ID / Reference
      actually paid.

    Confirming a registration fires the post_save signal that emails the
    participant their receipt and welcome message.
    """
    conference = get_active_conference()
    is_superadmin = _is_pv_staff(request)
    verifier_email = _active_verifier_email(request)
    authorized = is_superadmin or verifier_email is not None

    # ── Not authorized: show / handle the magic-link request form ──────────────
    if not authorized:
        if request.method == 'POST' and request.POST.get('action') == 'request_access':
            email = (request.POST.get('email') or '').strip()

            # This is a private tool with a small, known allowlist, so we give
            # explicit feedback (rather than hiding whether the email is listed)
            # — otherwise a missing entry or an SMTP error looks like success.
            verifier = PaymentVerifier.objects.filter(email__iexact=email).first()
            if not verifier:
                messages.error(
                    request,
                    f"“{email}” is not authorized for payment verification. "
                    "Ask an administrator to add it under Payment Verifiers.",
                )
                return redirect('conference:payment_verification')
            if not verifier.is_active:
                messages.error(
                    request,
                    f"Access for “{email}” has been deactivated. "
                    "Ask an administrator to re-activate it.",
                )
                return redirect('conference:payment_verification')

            try:
                token = signing.dumps(verifier.email, salt=PV_SALT)
                login_url = request.build_absolute_uri(
                    reverse('conference:payment_verification_login', args=[token])
                )
                from .emails import send_verifier_magic_link
                send_verifier_magic_link(verifier, login_url, conference)
            except Exception as exc:
                logger.error("Failed to send verifier magic link to %s: %s", email, exc, exc_info=True)
                messages.error(
                    request,
                    "We couldn't send the sign-in link due to a mail server error. "
                    "Please try again, or contact the site administrator.",
                )
                return redirect('conference:payment_verification')

            messages.success(
                request,
                f"A sign-in link has been sent to {verifier.email}. "
                "It expires in 2 hours — check your inbox (and spam folder).",
            )
            return redirect('conference:payment_verification')

        return render(request, 'conference/payment_verification.html', {
            'conference': conference,
            'needs_access': True,
        })

    # ── Authorized: lookup + confirm logic ─────────────────────────────────────
    context = {
        'conference': conference,
        'authorized': True,
        'is_superadmin': is_superadmin,
        'verifier_email': verifier_email,
    }

    query = (request.GET.get('q') or request.POST.get('q') or '').strip()
    action = request.POST.get('action', '')

    record = None
    record_type = None
    if query:
        record = Registration.objects.filter(ticket_id__iexact=query).first()
        if record:
            record_type = 'registration'
        else:
            record = Exhibitor.objects.filter(reference__iexact=query).first()
            if record:
                record_type = 'exhibitor'

    actor = str(request.user) if is_superadmin else f"verifier:{verifier_email}"

    if request.method == 'POST' and action and record:
        label = query.upper()
        if record.payment_status == 'confirmed':
            messages.info(request, f"{label} is already confirmed.")

        elif action == 'confirm_manual':
            record.payment_status = 'confirmed'
            if not record.payment_date:
                record.payment_date = timezone.now()
            record.save()
            logger.info("Bank transfer confirmed for %s by %s", label, actor)
            messages.success(
                request,
                f"Bank transfer for {label} confirmed. "
                f"{'A receipt and welcome email have been sent.' if record_type == 'registration' else ''}".strip(),
            )

        elif action == 'verify_paystack':
            reference = record.paystack_reference
            if not reference:
                messages.error(request, f"{label} has no Paystack reference to verify.")
            else:
                try:
                    paystack = PaystackService()
                    result = paystack.verify_transaction(reference)
                    if result.get('status') and result['data'].get('status') == 'success':
                        record.payment_status = 'confirmed'
                        record.paystack_transaction_id = str(result['data'].get('id', ''))
                        record.payment_date = timezone.now()
                        record.save()
                        logger.info("Paystack payment verified for %s by %s", label, actor)
                        messages.success(
                            request,
                            f"Paystack payment for {label} verified and confirmed. "
                            f"{'A receipt and welcome email have been sent.' if record_type == 'registration' else ''}".strip(),
                        )
                    else:
                        gateway_status = (result.get('data') or {}).get('status', 'unknown')
                        messages.warning(
                            request,
                            f"Paystack reports this payment as '{gateway_status}', not successful. "
                            "It has not been confirmed.",
                        )
                except Exception as exc:
                    logger.error("Paystack verification error for %s: %s", label, exc)
                    messages.error(request, "Could not reach Paystack to verify. Please try again.")

        if record.pk:
            record.refresh_from_db()

    # ── Paginated list of registrations awaiting confirmation ──────────────────
    # Built after the confirm logic so a just-confirmed registration drops off.
    unconfirmed_qs = (
        Registration.objects
        .exclude(payment_status__in=['confirmed', 'waived', 'cancelled'])
        .select_related('category')
        .order_by('-registered_at')
    )
    if conference:
        unconfirmed_qs = unconfirmed_qs.filter(conference=conference)

    paginator = Paginator(unconfirmed_qs, 20)
    page_obj = paginator.get_page(request.GET.get('page') or request.POST.get('page'))

    context.update({
        'query': query,
        'searched': bool(query),
        'record': record,
        'record_type': record_type,
        'page_obj': page_obj,
        'unconfirmed_total': paginator.count,
    })
    return render(request, 'conference/payment_verification.html', context)


# ─── Abstract review (staff + email exceptions) ───────────────────────────────

import csv
from functools import wraps

# Magic-link access for non-staff reviewers on the allowlist (AbstractReviewer).
AR_SALT = 'conference.abstract_review.magic-link'
AR_MAX_AGE = 60 * 60 * 2  # links valid for 2 hours
AR_SESSION_KEY = 'ar_reviewer_email'


def _active_abstract_reviewer_email(request):
    """Return the session's reviewer email if it still maps to an active
    AbstractReviewer, else None (so revoking access ends the session too)."""
    email = request.session.get(AR_SESSION_KEY)
    if email and AbstractReviewer.objects.filter(email__iexact=email, is_active=True).exists():
        return email
    return None


def _can_view_abstracts(request):
    """Staff/superusers always qualify; otherwise an allowlisted reviewer with
    an active magic-link session does."""
    user = request.user
    if user.is_authenticated and (user.is_staff or user.is_superuser):
        return True
    return _active_abstract_reviewer_email(request) is not None


def issue_abstract_reviewer_link(request, reviewer):
    """Build a signed magic link for a reviewer and email it. Records when the
    link was sent. Raises on mail failure so callers can report it."""
    from .emails import send_abstract_reviewer_magic_link
    token = signing.dumps(reviewer.email, salt=AR_SALT)
    login_url = request.build_absolute_uri(
        reverse('conference:abstract_reviewer_login', args=[token])
    )
    send_abstract_reviewer_magic_link(reviewer, login_url, get_active_conference())
    AbstractReviewer.objects.filter(pk=reviewer.pk).update(link_sent_at=timezone.now())


def abstract_access_required(view_func):
    """Allow staff or an allowlisted reviewer; otherwise send them to the
    access page where they can request a fresh sign-in link."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if _can_view_abstracts(request):
            return view_func(request, *args, **kwargs)
        return redirect('conference:abstract_access')
    return wrapper


@abstract_access_required
def abstract_list(request):
    """
    Listing of submitted abstracts for the active conference.

    Open to staff/superusers and to allowlisted reviewers (AbstractReviewer)
    who signed in via an emailed magic link. Supports searching and filtering
    by status, thematic area and presentation format, plus a CSV export of the
    current selection.
    """
    conference = get_active_conference()

    abstracts = (
        AbstractSubmission.objects
        .filter(conference=conference)
        .select_related('thematic_area')
    ) if conference else AbstractSubmission.objects.none()

    # ── Filters ────────────────────────────────────────────────────────────────
    query = (request.GET.get('q') or '').strip()
    status = (request.GET.get('status') or '').strip()
    thematic_area = (request.GET.get('thematic_area') or '').strip()
    fmt = (request.GET.get('format') or '').strip()

    if query:
        from django.db.models import Q
        abstracts = abstracts.filter(
            Q(title__icontains=query) |
            Q(author_name__icontains=query) |
            Q(co_authors__icontains=query) |
            Q(institution__icontains=query) |
            Q(reference_number__icontains=query) |
            Q(email__icontains=query) |
            Q(keywords__icontains=query)
        )
    if status:
        abstracts = abstracts.filter(status=status)
    if thematic_area:
        abstracts = abstracts.filter(thematic_area_id=thematic_area)
    if fmt:
        abstracts = abstracts.filter(presentation_format=fmt)

    # ── CSV export (respects the active filters) ───────────────────────────────
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        stamp = timezone.now().strftime('%Y%m%d')
        response['Content-Disposition'] = f'attachment; filename="abstracts_{stamp}.csv"'
        writer = csv.writer(response)
        writer.writerow([
            'Reference', 'Title', 'Presenting Author', 'Co-Authors',
            'Institution', 'Email', 'Phone', 'Thematic Area', 'Keywords',
            'Format', 'Status', 'Score', 'Word Count', 'Has File',
            'Submitted At',
        ])
        for a in abstracts:
            writer.writerow([
                a.reference_number, a.title, a.author_name, a.co_authors,
                a.institution, a.email, a.phone,
                a.thematic_area.name if a.thematic_area else '',
                a.keywords, a.get_presentation_format_display(),
                a.get_status_display(), a.score if a.score is not None else '',
                a.word_count(), 'Yes' if a.abstract_file else 'No',
                a.submitted_at.strftime('%Y-%m-%d %H:%M'),
            ])
        return response

    # ── Counts by status (for the summary chips) ───────────────────────────────
    from django.db.models import Count
    base_qs = (
        AbstractSubmission.objects.filter(conference=conference)
        if conference else AbstractSubmission.objects.none()
    )
    counts_by_status = {
        row['status']: row['count']
        for row in base_qs.values('status').annotate(count=Count('id'))
    }
    status_summary = [
        {'value': value, 'label': label, 'count': counts_by_status.get(value, 0)}
        for value, label in AbstractSubmission.STATUS_CHOICES
    ]

    paginator = Paginator(abstracts, 25)
    page_obj = paginator.get_page(request.GET.get('page'))

    # Preserve filters across pagination links
    params = request.GET.copy()
    params.pop('page', None)
    querystring = params.urlencode()

    context = {
        'conference': conference,
        'page_obj': page_obj,
        'total': paginator.count,
        'status_summary': status_summary,
        'status_choices': AbstractSubmission.STATUS_CHOICES,
        'format_choices': AbstractSubmission.PRESENTATION_FORMAT_CHOICES,
        'thematic_areas': AbstractThematicArea.objects.all(),
        'query': query,
        'sel_status': status,
        'sel_thematic_area': thematic_area,
        'sel_format': fmt,
        'querystring': querystring,
        'reviewer_email': _active_abstract_reviewer_email(request),
    }
    return render(request, 'conference/abstract_list.html', context)


@abstract_access_required
def abstract_detail(request, pk):
    """Staff-only full view of a single submitted abstract."""
    abstract = get_object_or_404(
        AbstractSubmission.objects.select_related('thematic_area', 'conference'),
        pk=pk,
    )
    return render(request, 'conference/abstract_detail.html', {
        'conference': abstract.conference,
        'abstract': abstract,
    })


@abstract_access_required
def abstract_download(request, pk):
    """
    Staff-only download of an abstract's uploaded file.

    Serving through this view (rather than linking the raw media URL) keeps
    the files behind the ``is_staff`` gate and forces an attachment download.
    """
    abstract = get_object_or_404(AbstractSubmission, pk=pk)
    if not abstract.abstract_file:
        raise Http404("This abstract has no uploaded file.")

    import os
    filename = os.path.basename(abstract.abstract_file.name)
    # Give the download a meaningful name based on the reference number,
    # keeping the original extension.
    ext = os.path.splitext(filename)[1]
    download_name = f"{abstract.reference_number}{ext}" if abstract.reference_number else filename
    try:
        return FileResponse(
            abstract.abstract_file.open('rb'),
            as_attachment=True,
            filename=download_name,
        )
    except FileNotFoundError:
        raise Http404("The file for this abstract is missing from storage.")


def abstract_access(request):
    """Landing/gate for the Abstract Review page.

    Staff and signed-in reviewers are sent straight through. Everyone else
    sees a page where an allowlisted reviewer can request a fresh sign-in
    link (useful when a link has expired).
    """
    if _can_view_abstracts(request):
        return redirect('conference:abstract_list')

    conference = get_active_conference()

    if request.method == 'POST' and request.POST.get('action') == 'request_access':
        email = (request.POST.get('email') or '').strip()
        reviewer = AbstractReviewer.objects.filter(email__iexact=email).first()
        if not reviewer:
            messages.error(
                request,
                f"“{email}” is not on the abstract-review access list. "
                "Ask an administrator to add it under Abstract Reviewers.",
            )
            return redirect('conference:abstract_access')
        if not reviewer.is_active:
            messages.error(
                request,
                f"Access for “{email}” has been deactivated. "
                "Ask an administrator to re-activate it.",
            )
            return redirect('conference:abstract_access')
        try:
            issue_abstract_reviewer_link(request, reviewer)
        except Exception as exc:
            logger.error("Failed to send abstract reviewer link to %s: %s", email, exc, exc_info=True)
            messages.error(
                request,
                "We couldn't send the sign-in link due to a mail server error. "
                "Please try again, or contact the site administrator.",
            )
            return redirect('conference:abstract_access')
        messages.success(
            request,
            f"A sign-in link has been sent to {reviewer.email}. "
            "It expires in 2 hours — check your inbox (and spam folder).",
        )
        return redirect('conference:abstract_access')

    return render(request, 'conference/abstract_access.html', {
        'conference': conference,
    })


def abstract_reviewer_login(request, token):
    """Consume a magic link: validate the signed token and grant a session."""
    try:
        email = signing.loads(token, salt=AR_SALT, max_age=AR_MAX_AGE)
    except signing.SignatureExpired:
        messages.error(request, "That access link has expired. Please request a new one.")
        return redirect('conference:abstract_access')
    except signing.BadSignature:
        messages.error(request, "That access link is invalid.")
        return redirect('conference:abstract_access')

    reviewer = AbstractReviewer.objects.filter(email__iexact=email, is_active=True).first()
    if not reviewer:
        messages.error(request, "Access for this email is no longer active.")
        return redirect('conference:abstract_access')

    request.session[AR_SESSION_KEY] = reviewer.email
    AbstractReviewer.objects.filter(pk=reviewer.pk).update(last_login_at=timezone.now())
    messages.success(request, f"Welcome, {reviewer.name or reviewer.email}. You can now view the submitted abstracts.")
    return redirect('conference:abstract_list')


@require_POST
def abstract_reviewer_logout(request):
    """End a reviewer's session."""
    request.session.pop(AR_SESSION_KEY, None)
    messages.info(request, "You have been signed out of Abstract Review.")
    return redirect('conference:abstract_access')


# ─── Frontend content editor (staff only) ─────────────────────────────────────

@staff_member_required
@require_POST
def save_content_block(request):
    """Save an inline-edited content block. Staff only."""
    try:
        data = json.loads(request.body)
        key = data.get('key', '').strip()
        content = data.get('content', '')
        if not key:
            return JsonResponse({'error': 'Key is required'}, status=400)
        ContentBlock.objects.update_or_create(
            key=key,
            defaults={'content': content, 'updated_by': request.user},
        )
        return JsonResponse({'success': True})
    except (json.JSONDecodeError, Exception) as exc:
        logger.error('Content block save error: %s', exc)
        return JsonResponse({'error': str(exc)}, status=500)


# ─── Category fee API (for dynamic price display on registration form) ─────────

def category_fee_api(request, category_id):
    """Return current fee for a given category (JSON)"""
    conference = get_active_conference()
    try:
        cat = RegistrationCategory.objects.get(pk=category_id, conference=conference)
        fee = cat.current_fee(conference)
        is_early = (
            conference.early_bird_deadline and
            cat.early_bird_fee and
            timezone.now().date() <= conference.early_bird_deadline
        )
        return JsonResponse({
            'fee': float(fee),
            'formatted': f"₦{fee:,.0f}",
            'is_early_bird': is_early,
            'includes': cat.get_includes_list(),
        })
    except RegistrationCategory.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)
