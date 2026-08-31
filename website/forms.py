"""
Forms used by partner organisations to maintain their own public page.
"""
from django import forms

from dashboard.models import PartnerOrganization, PartnerService, PartnerGalleryImage


class PartnerProfileForm(forms.ModelForm):
    """The 'About' tab — narrative and contact details a partner may edit."""

    class Meta:
        model = PartnerOrganization
        fields = [
            'about', 'mission', 'areas_of_work', 'organization_type',
            'success_story', 'logo', 'cover_image',
            'contact_person', 'email', 'phone_number', 'website',
            'address', 'city', 'state',
            'facebook_url', 'twitter_url', 'linkedin_url',
        ]
        widgets = {
            'about': forms.Textarea(attrs={'rows': 6, 'placeholder': 'Tell visitors what your organization does…'}),
            'mission': forms.Textarea(attrs={'rows': 3}),
            'areas_of_work': forms.Textarea(attrs={'rows': 5, 'placeholder': 'One area of work per line'}),
            'success_story': forms.Textarea(attrs={'rows': 5}),
            'address': forms.Textarea(attrs={'rows': 2}),
        }
        help_texts = {
            'areas_of_work': 'One per line. Each line becomes a tag on your public page.',
            'cover_image': 'Wide banner shown at the top of your page. Around 1600×500 works well.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            css = 'form-control'
            if isinstance(field.widget, forms.CheckboxInput):
                css = 'form-check-input'
            elif isinstance(field.widget, forms.Select):
                css = 'form-select'
            field.widget.attrs.setdefault('class', css)


class PartnerServiceForm(forms.ModelForm):
    """One service entry on the 'Services' tab."""

    class Meta:
        model = PartnerService
        fields = ['title', 'description', 'icon', 'order', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
        help_texts = {
            'icon': "Optional Bootstrap Icons class, e.g. bi-tree, bi-people, bi-graph-up",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            css = 'form-check-input' if isinstance(field.widget, forms.CheckboxInput) else 'form-control'
            field.widget.attrs.setdefault('class', css)


class PartnerGalleryImageForm(forms.ModelForm):
    """One photo on the 'Gallery' tab."""

    class Meta:
        model = PartnerGalleryImage
        fields = ['image', 'caption', 'description', 'location', 'taken_on', 'order', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
            'taken_on': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            css = 'form-check-input' if isinstance(field.widget, forms.CheckboxInput) else 'form-control'
            field.widget.attrs.setdefault('class', css)
