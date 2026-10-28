import json
from datetime import date
from decimal import Decimal
from unittest import mock

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import MembershipType, PartnerOrganization, Payment, Sector


def set_paid_mode():
    from website.models import SiteSettings
    site_settings = SiteSettings.objects.first() or SiteSettings.objects.create()
    site_settings.registration_mode = 'paid'
    site_settings.save()


SIGNUP = {
    'username': 'ada',
    'first_name': 'Ada',
    'last_name': 'Obi',
    'email': 'ada@example.com',
    'phone_number': '08000000000',
    'position': 'Director',
    'partner_organization': 'other',
    'other_organization': 'Cassava Growers Ltd',
    'password1': 'a-Strong-pass-123',
    'password2': 'a-Strong-pass-123',
}


class OrganizationSignupTests(TestCase):

    def setUp(self):
        set_paid_mode()
        self.private = Sector.objects.get(name='Private Sector')
        self.sme, _ = MembershipType.objects.update_or_create(
            code='sme', defaults={'sector': self.private, 'name': 'Medium Scale', 'registration_fee': Decimal('30000'),
                                  'annual_dues': Decimal('15000'), 'is_active': True})

    def signup(self, **overrides):
        category = overrides.pop('membership_category', self.sme)
        data = {**SIGNUP, 'sector': category.sector_id, 'membership_category': category.pk, **overrides}
        return self.client.post(reverse('dashboard:register'), data)

    def admin_user(self):
        return User.objects.get(email='ada@example.com')

    def add_member(self, email, first_name='Member'):
        return self.client.post(reverse('dashboard:organization_members'), {
            'action': 'add', 'first_name': first_name, 'last_name': 'Test',
            'email': email, 'phone_number': '0801', 'position': 'Officer',
        })

    def test_signup_creates_organization_with_admin(self):
        response = self.signup()
        self.assertRedirects(response, reverse('dashboard:payment_selection'))

        org = PartnerOrganization.objects.get(name='Cassava Growers Ltd')
        self.assertEqual(org.membership_category, self.sme)
        profile = self.admin_user().profile
        self.assertEqual(profile.partner_organization, org)
        self.assertTrue(profile.is_partner_admin)
        self.assertEqual(self.admin_user().membership.membership_type, 'organization')

    def test_organization_that_has_members_cannot_sign_up_again(self):
        self.signup()
        self.client.logout()
        response = self.signup(username='bola', email='bola@example.com',
                               other_organization='cassava growers ltd')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'already signed up')
        self.assertFalse(User.objects.filter(email='bola@example.com').exists())

    def test_admin_can_add_two_members_only(self):
        self.signup()
        self.add_member('m1@example.com')
        response = self.add_member('m2@example.com')
        self.assertContains(response, "We've emailed this link to m2@example.com")
        self.add_member('m3@example.com')

        org = PartnerOrganization.objects.get(name='Cassava Growers Ltd')
        self.assertEqual(org.member_profiles().count(), 3)
        self.assertFalse(User.objects.filter(email='m3@example.com').exists())
        member = User.objects.get(email='m1@example.com')
        self.assertFalse(member.has_usable_password())
        self.assertFalse(member.profile.is_partner_admin)

    def test_removing_a_member_frees_a_place(self):
        self.signup()
        self.add_member('m1@example.com')
        self.add_member('m2@example.com')
        m1 = User.objects.get(email='m1@example.com')
        self.client.post(reverse('dashboard:organization_members'), {'action': 'remove', 'user_id': m1.pk})
        m1.refresh_from_db()
        self.assertFalse(m1.is_active)
        self.add_member('m3@example.com')
        self.assertTrue(User.objects.filter(email='m3@example.com').exists())

    def test_member_cannot_add_members_or_pay(self):
        self.signup()
        self.add_member('m1@example.com')
        member = User.objects.get(email='m1@example.com')
        self.client.force_login(member)

        self.add_member('m2@example.com')
        self.assertFalse(User.objects.filter(email='m2@example.com').exists())

        response = self.client.post(reverse('dashboard:initiate_payment'),
                                    json.dumps({'payment_purpose': 'registration'}),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 403)

    def test_set_password_link_lets_member_sign_in(self):
        self.signup()
        response = self.add_member('m1@example.com')
        link = response.context['new_member_link']['link']
        path = link.split('testserver', 1)[1]

        set_page = self.client.get(path, follow=True)
        self.client.post(set_page.redirect_chain[-1][0], {
            'new_password1': 'Another-pass-456', 'new_password2': 'Another-pass-456',
        })
        self.assertTrue(User.objects.get(email='m1@example.com').check_password('Another-pass-456'))

    @mock.patch('dashboard.paystack_service.PaystackService.initialize_transaction')
    def test_admin_pays_category_price_and_members_get_access(self, initialize):
        initialize.return_value = {'status': True, 'data': {'authorization_url': 'https://pay.example'}}
        self.signup()
        self.add_member('m1@example.com')

        for purpose, price in (('registration', Decimal('30000')), ('annual_dues', Decimal('15000'))):
            response = self.client.post(reverse('dashboard:initiate_payment'),
                                        json.dumps({'payment_purpose': purpose}),
                                        content_type='application/json')
            self.assertEqual(response.status_code, 200, response.content)
            payment = Payment.objects.get(payment_purpose=purpose)
            self.assertEqual(payment.amount, price)
            payment.status = 'successful'
            payment.save()

        member = User.objects.get(email='m1@example.com')
        self.assertTrue(member.membership.registration_paid)
        self.assertEqual(member.membership.annual_dues_paid_for_year, date.today().year)
        self.assertTrue(member.membership.has_platform_access)

        # Someone added after payment starts with the paid membership.
        self.add_member('m2@example.com')
        self.assertTrue(User.objects.get(email='m2@example.com').membership.has_platform_access)

    @mock.patch('dashboard.paystack_service.PaystackService.initialize_transaction')
    def test_type_changed_in_admin_changes_the_price(self, initialize):
        initialize.return_value = {'status': True, 'data': {'authorization_url': 'https://pay.example'}}
        corporate = MembershipType.objects.create(
            sector=self.private, name='Corporate', registration_fee=Decimal('100000'), annual_dues=Decimal('50000'))
        self.signup()
        PartnerOrganization.objects.filter(name='Cassava Growers Ltd').update(membership_category=corporate)

        self.client.post(reverse('dashboard:initiate_payment'),
                         json.dumps({'payment_purpose': 'registration'}),
                         content_type='application/json')
        self.assertEqual(Payment.objects.get().amount, Decimal('100000'))

    @mock.patch('dashboard.paystack_service.PaystackService.initialize_transaction')
    def test_new_type_added_in_admin_is_offered_and_charged(self, initialize):
        initialize.return_value = {'status': True, 'data': {'authorization_url': 'https://pay.example'}}
        cooperative = MembershipType.objects.create(
            sector=self.private, name='Cooperative', description='Farmer cooperatives',
            registration_fee=Decimal('12000'), annual_dues=Decimal('6000'))
        self.assertEqual(cooperative.code, 'cooperative')

        self.assertContains(self.client.get(reverse('dashboard:register')), 'Cooperative')

        self.signup(membership_category=cooperative)
        self.client.post(reverse('dashboard:initiate_payment'),
                         json.dumps({'payment_purpose': 'registration'}),
                         content_type='application/json')
        payment = Payment.objects.get()
        self.assertEqual(payment.amount, Decimal('12000'))
        self.assertIn('COOPERATIVE', payment.paystack_reference)

    def test_inactive_type_is_not_offered_at_signup(self):
        MembershipType.objects.create(sector=self.private, name='Retired', registration_fee=1, annual_dues=1, is_active=False)
        self.assertNotContains(self.client.get(reverse('dashboard:register')), 'Retired')
        retired = MembershipType.objects.get(name='Retired')
        response = self.signup(membership_category=retired)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email='ada@example.com').exists())

    def test_type_in_use_cannot_be_deleted(self):
        from django.db.models import ProtectedError
        self.signup()
        with self.assertRaises(ProtectedError):
            self.sme.delete()

    def test_signup_offers_the_sectors_and_their_options(self):
        page = self.client.get(reverse('dashboard:register')).content.decode()
        for text in ['Public Sector', 'Private Sector', 'NGOs', 'Large Scale', 'Medium Scale', 'Small Scale',
                     'Research Institutes', 'FMARD', 'State Ministries of Agric (ADPs)',
                     'Federal &amp; State Universities', 'Other (please specify)']:
            self.assertIn(text, page)

    def test_category_must_belong_to_the_chosen_sector(self):
        public = Sector.objects.get(name='Public Sector')
        response = self.signup(sector=public.pk)
        self.assertContains(response, 'Choose a category listed under Public Sector')
        self.assertFalse(User.objects.filter(email='ada@example.com').exists())

    def test_other_option_requires_and_saves_details(self):
        other = MembershipType.objects.get(code='public-other')
        response = self.signup(membership_category=other)
        self.assertContains(response, 'Please specify your organization type')

        self.signup(membership_category=other, sector_details='Federal agency')
        org = PartnerOrganization.objects.get(name='Cassava Growers Ltd')
        self.assertEqual(org.membership_category, other)
        self.assertEqual(org.sector_details, 'Federal agency')

    def test_signup_page_shows_no_prices(self):
        page = self.client.get(reverse('dashboard:register'))
        self.assertNotContains(page, '₦')
        self.assertNotContains(page, 'Registration fee')

    def test_details_are_dropped_for_options_that_do_not_ask(self):
        self.signup(sector_details='ignored')
        self.assertEqual(PartnerOrganization.objects.get(name='Cassava Growers Ltd').sector_details, '')


