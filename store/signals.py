from django.contrib.auth import get_user_model
from django.db import models
from django.dispatch import receiver

from .models import Cart, Wishlist


@receiver(models.signals.post_save, sender=get_user_model())
def create_cart(sender, instance, *args, **kwargs):
    if not Cart.objects.filter(user=instance).exists():
        Cart.objects.create(user=instance)


@receiver(models.signals.post_save, sender=get_user_model())
def create_wishlist(sender, instance, *args, **kwargs):
    if not Wishlist.objects.filter(user=instance).exists():
        Wishlist.objects.create(user=instance)
