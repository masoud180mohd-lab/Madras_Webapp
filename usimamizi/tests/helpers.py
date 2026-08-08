"""Shared fixtures for usimamizi tests."""

from django.contrib.auth import get_user_model
from django.test import override_settings

from usimamizi.models import Mwalimu

User = get_user_model()

# Ensure Client host is accepted even when .env omits testserver.
HOSTS = override_settings(ALLOWED_HOSTS=["testserver", "localhost", "127.0.0.1"])


def create_user_with_cheo(username, cheo, password="pass12345"):
    user = User.objects.create_user(username, password=password)
    Mwalimu.objects.create(user=user, cheo=cheo)
    return user
