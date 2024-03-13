from typing import Optional

import redis
from fastapi import Header, UploadFile, File
from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks, Request
from fastapi.security import (
    HTTPBearer,
)
from fastapi_jwt_auth import AuthJWT
from fastapi_limiter.depends import RateLimiter
from sqlalchemy import and_
from sqlalchemy.orm import Session
import cloudinary
import cloudinary.uploader

from src.database.db import get_db
from src.database.models import User
from src.repository.users import get_current_user, get_user_by_email
from src.routes import rate_limiter
from src.schemas import UserModel, UserResponse, TokenModel, UserDb
from src.repository import users as repository_users
from src.services.auth import get_password_hash, get_email_from_token, verify_password
from src.conf.config import settings
from src.services.email import send_email

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()
r = redis.Redis(host=settings.redis_host, port=settings.redis_port)

@router.post(
    "/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    description=f"No more than {settings.rate_limit_requests_per_minute} requests per minute",
    dependencies=[Depends(rate_limiter)],
)
async def signup(
    body: UserModel,
    background_tasks: BackgroundTasks,
    request: Request,
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    """
    The signup function creates a new user in the database.
    It takes a UserModel object as input, which is validated by pydantic.
    If the email address already exists in the database, it raises an HTTP 409 error.
    Otherwise, it hashes and salts the password using passlib's get_password_hash
    function and then adds that to body before creating a new user with repository_users'
    create_user function.

    :param body: UserModel: Get the user's information from the request body
    :param background_tasks: BackgroundTasks: Add a task to the background tasks queue
    :param request: Request: Get the base_url
    :param Authorize: AuthJWT: Get the user_id from the jwt token
    :param db: Session: Access the database
    :return: A dict with the user and a message
    :doc-author: Trelent
    """
    exist_user = await repository_users.get_user_by_email(body.email, db)
    if exist_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with the email {body.email} already exists",
        )
    body.password = get_password_hash(body.password)
    new_user = await repository_users.create_user(body, db)
    background_tasks.add_task(
        send_email,
        new_user.email,
        f"{new_user.first_name} {new_user.last_name}",
        request.base_url,
    )
    return {
        "user": new_user,
        "detail": "User successfully created. Check your email for confirmation.",
    }


@router.delete(
    "/users/{email}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    description=f"No more than {settings.rate_limit_requests_per_minute} requests per minute",
    dependencies=[
        Depends(RateLimiter(times=settings.rate_limit_requests_per_minute, seconds=60))
    ],
)
async def remove_user(
    email: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    The remove_user function removes a user from the database.

    :param email: str: Get the email of the user to be deleted
    :param db: Session: Pass the database session to the function
    :param _: User: Ensure that the user is logged in
    :param : Get the database session
    :return: A boolean value
    :doc-author: Trelent
    """
    await repository_users.remove_user(email, db)


@router.post(
    "/access_token",
    response_model=Optional[TokenModel],
    description=f"No more than {settings.rate_limit_requests_per_minute} requests per "
    f"minute", dependencies=[Depends(rate_limiter)],
)
async def create_session(
    user: UserModel, Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)
):
    """
    The create_session function creates a new session for the user.

    :param user: UserModel: Pass the user object to the function
    :param Authorize: AuthJWT: Create the access token and refresh token
    :param db: Session: Access the database
    :return: A dictionary with three keys: access_token, refresh_token and token_type
    :doc-author: Trelent
    """
    _user = await repository_users.get_user_by_email(user.email, db)
    if _user:
        if not verify_password(user.password, _user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password"
            )
        if not _user.confirmed:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Email not confirmed"
            )
        access_token = Authorize.create_access_token(subject=_user.email)
        refresh_token = Authorize.create_refresh_token(subject=_user.email)

        _user.refresh_token = refresh_token
        db.commit()

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    raise HTTPException(status_code=401, detail="Invalid email")


@router.get(
    "/refresh_token",
    response_model=TokenModel,
    description=f"No more than {settings.rate_limit_requests_per_minute} requests per minute",
    dependencies=[
        Depends(RateLimiter(times=settings.rate_limit_requests_per_minute, seconds=60))
    ],
)
async def refresh_token(
    refresh_token: str = Header(..., alias="Authorization"),
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    """
    The refresh_token function is used to refresh the access token.
        The function takes in a refresh_token as an argument and returns a new access_token and refresh_token.
        The function also updates the user's current refresh token with a new one.

    :param refresh_token: str: Pass the refresh token from the request header
    :param Authorize: AuthJWT: Check if the user is authorized to access the endpoint
    :param db: Session: Access the database
    :param : Get the user's email from the jwt token
    :return: A new access token and a new refresh token
    :doc-author: Trelent
    """
    Authorize.jwt_refresh_token_required()
    # Check if refresh token is in DB
    user_email = Authorize.get_jwt_subject()
    user = db.query(User).filter(and_(user_email == User.email)).first()
    if f"Bearer {user.refresh_token}" == refresh_token:
        access_token = Authorize.create_access_token(subject=user_email)
        new_refresh_token = Authorize.create_refresh_token(subject=user_email)

        user.refresh_token = new_refresh_token
        db.commit()
        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
        }

    raise HTTPException(status_code=401, detail="Invalid or expired refresh token")


@router.get("/confirmed_email/{token}")
async def confirmed_email(token: str, db: Session = Depends(get_db)):
    """
    The confirmed_email function is used to confirm a user's email address.
    It takes in the token that was sent to the user's email and uses it to get their email address.
    Then, it gets the user from our database using their email address and checks if they exist. If not, an error is raised.
    If they do exist, we check if their account has already been confirmed or not (if so, we return a message saying so).
    Otherwise, we use our repository_users module to confirm their account by setting its confirmed field equal True.

    :param token: str: Get the token from the url
    :param db: Session: Get the database session
    :return: A message to the user
    :doc-author: Trelent
    """
    email = await get_email_from_token(token)
    user = await repository_users.get_user_by_email(email, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error"
        )
    if user.confirmed:
        return {"message": "Your email is already confirmed"}
    await repository_users.confirm_email(email, db)
    return {"message": "Email confirmed"}


@router.patch(
    "/avatar",
    response_model=UserDb,
    description=f"No more than"
    f" {settings.rate_limit_requests_per_minute} requests per minute",
    dependencies=[
        Depends(RateLimiter(times=settings.rate_limit_requests_per_minute, seconds=60))
    ],
)
async def update_avatar_user(
    file: UploadFile = File(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    The update_avatar_user function takes in a file, current_user and db.
    It then uploads the file to cloudinary using the user's email as a public id.
    The function then returns an updated user object with the new avatar url.

    :param file: UploadFile: Upload the file to cloudinary
    :param current_user: User: Get the current user from the database
    :param db: Session: Pass the database session to the repository function
    :param : Get the current user
    :return: The updated user object
    :doc-author: Trelent
    """
    cloudinary.config(
        cloud_name=settings.cloudinary_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True,
    )

    r = cloudinary.uploader.upload(
        file.file, public_id=f"ContactsApp/{current_user.email}", overwrite=True
    )
    src_url = cloudinary.CloudinaryImage(f"ContactsApp/{current_user.email}").build_url(
        width=250, height=250, crop="fill", version=r.get("version")
    )
    user = await repository_users.update_avatar(current_user.email, src_url, db)
    return user
