from django.db import models
from django.conf import settings


class LoanApplication(models.Model):
	class Status(models.TextChoices):
		ENQUIRY = 'enquiry', 'Enquiry'
		DOCUMENTS_SUBMITTED = 'documents_submitted', 'Documents submitted'
		DOCUMENTS_REJECTED = 'documents_rejected', 'Documents rejected'
		APPROVED = 'approved', 'Approved'
		REJECTED = 'rejected', 'Rejected'
		DISBURSED = 'disbursed', 'Disbursed'

	customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='loan_applications')
	loan_type = models.CharField(max_length=30, default='personal_loan', editable=False)
	amount = models.DecimalField(max_digits=12, decimal_places=2)
	tenure_months = models.PositiveIntegerField()
	status = models.CharField(max_length=30, choices=Status.choices, default=Status.ENQUIRY)
	rejection_reason = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['-created_at']


class LoanDocument(models.Model):
	class DocumentType(models.TextChoices):
		ID_PROOF = 'id_proof', 'ID proof'
		INCOME_PROOF = 'income_proof', 'Income proof'
		ADDRESS_PROOF = 'address_proof', 'Address proof'

	class Status(models.TextChoices):
		PENDING = 'pending', 'Pending'
		VERIFIED = 'verified', 'Verified'
		REJECTED = 'rejected', 'Rejected'

	application = models.ForeignKey(LoanApplication, on_delete=models.CASCADE, related_name='documents')
	document_type = models.CharField(max_length=20, choices=DocumentType.choices)
	original_name = models.CharField(max_length=255)
	storage_path = models.CharField(max_length=500)
	content_type = models.CharField(max_length=100, blank=True)
	status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
	rejection_reason = models.TextField(blank=True)
	verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='verified_documents')
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		constraints = [
			models.UniqueConstraint(fields=['application', 'document_type'], name='one_document_per_type'),
		]


class ApplicationTimeline(models.Model):
	application = models.ForeignKey(LoanApplication, on_delete=models.CASCADE, related_name='timeline')
	status = models.CharField(max_length=30, choices=LoanApplication.Status.choices)
	message = models.CharField(max_length=255)
	actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['created_at']
