from django.utils import timezone
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status

from store.models import Item, ItemVariant, Order, Purchase
from store.views import OrderViewSet


class OrderTest(TestCase):
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

        self.user = get_user_model().objects.create(email="shark@example.com")
        self.user.set_password("123")
        self.user.is_superuser = True
        self.user.save()

        self.customer_password = "123"

        self.customer = get_user_model().objects.create(email="customer@example.com")
        self.customer.set_password(self.customer_password)
        self.customer.save()

        self.customer1 = get_user_model().objects.create(email="customer1@example.com")
        self.customer1.set_password(self.customer_password)
        self.customer1.save()

        self.order = Order.objects.create(user=self.customer, timestamp=timezone.now())
        self.order1 = Order.objects.create(
            user=self.customer1, timestamp=timezone.now()
        )

        self.purchase = Purchase.objects.create(
            order=self.order,
            item_variant=self.item_variant,
            quantity=1,
        )

        self.purchase1 = Purchase.objects.create(
            order=self.order1,
            item_variant=self.item_variant,
            quantity=1,
        )

    def test_get_order_list(self):
        factory = APIRequestFactory()
        view = OrderViewSet.as_view({"get": "list"})

        request = factory.get("/order/")
        response = view(request)
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)

        force_authenticate(request, self.user)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 0)

        force_authenticate(request, self.customer)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

        force_authenticate(request, self.customer1)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_get_order(self):
        factory = APIRequestFactory()
        view = OrderViewSet.as_view({"get": "retrieve"})

        request = factory.get("/order/")
        response = view(request, pk=self.order.pk)
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)

        force_authenticate(request, self.user)
        response = view(request, pk=self.order.pk)
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)

        force_authenticate(request, self.customer)
        response = view(request, pk=self.order.pk)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        force_authenticate(request, self.customer1)
        response = view(request, pk=self.order.pk)
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)
