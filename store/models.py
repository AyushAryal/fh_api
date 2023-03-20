from types import DynamicClassAttribute

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model
from django.utils.html import mark_safe
from django.utils.translation import gettext_lazy as _
from django.conf import settings

from phonenumber_field.modelfields import PhoneNumberField
from ckeditor.fields import RichTextField


class CustomerProfile(models.Model):
    class Meta:
        verbose_name = _("Customer profile")
        verbose_name_plural = _("Customer profiles")

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="customer",
        primary_key=True,
        blank=True,
        verbose_name=_("user"),
    )
    first_name = models.CharField(max_length=20, verbose_name=_("first name"))
    last_name = models.CharField(max_length=20, verbose_name=_("last name"))
    address = models.CharField(max_length=100, verbose_name=_("address"))

    contact = PhoneNumberField(
        blank=True, verbose_name=_("contact"), help_text=_("Landline/Cell phone number")
    )

    def __str__(self):
        return str(self.first_name)


class MerchantProfile(models.Model):
    class Meta:
        verbose_name = _("Merchant profile")
        verbose_name_plural = _("Merchant profiles")

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="merchant",
        primary_key=True,
        blank=True,
        verbose_name=_("user"),
    )

    first_name = models.CharField(max_length=20, verbose_name=_("first name"))
    last_name = models.CharField(max_length=20, verbose_name=_("last name"))
    contact = PhoneNumberField(
        verbose_name=_("contact"), help_text=_("Landline/Cell phone number")
    )
    address = models.CharField(max_length=50, verbose_name=_("address"))
    reason_for_signup = models.CharField(
        max_length=1000,
        verbose_name=_("reason for signup"),
        help_text=_("The reason for signup provided by user"),
    )


class Category(models.Model):
    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")
        ordering = ("-id",)

    name = models.CharField(max_length=20, verbose_name=_("name"))
    description = RichTextField(verbose_name=_("description"))
    image = models.ImageField(
        upload_to="uploads/images/categories/", blank=True, verbose_name=_("image")
    )
    recommend = models.BooleanField(
        default=False,
        verbose_name=_("recommend"),
        help_text=_("If this category is recommended by the store owners"),
    )

    def __str__(self):
        return str(self.name)

    def preview(self):
        return mark_safe(f'<img src="{self.image.url}" style="max-height: 200px;" />')


class Item(models.Model):
    class Meta:
        verbose_name = _("Item")
        verbose_name_plural = _("Items")
        ordering = ("-id",)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="items",
        blank=True,
        verbose_name=_("user"),
    )

    name = models.CharField(max_length=100, verbose_name=_("name"))
    subtitle = models.CharField(max_length=1000, blank=True, verbose_name=_("subtitle"))
    description = RichTextField(verbose_name=_("description"))
    recommend = models.BooleanField(
        default=False,
        verbose_name=_("recommend"),
        help_text=_("If this item is recommended by the store owners"),
    )
    categories = models.ManyToManyField(
        Category, blank=True, verbose_name=_("categories")
    )

    def __str__(self):
        return str(self.name)


class ItemVariant(models.Model):
    class Meta:
        verbose_name = _("Item variant")
        verbose_name_plural = _("Item variants")

    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name="variants",
        verbose_name=_("item"),
        help_text=_("The item this item variant is linked with"),
    )
    color = models.CharField(max_length=100, verbose_name=_("color"))
    rate = models.PositiveIntegerField(verbose_name=_("rate"))
    stock = models.PositiveIntegerField(verbose_name=_("stock"))

    def __str__(self):
        return f"{self.color}"


class ItemVariantImage(models.Model):
    class Meta:
        verbose_name = _("Item variant's image")
        verbose_name_plural = _("Item variant's images")

    item_variant = models.ForeignKey(
        ItemVariant,
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name=_("item variant"),
        help_text=_("The item variant this image is linked with"),
    )
    image = models.ImageField(
        upload_to="uploads/images/items/", blank=True, verbose_name=_("image")
    )

    def __str__(self):
        return self.image.url

    def preview(self):
        return mark_safe(f'<img src="{self.image.url}" style="max-height: 200px;" />')


class OrderStatus(models.IntegerChoices):
    Pending, Delivered, Cancelled = range(3)

    @DynamicClassAttribute
    def label(self):
        label = super().label
        return {
            "Pending": _("Pending"),
            "Delivered": _("Delivered"),
            "Cancelled": _("Cancelled"),
        }.get(label, _("None"))


