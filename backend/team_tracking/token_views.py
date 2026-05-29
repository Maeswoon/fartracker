from django.conf import settings
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

JWT_SETTINGS = getattr(settings, 'SIMPLE_JWT', {})

class PermissionTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['is_admin'] = user.is_superuser
        token['is_team_member'] = user.groups.filter(name='team_member').exists()
        return token

def _set_jwt_cookies(response, access=None, refresh=None):
    cookie_kwargs = {
        'httponly': JWT_SETTINGS.get('AUTH_COOKIE_HTTP_ONLY', True),
        'secure': JWT_SETTINGS.get('AUTH_COOKIE_SECURE', True),
        'samesite': JWT_SETTINGS.get('AUTH_COOKIE_SAMESITE', 'Lax'),
        'path': JWT_SETTINGS.get('AUTH_COOKIE_PATH', '/api/'),
    }
    access_cookie = JWT_SETTINGS.get('AUTH_COOKIE', 'access_token')
    refresh_cookie = JWT_SETTINGS.get('AUTH_COOKIE_REFRESH', 'refresh_token')
    access_lifetime = JWT_SETTINGS.get('ACCESS_TOKEN_LIFETIME')
    refresh_lifetime = JWT_SETTINGS.get('REFRESH_TOKEN_LIFETIME')

    if access:
        max_age = int(access_lifetime.total_seconds()) if access_lifetime else None
        response.set_cookie(access_cookie, access, max_age=max_age, **cookie_kwargs)
    if refresh:
        max_age = int(refresh_lifetime.total_seconds()) if refresh_lifetime else None
        response.set_cookie(refresh_cookie, refresh, max_age=max_age, **cookie_kwargs)
    return response

class CookieTokenObtainPairView(TokenObtainPairView):
    serializer_class = PermissionTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        data = response.data
        return _set_jwt_cookies(
            response,
            access=data.get('access'),
            refresh=data.get('refresh'),
        )

class CookieTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get('refresh_token')
        if refresh_token:
            request._full_data = {'refresh': refresh_token}
        response = super().post(request, *args, **kwargs)
        if 'access' in response.data:
            _set_jwt_cookies(response, access=response.data['access'])
        return response
