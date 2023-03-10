from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError as DjValidationError
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _


from rest_framework import mixins
from rest_framework import permissions
from rest_framework import status
from rest_framework import viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.reverse import reverse
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError as DRFValidationError

from .tokens import VerificationLinkTokenGenerator
from . import signals
from . import permissions as authentication_permissions
from . import serializers
from . import utils


class UserViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """
    Endpoint for the User resource.

    ---

    ## GET /user/*id*/

    Use the GET method to get the user information.

    You can get the User *id* from the token endpoint.

    ---

    ### Example response

    ```
    {
        "email": "john@example.com",
        "email_verified": false
    }
    ```

    ---

    ## GET /user/verification_link

    Use this endpoint to create (and possibly email) the verification link
    for the authenticated user.

    ---

    ## GET /user/*id*/verify

    Endpoint to process the verification link.
    A link to this endpoint was (possibly) emailed to users.

    ---

    ## PUT /user/*id*/change_password

    Endpoint to change the user password.

    Requires two fields `password` and `new_password`

    ---

    ## PUT /user/*id*/change_email

    Endpoint to change the user email.

    Requires two fields `password` and `new_email`

    ---

    """

    queryset = get_user_model().objects.all()
    serializer_class = serializers.UserSerializer

    def get_permissions(self):
        permissions_classes = {
            "list": [permissions.IsAuthenticated],
            "retrieve": [authentication_permissions.IsOwner],
            "change_password": [authentication_permissions.IsOwner],
            "change_email": [authentication_permissions.IsOwner],
            "verification_link": [permissions.IsAuthenticated],
            "verify": [permissions.AllowAny],
            "password_reset_link": [permissions.AllowAny],
            "password_reset": [permissions.AllowAny],
        }.get(self.action, [permissions.AllowAny])
        return (permission() for permission in permissions_classes)

    def get_serializer_class(self):
        return {
            "change_password": serializers.ChangePasswordSerializer,
            "change_email": serializers.ChangeEmailSerializer,
        }.get(self.action, super().get_serializer_class())

    def list(self, request, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        return Response(
            serializer_class(request.user, context={"request": request}).data
        )

    @action(detail=False, methods=["get"])
    def verification_link(self, request):
        if request.user.email_verified:
            return Response(
                {"detail": _("Email has already been verified")},
                status=status.HTTP_400_BAD_REQUEST,
            )
        link = utils.get_verification_link(request, request.user)
        signals.new_verification_link.send(
            sender=self.__class__, link=link, user=request.user
        )
        return Response()

    @action(detail=True, methods=["get"])
    def verify(self, request, *args, **kwargs):
        user = self.get_object()
        site = Site.objects.get_current()
        token = request.query_params.get("token", "")
        success_path = settings.FRONTEND_URLS["email_verification_successful"]
        error_path = settings.FRONTEND_URLS["email_verification_failed"]
        if not VerificationLinkTokenGenerator().check_token(user, token):
            return redirect(f"{site.domain}{error_path}")
        elif user.email_verified:
            return redirect(f"{site.domain}{error_path}")
        else:
            user.email_verified = True
            user.save()
            return redirect(f"{site.domain}{success_path}")

    @action(detail=False, methods=["post"])
    def password_reset_link(self, request):
        email = request.data.get("email", None)
        user = get_user_model().objects.filter(email=email).first()
        if email and user:
            link = utils.get_password_reset_link(user)
            signals.new_password_reset_link.send(
                sender=self.__class__, link=link, user=user
            )
            return Response()
        return Response(
            {"detail": _("Email doesn't exist")}, status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=True, methods=["post"])
    def password_reset(self, request, *args, **kwargs):
        user = self.get_object()
        token = request.data.get("token")
        password = request.data.get("password")

        try:
            validate_password(password)
        except DjValidationError as e:
            raise DRFValidationError(detail={"password": e.messages})

        if not PasswordResetTokenGenerator().check_token(user, token):
            return Response(
                {"detail": _("Invalid/Expired token")},
                status=status.HTTP_400_BAD_REQUEST,
            )
        else:
            user.set_password(password)
            user.save()
            return Response()

    @action(detail=True, methods=["put"])
    def change_password(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=True, methods=["put"])
    def change_email(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        link = utils.get_verification_link(request, request.user)
        signals.new_verification_link.send(
            sender=self.__class__, link=link, user=request.user
        )
        return Response(serializer.data)


class TokenViewSet(viewsets.GenericViewSet):
    """
    Endpoint for token based authentication. Can be used for login/logout.

    ---

    ### General instructions for Authenticating

    We use a token based authentication scheme.

    To authenticate, use the HTTP Header `Authorization`.
    The value of the header should be `Token XXXX` where XXXX is replaced
    with the generated token.

    Example:

    ```
    http_headers = {
        "Authorization": "Token 504f7d23ebd7fac6e7a8d1d6e73ea3fefd17231b" }
    ```

    **Note: The authorization header must be present in all requests moving forward.**

    ---

    ## POST /token

    Use the POST method to **get** a token for the user.
    You can then use the generated token for authentication.

    There are two required fields `email` and `password`.
    They must be POSTed to this endpoint as a `application/json` document.

    ---
    ### Example:
    Request

    ```
    {
        'email': 'john_doe@example.com',
        'password': 'd*0A2IapFWf'
    }
    ```

    Response

    ```
    { 'token': '504f7d23ebd7fac6e7a8d1d6e73ea3fefd17231b',
        'user': '1'}
    ```
    ---

    ## GET /token

    Use the GET method to get details about the token.
    **You must be authenticated, to get details of a token!**.
    See above, for details on authentication.

    For instance, if you want to get the user ID,
    you can use the GET method on this endpoint.

    ---

    ### Example:
    Response

    ```
    { 'token': '504f7d23ebd7fac6e7a8d1d6e73ea3fefd17231b',
        'user': '1'}
    ```

    ---

    ## DELETE /token

    Use the DELETE method on this endpoint to revoke your token.
    While deleting the token on the client side logs out the user in the client,
    the token is still valid. Revoking a token logs out the user from all devices.

    **Therefore, it is highly recommended to use this endpoint,
    instead of deleting token in the client.**
    This is a mechanism to stop abuse of stolen tokens
    ---
    """

    serializer_class = serializers.EmailAuthTokenSerializer

    @staticmethod
    def get_token(user, request):
        if not user or not user.is_authenticated:
            return Response(
                {"detail": _("Unauthenticated")}, status=status.HTTP_401_UNAUTHORIZED
            )

        from authentication.hooks import ADDITIONAL_AUTH_CHECKS  # noqa

        for auth_check in ADDITIONAL_AUTH_CHECKS:
            ret, response = auth_check(user)
            if not ret:
                return response

        token, _status = Token.objects.get_or_create(user=user)
        return Response(
            {
                "token": token.key,
                "user": reverse(
                    "api:user-detail", request=request, kwargs={"pk": user.pk}
                ),
            }
        )

    def create(self, request):
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        return TokenViewSet.get_token(user, request)

    def list(self, request):
        return TokenViewSet.get_token(request.user, request)

    @staticmethod
    def delete(request):
        if (
            request.user.is_authenticated
            and Token.objects.filter(user=request.user).exists()
        ):
            request.user.auth_token.delete()
        return Response(status=status.HTTP_200_OK)
