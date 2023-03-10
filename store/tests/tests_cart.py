from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status

from store.models import Item, ItemVariant, CartItem
from store.views import CartViewSet


class CartTest(TestCase):
    def setUp(self):
        self.merchant_password = "123"
        self.merchant = get_user_model().objects.create(email="merchant@example.com")
        self.merchant.set_password(self.merchant_password)

        self.item = Item.objects.create(
            user=self.merchant, name="item", description="description"
        )
        self.stock = 2
        self.item_variant = ItemVariant.objects.create(
            item=self.item, rate=2, stock=self.stock, color="Black"
        )

        self.customer_password = "123"
        self.customer = get_user_model().objects.create(email="customer@example.com")
        self.customer.set_password(self.customer_password)
        self.customer.save()

    def test_get_cart_list(self):
        factory = APIRequestFactory()
        view = CartViewSet.as_view({"get": "list"})

        request = factory.get("/cart/")
        response = view(request)
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)

        force_authenticate(request, self.customer)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_checkout(self):
        factory = APIRequestFactory()
        view = CartViewSet.as_view({"get": "checkout"})

        request = factory.get("/cart/")
        response = view(request)
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)

        # Can't checkout empty cart
        force_authenticate(request, self.customer)
        response = view(request)
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)

        # Normal
        CartItem.objects.create(
            cart=self.customer.cart, item_variant=self.item_variant, quantity=1
        )
        force_authenticate(request, self.customer)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.customer.orders.all().count(), 1)
        self.assertEqual(self.customer.cart.items.all().count(), 0)
        self.item_variant = ItemVariant.objects.get(
            pk=self.item_variant.pk
        )  # Requery database
        self.assertEqual(self.item_variant.stock, 1)

        # Check when quantity > stock
        CartItem.objects.create(
            cart=self.customer.cart, item_variant=self.item_variant, quantity=5
        )
        force_authenticate(request, self.customer)
        response = view(request)
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)
        self.item_variant = ItemVariant.objects.get(
            pk=self.item_variant.pk
        )  # Requery database
        self.assertEqual(self.item_variant.stock, 1)

    def test_put_cart(self):
        factory = APIRequestFactory()
        view = CartViewSet.put

        from rest_framework.request import Request
        from rest_framework.parsers import JSONParser
        from rest_framework.exceptions import ValidationError

        data = {
            "items": [
                {"item_variant": 1, "quantity": 1},
            ]
        }

        # Unauthenticated and invalid data
        request = factory.put("/cart/", data={}, format="json")
        request = Request(request, parsers=[JSONParser()])
        response = view(request)
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)

        # Unauthenticated, and valid data
        request = factory.put("/cart/", data=data, format="json")
        request = Request(request, parsers=[JSONParser()])
        response = view(request)
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)

        # Authenticated, but invalid data
        CartItem.objects.create(
            cart=self.customer.cart, quantity=1, item_variant=self.item_variant
        )
        request = factory.put("/cart/", data={}, format="json")
        force_authenticate(request, self.customer)
        request = Request(request, parsers=[JSONParser()])
        with self.assertRaises(ValidationError):
            response = view(request)

        # Authenticated, but repeated item_variant
        request = factory.put(
            "/cart/",
            data={
                "items": [
                    {"item_variant": 1, "quantity": 1},
                    {"item_variant": 1, "quantity": 1},
                ]
            },
            format="json",
        )
        force_authenticate(request, self.customer)
        request = Request(request, parsers=[JSONParser()])
        with self.assertRaises(ValidationError):
            response = view(request)

        # Authenticated and valid data
        request = factory.put("/cart/", data=data, format="json")
        force_authenticate(request, self.customer)
        request = Request(request, parsers=[JSONParser()])
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
