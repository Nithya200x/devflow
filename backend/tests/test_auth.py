import os
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

import pytest
from app import create_app
from extensions import db as _db
from models import User


@pytest.fixture
def app():
    application = create_app()
    application.config['TESTING'] = True
    application.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with application.app_context():
        _db.create_all()
        yield application
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def seeded_user(app):
    with app.app_context():
        user = User.query.filter_by(username="testuser").first()
        if not user:
            user = User(name="Test User", email="test@example.com", username="testuser", role="developer")
            user.set_password("testpass123")
            _db.session.add(user)
            _db.session.commit()
        return user


class TestRegister:
    def test_register_success(self, client):
        resp = client.post('/api/v1/auth/register', json={
            'name': 'New User',
            'email': 'new@example.com',
            'username': 'newuser',
            'password': 'secure123'
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert 'access_token' in data
        assert data['user']['username'] == 'newuser'
        assert data['user']['email'] == 'new@example.com'
        assert data['user']['name'] == 'New User'

    def test_register_missing_fields(self, client):
        resp = client.post('/api/v1/auth/register', json={
            'name': '',
            'email': '',
            'username': '',
            'password': ''
        })
        assert resp.status_code == 400
        assert resp.get_json()['msg'] == 'Name is required'

    def test_register_invalid_email(self, client):
        resp = client.post('/api/v1/auth/register', json={
            'name': 'User',
            'email': 'not-an-email',
            'username': 'user',
            'password': 'secure123'
        })
        assert resp.status_code == 400
        assert resp.get_json()['msg'] == 'Invalid email format'

    def test_register_short_password(self, client):
        resp = client.post('/api/v1/auth/register', json={
            'name': 'User',
            'email': 'u@example.com',
            'username': 'user',
            'password': '123'
        })
        assert resp.status_code == 400
        assert resp.get_json()['msg'] == 'Password must be at least 6 characters'

    def test_register_duplicate_username(self, client, seeded_user):
        resp = client.post('/api/v1/auth/register', json={
            'name': 'Other',
            'email': 'other@example.com',
            'username': 'testuser',
            'password': 'secure123'
        })
        assert resp.status_code == 400
        assert resp.get_json()['msg'] == 'Username already taken'

    def test_register_duplicate_email(self, client, seeded_user):
        resp = client.post('/api/v1/auth/register', json={
            'name': 'Other',
            'email': 'test@example.com',
            'username': 'other',
            'password': 'secure123'
        })
        assert resp.status_code == 400
        assert resp.get_json()['msg'] == 'Email already registered'

    def test_register_no_body(self, client):
        resp = client.post('/api/v1/auth/register', json={})
        assert resp.status_code == 400


class TestLogin:
    def test_login_success(self, client, seeded_user):
        resp = client.post('/api/v1/auth/login', json={
            'username': 'testuser',
            'password': 'testpass123'
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'access_token' in data
        assert data['user']['username'] == 'testuser'

    def test_login_user_not_found(self, client):
        resp = client.post('/api/v1/auth/login', json={
            'username': 'nonexistent',
            'password': 'password'
        })
        assert resp.status_code == 401
        assert resp.get_json()['msg'] == 'User not found'

    def test_login_wrong_password(self, client, seeded_user):
        resp = client.post('/api/v1/auth/login', json={
            'username': 'testuser',
            'password': 'wrongpass'
        })
        assert resp.status_code == 401
        assert resp.get_json()['msg'] == 'Invalid password'

    def test_login_missing_credentials(self, client):
        resp = client.post('/api/v1/auth/login', json={
            'username': '',
            'password': ''
        })
        assert resp.status_code == 400
        assert resp.get_json()['msg'] == 'Username and password are required'

    def test_login_no_body(self, client):
        resp = client.post('/api/v1/auth/login', json={})
        assert resp.status_code == 400
        assert resp.get_json()['msg'] == 'Request body is required'
