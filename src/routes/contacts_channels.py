from typing import List

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.orm import Session

from src.conf.config import settings
from src.database.db import get_db
from src.database.models import User
from src.repository.users import get_current_user
from src.schemas import (
    ContactChannelModel,
    ContactChannelResponse,
)
from src.repository import contacts_channels as repository_contacts_channels


router = APIRouter(prefix="/contactsChannels", tags=["contactsChannels"])


@router.get(
    "/",
    response_model=List[ContactChannelResponse],
    description=f"No more than {settings.rate_limit_requests_per_minute} requests per minute",
    dependencies=[
        Depends(RateLimiter(times=settings.rate_limit_requests_per_minute, seconds=60))
    ],
)
async def read_contacts_channels(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    The read_contacts_channels function returns a list of contacts_channels.

    :param skip: int: Skip a number of records
    :param limit: int: Limit the number of contacts_channels returned
    :param db: Session: Pass the database session to the repository layer
    :param current_user: User: Get the current user's id
    :param : Get the contacts_channels by id
    :return: A list of contacts_channels
    :doc-author: Trelent
    """
    contacts_channels = await repository_contacts_channels.get_contacts_channels(
        skip, limit, db, current_user.id
    )
    return contacts_channels


@router.post(
    "/",
    response_model=ContactChannelResponse,
    description=f"No more than {settings.rate_limit_requests_per_minute} requests per minute",
    dependencies=[
        Depends(RateLimiter(times=settings.rate_limit_requests_per_minute, seconds=60))
    ],
)
async def create_contacts_channels(
    body: ContactChannelModel,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    The create_contacts_channels function creates a new contacts_channels in the database.
        It takes in a ContactChannelModel object, which is validated by pydantic and then passed to the repository function.
        The repository function returns an integer value that indicates whether or not the creation was successful:
            0 - Successful creation of contacts_channels entry into DB
            1 - Unsuccessful due to duplicate channel value for contact name already existing in DB (409 Conflict)
            2 - Unsuccessful due to either contact or channel name not found (404 Not Found)

    :param body: ContactChannelModel: Get the data from the request body
    :param db: Session: Get the database connection,
    :param current_user: User: Get the current user's id
    :param : Get the id of a contact channel
    :return: The id of the created channel
    :doc-author: Trelent
    """
    contacts_channels = await repository_contacts_channels.create_contacts_channels(
        body, db, current_user.id
    )
    if contacts_channels == 1:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Such channel value already " "exists in the DB",
        )
    elif contacts_channels == 2:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact or channel name " "is not found",
        )
    return contacts_channels


@router.put(
    "/{contactChannelId}",
    response_model=ContactChannelResponse,
    description=f"No more than {settings.rate_limit_requests_per_minute} requests per minute",
    dependencies=[
        Depends(RateLimiter(times=settings.rate_limit_requests_per_minute, seconds=60))
    ],
)
async def update_contact_channel(
    contactChannelId: int,
    body: ContactChannelModel,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    The update_contact_channel function updates a contact channel in the database.
        Args:
            contactChannelId (int): The id of the contact channel to update.
            body (ContactChannelModel): The updated information for the specified contact channel.

    :param contactChannelId: int: Specify the contact channel to be updated
    :param body: ContactChannelModel: Pass in the data that will be used to update the contact channel
    :param db: Session: Access the database
    :param current_user: User: Get the user id of the current user
    :param : Get the contact channel id
    :return: The updated contact channel
    :doc-author: Trelent
    """
    contact_channel = await repository_contacts_channels.update_contact_channel(
        contactChannelId, body, db, current_user.id
    )
    if not contact_channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contact channel {contactChannelId} " "is not found",
        )
    return contact_channel


@router.delete(
    "/{contactChannelId}",
    response_model=ContactChannelResponse,
    description=f"No more than {settings.rate_limit_requests_per_minute} requests per minute",
    dependencies=[
        Depends(RateLimiter(times=settings.rate_limit_requests_per_minute, seconds=60))
    ],
)
async def delete_contact_channel(
    contactChannelId: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    The delete_contact_channel function deletes a contact channel from the database.
        The function takes in an integer representing the id of the contact channel to be deleted,
        and returns a dictionary containing information about that contact channel.

    :param contactChannelId: int: Specify the id of the contact channel to be deleted
    :param db: Session: Get the database session
    :param current_user: User: Get the user that is currently logged in
    :return: The deleted contact channel
    :doc-author: Trelent
    """
    contact_channel = await repository_contacts_channels.remove_contact_channel(
        contactChannelId, db, current_user.id
    )
    if not contact_channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contact channel {contactChannelId} " "is not found",
        )
    return contact_channel
