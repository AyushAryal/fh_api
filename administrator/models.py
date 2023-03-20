from django.utils.html import format_html
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.template.loader import get_template

from store.models import (
    BannerImage,
    Cart,
    CartItem,
    Category,
    CustomerProfile,
    MerchantProfile,
    Item,
    ItemVariant,
    ItemVariantImage,
    Order,
    OrderStatus,
    Purchase,
    Wishlist,
    WishlistItem,
    Rating,
)
from core.models import Site
from . import forms as admin_forms


class SiteSettingsAdmin(admin.ModelAdmin):
    model = Site
    list_display = ("domain", "name")

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class RatingAdmin(admin.ModelAdmin):
    model = Rating
    form = admin_forms.BootstrapModelForm
    list_display = ("item", "stars", "user")

    @admin.display(description=_("rating"))
    def stars(self, rating):
        html = ""
        for i in range(5):
            color = "text-warning" if i < rating.rating else "text-muted"
            html += f"<i class='fa-solid fa-star {color}'></i>"
        return format_html(html)


class CategoryAdmin(admin.ModelAdmin):
    model = Category
    form = admin_forms.BootstrapModelForm
    list_display = ("__str__", "recommend")
    readonly_fields = ("preview",)
    list_filter = ("recommend",)
    search_fields = (
        "name",
        "description",
    )


class ItemVariantImageInline(admin.StackedInline):
    model = ItemVariantImage
    form = admin_forms.BootstrapModelForm
    extra = 0
    readonly_fields = ("preview",)


class ItemVariantAdmin(admin.ModelAdmin):
    model = ItemVariant
    form = admin_forms.BootstrapModelForm
    inlines = (ItemVariantImageInline,)
    list_display = ("item", "colour")
    search_fields = (
        "item__name",
        "color",
    )

    @admin.display(description=_("color"))
    def colour(self, item_variant):
        html = "<i style='color: {}' class='fa-solid fa-carrot me-2'></i>{}"
        return format_html(html.format(item_variant.color, item_variant.color))


class ItemVariantLinkInline(admin.StackedInline):
    model = ItemVariant
    form = admin_forms.BootstrapModelForm
    show_change_link = True
    extra = 1


class ItemAdmin(admin.ModelAdmin):
    model = Item
    form = admin_forms.BootstrapModelForm
    inlines = (ItemVariantLinkInline,)
    list_display = ("__str__", "subtitle", "recommend")
    list_filter = ("recommend",)
    search_fields = (
        "name",
        "subtitle",
    )


class PurchaseInline(admin.StackedInline):
    model = Purchase
    form = admin_forms.PurchaseInlineAdminForm
    extra = 0


class OrderAdmin(admin.ModelAdmin):
    model = Order
    form = admin_forms.BootstrapModelForm
    inlines = (PurchaseInline,)
    list_display = (
        "id",
        "user",
        "state",
        "timestamp",
        "details",
    )
    list_filter = ("status",)
    search_fields = (
        "user__email",
        "timestamp",
    )

    @admin.display(description=_("state"))
    def state(self, order):
        color, icon = {
            OrderStatus.Delivered: ("success", "check"),
            OrderStatus.Pending: ("muted", "clock"),
            OrderStatus.Cancelled: ("danger", "xmark"),
        }.get(order.status, ("black", "box"))
        return format_html(
            "<b class='text-{}'><i class='fa-solid fa-{} me-1'></i>{}</b>",
            color,
            icon,
            _(OrderStatus(order.status).label),
        )

    @admin.display(description=_("details"))
    def details(self, order):
        template = get_template("admin/addons/order_table.html")
        html = template.render({"instance": order})
        return format_html(html)


class CartItemInline(admin.StackedInline):
    model = CartItem
    form = admin_forms.CartItemInlineAdminForm
    extra = 0


class CartAdmin(admin.ModelAdmin):
    model = Cart
    form = admin_forms.BootstrapModelForm
    inlines = (CartItemInline,)
    list_display = ("id", "email", "details")
    search_fields = ("user__email",)

    @admin.display(description=_("email"))
    def email(self, cart):
        return cart.user.email

    @admin.display(description=_("details"))
    def details(self, cart):
        template = get_template("admin/addons/cart_table.html")
        html = template.render({"instance": cart})
        return format_html(html)


class WishlistItemInline(admin.StackedInline):
    model = WishlistItem
    form = admin_forms.WishlistItemInlineAdminForm
    extra = 0


class WishlistAdmin(admin.ModelAdmin):
    model = Wishlist
    form = admin_forms.BootstrapModelForm
    inlines = (WishlistItemInline,)
    list_display = ("id", "user", "details")
    search_fields = ("user__email",)

    @admin.display(description=_("details"))
    def details(self, wishlist):
        template = get_template("admin/addons/wishlist_table.html")
        html = template.render({"instance": wishlist})
        return format_html(html)


class BannerImageAdmin(admin.ModelAdmin):
    model = BannerImage
    form = admin_forms.BootstrapModelForm
    list_display = ("__str__", "for_mobile")
    readonly_fields = ("preview",)


class CustomerProfileInline(admin.StackedInline):
    model = CustomerProfile
    form = admin_forms.BootstrapModelForm
    can_delete = False
    extra = 0


class MerchantProfileInline(admin.StackedInline):
    model = MerchantProfile
    form = admin_forms.BootstrapModelForm
    can_delete = False
    extra = 0


class UserAdmin(BaseUserAdmin):
    inlines = (
        CustomerProfileInline,
        MerchantProfileInline,
    )
    list_display = ("email", "user_type", "email_verified")
    list_filter = ("is_superuser", "is_active", "email_verified")
    fieldsets = (
        (_("Personal info"), {"fields": ("email", "password", "email_verified")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2"),
            },
        ),
    )
    ordering = ("email",)
    search_fields = ("email",)

    @admin.display(description=_("user type"))
    def user_type(self, user):
        if user.is_superuser:
            return _("Admin")
        elif hasattr(user, "customer"):
            return _("Customer")
        elif hasattr(user, "merchant"):
            return _("Merchant")
        return _("None")
