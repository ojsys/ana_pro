"""
Export resource classes for conference models.
"""
from import_export import resources, fields

from .models import Registration


class RegistrationResource(resources.ModelResource):
    """
    Export resource for conference registrations.

    Flattens the related conference / category and the computed full name so a
    CSV can be handed straight to caterers, badge printers or finance.
    """
    conference = fields.Field(column_name='conference', attribute='conference__name', readonly=True)
    category = fields.Field(column_name='category', attribute='category__name', readonly=True)
    full_name = fields.Field(column_name='full_name', readonly=True)
    payment_status = fields.Field(column_name='payment_status', readonly=True)
    payment_method = fields.Field(column_name='payment_method', readonly=True)

    class Meta:
        model = Registration
        # Export only — importing registrations would bypass ticket numbering
        # and the payment-confirmation flow.
        fields = (
            'ticket_id', 'conference', 'category',
            'first_name', 'last_name', 'full_name', 'email', 'phone',
            'organization', 'position', 'state_of_origin',
            'dietary_requirements', 't_shirt_size', 'abstract_reference',
            'amount', 'is_stakeholder', 'payment_method', 'payment_status',
            'paystack_reference', 'paystack_transaction_id', 'payment_date',
            'confirmation_email_sent', 'receipt_email_sent',
            'terms_accepted', 'checked_in', 'checked_in_at', 'registered_at',
        )
        export_order = fields

    def dehydrate_full_name(self, registration):
        return registration.full_name

    def dehydrate_payment_status(self, registration):
        return registration.get_payment_status_display()

    def dehydrate_payment_method(self, registration):
        return registration.get_payment_method_display()
