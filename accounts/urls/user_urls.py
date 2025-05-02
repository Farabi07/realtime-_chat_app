from accounts.views import user_views as views
from django.urls import path

urlpatterns = [
    path('signup/', views.register),
    path('login/', views.login),
    path('token/refresh/', views.token_refresh_view),
    path('reset-password/', views.reset_password)
]