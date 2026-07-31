from django.contrib.auth.backends import ModelBackend

from api.models import User


class WorkIdAuthBackend(ModelBackend):
    """Authenticate by username or work_id (工号)."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None

        user = None
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            try:
                user = User.objects.get(work_id=username)
            except User.DoesNotExist:
                return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
