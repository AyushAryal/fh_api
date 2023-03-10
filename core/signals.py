from django.db.models.signals import pre_save, pre_delete
from django.contrib.sites.models import clear_site_cache
from .models import SiteSettings

# Updating/Deleting site settings should also invalidate cache.
pre_save.connect(clear_site_cache, sender=SiteSettings)
pre_delete.connect(clear_site_cache, sender=SiteSettings)
