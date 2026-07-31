"""
URL configuration for the accounts app.
"""

from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('refresh/', views.RefreshTokenView.as_view(), name='token-refresh'),
    path('me/', views.ProfileView.as_view(), name='profile'),
    path('users/', views.UserListView.as_view(), name='user-list'),
    path('dashboard/', views.DashboardStatsView.as_view(), name='dashboard-stats'),
]
