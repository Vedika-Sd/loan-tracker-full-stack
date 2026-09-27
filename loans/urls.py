from django.urls import path

from .views import (
    ApplicationDetailView,
    ApplicationListCreateView,
    DashboardView,
    DocumentUploadView,
    DocumentVerificationView,
    LoanDecisionView,
    DisbursementView,
)

urlpatterns = [
    path('', ApplicationListCreateView.as_view(), name='application-list'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('<int:application_id>/', ApplicationDetailView.as_view(), name='application-detail'),
    path('<int:application_id>/documents/', DocumentUploadView.as_view(), name='document-upload'),
    path('<int:application_id>/documents/<int:document_id>/verify/', DocumentVerificationView.as_view(), name='document-verify'),
    path('<int:application_id>/decision/', LoanDecisionView.as_view(), name='loan-decision'),
    path('<int:application_id>/disburse/', DisbursementView.as_view(), name='loan-disburse'),
]