from unittest.mock import patch

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from .models import LoanApplication, LoanDocument


class LoanWorkflowTests(APITestCase):
	def setUp(self):
		user_model = get_user_model()
		self.customer = user_model.objects.create_user(username='customer', password='pass1234', role='customer')
		self.officer = user_model.objects.create_user(username='officer', password='pass1234', role='officer')
		self.application = LoanApplication.objects.create(customer=self.customer, amount='10000', tenure_months=12)

	def authenticate(self, user):
		self.client.force_authenticate(user=user)

	def test_customer_can_create_and_read_only_own_applications(self):
		self.authenticate(self.customer)
		response = self.client.get('/api/loans/')
		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(response.data), 1)

		response = self.client.get('/api/loans/dashboard/')
		self.assertEqual(response.status_code, 403)

	def test_officer_cannot_approve_until_all_documents_are_verified(self):
		self.authenticate(self.officer)
		response = self.client.post(f'/api/loans/{self.application.id}/decision/', {'decision': 'approve'}, format='json')
		self.assertEqual(response.status_code, 400)

	@patch('loans.views.upload_document', return_value=('customer/application/file.pdf', 'application/pdf'))
	def test_customer_can_replace_rejected_document(self, upload_document):
		self.authenticate(self.customer)
		response = self.client.post(
			f'/api/loans/{self.application.id}/documents/',
			{'document_type': 'id_proof', 'file': self._file()},
		)
		self.assertEqual(response.status_code, 201)
		document = LoanDocument.objects.get(application=self.application, document_type='id_proof')

		self.authenticate(self.officer)
		response = self.client.post(
			f'/api/loans/{self.application.id}/documents/{document.id}/verify/',
			{'status': LoanDocument.Status.REJECTED, 'reason': 'Image is not readable.'},
			format='json',
		)
		self.assertEqual(response.status_code, 200)

		self.authenticate(self.customer)
		response = self.client.post(
			f'/api/loans/{self.application.id}/documents/',
			{'document_type': 'id_proof', 'file': self._file()},
		)
		self.assertEqual(response.status_code, 201)
		document.refresh_from_db()
		self.assertEqual(document.status, LoanDocument.Status.PENDING)
		self.assertEqual(document.rejection_reason, '')

	@patch('loans.views.upload_document', return_value=('customer/application/file.pdf', 'application/pdf'))
	def test_document_upload_and_full_workflow(self, upload_document):
		self.authenticate(self.customer)
		for document_type in ('id_proof', 'income_proof', 'address_proof'):
			response = self.client.post(
				f'/api/loans/{self.application.id}/documents/',
				{'document_type': document_type, 'file': self._file()},
			)
			self.assertEqual(response.status_code, 201)
		self.application.refresh_from_db()
		self.assertEqual(self.application.status, LoanApplication.Status.DOCUMENTS_SUBMITTED)

		self.authenticate(self.officer)
		for document in self.application.documents.all():
			response = self.client.post(
				f'/api/loans/{self.application.id}/documents/{document.id}/verify/',
				{'status': LoanDocument.Status.VERIFIED},
				format='json',
			)
			self.assertEqual(response.status_code, 200)
		response = self.client.post(f'/api/loans/{self.application.id}/decision/', {'decision': 'approve'}, format='json')
		self.assertEqual(response.status_code, 200)
		response = self.client.post(f'/api/loans/{self.application.id}/disburse/', {}, format='json')
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data['status'], LoanApplication.Status.DISBURSED)
		self.assertEqual(len(response.data['timeline']), 6)

	@staticmethod
	def _file():
		from django.core.files.uploadedfile import SimpleUploadedFile
		return SimpleUploadedFile('proof.pdf', b'%PDF-1.4 demo', content_type='application/pdf')
