from django.conf import settings
from rest_framework.permissions import BasePermission
from rest_framework_simplejwt.authentication import JWTAuthentication

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.auth and request.auth.get('is_admin'))

class IsTeamMember(BasePermission):
    def has_permission(self, request, view):
        return bool(request.auth and request.auth.get('is_team_member'))

class IsAdminOrTeamOwner(BasePermission):
    def has_permission(self, request, view):
        token = request.auth
        if token and token.get('is_admin'):
            return True
        team_id = view.kwargs.get('team_id')
        return bool(token and team_id and request.user.username == team_id)

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
