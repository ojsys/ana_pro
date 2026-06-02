import json
import uuid
import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.views.generic import TemplateView, FormView, DetailView
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.conf import settings

from .models import (
    Conference, Speaker, AbstractSubmission, RegistrationCategory,
    Registration, ProgramDay, Sponsor, KeyMessage, ContentBlock,
    Exhibitor, ExhibitorPackage, ExhibitorShowcase,
)
from .forms import (
    AbstractSubmissionForm, RegistrationForm,
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
