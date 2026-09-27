from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase


class AuthenticationTests(APITestCase):
	def test_customer_can_register_and_login_with_jwt(self):
		response = self.client.post(
			'/api/auth/register/',
			{'username': 'new-customer', 'email': 'customer@example.com', 'password': 'pass1234', 'role': 'customer'},
			format='json',
		)
		self.assertEqual(response.status_code, 201)
		self.assertEqual(response.data['role'], get_user_model().Role.CUSTOMER)

		response = self.client.post(
			'/api/auth/login/',
			{'username': 'new-customer', 'password': 'pass1234'},
			format='json',
		)
		self.assertEqual(response.status_code, 200)
		self.assertIn('access', response.data)
		self.assertIn('refresh', response.data)

	def test_public_registration_cannot_create_officer(self):
		response = self.client.post(
			'/api/auth/register/',
			{'username': 'bad-officer', 'email': 'officer@example.com', 'password': 'pass1234', 'role': 'officer'},
			format='json',
		)
		self.assertEqual(response.status_code, 400)
