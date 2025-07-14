import requests
import json
import logging
from django.conf import settings
from django.utils import timezone
from decimal import Decimal

logger = logging.getLogger(__name__)


class PaystackService:
    """Service for handling Paystack payment integration"""
    
    def __init__(self):
        # Use test key for development, live key for production
        self.secret_key = getattr(settings, 'PAYSTACK_SECRET_KEY', 'sk_test_1ccdb1ad0a8a19c53492781336ad15390760afd8')
        self.public_key = getattr(settings, 'PAYSTACK_PUBLIC_KEY', 'pk_test_96b9995fbf552beec8da11acbb821aa5c1d06341')
        self.base_url = 'https://api.paystack.co'
        
        self.headers = {
            'Authorization': f'Bearer {self.secret_key}',
            'Content-Type': 'application/json',
        }
    
    def initialize_transaction(self, email, amount, reference, callback_url, metadata=None):
        """
        Initialize a payment transaction with Paystack
        
        Args:
            email (str): Customer's email
            amount (int): Amount in kobo (multiply naira by 100)
            reference (str): Unique transaction reference
            callback_url (str): URL to redirect after payment
            metadata (dict): Additional data for the transaction
        
        Returns:
            dict: Paystack response
        """
        url = f'{self.base_url}/transaction/initialize'
        
        data = {
            'email': email,
            'amount': int(amount * 100),  # Convert to kobo
            'reference': reference,
            'callback_url': callback_url,
            'metadata': metadata or {}
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=data, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Paystack initialization error: {str(e)}")
            return {
                'status': False,
                'message': f'Payment initialization failed: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Unexpected error during payment initialization: {str(e)}")
            return {
                'status': False,
                'message': 'Unexpected error occurred'
            }
    
    def verify_transaction(self, reference):
        """
        Verify a payment transaction with Paystack
        
        Args:
            reference (str): Transaction reference to verify
        
        Returns:
            dict: Paystack verification response
        """
        url = f'{self.base_url}/transaction/verify/{reference}'
        
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Paystack verification error: {str(e)}")
            return {
                'status': False,
                'message': f'Payment verification failed: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Unexpected error during payment verification: {str(e)}")
            return {
                'status': False,
                'message': 'Unexpected error occurred'
            }
    
    def list_transactions(self, page=1, per_page=50):
        """
        List transactions from Paystack
        
        Args:
            page (int): Page number
            per_page (int): Number of transactions per page
        
        Returns:
            dict: Paystack response with transactions list
        """
        url = f'{self.base_url}/transaction'
        params = {
            'page': page,
            'perPage': per_page
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Paystack list transactions error: {str(e)}")
            return {
                'status': False,
                'message': f'Failed to fetch transactions: {str(e)}'
            }
    
    def create_customer(self, email, first_name, last_name, phone=None):
        """
        Create a customer on Paystack
        
        Args:
            email (str): Customer email
            first_name (str): Customer first name
            last_name (str): Customer last name
            phone (str): Customer phone number
        
        Returns:
            dict: Paystack response
        """
        url = f'{self.base_url}/customer'
        
        data = {
            'email': email,
            'first_name': first_name,
            'last_name': last_name,
        }
        
        if phone:
            data['phone'] = phone
        
        try:
            response = requests.post(url, headers=self.headers, json=data, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Paystack customer creation error: {str(e)}")
            return {
                'status': False,
                'message': f'Customer creation failed: {str(e)}'
            }
    
    def get_banks(self):
        """
        Get list of supported banks from Paystack
        
        Returns:
            dict: Paystack response with banks list
        """
        url = f'{self.base_url}/bank'
        
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Paystack banks list error: {str(e)}")
            return {
                'status': False,
                'message': f'Failed to fetch banks: {str(e)}'
            }


# Membership pricing (in Naira)
MEMBERSHIP_PRICING = {
    'individual': Decimal('10000.00'),  # ₦10,000 per year for individuals
    'organization': Decimal('50000.00'),  # ₦50,000 per year for organizations
}


def get_membership_price(membership_type):
    """Get membership price by type"""
    return MEMBERSHIP_PRICING.get(membership_type, MEMBERSHIP_PRICING['individual'])


def generate_payment_reference(user_id, membership_type):
    """Generate unique payment reference"""
    timestamp = int(timezone.now().timestamp())
    return f"ANA_{membership_type.upper()}_{user_id}_{timestamp}"


def format_currency(amount):
    """Format amount as Nigerian Naira"""
    return f"₦{amount:,.2f}"