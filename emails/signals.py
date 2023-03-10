from django.db import models
from django.conf import settings
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.template.loader import get_template
from django.core.mail import send_mail
from django.contrib.sites.models import Site

from core.models import SiteSettings
from store.models import Order
from authentication.signals import new_verification_link, new_password_reset_link


@receiver(models.signals.post_save, sender=Order)
def on_order_changed(sender, instance, *args, **kwargs):
    site = Site.objects.get_current()
    msg = get_template("emails/order_changed.html").render(
        {
            "site": site,
            "admin_email": settings.EMAIL_HOST_USER,
            "order": instance,
        }
    )
    send_mail(
        "Update on your order",
        None,
        settings.EMAIL_HOST_USER,
        [instance.user.email],
        html_message=msg,
    )


@receiver(models.signals.post_save, sender=get_user_model())
def on_new_user(sender, instance, created, *args, **kwargs):
    if created:
        site = SiteSettings.objects.get_current()
        msg = get_template("emails/new_user.html").render(
            {
                "site": site,
                "admin_email": settings.EMAIL_HOST_USER,
                "user": instance,
            }
        )
        send_mail(
            f"Welcome to {site.name}",
            None,
            settings.EMAIL_HOST_USER,
            [instance.email],
            html_message=msg,
        )

        if site.email_admin_on_new_user:
            msg = get_template("emails/admin_new_user.html").render(
                {
                    "site": site,
                    "admin_email": settings.EMAIL_HOST_USER,
                    "user": instance,
                }
            )
            send_mail(
                "New user registration",
                None,
                settings.EMAIL_HOST_USER,
                [settings.EMAIL_HOST_USER],
                html_message=msg,
            )


@receiver(new_verification_link)
def on_new_verification_link(sender, link, user, **kwargs):
    site = Site.objects.get_current()
    msg = get_template("emails/confirm_email.html").render(
        {
            "site": site,
            "admin_email": settings.EMAIL_HOST_USER,
            "link": link,
            "user": user,
        }
    )
    send_mail(
        "Verification Link",
        None,
        settings.EMAIL_HOST_USER,
        [user.email],
        html_message=msg,
    )


@receiver(new_password_reset_link)
def on_new_password_reset_link(sender, link, user, **kwargs):
    site = Site.objects.get_current()
    msg = get_template("emails/password_reset.html").render(
        {
            "site": site,
            "admin_email": settings.EMAIL_HOST_USER,
            "link": link,
            "user": user,
        }
    )
    send_mail(
        "Verification Link",
        None,
        settings.EMAIL_HOST_USER,
        [user.email],
        html_message=msg,
    )
