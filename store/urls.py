from rest_framework import routers

from . import views

app_name = "store"

router = routers.DefaultRouter()

router.register("customer", views.CustomerProfileViewSet, basename="customer")
router.register("item", views.ItemViewSet, basename="item")
router.register("category", views.CategoryViewSet, basename="category")
router.register("order", views.OrderViewSet, basename="order")
router.register("cart", views.CartViewSet, basename="cart")
router.register("wishlist", views.WishlistViewSet, basename="wishlist")
router.register("banner", views.BannerImageViewSet, basename="banner")
