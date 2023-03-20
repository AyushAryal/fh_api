from django.db import transaction
from django.db.models import Avg
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

from rest_framework import serializers
from rest_framework.reverse import reverse
from rest_framework.exceptions import ValidationError


from store.models import (
    CustomerProfile,
    Item,
    ItemVariant,
    Cart,
    CartItem,
    Wishlist,
    WishlistItem,
    Purchase,
    Category,
    Order,
    OrderStatus,
    BannerImage,
    Rating,
)
from authentication.serializers import UserSerializer


class CustomerProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(required=False)

    class Meta:
        model = CustomerProfile
        fields = (
            "user",
            "first_name",
            "last_name",
            "address",
            "contact",
        )


class SignupCustomerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerProfile
        fields = (
            "first_name",
            "last_name",
            "address",
            "contact",
        )

class SignupSerializer(serializers.ModelSerializer):
    customer = SignupCustomerProfileSerializer()

    class Meta:
        model = get_user_model()
        fields = ("email", "password", "customer")
        extra_kwargs = {"password": {"write_only": True}}

    def validate_password(self, password):
        validate_password(password)
        return password

    def create(self, validated_data):
        customer = validated_data.pop("customer", None)
        with transaction.atomic():
            user = get_user_model().objects.create(**validated_data)
            user.set_password(validated_data["password"])
            user.save()

            if customer:
                CustomerProfile.objects.create(user=user, **customer)
            return user


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"


class ItemVariantSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()

    def get_images(self, item_variant):
        request = self.context["request"]
        return [
            request.build_absolute_uri(image.image.url)
            for image in item_variant.images.all()
        ]

    class Meta:
        model = ItemVariant
        fields = ("id", "color", "rate", "stock", "images")


class ItemSerializer(serializers.HyperlinkedModelSerializer):
    variants = ItemVariantSerializer(many=True)
    categories = CategorySerializer(many=True)
    user = UserSerializer(required=False)
    rating = serializers.SerializerMethodField()

    def get_rating(self, item):
        ratings = Rating.objects.filter(item=item).aggregate(Avg("rating"))
        return ratings["rating__avg"] or 0.0

    class Meta:
        model = Item
        fields = "__all__"
        extra_kwargs = {"url": {"view_name": "api:item-detail"}}


class PurchaseSerializer(serializers.ModelSerializer):
    item = serializers.SerializerMethodField()

    def get_item(self, purchase):
        return ItemSerializer(
            instance=purchase.item_variant.item, context=self.context
        ).data

    class Meta:
        model = Purchase
        exclude = ("id", "order")


class OrderSerializer(serializers.HyperlinkedModelSerializer):
    purchases = PurchaseSerializer(many=True)
    user = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    def get_user(self, order):
        return reverse(
            "api:user-detail",
            request=self.context["request"],
            kwargs={"pk": order.user.pk},
        )

    def get_status(self, order):
        return OrderStatus(order.status).label

    class Meta:
        model = Order
        fields = ("url", "user", "timestamp", "purchases", "status")
        read_only_fields = ("timestamp",)
        extra_kwargs = {"url": {"view_name": "api:order-detail"}}


class CartItemSerializer(serializers.ModelSerializer):
    item = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        exclude = ("id", "cart")

    def get_item(self, cart_item):
        return ItemSerializer(
            instance=cart_item.item_variant.item, context=self.context
        ).data


class CartSerializer(serializers.HyperlinkedModelSerializer):
    items = CartItemSerializer(many=True)

    class Meta:
        model = Cart
        fields = ("items",)

    def update(self, cart, validated_data):
        items = validated_data["items"]

        # Ensure cart_items have unique item_variant
        item_variant_set = set()
        for item in items:
            item_variant = item["item_variant"]
            if item_variant in item_variant_set:
                raise ValidationError(
                    detail={"detail": _("Multiple items with same item_variant")}
                )
            item_variant_set.add(item_variant)

        cart.clear()
        for item in items:
            CartItem.objects.create(cart=cart, **item)
        return cart


class WishlistItemSerializer(serializers.ModelSerializer):
    item = serializers.SerializerMethodField()

    class Meta:
        model = WishlistItem
        exclude = ("id", "wishlist")

    def get_item(self, wishlist_item):
        return ItemSerializer(
            instance=wishlist_item.item_variant.item, context=self.context
        ).data


class WishlistSerializer(serializers.HyperlinkedModelSerializer):
    items = WishlistItemSerializer(many=True)

    class Meta:
        model = Wishlist
        fields = ("items",)

    def update(self, wishlist, validated_data):
        items = validated_data["items"]

        # Ensure cart_items have unique item_variant
        item_variant_set = set()
        for item in items:
            item_variant = item["item_variant"]
            if item_variant in item_variant_set:
                raise ValidationError(
                    detail={"detail": _("Multiple items with same item_variant")}
                )
            item_variant_set.add(item_variant)

        wishlist.clear()
        for item in items:
            WishlistItem.objects.create(wishlist=wishlist, **item)
        return wishlist


class BannerImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = BannerImage
        fields = "__all__"
