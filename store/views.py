from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from rest_framework import viewsets
from rest_framework import mixins
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend

from authentication.signals import new_verification_link
from authentication import utils
import store.permissions as store_permissions
from .serializers import (
    CustomerProfileSerializer,
    SignupSerializer,
    ItemSerializer,
    ItemAddSerializer,
    OrderSerializer,
    CartSerializer,
    WishlistSerializer,
    BannerImageSerializer,
    CategorySerializer,
)
from .models import (
    Item,
    CustomerProfile,
    Order,
    Cart,
    Wishlist,
    BannerImage,
    Purchase,
    Category,
    Rating,
)


class CustomerProfileViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """
    Endpoint for customer resource. Also includes signup as a customer.

    ---
    ## POST /customer

    Use the POST method to create a new customer.
    **This is usually what you use to signup as a customer.**

    Use the OPTIONS method to view details on the fields.
    (You can use the OPTIONS button above)

    ---

    ### Example request body

    ```
    {
        "email": "custmer@example.com",
        "password": "shark@123",
        "customer": {
            "first_name": "John",
            "last_name": "Doe",
            "address": "Kathmandu",
            "contact": "+9779840424012",
        }
    }
    ```

    ---

    ## PUT | PATCH /customer/*id*

    Use the PUT/PATCH method to update the user information
    (excluding password and email).

    *id* is the User ID. You can get this from token endpoint.

    Password and email are **sensitive**, requiring you to reenter your password.
    Use endpoints in `/user` to change these values.

    ---

    ### Example request body:
    ```
        {
            "first_name": "John",
            "last_name": "Doe",
            "address": "Kathmandu",
            "contact": "+9779840424012",
        }
    ```

    ---
    """

    queryset = CustomerProfile.objects.all()
    serializer_class = CustomerProfileSerializer

    def get_permissions(self):
        permissions_classes = {
            "list": [permissions.IsAuthenticated],
            "retrieve": [store_permissions.IsOwner],
            "create": [permissions.AllowAny],
            "update": [store_permissions.IsOwner],
            "partial_update": [store_permissions.IsOwner],
        }.get(self.action, [permissions.AllowAny])
        return (permission() for permission in permissions_classes)

    def get_serializer_class(self):
        return {
            "create": SignupSerializer,
        }.get(self.action, super().get_serializer_class())

    def get_queryset(self):
        return {"create": get_user_model().objects.all()}.get(
            self.action, super().get_queryset()
        )

    def list(self, request, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        if hasattr(request.user, "customer"):
            return Response(
                serializer_class(
                    request.user.customer, context={"request": request}
                ).data
            )
        return Response(
            {"detail": _("No customer profile present for this user")},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        user = self.get_queryset().filter(email=response.data["email"]).first()
        link = utils.get_verification_link(request, user)
        new_verification_link.send(sender=self.__class__, link=link, user=user)
        return response


class ItemViewSet(
    mixins.ListModelMixin, mixins.CreateModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """
    Endpoint for the Item resource.

    ---

    ## GET /item/

    Use the GET method to list items

    ---

    ## GET /item/*id*/

    Provide the *id* in the URL to GET item details.

    ---

    ## GET /item/recommend/

    Get items from user preference

    ---

    ## POST /item/

    Create new items (for merchants only)

    ---
    """

    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    filterset_fields = ("categories", "recommend")
    search_fields = ("name", "description")

    def get_serializer_class(self):
        return {
            "create": ItemAddSerializer,
        }.get(self.action, super().get_serializer_class())

    def get_permissions(self):
        permissions_classes = {
            "list": [permissions.AllowAny],
            "create": [store_permissions.IsMerchant],
            "retrieve": [permissions.AllowAny],
            "recommend": [permissions.IsAuthenticated],
            "get_user_rating": [permissions.IsAuthenticated],
            "rating": [permissions.IsAuthenticated],
        }.get(self.action, [permissions.AllowAny])
        return (permission() for permission in permissions_classes)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["get"])
    def get_user_rating(self, request, pk=None):
        item = Item.objects.get(pk=pk)
        rating = Rating.objects.filter(user=request.user, item=item).first()
        if rating:
            return Response(rating.rating)
        return Response(
            {"detail": _("Rating for this item doesn't exist")},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(detail=True, methods=["post"])
    def rating(self, request, pk=None):
        item = Item.objects.get(pk=pk)
        try:
            _rating = int(request.body)
            if _rating < 0 or _rating > 5:
                return Response(
                    {"detail": "Rating must be a integer [0-5]"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            rating = Rating.objects.filter(item=item, user=request.user).first()
            if rating:
                rating.rating = _rating
                rating.save()
            else:
                Rating.objects.create(item=item, user=request.user, rating=_rating)
            return Response()
        except ValueError:
            return Response(
                {"detail": "Send a valid integer"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=False, methods=["get"])
    def recommend(self, request):
        if not getattr(request.user, "customer", None):
            return Response(
                {"detail": "Must be a customer"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        import numpy as np
        from django.db import models
        from .recommender import Recommender

        num_users = (
            get_user_model().objects.all().aggregate(models.Max("id")).get("id__max", 0)
        )
        num_items = Item.objects.all().aggregate(models.Max("id")).get("id__max", 0)
        ratings = np.zeros((num_users + 1, num_items + 1))
        for rating in Rating.objects.all():
            ratings[rating.user.pk, rating.item.pk] = rating.rating

        recommender = Recommender(ratings)
        recommendations = recommender.recommend(request.user.pk)[:10]

        return Response(recommendations)


class OrderViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """
    Endpoint for the Order resource.

    **As expected, only orders that you have access to can be listed/viewed.**

    ---

    ## GET /order/

    Use the GET method to list orders

    ---

    ## GET /order/*id*/

    Provide the *id* in the URL to GET order details.

    ---
    """

    serializer_class = OrderSerializer

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user.pk)

    def get_permissions(self):
        permissions_classes = {
            "create": [permissions.IsAuthenticated],
            "list": [permissions.IsAuthenticated],
            "retrieve": [store_permissions.IsOwner],
        }.get(self.action, [permissions.AllowAny])
        return (permission() for permission in permissions_classes)


class CartViewSet(viewsets.GenericViewSet):
    """
    Endpoint for the Cart resource.

    ---

    ## GET /cart/

    GET cart details

    ---

    ## GET /cart/checkout

    Checkout cart

    ---
    ## PUT /cart

    Update cart

    ---

    ### Example request

    Clear Cart

    ```
    {"items": []}
    ```

    Set cart with one item

    ```
    {"items": [{"item_variant": 1, "quantity": 1}]}
    ```
    ---
    """

    serializer_class = CartSerializer
    queryset = Cart.objects.none()

    def get_permissions(self):
        permissions_classes = {
            "create": [permissions.IsAuthenticated],
            "list": [permissions.IsAuthenticated],
            "retrieve": [store_permissions.IsOwner],
            "checkout": [permissions.IsAuthenticated],
        }.get(self.action, [permissions.AllowAny])
        return (permission() for permission in permissions_classes)

    def list(self, request, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        return Response(
            serializer_class(request.user.cart, context={"request": request}).data
        )

    @staticmethod
    def put(request):
        if request.user and request.user.is_authenticated:
            instance = request.user.cart
            serializer = CartSerializer(
                instance=instance,
                data=request.data,
                partial=False,
                context={"request": request},
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    @action(detail=False, methods=["get"])
    def checkout(self, request):
        cart = request.user.cart
        if not cart.items.all():
            return Response(
                {"detail": _("Cart is empty")}, status=status.HTTP_400_BAD_REQUEST
            )

        for item in cart.items.all():
            if item.quantity > item.item_variant.stock:
                return Response(
                    {"detail": _("Some items are out of stock")},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        order = Order.objects.create(user=request.user, timestamp=timezone.now())
        for cart_item in cart.items.all():
            Purchase.objects.create(
                order=order,
                quantity=cart_item.quantity,
                item_variant=cart_item.item_variant,
            )
            cart_item.item_variant.stock -= cart_item.quantity
            cart_item.item_variant.save()
        cart.clear()
        return Response(CartSerializer(instance=cart).data)


class WishlistViewSet(viewsets.GenericViewSet):
    """
    Endpoint for the Wishlist resource.

    ---

    ## GET /wishlist/

    GET wishlist details

    ---
    ## PUT /wishlist

    Update wishlist

    ---

    ### Example request

    Clear Wishlist

    ```
    {"items": []}
    ```

    Set wishlist with one item

    ```
    {"items": [{"item_variant": 1}]}
    ```
    ---
    """

    serializer_class = WishlistSerializer
    queryset = Wishlist.objects.none()

    def get_permissions(self):
        permissions_classes = {
            "create": [permissions.IsAuthenticated],
            "list": [permissions.IsAuthenticated],
            "retrieve": [store_permissions.IsOwner],
        }.get(self.action, [permissions.AllowAny])
        return (permission() for permission in permissions_classes)

    def list(self, request, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        return Response(
            serializer_class(request.user.wishlist, context={"request": request}).data
        )

    @staticmethod
    def put(request):
        if request.user and request.user.is_authenticated:
            instance = request.user.wishlist
            serializer = WishlistSerializer(
                instance=instance,
                data=request.data,
                partial=False,
                context={"request": request},
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        return Response(status=status.HTTP_401_UNAUTHORIZED)


class CategoryViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """
    Endpoint for the Category resource.

    ---

    ## GET /category/

    GET list of categories

    ---

    ## GET /category/*id*/

    GET category details

    ---
    """

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ("recommend",)


class BannerImageViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """
    Endpoint for the Banner Image resource.

    ---

    ## GET /banner/

    GET list of banners

    ---

    ## GET /banner/*id*/

    GET banner image details

    ---
    """

    queryset = BannerImage.objects.all()
    serializer_class = BannerImageSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ("for_mobile",)
