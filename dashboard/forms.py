from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q
from .models import UserProfile, PartnerOrganization, MembershipType


class CustomUserCreationForm(UserCreationForm):
    """
    Organization sign-up form.

    Membership is sold to organizations. Whoever signs an organization up becomes
    its admin and can add up to two colleagues later; an organization that already
    has members cannot be signed up again.
    """
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your first name'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your last name'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address'
        })
    )
    phone_number = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your phone number'
        })
    )
    position = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your job title/position'
        })
    )
    partner_organization = forms.ChoiceField(
        required=True,
        label='Organization',
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_partner_organization'
        })
    )
    other_organization = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your organization name',
            'id': 'id_other_organization',
            'style': 'display: none;'  # Initially hidden
        }),
        help_text="Please specify your organization if it's not listed above"
    )
    membership_category = forms.ModelChoiceField(
        queryset=MembershipType.objects.filter(is_active=True),
        required=True,
        label='Membership Type',
        empty_label='Select your membership type',
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text='Your membership type sets your registration fee and annual dues. '
                  'ANA may review and update it.'
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email',
                 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to all fields
        for field_name, field in self.fields.items():
            if field_name not in ['partner_organization', 'membership_category', 'phone_number', 'position']:
                field.widget.attrs.update({'class': 'form-control'})

        # Custom placeholders
        self.fields['username'].widget.attrs.update({
            'placeholder': 'Choose a username'
        })
        self.fields['password1'].widget.attrs.update({
            'placeholder': 'Enter a secure password'
        })
        self.fields['password2'].widget.attrs.update({
            'placeholder': 'Confirm your password'
        })

        # Organizations that already have members are signed up; their admin adds
        # anyone else, so they are not offered here.
        from dashboard.models import AkilimoParticipant

        partner_choices = [('', 'Select your organization')]

        open_orgs = PartnerOrganization.objects.filter(
            Q(status=PartnerOrganization.STATUS_APPROVED, is_active=True)
            | Q(status=PartnerOrganization.STATUS_PENDING)
        ).exclude(
            userprofile__user__is_active=True
        ).distinct().order_by('name')

        for org in open_orgs:
            label = org.name if org.is_approved else f'{org.name} (Pending Approval)'
            partner_choices.append((f'org_{org.id}', label))

        # Partner names from the AKILIMO data that have no organization record yet
        partners = AkilimoParticipant.objects.values_list('partner', flat=True).distinct().exclude(partner__isnull=True).exclude(partner='')
        unique_partners = sorted(set([p.strip() for p in partners if p and p.strip()]))
        existing_org_names = {n.lower() for n in PartnerOrganization.objects.values_list('name', flat=True)}
        for partner in unique_partners:
            if partner.lower() not in existing_org_names:
                partner_choices.append((f'legacy_{partner}', partner))

        partner_choices.append(('other', 'Other (please specify)'))

        self.fields['partner_organization'].choices = partner_choices

    def clean_email(self):
        """Ensure email uniqueness"""
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("A user with this email address already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        partner_organization = cleaned_data.get('partner_organization')
        other_organization = (cleaned_data.get('other_organization') or '').strip()

        # Check if "Other" was selected but no organization name provided
        if partner_organization == 'other' and not other_organization:
            raise forms.ValidationError(
                "Please specify your organization name when selecting 'Other'."
            )

        # Check if a partner was selected but other organization was also filled
        if partner_organization and partner_organization != 'other' and other_organization:
            raise forms.ValidationError(
                "Please either select an organization from the list OR specify 'Other', not both."
            )

        if partner_organization:
            org = self._resolve_existing_organization(partner_organization, other_organization)
            if org is not None and org.member_profiles().exists():
                admins = [p.user.get_full_name() or p.user.email
                          for p in org.member_profiles() if p.is_partner_admin]
                who = f" ({', '.join(admins)})" if admins else ''
                raise forms.ValidationError(
                    f"{org.name} is already signed up. Ask your organization's admin{who} "
                    f"to add you as a member."
                )
            cleaned_data['existing_organization'] = org

        return cleaned_data

    def _resolve_existing_organization(self, choice, other_name):
        """The PartnerOrganization the chosen option refers to, if one exists."""
        if choice.startswith('org_'):
            try:
                return PartnerOrganization.objects.get(id=int(choice[4:]))
            except (ValueError, PartnerOrganization.DoesNotExist):
                raise forms.ValidationError("Please select a valid organization.")
        name = choice[7:] if choice.startswith('legacy_') else other_name
        return PartnerOrganization.objects.filter(name__iexact=name.strip()).first() if name else None

    def _create_organization(self, name, user):
        import re
        base_code = re.sub(r'[^A-Z0-9]', '', name.upper()[:10]) or 'ORG'
        code = base_code
        counter = 1
        while PartnerOrganization.objects.filter(code=code).exists():
            code = f"{base_code}{counter}"
            counter += 1

        return PartnerOrganization.objects.create(
            name=name,
            code=code,
            status=PartnerOrganization.STATUS_PENDING,
            requested_by=user
        )

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']

        if commit:
            user.save()
            # Update the automatically created profile
            profile = user.profile
            profile.phone_number = self.cleaned_data['phone_number']
            profile.position = self.cleaned_data['position']

            org = self.cleaned_data.get('existing_organization')
            if org is None:
                choice = self.cleaned_data['partner_organization']
                name = choice[7:] if choice.startswith('legacy_') else self.cleaned_data['other_organization']
                org = self._create_organization(name.strip(), user)

            # Lock the organization so two people can't sign the same one up at once.
            org = PartnerOrganization.objects.select_for_update().get(pk=org.pk)
            if org.member_profiles().exclude(user=user).exists():
                raise forms.ValidationError(f"{org.name} is already signed up.")

            # A category already set by ANA is kept.
            if not org.membership_category:
                org.membership_category = self.cleaned_data['membership_category']
                org.save(update_fields=['membership_category', 'updated_at'])

            profile.partner_organization = org
            profile.partner_name = org.name
            profile.is_partner_admin = True
            profile.save()

        return user


class OrganizationMemberForm(forms.Form):
    """Lets an organization's admin add a colleague to its membership."""
    first_name = forms.CharField(max_length=30, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=30, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    phone_number = forms.CharField(max_length=20, widget=forms.TextInput(attrs={'class': 'form-control'}))
    position = forms.CharField(max_length=100, label='Position/Title',
                               widget=forms.TextInput(attrs={'class': 'form-control'}))

    def clean_email(self):
        email = self.cleaned_data['email'].strip()
        if User.objects.filter(Q(email__iexact=email) | Q(username__iexact=email)).exists():
            raise forms.ValidationError(
                "Someone with this email already has an account. Ask ANA to move them to your organization."
            )
        return email

    def save(self, organization):
        """Create the member's account (without a password) in ``organization``."""
        data = self.cleaned_data
        user = User(
            username=data['email'][:150],
            email=data['email'],
            first_name=data['first_name'],
            last_name=data['last_name'],
        )
        user.set_unusable_password()
        user.save()

        profile = user.profile
        profile.partner_organization = organization
        profile.partner_name = organization.name
        profile.phone_number = data['phone_number']
        profile.position = data['position']
        profile.save()
        return user


class CustomAuthenticationForm(AuthenticationForm):
    """Enhanced login form with email authentication and Bootstrap styling"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Change username field to email
        self.fields['username'].label = 'Email Address'
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter your email address',
            'type': 'email'
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter your password'
        })
    
    def clean_username(self):
        """Validate email format for username field"""
        username = self.cleaned_data.get('username')
        if username:
            # Allow both email and username for flexibility
            if '@' in username:
                # If it contains @, validate as email
                from django.core.validators import validate_email
                from django.core.exceptions import ValidationError
                try:
                    validate_email(username)
                except ValidationError:
                    raise forms.ValidationError("Please enter a valid email address.")
        return username


class UserProfileForm(forms.ModelForm):
    """Form for updating user profile"""
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    partner_organization_select = forms.ModelChoiceField(
        queryset=PartnerOrganization.objects.filter(is_active=True),
        required=False,
        empty_label="Select a partner organization (optional)",
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Link your profile to an official partner organization for verification"
    )
    
    class Meta:
        model = UserProfile
        fields = ['phone_number', 'position', 'department', 'profile_photo', 'email_notifications']
        widgets = {
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'position': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'profile_photo': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'email_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            self.fields['first_name'].initial = self.user.first_name
            self.fields['last_name'].initial = self.user.last_name
            self.fields['email'].initial = self.user.email
            
        # The organization is set at sign-up (or by its admin) and can't be changed
        # here. Organizations on an organization membership are never offered,
        # so nobody can join one without its admin.
        if self.instance and self.instance.partner_organization:
            del self.fields['partner_organization_select']
        else:
            self.fields['partner_organization_select'].queryset = PartnerOrganization.objects.filter(
                is_active=True, membership_category__isnull=True,
            )
    
    def save(self, commit=True):
        profile = super().save(commit=False)
        
        if self.user:
            # Update User model fields
            self.user.first_name = self.cleaned_data['first_name']
            self.user.last_name = self.cleaned_data['last_name']
            self.user.email = self.cleaned_data['email']
            
            # Handle partner organization selection
            partner_org = self.cleaned_data.get('partner_organization_select')
            if partner_org:
                profile.partner_organization = partner_org
            
            if commit:
                self.user.save()
                profile.save()
        
        return profile


class PartnerOrganizationForm(forms.ModelForm):
    """Form for creating/updating partner organizations (admin use)"""
    
    class Meta:
        model = PartnerOrganization
        fields = [
            'name', 'code', 'description', 'contact_person', 'email',
            'phone_number', 'website', 'logo', 'address', 'city', 'state',
            'country', 'organization_type', 'established_date', 'is_featured',
            'feature_order', 'success_story', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'logo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'organization_type': forms.TextInput(attrs={'class': 'form-control'}),
            'established_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'feature_order': forms.NumberInput(attrs={'class': 'form-control'}),
            'success_story': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }