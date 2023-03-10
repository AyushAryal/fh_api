from django import template

from django.contrib.auth import get_user_model
from core.models import SiteSettings
from store.models import (
    BannerImage,
    Cart,
    Category,
    Item,
    ItemVariant,
    Order,
    Wishlist,
    Rating,
)

register = template.Library()


@register.filter()
def modelicon(model):
    return {
        get_user_model(): "fa-solid fa-user",
        SiteSettings: "fa-solid fa-globe",
        BannerImage: "fa-solid fa-image",
        Cart: "fa-solid fa-cart-shopping",
        Category: "fa-solid fa-list",
        ItemVariant: "fa-solid fa-palette",
        Item: "fa-solid fa-carrot",
        Order: "fa-solid fa-receipt",
        Rating: "fa-solid fa-star",
        Wishlist: "fa-solid fa-wand-sparkles",
    }.get(model.get("model", None), "fa-solid fa-box")


@register.filter()
def appicon(app):
    return {
        "authentication": "fa-solid fa-lock",
        "store": "fa-solid fa-store",
        "core": "fa-brands fa-centercode",
    }.get(app["app_label"], "fa-solid fa-box")
