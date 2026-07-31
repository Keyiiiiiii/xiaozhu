from api.models import User


def get_user_from_request(request):
    auth_header = request.META.get("HTTP_AUTHORIZATION", "")
    if not auth_header.startswith("Bearer "):
        return None

    token = auth_header[7:].strip()
    if not token:
        return None

    from rest_framework_simplejwt.authentication import JWTAuthentication

    jwt_auth = JWTAuthentication()
    try:
        validated = jwt_auth.get_validated_token(token)
        user = jwt_auth.get_user(validated)
        if isinstance(user, User):
            return user
    except Exception:
        return None
    return None
