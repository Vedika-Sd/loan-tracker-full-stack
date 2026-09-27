from django.db.models import Count
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ApplicationTimeline, LoanApplication, LoanDocument
from .permissions import IsCustomer, IsOfficer
from .serializers import LoanApplicationCreateSerializer, LoanApplicationSerializer
from .storage import upload_document

REQUIRED_DOCUMENTS = {choice[0] for choice in LoanDocument.DocumentType.choices}


def application_for_user(request, application_id):
	queryset = LoanApplication.objects.prefetch_related('documents', 'timeline').select_related('customer')
	if request.user.is_officer():
		return get_object_or_404(queryset, id=application_id)
	return get_object_or_404(queryset, id=application_id, customer=request.user)


def add_event(application, actor, message, status_value=None):
	ApplicationTimeline.objects.create(application=application, actor=actor, status=status_value or application.status, message=message)


class ApplicationListCreateView(generics.ListCreateAPIView):
	serializer_class = LoanApplicationSerializer

	def get_queryset(self):
		queryset = LoanApplication.objects.prefetch_related('documents', 'timeline').select_related('customer')
		return queryset if self.request.user.is_officer() else queryset.filter(customer=self.request.user)

	def get_permissions(self):
		return [IsCustomer()] if self.request.method == 'POST' else [permissions.IsAuthenticated()]

	def create(self, request, *args, **kwargs):
		serializer = LoanApplicationCreateSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		application = serializer.save(customer=request.user)
		add_event(application, request.user, 'Loan enquiry submitted', LoanApplication.Status.ENQUIRY)
		return Response(LoanApplicationSerializer(application).data, status=status.HTTP_201_CREATED)


class ApplicationDetailView(APIView):
	permission_classes = [permissions.IsAuthenticated]

	def get(self, request, application_id):
		return Response(LoanApplicationSerializer(application_for_user(request, application_id)).data)


class DocumentUploadView(APIView):
	permission_classes = [IsCustomer]
	parser_classes = [MultiPartParser, FormParser]

	def post(self, request, application_id):
		application = get_object_or_404(LoanApplication, id=application_id, customer=request.user)
		document_type = request.data.get('document_type')
		upload = request.FILES.get('file')
		if document_type not in REQUIRED_DOCUMENTS:
			return Response({'detail': 'document_type must be id_proof, income_proof, or address_proof.'}, status=400)
		if not upload:
			return Response({'detail': 'A file is required.'}, status=400)
		existing_document = LoanDocument.objects.filter(application=application, document_type=document_type).first()
		if existing_document and existing_document.status != LoanDocument.Status.REJECTED:
			return Response({'detail': 'That document type has already been uploaded.'}, status=400)
		storage_path, content_type = upload_document(upload, request.user.id, application.id)
		if existing_document:
			document = existing_document
			document.original_name = upload.name
			document.storage_path = storage_path
			document.content_type = content_type
			document.status = LoanDocument.Status.PENDING
			document.rejection_reason = ''
			document.verified_by = None
			document.save(update_fields=['original_name', 'storage_path', 'content_type', 'status', 'rejection_reason', 'verified_by', 'updated_at'])
		else:
			document = LoanDocument.objects.create(application=application, document_type=document_type, original_name=upload.name, storage_path=storage_path, content_type=content_type)
		if set(application.documents.values_list('document_type', flat=True)) | {document_type} == REQUIRED_DOCUMENTS:
			application.status = LoanApplication.Status.DOCUMENTS_SUBMITTED
			application.save(update_fields=['status', 'updated_at'])
			add_event(application, request.user, 'All required documents uploaded')
		return Response({'id': document.id, 'document_type': document.document_type, 'status': document.status}, status=status.HTTP_201_CREATED)


class DocumentVerificationView(APIView):
	permission_classes = [IsOfficer]

	def post(self, request, application_id, document_id):
		application = get_object_or_404(LoanApplication, id=application_id)
		document = get_object_or_404(LoanDocument, id=document_id, application=application)
		verified = request.data.get('status') == LoanDocument.Status.VERIFIED
		document.status = LoanDocument.Status.VERIFIED if verified else LoanDocument.Status.REJECTED
		document.rejection_reason = '' if verified else request.data.get('reason', 'Document was rejected.')
		document.verified_by = request.user
		document.save(update_fields=['status', 'rejection_reason', 'verified_by', 'updated_at'])
		if not verified:
			application.status = LoanApplication.Status.DOCUMENTS_REJECTED
			application.rejection_reason = document.rejection_reason
			application.save(update_fields=['status', 'rejection_reason', 'updated_at'])
		add_event(application, request.user, f'{document.get_document_type_display()} {document.status}', application.status)
		return Response(LoanApplicationSerializer(application_for_user(request, application.id)).data)


class LoanDecisionView(APIView):
	permission_classes = [IsOfficer]

	def post(self, request, application_id):
		application = get_object_or_404(LoanApplication, id=application_id)
		decision = request.data.get('decision')
		if decision not in ('approve', 'reject'):
			return Response({'detail': 'decision must be approve or reject.'}, status=400)
		if decision == 'approve' and set(application.documents.filter(status=LoanDocument.Status.VERIFIED).values_list('document_type', flat=True)) != REQUIRED_DOCUMENTS:
			return Response({'detail': 'All three documents must be verified before approval.'}, status=400)
		application.status = LoanApplication.Status.APPROVED if decision == 'approve' else LoanApplication.Status.REJECTED
		application.rejection_reason = '' if decision == 'approve' else request.data.get('reason', 'Application was rejected.')
		application.save(update_fields=['status', 'rejection_reason', 'updated_at'])
		add_event(application, request.user, f'Loan application {application.status}', application.status)
		return Response(LoanApplicationSerializer(application_for_user(request, application.id)).data)


class DisbursementView(APIView):
	permission_classes = [IsOfficer]

	def post(self, request, application_id):
		application = get_object_or_404(LoanApplication, id=application_id)
		if application.status != LoanApplication.Status.APPROVED:
			return Response({'detail': 'Only approved applications can be disbursed.'}, status=400)
		application.status = LoanApplication.Status.DISBURSED
		application.save(update_fields=['status', 'updated_at'])
		add_event(application, request.user, 'Loan marked as disbursed', application.status)
		return Response(LoanApplicationSerializer(application_for_user(request, application.id)).data)


class DashboardView(APIView):
	permission_classes = [IsOfficer]

	def get(self, request):
		counts = LoanApplication.objects.values('status').annotate(count=Count('id'))
		result = {status_value: 0 for status_value, _ in LoanApplication.Status.choices}
		result.update({row['status']: row['count'] for row in counts})
		return Response({'counts': result})
