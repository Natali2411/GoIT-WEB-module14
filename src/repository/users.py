from __future__ import annotations

import pickle
from typing import Type

import redis
from fastapi import Depends
from fastapi_jwt_auth import AuthJWT
from libgravatar import Gravatar
from sqlalchemy.orm import Session

from src.conf.config import settings
from src.database.db import get_db
from src.database.models import User
from src.schemas import UserModel

r = redis.Redis(host=settings.redis_host, port=settings.redis_port)


async def get_user_by_email(email: str, db: Session) -> Type[User] | bool:
    """
    The get_user_by_email function takes in an email and a database session.
    It then checks the Redis cache for a user with that email, if it finds one, it returns the user object.
    If not, it queries the database for that user and stores them in Redis before returning them.

    :param email: Get the user by email
    :type email: str
    :param db: Connect to the database
    :type db: Session
    :return: A user object if the email exists in the database
    :rtype: Type[User] | bool
    """
    current_user = r.get(f"user:{email}")
    if current_user is None:
        current_user = db.query(User).filter(User.email == email).first()
        if current_user is None:
            return False
        r.set(f"user:{email}", pickle.dumps(current_user))
        r.expire(f"user:{email}", 900)
    else:
        current_user = pickle.loads(current_user)
    return current_user


async def create_user(body: UserModel, db: Session) -> User:
    """
    The create_user function creates a new user in the database.

    :param body: Create a new user object
    :type body: UserModel
    :param db: Pass the database session to the function
    :type db: Session
    :return: A user object
    :rtype: User
    """
    avatar = None
    try:
        g = Gravatar(body.email)
        avatar = g.get_image()
    except Exception as e:
        print(e)
    new_user = User(**body.dict(), avatar=avatar)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


async def remove_user(email: str, db: Session) -> User:
    """
    The remove_user function deletes a user in the database.

    :param email: User email
    :type email: str
    :param db: Pass the database session to the function
    :type db: Session
    :return: A user object
    :rtype: User
    """
    exist_user = await get_user_by_email(email, db)
    if exist_user:
        db.query(User).delete()
        db.commit()


async def update_token(user: User, token: str | None, db: Session) -> None:
    """
    The update_token function updates the refresh token for a user.

    :param user: Identify the user that is being updated
    :type user: User
    :param token: Update the refresh token in the database
    :type token: str | None
    :param db: Pass the database session to the function
    :type db: Session
    :return: None
    :rtype: None
    """
    user.refresh_token = token
    db.commit()


async def get_current_user(
    Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)
) -> Type[User]:
    """
    The get_current_user function is a dependency that can be used to get the current user.
    It will use the JWT token in the Authorization header to retrieve and return a User object.

    :param Authorize: Get the current user's email
    :type Authorize: AuthJWT
    :param db: Get the database session
    :type db: Session
    :return: The current user
    :rtype: Type[User]
    """
    Authorize.jwt_required()

    email = Authorize.get_jwt_subject()

    return await get_user_by_email(email, db)


async def update_avatar(email: str, url: str, db: Session) -> Type[User] | None:
    """
    The update_avatar function updates the avatar of a user in the database.

    :param email: Identify the user we want to update
    :type email: str
    :param url: Update the avatar url of a user
    :type url: str
    :param db: Pass in the database session object
    :type db: Session
    :return: A user object if a user is found, or none if no user is found
    :rtype: Type[User] | None
    """
    user = await get_user_by_email(email, db)
    user.avatar = url
    db.commit()
    return user


async def confirm_email(email: str, db: Session) -> None:
    """
    The confirm_email function takes an email and a database session as arguments.
    It then gets the user with that email from the database, sets their confirmed field to True,
    and commits those changes to the database.

    :param email: Get the user's email address
    :type email: str
    :param db: Pass the database session to the function
    :type db: Session
    :return: None
    :rtype: None
    :doc-author: Trelent
    """
    user = await get_user_by_email(email, db)
    user.confirmed = True
    r.set(f"user:{email}", pickle.dumps(user))
    r.expire(f"user:{email}", 900)
    db.commit()
