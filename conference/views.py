import uuid
import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView, FormView, DetailView
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.conf import settings

from .models import (
    Conference, Speaker, AbstractSubmission, RegistrationCategory,
    Registration, ProgramDay, Sponsor, KeyMessage
)
from .forms import AbstractSubmissionForm, RegistrationForm
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
