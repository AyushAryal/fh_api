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
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
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

    ## GET /item/*id*/recommend/

    Get items similar to this

    ---
    """

    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    filterset_fields = ("categories", "recommend")
    search_fields = ("name", "description")

    @action(detail=True, methods=["get"])
    def recommend(self, request, pk=None):
        item = Item.objects.get(pk=pk)
        queryset = Item.objects.all().exclude(pk=pk)
        if item.categories.all().exists():
            queryset = queryset.filter(categories__in=item.categories.all())

        # WARN: Bad performance to SORT BY RAND().
        # This endpoint itself is not great.
        # If this ever becomes an issue,
        # then write an ACTUAL recommendation system.
        queryset = queryset.order_by("?")

        queryset, self.queryset = self.queryset, queryset
        response = self.list(request=request)
        queryset, self.queryset = self.queryset, queryset
        return response


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
