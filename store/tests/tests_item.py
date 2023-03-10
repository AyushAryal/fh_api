from django.test import TestCase
from django.contrib.auth import get_user_model

from rest_framework.test import APIRequestFactory
from rest_framework import status

from store.models import Item
from store.views import ItemViewSet


class ItemTest(TestCase):
    def setUp(self):
        self.merchant_password = "123"
        self.merchant = get_user_model().objects.create(email="merchant@example.com")
        self.merchant.set_password(self.merchant_password)

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

    def test_get_item_recommend(self):
        factory = APIRequestFactory()
        view = ItemViewSet.as_view({"get": "recommend"})

        request = factory.get("/item/1/recommend/")
        response = view(request, pk=self.item.pk)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 0)

        Item.objects.create(user=self.merchant, name="Name", description="description")
        request = factory.get("/item/1/recommend/")
        response = view(request, pk=self.item.pk)
        self.assertEqual(response.data["count"], 1)
