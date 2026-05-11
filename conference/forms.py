from django import forms
from .models import AbstractSubmission, Registration, RegistrationCategory, AbstractThematicArea


class AbstractSubmissionForm(forms.ModelForm):
    class Meta:
        model = AbstractSubmission
        fields = [
            'author_name', 'co_authors', 'institution', 'email', 'phone',
            'title', 'thematic_area', 'abstract_text', 'keywords',
            'presentation_format', 'abstract_file', 'declaration',
        ]
        widgets = {
            'author_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full name of presenting author'}),
            'co_authors': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., John Doe; Jane Smith (optional)'}),
            'institution': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'University / Research Institute / Organization'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'your@email.com'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+234 800 000 0000 (optional)'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full title of your abstract'}),
            'thematic_area': forms.Select(attrs={'class': 'form-select'}),
            'abstract_text': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 8,
                'placeholder': 'Write your abstract here (max 300 words).\n\nStructure: Introduction | Methodology | Results/Findings | Conclusion'
            }),
            'keywords': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., cassava, AKILIMO, food security, Nigeria, yield'}),
            'presentation_format': forms.Select(attrs={'class': 'form-select'}),
            'abstract_file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'declaration': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, conference, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['thematic_area'].queryset = AbstractThematicArea.objects.filter(
            conference=conference, is_active=True
        )
        self.fields['declaration'].required = True

    def clean_abstract_text(self):
        text = self.cleaned_data.get('abstract_text', '')
        word_count = len(text.split())
        if word_count > 300:
            raise forms.ValidationError(f"Abstract exceeds 300 words ({word_count} words). Please shorten it.")
        if word_count < 50:
            raise forms.ValidationError("Abstract is too short. Please provide at least 50 words.")
        return text

    def clean_keywords(self):
        kw = self.cleaned_data.get('keywords', '')
        items = [k.strip() for k in kw.split(',') if k.strip()]
        if len(items) < 3:
            raise forms.ValidationError("Please provide at least 3 keywords.")
        if len(items) > 8:
            raise forms.ValidationError("Please provide no more than 8 keywords.")
        return ', '.join(items)


class RegistrationForm(forms.ModelForm):
    class Meta:
        model = Registration
        fields = [
            'first_name', 'last_name', 'email', 'phone',
            'organization', 'position', 'state_of_origin',
            'category', 'dietary_requirements', 't_shirt_size',
            'abstract_reference', 'payment_method', 'terms_accepted',
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'your@email.com'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+234 800 000 0000'}),
            'organization': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Organization / Institution'}),
            'position': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your role or title (optional)'}),
            'state_of_origin': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'State (optional)'}),
            'category': forms.Select(attrs={'class': 'form-select', 'id': 'id_category'}),
            'dietary_requirements': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Vegetarian, Halal, None'}),
            't_shirt_size': forms.Select(attrs={'class': 'form-select'}),
            'abstract_reference': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., ANC2026-0012 (if applicable)'}),
            'payment_method': forms.RadioSelect(attrs={'class': 'pay-method-radio'}),
            'terms_accepted': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, conference, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = RegistrationCategory.objects.filter(
            conference=conference, is_active=True
        )
        self.fields['terms_accepted'].required = True

    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Check for duplicate registration in same conference
        return email
