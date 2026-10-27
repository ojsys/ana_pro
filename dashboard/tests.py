import json
from datetime import date
from decimal import Decimal
from unittest import mock

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import MembershipPricing, PartnerOrganization, Payment


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
    'membership_category': 'sme',
    'password1': 'a-Strong-pass-123',
    'password2': 'a-Strong-pass-123',
}


class OrganizationSignupTests(TestCase):

    def setUp(self):
        set_paid_mode()
        MembershipPricing.objects.update_or_create(
            membership_type='sme', payment_type='registration',
            defaults={'price': Decimal('30000'), 'is_active': True})
        MembershipPricing.objects.update_or_create(
            membership_type='sme', payment_type='annual_dues',
            defaults={'price': Decimal('15000'), 'is_active': True})

    def signup(self, **overrides):
        return self.client.post(reverse('dashboard:register'), {**SIGNUP, **overrides})

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
        self.assertEqual(org.membership_category, 'sme')
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
        self.assertContains(response, 'set their password')
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
    def test_category_changed_in_admin_changes_the_price(self, initialize):
        initialize.return_value = {'status': True, 'data': {'authorization_url': 'https://pay.example'}}
        MembershipPricing.objects.update_or_create(
            membership_type='corporate', payment_type='registration',
            defaults={'price': Decimal('100000'), 'is_active': True})
        self.signup()
        PartnerOrganization.objects.filter(name='Cassava Growers Ltd').update(membership_category='corporate')

        self.client.post(reverse('dashboard:initiate_payment'),
                         json.dumps({'payment_purpose': 'registration'}),
                         content_type='application/json')
        self.assertEqual(Payment.objects.get().amount, Decimal('100000'))
