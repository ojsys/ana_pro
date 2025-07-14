from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from django.db.models import Q


class EmailBackend(ModelBackend):
    """Custom authentication backend that allows users to log in using their email address"""
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)
        
        if username is None or password is None:
            return
        
        try:
            # Try to find user by email or username (get the first match if multiple exist)
            user = User.objects.filter(Q(email=username) | Q(username=username)).first()
            if not user:
                raise User.DoesNotExist
        except User.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a nonexistent user (#20760).
            User().set_password(password)
        else:
            if user.check_password(password) and self.user_can_authenticate(user):
                return user