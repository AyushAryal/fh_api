from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AdministratorConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "administrator"
    verbose_name = _("Administrator")
