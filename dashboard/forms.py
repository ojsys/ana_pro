from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import UserProfile, PartnerOrganization


class CustomUserCreationForm(UserCreationForm):
    """Enhanced user registration form with additional fields"""
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
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 
                 'password1', 'password2')
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to all fields
        for field_name, field in self.fields.items():
            if field_name not in ['partner_organization', 'phone_number', 'position']:
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
        
        # Set up partner organization choices from AkilimoParticipant data
        from dashboard.models import AkilimoParticipant
        
        partner_choices = [('', 'Select your organization')]
        
        # Get unique partner names from AkilimoParticipant
        partners = AkilimoParticipant.objects.values_list('partner', flat=True).distinct().exclude(partner__isnull=True).exclude(partner='')
        unique_partners = sorted(set([p for p in partners if p and p.strip()]))
        
        for partner in unique_partners:
            partner_choices.append((partner, partner))
        
        partner_choices.append(('other', 'Other (please specify)'))
        
        self.fields['partner_organization'].choices = partner_choices
    
    def clean_email(self):
        """Ensure email uniqueness"""
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email address already exists.")
        return email
    
    def clean(self):
        cleaned_data = super().clean()
        partner_organization = cleaned_data.get('partner_organization')
        other_organization = cleaned_data.get('other_organization')
        
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
        
        return cleaned_data
    
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
            
            # Handle partner organization assignment
            partner_name = self.cleaned_data.get('partner_organization')
            other_org = self.cleaned_data.get('other_organization')
            
            if partner_name == 'other' and other_org:
                # Use the custom organization name provided
                profile.partner_name = other_org
            elif partner_name and partner_name != 'other':
                # Use the selected partner name from AkilimoParticipant data
                profile.partner_name = partner_name
            
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
            
        # Set initial value for partner organization if one is already linked
        if self.instance and self.instance.partner_organization:
            self.fields['partner_organization_select'].initial = self.instance.partner_organization
    
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
            'phone_number', 'website', 'address', 'city', 'state',
            'country', 'organization_type', 'established_date', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'organization_type': forms.TextInput(attrs={'class': 'form-control'}),
            'established_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }