from django.utils.translation import gettext_lazy as _

from rest_framework.response import Response
from rest_framework import status


def check_if_email_verified(user):
    if not user.email_verified:
        return (
            False,
            Response(
                {"detail": _("Unverified email")}, status=status.HTTP_401_UNAUTHORIZED
            ),
        )
    return (True, None)


ADDITIONAL_AUTH_CHECKS = [check_if_email_verified]
