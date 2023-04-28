from django.test import TestCase
from django.contrib.auth import get_user_model

from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status

from store.models import Item, Rating, MerchantProfile
from store.views import ItemViewSet


class ItemTest(TestCase):
    def setUp(self):
        self.merchant_password = "123"
        self.merchant = get_user_model().objects.create(email="merchant@example.com")
        self.merchant.set_password(self.merchant_password)
        self.merchant_profile = MerchantProfile.objects.create(
            user=self.merchant,
            first_name="Merchant",
            last_name="Merchant",
            contact="+9779840424011",
            reason_for_signup="reason",
            address="location"
        )
        self.customer_password = "123"
        self.customer = get_user_model().objects.create(email="customer@example.com")
        self.customer.set_password(self.customer_password)
        self.customer.save()

        self.item = Item.objects.create(
            user=self.merchant, name="Name", description="description"
        )

    def test_get_item_list(self):
        factory = APIRequestFactory()
        view = ItemViewSet.as_view({"get": "list"})

        request = factory.get("/item/")
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_item(self):
        factory = APIRequestFactory()
        view = ItemViewSet.as_view({"get": "retrieve"})

        request = factory.get("/item/")
        response = view(request, pk=self.item.pk)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_item(self):
        factory = APIRequestFactory()
        view = ItemViewSet.as_view({"post": "create"})
        valid_data = {
            "name": "item1",
            "subtitle": "subtitle",
            "description": "description",
            "recommend": True,
            "categories": []
        }
        invalid_data = {
            "subtitle": "subtitle",
            "description": 12,
            "recommend": "abc",
            "categories": []
        }
        # Unauthenticated
        request = factory.post("/item/", format="json")
        response = view(request)
        self.assertNotEqual(response.status_code, status.HTTP_201_CREATED)

        # Authenticated as customer but invalid
        request = factory.post("/item/", data=invalid_data, format="json")
        force_authenticate(request, self.customer)
        response = view(request)
        self.assertNotEqual(response.status_code, status.HTTP_201_CREATED)

        # Authenticated as customer and valid
        request = factory.post("/item/", data=valid_data, format="json")
        force_authenticate(request, self.customer)
        response = view(request)
        self.assertNotEqual(response.status_code, status.HTTP_201_CREATED)

        # Authenticated as merchant but invalid
        request = factory.post("/item/", data=invalid_data, format="json")
        force_authenticate(request, self.merchant)
        response = view(request)
        self.assertNotEqual(response.status_code, status.HTTP_201_CREATED)

        # Authenticated as merchant and valid
        request = factory.post("/item/", data=valid_data, format="json")
        force_authenticate(request, self.merchant)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_post_rating(self):
        factory = APIRequestFactory()
        view = ItemViewSet.as_view({"post": "rating"})

        # Unauthenticated
        request = factory.post("/item/1/rating/", 4, format="json")
        response = view(request, pk=self.item.pk)
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)

        # Authenticated but out of range
        request = factory.post("/item/1/rating/", 6, format="json")
        force_authenticate(request, self.customer)
        response = view(request, pk=self.item.pk)
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)

        # Authenticated but invalid
        request = factory.post("/item/1/rating/", "a", format="json")
        force_authenticate(request, self.customer)
        response = view(request, pk=self.item.pk)
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)

        # Authenticated and valid
        request = factory.post("/item/1/rating/", 4, format="json")
        force_authenticate(request, self.customer)
        response = view(request, pk=self.item.pk)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Authenticated and valid and redo
        request = factory.post("/item/1/rating/", 2, format="json")
        force_authenticate(request, self.customer)
        response = view(request, pk=self.item.pk)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_user_rating(self):
        factory = APIRequestFactory()
        view = ItemViewSet.as_view({"get": "get_user_rating"})

        # Unauthenticated
        request = factory.get("/item/1/get_user_rating/")
        response = view(request, pk=self.item.pk)
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)

        # Authenticated but rating doesn't exist
        request = factory.get("/item/1/get_user_rating/")
        response = view(request, pk=self.item.pk)
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)

        # Authenticated and rating exists
        Rating.objects.create(user=self.customer, item=self.item, rating=2)
        request = factory.get("/item/1/get_user_rating/")
        response = view(request, pk=self.item.pk)
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)
