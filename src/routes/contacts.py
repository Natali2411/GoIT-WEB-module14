from typing import List

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.orm import Session

from src.conf.config import settings
from src.database.db import get_db
from src.database.models import User
from src.repository.users import get_current_user
from src.schemas import (
    ChannelResponse,
    ContactResponse,
    ContactChannelResponse,
    ContactModel,
)
from src.repository import contacts as repository_contacts

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.get(
    "/",
    response_model=List[ContactResponse],
    description=f"No more than {settings.rate_limit_requests_per_minute} requests per minute",
    dependencies=[
        Depends(RateLimiter(times=settings.rate_limit_requests_per_minute, seconds=60))
    ],
)
async def read_contacts(
    firstName: str = None,
    lastName: str = None,
    email: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    The read_contacts function returns a list of contacts.

    :param firstName: str: Specify the first name of a contact
    :param lastName: str: Filter contacts by last name
    :param email: str: Filter the contacts by email
    :param db: Session: Pass in the database session
    :param current_user: User: Get the current user from the database
    :param : Pass the contact id to the function
    :return: A list of contacts
    :doc-author: Trelent
    """
    contacts = await repository_contacts.get_contacts(
        db, current_user.id, firstName, lastName, email
    )
    return contacts


@router.get(
    "/birthdays",
    response_model=List[ContactResponse],
    description=f"No more than {settings.rate_limit_requests_per_minute} requests per minute",
    dependencies=[
        Depends(RateLimiter(times=settings.rate_limit_requests_per_minute, seconds=60))
    ],
)
async def read_contacts_birthdays(
    daysForward: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    The read_contacts_birthdays function returns a list of contacts with birthdays in the next X days.

    :param daysForward: int: Specify how many days forward from today to look for birthdays
    :param db: Session: Pass the database session to the function
    :param current_user: User: Get the user id of the current user
    :param : Get the contacts birthdays in a certain number of days
    :return: A list of contacts that have birthdays in the next n days
    :doc-author: Trelent
    """
    contacts = await repository_contacts.get_contacts_birthdays(
        db, daysForward, current_user.id
    )
    return contacts


@router.get(
    "/{contactId}",
    response_model=ContactResponse,
    description=f"No more than {settings.rate_limit_requests_per_minute} requests per minute",
    dependencies=[
        Depends(RateLimiter(times=settings.rate_limit_requests_per_minute, seconds=60))
    ],
)
async def read_contact(
    contactId: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    The read_contact function is used to retrieve a single contact from the database.
    It takes in an integer representing the ID of the contact, and returns a Contact object.

    :param contactId: int: Pass the contact id to the function
    :param db: Session: Get a database session
    :param current_user: User: Get the user id from the current_user object
    :param : Get the contactid from the path
    :return: A contact object
    :doc-author: Trelent
    """
    contact = await repository_contacts.get_contact(contactId, db, current_user.id)
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found"
        )
    return contact


@router.post(
    "/",
    response_model=ContactResponse,
    description=f"No more than {settings.rate_limit_requests_per_minute} requests per minute",
    dependencies=[
        Depends(RateLimiter(times=settings.rate_limit_requests_per_minute, seconds=60))
    ],
)
async def create_contact(
    body: ContactModel,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    The create_contact function creates a new contact in the database.

    :param body: ContactModel: Get the data from the request body
    :param db: Session: Pass the database session to the repository
    :param current_user: User: Get the user_id from the token
    :param : Get the contact id from the url
    :return: A contactmodel object
    :doc-author: Trelent
    """
    return await repository_contacts.create_contact(body, db, current_user.id)
