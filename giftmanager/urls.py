"""
URL configuration for giftmanager project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from django.urls import path
from gifts.views import home, gift_list, family_select, register, add_gift, account, notifications
from django.urls import re_path
from django.conf.urls import include
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", gift_list, name="home"),
    path("family/", family_select, name="family-select"),
    path('register/', register, name='register'),
    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
    path("gift/add/", add_gift, name="add_gift"),
    path("account/", account, name="account"),
    path("notifications/", notifications, name="notifications")
]

urlpatterns += [
    path('accounts/', include('django.contrib.auth.urls')),]