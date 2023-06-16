"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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
from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from whitelist import views as whitelist_views
from file_formats import views as file_formats_views
from printers import views as printers_views

router = routers.DefaultRouter()
router.register(r'whitelist', whitelist_views.EmailView, 'email')
router.register(r'file_formats', file_formats_views.FileFormatView, 'file_format')
router.register(r'printers', printers_views.PrinterViewSet, 'printer')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls))
]
