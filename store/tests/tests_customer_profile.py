from django.contrib.auth import get_user_model
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from store.models import CustomerProfile
from store.views import CustomerProfileViewSet
from authentication.views import TokenViewSet


class CustomerProfileTest(TestCase):
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

        self.customer_profile = CustomerProfile.objects.create(
            user=self.customer,
            first_name="c",
            last_name="c",
            address="a",
        )

    def test_get_token(self):
        factory = APIRequestFactory()
        view = TokenViewSet.as_view({"get": "list"})

        # Get token test for customer
        self.customer.email_verified = True
        self.customer.save()
        request = factory.get("/token/")
        force_authenticate(request, self.customer)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_customer_profile_list(self):
        factory = APIRequestFactory()
        view = CustomerProfileViewSet.as_view({"get": "list"})

        # Unauthenticated
        request = factory.get("/customer")
        response = view(request)
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)

        # Authenticated superuser (doesn't have profile)
        force_authenticate(request, self.user)
        response = view(request)
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)

        # Authenticated normal
        force_authenticate(request, self.customer)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_customer_profile(self):
        factory = APIRequestFactory()
        view = CustomerProfileViewSet.as_view({"get": "retrieve"})

        # Unauthenticated
        request = factory.get("/customer")
        response = view(request, pk=self.user.pk)
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)

        # Authenticated customer
        force_authenticate(request, self.customer)
        response = view(request, pk=self.customer.pk)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Attempting to get details for different user
        response = view(request, pk=self.user.pk)
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)

    def test_post_customer_profile(self):
        factory = APIRequestFactory()
        view = CustomerProfileViewSet.as_view({"post": "create"})

        # Invalid data
        request = factory.post("/customer/", data={}, format="json")
        response = view(request)
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)

        # Valid data but password is insecure
        data = {
            "email": "custmer@example.com",
            "password": "123",
            "customer": {
                "first_name": "Example company",
                "last_name": "Example company",
                "address": "Kathmandu",
                "contact": "+9779840424012",
            },
        }

        request = factory.post("/customer/", data=data, format="json")
        response = view(request)
        self.assertNotEqual(response.status_code, status.HTTP_201_CREATED)

        # Valid data
        data["password"] = "shark@123"
        request = factory.post("/customer/", data=data, format="json")
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_put_customer_profile(self):
        factory = APIRequestFactory()
        view = CustomerProfileViewSet.as_view({"put": "update"})

        data = {
            "first_name": "John",
            "last_name": "Doe",
            "address": "Kathmandu",
            "contact": "+9779840424012",
        }

        # Unauthenticated and invalid data
        request = factory.put(f"/customer/{self.customer.pk}/", data={}, format="json")
        response = view(request, pk=self.customer.pk)
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)

        # Unauthenticated, and valid data
        request = factory.put(
            f"/customer/{self.customer.pk}/", data=data, format="json"
        )
        response = view(request, pk=self.customer.pk)
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)

        # Authenticated, but invalid data
        request = factory.put(f"/customer/{self.customer.pk}/", data={}, format="json")
        force_authenticate(request, self.customer)
        response = view(request, pk=self.customer.pk)
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)

        # Authenticated and valid data
        request = factory.put(
            f"/customer/{self.customer.pk}/", data=data, format="json"
        )
        force_authenticate(request, self.customer)
        response = view(request, pk=self.customer.pk)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