class MembershipEmailTests(TestCase):

    def setUp(self):
        set_paid_mode()
        self.sme = MembershipType.objects.get(code='sme')
        self.sme.registration_fee = Decimal('30000')
        self.sme.annual_dues = Decimal('15000')
        self.sme.save()

    def signup(self):
        return self.client.post(reverse('dashboard:register'), {
            **SIGNUP, 'sector': self.sme.sector_id, 'membership_category': self.sme.pk,
        })

    def pay(self, purpose, **extra):
        membership = User.objects.get(email='ada@example.com').membership
        payment = Payment.objects.create(membership=membership, amount=Decimal('30000'),
                                         payment_purpose=purpose, paystack_reference='ANA-REG-SME-1', **extra)
        with self.captureOnCommitCallbacks(execute=True):
            payment.status = 'successful'
            payment.save()
        return payment

    def test_signup_sends_welcome_email_pointing_to_payment(self):
        from django.core import mail
        self.signup()
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, ['ada@example.com'])
        self.assertIn('Welcome', email.subject)
        self.assertIn(reverse('dashboard:payment_selection'), email.body)
        self.assertIn('Cassava Growers Ltd', email.body)
        self.assertIn('N30,000', email.body)

    def test_free_mode_welcome_email_has_no_payment_prompt(self):
        from django.core import mail
        from website.models import SiteSettings
        SiteSettings.objects.update(registration_mode='free')
        self.signup()
        self.assertIn('already active', mail.outbox[0].body)
        self.assertNotIn(reverse('dashboard:payment_selection'), mail.outbox[0].body)

    def test_registration_payment_sends_confirmation_and_receipt_once(self):
        from django.core import mail
        self.signup()
        mail.outbox.clear()
        payment = self.pay('registration')

        self.assertEqual([m.subject.split()[0] for m in mail.outbox], ['Your', 'Payment'])
        self.assertIn('confirmed', mail.outbox[0].subject)
        receipt = mail.outbox[1]
        self.assertEqual(receipt.to, ['ada@example.com'])
        self.assertIn('ANA-REG-SME-1', receipt.body)
        self.assertIn('N30,000.00', receipt.body)
        self.assertEqual(len(receipt.alternatives), 1)

        # Saving the payment again (e.g. the webhook after the callback) sends nothing more.
        with self.captureOnCommitCallbacks(execute=True):
            payment.save()
        from .emails import send_payment_emails
        self.assertFalse(send_payment_emails(payment.pk))
        self.assertEqual(len(mail.outbox), 2)
        payment.refresh_from_db()
        self.assertIsNotNone(payment.receipt_email_sent_at)

    def test_annual_dues_payment_sends_receipt_only(self):
        from django.core import mail
        self.signup()
        mail.outbox.clear()
        self.pay('annual_dues', subscription_year=date.today().year)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Annual Membership Dues', mail.outbox[0].subject)
        self.assertIn(f'({date.today().year})', mail.outbox[0].body)

    def test_failed_send_can_be_retried(self):
        from django.core import mail
        self.signup()
        mail.outbox.clear()
        with mock.patch('django.core.mail.EmailMultiAlternatives.send', side_effect=OSError('smtp down')):
            payment = self.pay('annual_dues', subscription_year=date.today().year)
        payment.refresh_from_db()
        self.assertIsNone(payment.receipt_email_sent_at)
        # Membership was still updated.
        self.assertEqual(payment.membership.member.membership.annual_dues_paid_for_year, date.today().year)

        from .emails import send_payment_emails
        self.assertTrue(send_payment_emails(payment.pk))
        self.assertEqual(len(mail.outbox), 1)

    def test_signup_succeeds_even_if_welcome_email_fails(self):
        with mock.patch('django.core.mail.EmailMultiAlternatives.send', side_effect=OSError('smtp down')):
            response = self.signup()
        self.assertRedirects(response, reverse('dashboard:payment_selection'))


