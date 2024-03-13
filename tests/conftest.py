import json
from typing import List
from unittest.mock import MagicMock, AsyncMock

import pytest
import sqlalchemy
from fastapi.testclient import TestClient
from fastapi_limiter.depends import RateLimiter
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from src.conf.config import settings
from src.database.models import Base, User
from src.database.db import get_db
from src.repository.users import get_current_user
from src.routes import rate_limiter
from src.schemas import UserDb, ChannelType

engine = create_engine(settings.sqlalchemy_test_database_url)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="module")
def session():
    # Create the database
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module")
def client(session):
    # Dependency override

    def override_get_db():
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[rate_limiter] = lambda: AsyncMock(spec=RateLimiter)
    # app.dependency_overrides[get_current_user] = True

    yield TestClient(app)


@pytest.fixture(scope="module")
def user():
    return {"email": "deadpool@example.com", "password": "123456789"}


@pytest.fixture()
def post_user(client, user, session, monkeypatch):
    # create user
    mock_get_user_by_email = AsyncMock()
    mock_get_user_by_email.return_value = False
    monkeypatch.setattr("src.repository.users.get_user_by_email", mock_get_user_by_email)
    try:
        client.post(
            "/api/auth/users",
            json=user,
        ).json().get("user").get("email")
    except sqlalchemy.exc.IntegrityError:
        print(f"User with email {user.get('email')} already exist")
    monkeypatch.undo()
    yield user.get('email')


@pytest.fixture()
def user_login(session, user, post_user, client, monkeypatch):
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
    monkeypatch.undo()
    return response.json()


@pytest.fixture()
def create_channels(session, client, user_login):
    channels: List[ChannelType] = [ChannelType.PHONE.value, ChannelType.EMAIL.value,
                                   ChannelType.POST.value]
    for channel in channels:
        try:
            client.post(
                "/api/channels/",
                data=json.dumps({"name": channel}),
                headers={"Authorization": f"Bearer {user_login.get('access_token')}"}
            )
        except sqlalchemy.exc.IntegrityError:
            print(f"Channel with a name {channel} already exist")
    yield channels
    get_channels = client.get(
        "/api/channels/",
        headers={"Authorization": f"Bearer {user_login.get('access_token')}"}
    ).json()
    for channel in get_channels:
        client.delete(
            f"/api/channels/{channel.get('id')}",
            headers={"Authorization": f"Bearer {user_login.get('access_token')}"}
        )
