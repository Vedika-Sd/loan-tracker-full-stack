from django.contrib import admin
from .models import ApplicationTimeline, LoanApplication, LoanDocument


@admin.register(LoanApplication)
class LoanApplicationAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'amount', 'status', 'created_at']
    list_filter = ['status', 'loan_type']
    search_fields = ['customer__username', 'customer__email']


@admin.register(LoanDocument)
class LoanDocumentAdmin(admin.ModelAdmin):
    list_display = ['id', 'application', 'document_type', 'status', 'verified_by', 'created_at']
    list_filter = ['document_type', 'status']


@admin.register(ApplicationTimeline)
class ApplicationTimelineAdmin(admin.ModelAdmin):
    list_display = ['application', 'status', 'message', 'actor', 'created_at']
    list_filter = ['status']
