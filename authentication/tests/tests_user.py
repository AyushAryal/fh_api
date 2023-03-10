from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from authentication.views import UserViewSet
from authentication.tokens import (
    VerificationLinkTokenGenerator,
    PasswordResetTokenGenerator,
)


class UserTest(TestCase):
    def setUp(self):
        self.email = "shark@example.com"
        self.password = "123"

        self.customer_email = "customer@example.com"
        self.customer_password = "123"

        self.user = get_user_model().objects.create(email=self.email)
        self.user.set_password(self.password)
        self.user.is_superuser = True
        self.user.save()

        self.customer = get_user_model().objects.create(email=self.customer_email)
        self.customer.set_password(self.customer_password)
        self.customer.save()

    def test_get_user_list(self):
        factory = APIRequestFactory()
        view = UserViewSet.as_view({"get": "list"})

        # Unauthenticated
        request = factory.get("/user")
        response = view(request)
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)

        # Authenticated superuser
        force_authenticate(request, self.user)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Authenticated normal
        force_authenticate(request, self.customer)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_user(self):
        factory = APIRequestFactory()
        view = UserViewSet.as_view({"get": "retrieve"})

        # Unauthenticated
        request = factory.get("/user")
        response = view(request, pk=self.user.pk)
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)

        # Authenticated customer
        force_authenticate(request, self.customer)
        response = view(request, pk=self.customer.pk)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Attempting to get details for different user
        response = view(request, pk=self.user.pk)
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)

    def test_get_verification_link(self):
        factory = APIRequestFactory()
        view = UserViewSet.as_view({"get": "verification_link"})

        # Unauthenticated
        request = factory.get("/user/verification-link")
        response = view(request)
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)

        # Authenticated
        force_authenticate(request, self.customer)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Authenticated but email is already verified
        self.customer.email_verified = True
        self.customer.save()
        response = view(request)
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)

    def test_get_verify(self):
        factory = APIRequestFactory()
        view = UserViewSet.as_view({"get": "verify"})

        # Get verification link
        token = VerificationLinkTokenGenerator().make_token(self.customer)
        request = factory.get(f"/user/{self.customer.pk}/verify?token={token}")
        response = view(request, pk=self.customer.pk)

        # Check if opening link results in a redirect to frontend
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(
            get_user_model().objects.get(pk=self.customer.pk).email_verified, True
        )

        # Email is already verified
        token = VerificationLinkTokenGenerator().make_token(self.customer)
        request = factory.get(f"/user/{self.customer.pk}/verify?token={token}")
        response = view(request, pk=self.customer.pk)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

    def test_post_password_reset_link(self):
        factory = APIRequestFactory()
        view = UserViewSet.as_view({"post": "password_reset_link"})

        # Invalid data
        request = factory.post("/user/password-reset-link", data={}, format="json")
        response = view(request)
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)

        # Valid data
        request = factory.post(
            "/user/password-reset-link",
            data={"email": self.customer_email},
            format="json",
        )
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_post_password_reset(self):
        factory = APIRequestFactory()
        view = UserViewSet.as_view({"post": "password_reset"})
        token = PasswordResetTokenGenerator().make_token(self.customer)

        # Incorrect token
        request = factory.post(
            f"/user/{self.customer.pk}/password-reset",
            format="json",
            data={
                "token": "invalid",
                "password": "this_isNewPassword!2",
            },
        )
        response = view(request, pk=self.customer.pk)
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)

        # Insecure password
        request = factory.post(
            f"/user/{self.customer.pk}/password-reset",
            format="json",
            data={
                "token": "invalid",
                "password": "123",
            },
        )
        response = view(request, pk=self.customer.pk)
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)

        # Correct info and secure password
        token = PasswordResetTokenGenerator().make_token(self.customer)
        request = factory.post(
            f"/user/{self.customer.pk}/password-reset",
            format="json",
            data={
                "token": token,
                "password": "this_isNewPassword!2",
            },
        )
        response = view(request, pk=self.customer.pk)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_put_change_email(self):
        factory = APIRequestFactory()
        view = UserViewSet.as_view({"put": "change_email"})

        data = {
            "password": self.customer_password,
            "new_email": "doesntexist@e.com",
        }

        # Unauthenticated and invalid data
        request = factory.put(
            f"/user/{self.customer.pk}/change_email/", data={}, format="json"
        )
        response = view(request, pk=self.customer.pk)
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)

        # Unauthenticated, and valid data
        request = factory.put(
            f"/user/{self.customer.pk}/change_email/", data=data, format="json"
        )
        response = view(request, pk=self.customer.pk)
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)

        # Authenticated, but invalid data
        request = factory.put(
            f"/user/{self.customer.pk}/change_email/", data={}, format="json"
        )
        force_authenticate(request, self.customer)
        response = view(request, pk=self.customer.pk)
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)

        # Authenticated but wrong password
        request = factory.put(
            f"/user/{self.customer.pk}/change_email/",
            data={
                "password": "wrong",
                "new_email": "doesntexist@e.com",
            },
            format="json",
        )
        force_authenticate(request, self.customer)
        response = view(request, pk=self.customer.pk)
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)

        # Authenticated as different user (correct password)
        request = factory.put(
            f"/user/{self.user.pk}/change_email/", data=data, format="json"
        )
        force_authenticate(request, self.customer)
        response = view(request, pk=self.user.pk)
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)

        # Authenticated as correct user and valid data, but email is taken
        request = factory.put(
            f"/user/{self.customer.pk}/change_email/",
            data={
                "password": self.customer_password,
                "new_email": self.email,
            },
            format="json",
        )
        force_authenticate(request, self.customer)
        response = view(request, pk=self.customer.pk)
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)

        # Authenticated as correct user and valid data
        request = factory.put(
            f"/user/{self.customer.pk}/change_email/", data=data, format="json"
        )
        force_authenticate(request, self.customer)
        response = view(request, pk=self.customer.pk)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_put_change_password(self):
        factory = APIRequestFactory()
        view = UserViewSet.as_view({"put": "change_password"})

        data = {
            "password": self.customer_password,
            "new_password": "sufficiently_complex_password123",
        }

        # Unauthenticated and invalid data
        request = factory.put(
            f"/user/{self.customer.pk}/change_password/", data={}, format="json"
        )
        response = view(request, pk=self.customer.pk)
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)

        # Unauthenticated, and valid data
        request = factory.put(
            f"/user/{self.customer.pk}/change_password/", data=data, format="json"
        )
        response = view(request, pk=self.customer.pk)
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)

        # Authenticated, but invalid data
        request = factory.put(
            f"/user/{self.customer.pk}/change_password/", data={}, format="json"
        )
        force_authenticate(request, self.customer)
        response = view(request, pk=self.customer.pk)
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)

        # Authenticated but wrong password
        request = factory.put(
            f"/user/{self.customer.pk}/change_password/",
            data={
                "password": "wrong",
                "new_password": self.password,
            },
            format="json",
        )
        force_authenticate(request, self.customer)
        response = view(request, pk=self.customer.pk)
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)

        # Authenticated as different user (correct password)
        request = factory.put(
            f"/user/{self.user.pk}/change_password/", data=data, format="json"
        )
        force_authenticate(request, self.customer)
        response = view(request, pk=self.user.pk)
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)

        # Authenticated as correct user and valid data, but password is insecure
        request = factory.put(
            f"/user/{self.customer.pk}/change_password/",
            data={
                "password": self.customer_password,
                "new_password": "123",
            },
            format="json",
        )
        force_authenticate(request, self.customer)
        response = view(request, pk=self.customer.pk)
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)

        # Authenticated as correct user and valid data
        request = factory.put(
            f"/user/{self.customer.pk}/change_password/", data=data, format="json"
        )
        force_authenticate(request, self.customer)
        response = view(request, pk=self.customer.pk)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
