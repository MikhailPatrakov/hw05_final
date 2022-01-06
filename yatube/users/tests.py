from http import HTTPStatus

from django.test import Client, TestCase


class UserURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_signup_page(self):
        response = self.guest_client.get('/auth/signup/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_logout_page(self):
        response = self.guest_client.get('/auth/logout/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_login_page(self):
        response = self.guest_client.get('/auth/login/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
