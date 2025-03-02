from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.urls import reverse


class SimpleJWTTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='testpassword')
        self.token_url = reverse('token_obtain_pair')
        self.refresh_url = reverse('token_refresh')

    def test_token_obtain_pair(self):
        response = self.client.post(
            self.token_url, {'username': 'testuser', 'password': 'testpassword'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_token_refresh(self):
        refresh = RefreshToken.for_user(self.user)
        response = self.client.post(
            self.refresh_url, {'refresh': str(refresh)})
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)
