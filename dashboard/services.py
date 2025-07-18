import requests
from typing import Dict, List, Optional
from django.conf import settings
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

class EiAMeliaAPIService:
    """Service class to interact with EiA MELIA API"""
    
    BASE_URL = "https://my.eia.cgiar.org/api/v1/melia"
    
    def __init__(self, token: str):
        self.token = token
        self.headers = {
            'Authorization': f'Token {token}',
            'Content-Type': 'application/json'
        }
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make authenticated request to EiA MELIA API"""
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise
    
    def get_participants_by_usecase(self, usecase_ref: str, page: int = 1, page_size: int = 100) -> Dict:
        """
        Get event participants by use case
        
        Args:
            usecase_ref: Reference for the use case (e.g., 'akilimo')
            page: Page number for pagination
            page_size: Number of records per page (max 1000)
        
        Returns:
            Dict containing count, next, previous, and data
        """
        endpoint = f"data/eventsparts/usecase/{usecase_ref}/"
        params = {
            'page': page,
            'page_size': min(page_size, 2000)  # Ensure max limit
        }
        
        cache_key = f"participants_{usecase_ref}_{page}_{page_size}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        data = self._make_request(endpoint, params)
        
        # Cache for 15 minutes
        cache.set(cache_key, data, 900)
        
        return data
    
    def get_all_participants_by_usecase(self, usecase_ref: str, max_pages: int = 10) -> List[Dict]:
        """
        Get all participants for a use case across multiple pages
        
        Args:
            usecase_ref: Reference for the use case
            max_pages: Maximum number of pages to fetch
        
        Returns:
            List of all participant records
        """
        all_participants = []
        page = 1
        
        while page <= max_pages:
            try:
                response = self.get_participants_by_usecase(usecase_ref, page=page, page_size=1000)
                participants = response.get('data', [])
                
                if not participants:
                    break
                
                all_participants.extend(participants)
                
                # Check if there's a next page
                if not response.get('next'):
                    break
                
                page += 1
                
            except Exception as e:
                logger.error(f"Error fetching page {page}: {e}")
                break
        
        return all_participants

class AkilimoDataService:
    """Service specifically for Akilimo data processing"""
    
    def __init__(self, token: str):
        self.api_service = EiAMeliaAPIService(token)
    
    def get_akilimo_participants(self, page: int = 1, page_size: int = 100) -> Dict:
        """Get Akilimo participants data"""
        return self.api_service.get_participants_by_usecase('akilimo', page, page_size)
    
    def get_all_akilimo_participants(self) -> List[Dict]:
        """Get all Akilimo participants data"""
        return self.api_service.get_all_participants_by_usecase('akilimo')
    
    def process_participant_data(self, participants: List[Dict]) -> Dict:
        """
        Process and analyze participant data for dashboard metrics
        
        Returns:
            Dict containing processed metrics
        """
        if not participants:
            return {
                'total_participants': 0,
                'gender_distribution': {},
                'location_distribution': {},
                'training_events': 0,
                'adoption_metrics': {}
            }
        
        # Process data for dashboard metrics
        total_participants = len(participants)
        gender_distribution = {}
        location_distribution = {}
        
        for participant in participants:
            # Gender analysis
            gender = participant.get('gender', 'Unknown')
            gender_distribution[gender] = gender_distribution.get(gender, 0) + 1
            
            # Location analysis
            location = participant.get('location', 'Unknown')
            location_distribution[location] = location_distribution.get(location, 0) + 1
        
        return {
            'total_participants': total_participants,
            'gender_distribution': gender_distribution,
            'location_distribution': location_distribution,
            'raw_data': participants
        }