class MemberInvitationEmailTests(TestCase):

    def setUp(self):
        set_paid_mode()
        sme = MembershipType.objects.get(code='sme')
        self.client.post(reverse('dashboard:register'), {
            **SIGNUP, 'sector': sme.sector_id, 'membership_category': sme.pk,
        })

    def add_member(self):
        return self.client.post(reverse('dashboard:organization_members'), {
            'action': 'add', 'first_name': 'Bola', 'last_name': 'Ade',
            'email': 'bola@example.com', 'phone_number': '0801', 'position': 'Officer',
        })

    def test_added_member_is_emailed_a_working_set_password_link(self):
        from django.core import mail
        mail.outbox.clear()
        response = self.add_member()
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, ['bola@example.com'])
        self.assertIn('Cassava Growers Ltd', email.subject)
        self.assertIn('Ada Obi has added you', email.body)
        link = response.context['new_member_link']['link']
        self.assertIn(link, email.body)

        self.client.logout()
        set_page = self.client.get(link.split('testserver', 1)[1], follow=True)
        self.client.post(set_page.redirect_chain[-1][0], {
            'new_password1': 'Another-pass-456', 'new_password2': 'Another-pass-456',
        })
        self.assertTrue(User.objects.get(email='bola@example.com').check_password('Another-pass-456'))

    def test_resend_emails_a_new_link(self):
        from django.core import mail
        self.add_member()
        mail.outbox.clear()
        member = User.objects.get(email='bola@example.com')
        self.client.post(reverse('dashboard:organization_members'), {'action': 'link', 'user_id': member.pk})
        self.assertEqual([m.to for m in mail.outbox], [['bola@example.com']])

    def test_link_is_shown_to_admin_if_email_fails(self):
        with mock.patch('django.core.mail.EmailMultiAlternatives.send', side_effect=OSError('smtp down')):
            response = self.add_member()
        self.assertTrue(User.objects.filter(email='bola@example.com').exists())
        self.assertFalse(response.context['new_member_link']['emailed'])
        self.assertContains(response, "couldn't email bola@example.com")
        self.assertContains(response, response.context['new_member_link']['link'])
