"""
Tests for the accounts app — registration, login, profile, and permissions.
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user_data():
    return {
        'email': 'test@example.com',
        'username': 'testuser',
        'password': 'StrongPass123!',
        'password_confirm': 'StrongPass123!',
        'first_name': 'Test',
        'last_name': 'User',
    }


@pytest.fixture
def create_user():
    def _create(email='user@test.com', password='TestPass123!', **kwargs):
        defaults = {
            'username': email.split('@')[0],
            'first_name': 'Test',
            'last_name': 'User',
            'role': 'BUYER',
        }
        defaults.update(kwargs)
        user = User.objects.create_user(
            email=email,
            password=password,
            **defaults,
        )
        return user
    return _create


@pytest.fixture
def authenticated_client(api_client, create_user):
    user = create_user()
    api_client.force_authenticate(user=user)
    return api_client, user


@pytest.mark.django_db
class TestRegistration:
    """Tests for user registration endpoint."""

    def test_register_success(self, api_client, user_data):
        response = api_client.post('/api/auth/register/', user_data)
        assert response.status_code == status.HTTP_201_CREATED
        assert 'tokens' in response.data
        assert 'user' in response.data
        assert response.data['user']['email'] == user_data['email']

    def test_register_duplicate_email(self, api_client, user_data, create_user):
        create_user(email=user_data['email'])
        response = api_client.post('/api/auth/register/', user_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_password_mismatch(self, api_client, user_data):
        user_data['password_confirm'] = 'DifferentPass123!'
        response = api_client.post('/api/auth/register/', user_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_weak_password(self, api_client, user_data):
        user_data['password'] = '123'
        user_data['password_confirm'] = '123'
        response = api_client.post('/api/auth/register/', user_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_missing_fields(self, api_client):
        response = api_client.post('/api/auth/register/', {})
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestLogin:
    """Tests for user login endpoint."""

    def test_login_success(self, api_client, create_user):
        create_user(email='login@test.com', password='TestPass123!')
        response = api_client.post('/api/auth/login/', {
            'email': 'login@test.com',
            'password': 'TestPass123!',
        })
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data

    def test_login_wrong_password(self, api_client, create_user):
        create_user(email='login@test.com', password='TestPass123!')
        response = api_client.post('/api/auth/login/', {
            'email': 'login@test.com',
            'password': 'WrongPass123!',
        })
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_nonexistent_user(self, api_client):
        response = api_client.post('/api/auth/login/', {
            'email': 'nobody@test.com',
            'password': 'TestPass123!',
        })
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestProfile:
    """Tests for user profile endpoint."""

    def test_get_profile_authenticated(self, authenticated_client):
        client, user = authenticated_client
        response = client.get('/api/auth/me/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == user.email

    def test_get_profile_unauthenticated(self, api_client):
        response = api_client.get('/api/auth/me/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_profile(self, authenticated_client):
        client, user = authenticated_client
        response = client.patch('/api/auth/me/', {
            'first_name': 'Updated',
        })
        assert response.status_code == status.HTTP_200_OK
        assert response.data['first_name'] == 'Updated'
