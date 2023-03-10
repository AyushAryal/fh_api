"""farmerz_api URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.urls import path, include, re_path
from django.conf.urls.static import static
from django.views.generic.base import RedirectView, TemplateView

from .router import FarmerzRouter
from authentication.urls import router as authentication_router
from store.urls import router as store_router

favicon_view = RedirectView.as_view(url='/static/favicon.ico', permanent=True)

router = FarmerzRouter()
router.registry.extend(authentication_router.registry)
router.registry.extend(store_router.registry)

urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),
    path('admin/', include('administrator.urls')),
    path('api/', include((router.urls, 'api'))),
    path('ckeditor/', include('ckeditor_uploader.urls')),
    re_path(r'^favicon\.ico$', favicon_view),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# login for browsable api only on development
if settings.DEBUG:
    urlpatterns += [
        path('api-auth/', include('rest_framework.urls', namespace='rest_framework'))
    ]
