from rest_framework import routers

from . import views

app_name = "authentication"

router = routers.DefaultRouter()

router.register("user", views.UserViewSet, basename="user")
router.register("token", views.TokenViewSet, basename="token")
