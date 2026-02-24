from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet, 
    LoginView, 
    SystemLogViewSet, 
    DashboardSummaryView, 
    StorageStatsView,
    CustomTokenObtainPairView,
    LogoutView,
    CustomTokenRefreshView,
    ChangePasswordView
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'logs', SystemLogViewSet, basename='system-log')

urlpatterns = [
    path('', include(router.urls)),
    
    # JWT Authentication endpoints
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('auth/change-password/', ChangePasswordView.as_view(), name='change_password'),
    
    # Legacy login endpoint (for backward compatibility)
    path('login/', LoginView.as_view(), name='login_legacy'),
    
    # Dashboard and storage
    path('dashboard/summary/', DashboardSummaryView.as_view(), name='dashboard-summary'),
    path('storage/summary/', StorageStatsView.as_view(), name='storage-summary'),
]
