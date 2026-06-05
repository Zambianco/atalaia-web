from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path

from dashboard.views import dashboard_view, device_detail_view, device_list_view


urlpatterns = [
    path("admin/", admin.site.urls),
    path("login/", auth_views.LoginView.as_view(template_name="auth/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("", dashboard_view, name="dashboard"),
    path("devices/", device_list_view, name="device-list"),
    path("devices/<int:pk>/", device_detail_view, name="device-detail"),
]
