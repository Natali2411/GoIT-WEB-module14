import json
from unittest.mock import MagicMock, AsyncMock

import pytest
import sqlalchemy

from src.database.models import User
from src.repository import users


@pytest.mark.asyncio
async def test_create_user(session, client, user, monkeypatch):
    mock_send_email = MagicMock()
    monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)

    mock_get_user_by_email = AsyncMock()
    mock_get_user_by_email.return_value = False
    monkeypatch.setattr("src.repository.users.get_user_by_email", mock_get_user_by_email)

    response = client.post(
        "/api/auth/users",
        json=user,
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["user"]["email"] == user.get("email")
    assert "id" in data["user"]

@pytest.mark.asyncio
async def test_repeat_create_user(client, user, session, monkeypatch):
    def post_user():
        return client.post(
            "/api/auth/users",
            json=user,
        )

    await users.remove_user(email=user.get("email"), db=session)

    mock_get_user_by_email = AsyncMock()
    mock_get_user_by_email.return_value = False
    monkeypatch.setattr("src.repository.users.get_user_by_email", mock_get_user_by_email)
    response = post_user()
    assert response.status_code == 201, response.text

    mock_get_user_by_email.return_value = response.json()
    response2 = post_user()
    assert response2.status_code == 409, response2.text
    data = response2.json()
    assert data["detail"] == f"User with the email {user.get('email')} already exists"

@pytest.mark.asyncio
async def test_login_user_not_confirmed(client, user, post_user):
    response = client.post(
        "/api/auth/access_token",
        data=json.dumps({"email": user.get('email'), "password": user.get('password')}),
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Email not confirmed"

@pytest.mark.asyncio
async def test_login_user(monkeypatch, client, session, user, post_user):
    current_user = session.query(User).filter(User.email == user.get("email")).first()
    current_user.confirmed = True
    session.commit()

    mock_get_user_by_email = AsyncMock()
    mock_get_user_by_email.return_value = current_user
    monkeypatch.setattr("src.repository.users.get_user_by_email", mock_get_user_by_email)

    response = client.post(
        "/api/auth/access_token",
        data=json.dumps({"email": user.get('email'), "password": user.get('password')}),
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_wrong_password(client, user, post_user):
    response = client.post(
        "/api/auth/access_token",
        data=json.dumps({"email": user.get('email'), "password": 'password'})
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Invalid password"

@pytest.mark.asyncio
async def test_login_wrong_email(client, user):
    response = client.post(
        "/api/auth/access_token",
        data=json.dumps({"email": 'email@test.com', "password": user.get('password')})
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Invalid email"