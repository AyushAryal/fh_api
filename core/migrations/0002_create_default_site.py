# Generated by Django 4.1.7 on 2023-03-03 07:53

from django.db import migrations
from django.conf import settings


def create_site(apps, schema_editor):
    SiteSettings = apps.get_model('core', 'SiteSettings')
    SiteSettings.objects.all().delete()
    SiteSettings.objects.create(pk=settings.SITE_ID, domain="farmerz.com", name="FARMERZ")


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_site)
    ]
