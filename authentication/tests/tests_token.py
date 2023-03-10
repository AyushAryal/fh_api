from django.test import TestCase
from django.contrib.auth import get_user_model

from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status

from authentication.views import TokenViewSet


class TokenTest(TestCase):
    def setUp(self):
        self.email = "shark@example.com"
        self.password = "123"

        self.user = get_user_model().objects.create(email=self.email)
        self.user.set_password(self.password)
        self.user.save()

    def test_delete_token(self):
        factory = APIRequestFactory()
        view = TokenViewSet.delete

        from rest_framework.request import Request
        from rest_framework.parsers import JSONParser

        # Get token
        list_view = TokenViewSet.as_view({"get": "list"})
        request = factory.get("/token/")
        force_authenticate(request, self.user)
        response = list_view(request)

        # Unauthenticated but token exists
        request = factory.delete("/token/")
        request = Request(request, parsers=[JSONParser()])
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Authenticated and token exists
        request = factory.delete("/token/")
        force_authenticate(request, self.user)
        request = Request(request, parsers=[JSONParser()])
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Authenticated but token doesn't exist
        request = factory.delete("/token/")
        force_authenticate(request, self.user)
        request = Request(request, parsers=[JSONParser()])
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Unauthenticated and token doesn't exist
        request = factory.delete("/token/")
        request = Request(request, parsers=[JSONParser()])
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_token(self):
        factory = APIRequestFactory()
        view = TokenViewSet.as_view({"get": "list"})

        # Unauthenticated
        request = factory.get("/token/")
        response = view(request)
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)

        # Authenticated but unverified email
        request = factory.get("/token/")
        force_authenticate(request, self.user)
        response = view(request)
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)

        self.user.email_verified = True
        self.user.save()

        # Authenticated and verified email
        request = factory.get("/token/")
        force_authenticate(request, self.user)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_post_token(self):
        factory = APIRequestFactory()
        view = TokenViewSet.as_view({"post": "create"})

        # Invalid credentials
        request = factory.post("/token/", {"email": "", "password": ""}, format="json")
        response = view(request)
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)

        # Valid credentials but email is not verified
        request = factory.post(
            "/token/", {"email": self.email, "password": self.password}, format="json"
        )
        response = view(request)
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)

        # Valid credentials and email is verified
        self.user.email_verified = True
        self.user.save()
        request = factory.post(
            "/token/", {"email": self.email, "password": self.password}, format="json"
        )
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
