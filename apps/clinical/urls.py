from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PatientViewSet,
    AlertViewSet, 
    AlertStatsView, 
    DoctorDashboardSummaryView, 
    DoctorScheduledTasksView, 
    WoundStatsView,
    DoctorDashboardStatsView,
    DoctorTaskViewSet,
    NurseDashboardStatsView,
    NurseTaskViewSet,
    NurseClinicalViewSet
)

router = DefaultRouter()
router.register(r'patients', PatientViewSet, basename='patient')
router.register(r'alerts', AlertViewSet, basename='alert')
router.register(r'doctor/tasks', DoctorTaskViewSet, basename='doctor-tasks')
router.register(r'nurse/tasks', NurseTaskViewSet, basename='nurse-tasks')
router.register(r'nurse/clinical', NurseClinicalViewSet, basename='nurse-clinical')

urlpatterns = [
    path('', include(router.urls)),
    path('alert-stats/', AlertStatsView.as_view(), name='alert-stats'),
    path('doctor/summary/', DoctorDashboardSummaryView.as_view(), name='doctor-summary'),
    path('doctor/schedule/', DoctorScheduledTasksView.as_view(), name='doctor-schedule'),
    path('doctor/stats/', WoundStatsView.as_view(), name='doctor-stats'),
    
    # New segregated stats endpoints
    path('doctor/dashboard-stats/', DoctorDashboardStatsView.as_view(), name='doctor-dashboard-stats'),
    path('nurse/dashboard-stats/', NurseDashboardStatsView.as_view(), name='nurse-dashboard-stats'),
]