class Order(models.Model):
    class Meta:
        verbose_name = _("Order")
        verbose_name_plural = _("Orders")
        ordering = ("-timestamp",)

    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.RESTRICT,
        related_name="orders",
        verbose_name=_("user"),
    )
    timestamp = models.DateTimeField(
        verbose_name=_("timestamp"), help_text=_("Date and time the order was placed")
    )
    status = models.SmallIntegerField(
        choices=OrderStatus.choices,
        default=OrderStatus.Pending,
        verbose_name=_("status"),
    )

    def total_items(self):
        return sum(purchase.quantity for purchase in self.purchases.all())

    def status_humanized(self):
        return OrderStatus(self.status).label

    def __str__(self):
        return ", ".join(
            f"{purchase.quantity} x {purchase.item_variant.item.name}"
            for purchase in self.purchases.all()
        )


class Purchase(models.Model):
    class Meta:
        verbose_name = _("Purchase")
        verbose_name_plural = _("Purchases")

    order = models.ForeignKey(
        Order,
        related_name="purchases",
        on_delete=models.CASCADE,
        verbose_name=_("order"),
        help_text=_("The order this purchase is linked with"),
    )
    item_variant = models.ForeignKey(
        ItemVariant, on_delete=models.RESTRICT, verbose_name=_("item variant")
    )
    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)], verbose_name=_("quantity")
    )

    def __str__(self):
        return f"{self.quantity} x {self.item_variant.item}"


class Cart(models.Model):
    class Meta:
        verbose_name = _("Cart")
        verbose_name_plural = _("Carts")

    user = models.OneToOneField(
        get_user_model(), on_delete=models.CASCADE, verbose_name=_("user")
    )

    def clear(self):
        self.items.all().delete()

    def __str__(self):
        return f"{self.user} Cart"


class CartItem(models.Model):
    class Meta:
        verbose_name = _("Cart item")
        verbose_name_plural = _("Cart items")

    cart = models.ForeignKey(
        Cart,
        related_name="items",
        on_delete=models.CASCADE,
        verbose_name=_("cart"),
        help_text=_("The cart this cart item is linked with"),
    )
    item_variant = models.ForeignKey(ItemVariant, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    def __str__(self):
        return f"{self.quantity} x {self.item_variant.item}"


class Wishlist(models.Model):
    class Meta:
        verbose_name = _("Wishlist")
        verbose_name_plural = _("Wishlist")

    user = models.OneToOneField(
        get_user_model(), on_delete=models.CASCADE, verbose_name=_("user")
    )

    def clear(self):
        self.items.all().delete()

    def __str__(self):
        return f"{self.user} Wishlist"


class WishlistItem(models.Model):
    class Meta:
        verbose_name = _("Wishlist item")
        verbose_name_plural = _("Wishlist items")

    wishlist = models.ForeignKey(
        Wishlist,
        related_name="items",
        on_delete=models.CASCADE,
        verbose_name=_("wishlist"),
        help_text=_("The wishlist this wishlist item is linked with"),
    )
    item_variant = models.ForeignKey(
        ItemVariant, on_delete=models.CASCADE, verbose_name=_("item variant")
    )

    def __str__(self):
        return f"{self.item_variant.item}"


class Rating(models.Model):
    class Meta:
        verbose_name = _("Rating")
        verbose_name_plural = _("Ratings")
        constraints = (
            models.constraints.UniqueConstraint(
                fields=["item", "user"], name="rating:item_user_constraint"
            ),
        )

    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        verbose_name=_("item"),
        related_name="ratings",
    )

    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        verbose_name=_("user"),
        related_name="ratings",
    )

    rating = models.PositiveIntegerField(
        validators=[MaxValueValidator(5)], verbose_name=_("rating")
    )

    def __str__(self):
        return f"{self.rating} stars by {self.user.email} for {self.item.name}"


class BannerImage(models.Model):
    class Meta:
        verbose_name = _("Banner image")
        verbose_name_plural = _("Banner images")
        ordering = ("-id",)

    image = models.ImageField(
        upload_to="uploads/images/banners/", verbose_name=_("image")
    )
    for_mobile = models.BooleanField(
        default=False,
        verbose_name=_("Used in mobile devices"),
        help_text=_("If this image is used on mobile devices."),
    )

    def __str__(self):
        return self.image.url if self.image else ""

    def preview(self):
        return mark_safe(f'<img src="{self.image.url}" style="max-height: 200px;" />')
