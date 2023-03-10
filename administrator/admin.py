from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.urls import path
from django.utils.translation import gettext_lazy as _

from . import models as admin_models
from core.models import SiteSettings
from store.models import (
    Category,
    Item,
    ItemVariant,
    Order,
    Cart,
    Wishlist,
    Rating,
    BannerImage,
)
from . import views


class SiteComputedProperty:
    def __init__(self, property_name):
        self.property_name = property_name

    def __str__(self):
        return getattr(Site.objects.get_current(), self.property_name)


class MainAdminSite(admin.AdminSite):
    site_title = _("Dashboard")
    site_header = _("Admin Dashboard")
    index_title = SiteComputedProperty("name")

    def get_urls(self):
        urls = super().get_urls()
        extra_urls = [
            path("brief_info", self.admin_view(views.brief_info), name="brief_info"),
            path(
                "recent_orders/<int:count>",
                self.admin_view(views.recent_orders),
                name="recent_orders",
            ),
            path(
                "top_items/<int:count>",
                self.admin_view(views.top_items),
                name="top_items",
            ),
            path(
                "top_categories/<int:count>",
                self.admin_view(views.top_categories),
                name="top_categories",
            ),
            path(
                "user_activity/<int:count>",
                self.admin_view(views.user_activity),
                name="user_activity",
            ),
        ]
        return extra_urls + urls


admin_site = MainAdminSite()
admin_site.register(SiteSettings, admin_models.SiteSettingsAdmin)
admin_site.register(Category, admin_models.CategoryAdmin)
admin_site.register(ItemVariant, admin_models.ItemVariantAdmin)
admin_site.register(Item, admin_models.ItemAdmin)
admin_site.register(Order, admin_models.OrderAdmin)
admin_site.register(Cart, admin_models.CartAdmin)
admin_site.register(Wishlist, admin_models.WishlistAdmin)
admin_site.register(Rating, admin_models.RatingAdmin)
admin_site.register(BannerImage, admin_models.BannerImageAdmin)
admin_site.register(get_user_model(), admin_models.UserAdmin)
