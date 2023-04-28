from rest_framework.permissions import IsAuthenticated, BasePermission

from store.models import CustomerProfile, Order, Cart, Wishlist


class IsCustomer(BasePermission):
    def has_permission(self, request, _):
        return hasattr(request.user, "customer")


class IsMerchant(BasePermission):
    def has_permission(self, request, _):
        return hasattr(request.user, "merchant")


class IsOwner(IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        return request.user.is_superuser or {
            CustomerProfile: self.owns_customer_profile,
            Order: self.owns_order,
            Cart: self.owns_cart,
            Wishlist: self.owns_wishlist,
        }[type(obj)](request, view, obj)

    def owns_customer_profile(self, request, _, customer):
        return hasattr(request.user, "customer") and request.user.customer == customer

    def owns_order(self, request, _, order):
        return request.user == order.user

    def owns_cart(self, request, _, cart):
        return request.user.cart == cart

    def owns_wishlist(self, request, _, wishlist):
        return request.user.wishlist == wishlist
