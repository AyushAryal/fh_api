from django.db import models
from django.contrib.sites.models import Site
from django.utils.translation import gettext_lazy as _


class SiteSettings(Site):
    class Meta:
        verbose_name = _("site settings")
        verbose_name_plural = _("site settings")

    email_admin_on_new_user = models.BooleanField(
        default=True,
        verbose_name=_("Email admin on new user"),
        help_text=_("Email admin when a new user has registered"),
    )
