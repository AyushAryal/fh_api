from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status

from store.models import Item, ItemVariant, WishlistItem
from store.views import WishlistViewSet


class WishlistTest(TestCase):
    def setUp(self):
        self.merchant_password = "123"
        self.merchant = get_user_model().objects.create(email="merchant@example.com")
        self.merchant.set_password(self.merchant_password)

        self.item = Item.objects.create(
            user=self.merchant, name="item", description="description"
        )
        self.item_variant = ItemVariant.objects.create(
            item=self.item, stock=2, rate=2, color="Black"
        )

        self.customer_password = "123"
        self.customer = get_user_model().objects.create(email="customer@example.com")
        self.customer.set_password(self.customer_password)
        self.customer.save()

    def test_get_wishlist_list(self):
        factory = APIRequestFactory()
        view = WishlistViewSet.as_view({"get": "list"})

        request = factory.get("/wishlist/")
        response = view(request)
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)

        force_authenticate(request, self.customer)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_put_wishlist(self):
        factory = APIRequestFactory()
        view = WishlistViewSet.put

        from rest_framework.request import Request
        from rest_framework.parsers import JSONParser
        from rest_framework.exceptions import ValidationError

        data = {
            "items": [
                {
                    "item_variant": 1,
                },
            ]
        }

        # Unauthenticated and invalid data
        request = factory.put("/wishlist/", data={}, format="json")
        request = Request(request, parsers=[JSONParser()])
        response = view(request)
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)

        # Unauthenticated, and valid data
        request = factory.put("/wishlist/", data=data, format="json")
        request = Request(request, parsers=[JSONParser()])
        response = view(request)
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)

        # Authenticated, but invalid data
        WishlistItem.objects.create(
            wishlist=self.customer.wishlist, item_variant=self.item_variant
        )
        request = factory.put("/wishlist/", data={}, format="json")
        force_authenticate(request, self.customer)
        request = Request(request, parsers=[JSONParser()])
        with self.assertRaises(ValidationError):
            response = view(request)

        # Authenticated, but repeated item_variant
        request = factory.put(
            "/wishlist/",
            data={
                "items": [
                    {
                        "item_variant": 1,
                    },
                    {
                        "item_variant": 1,
                    },
                ]
            },
            format="json",
        )
        force_authenticate(request, self.customer)
        request = Request(request, parsers=[JSONParser()])
        with self.assertRaises(ValidationError):
            response = view(request)

        # Authenticated and valid data
        request = factory.put("/wishlist/", data=data, format="json")
        force_authenticate(request, self.customer)
        request = Request(request, parsers=[JSONParser()])
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
