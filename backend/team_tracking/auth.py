from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication

class JWTCookieAuthentication(JWTAuthentication):
    def authenticate(self, request):
        cookie_name = getattr(settings, 'SIMPLE_JWT', {}).get('AUTH_COOKIE', 'access_token')
        raw_token = request.COOKIES.get(cookie_name)
        if raw_token:
            try:
                validated_token = self.get_validated_token(raw_token)
            except Exception:
                return None
            return self.get_user(validated_token), validated_token
        return super().authenticate(request)
