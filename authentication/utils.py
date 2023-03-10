from urllib.parse import urlencode

from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.sites.models import Site
from django.conf import settings

from rest_framework.reverse import reverse

from authentication.tokens import VerificationLinkTokenGenerator


@staticmethod
def get_verification_link(request, user):
    token = VerificationLinkTokenGenerator().make_token(user)
    url = reverse("api:user-verify", request=request, kwargs={"pk": user.pk})
    query = urlencode({"token": token})
    return f"{url}?{query}"


@staticmethod
def get_password_reset_link(user):
    token = PasswordResetTokenGenerator().make_token(user)
    scheme = "https"
    authority = Site.objects.get_current().domain
    path = settings.FRONTEND_URLS["reset_password_form"]
    query = urlencode({"id": user.pk, "token": token})
    return f"{scheme}://{authority}{path}?{query}"
