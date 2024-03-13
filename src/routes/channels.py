from typing import List

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.orm import Session

from src.conf.config import settings
from src.database.db import get_db
from src.database.models import User
from src.repository.users import get_current_user
from src.routes import rate_limiter
from src.schemas import ChannelResponse, ChannelModel
from src.repository import channels as repository_channels

router = APIRouter(prefix="/channels", tags=["channels"])

@router.get(
    "/",
    response_model=List[ChannelResponse],
    description=f"No more than {settings.rate_limit_requests_per_minute} requests per minute",
    dependencies=[Depends(rate_limiter)],
)
async def read_channels(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    The read_channels function returns a list of channels.

    :param db: Session: Get the database session
    :param _: User: Get the current user
    :param : Get the database session
    :return: A list of channels
    :doc-author: Trelent
    """
    channels = await repository_channels.get_channels(db)
    return channels


@router.get(
    "/{channelId}",
    response_model=ChannelResponse,
    description=f"No more than {settings.rate_limit_requests_per_minute} requests per minute",
    dependencies=[Depends(rate_limiter)],
)
async def read_channel(
    channelId: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    The read_channel function is used to read a channel from the database.

    :param channelId: int: Specify the channel id
    :param db: Session: Get a database session
    :param _: User: Check if the user is authenticated
    :param : Get the channel id from the url
    :return: A channel object
    :doc-author: Trelent
    """
    channel = await repository_channels.get_channel(channelId, db)
    if channel is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found"
        )
    return channel


@router.post(
    "/",
    response_model=ChannelResponse,
    description=f"No more than {settings.rate_limit_requests_per_minute} requests per minute",
    dependencies=[Depends(rate_limiter)],
)
async def create_channel(
    body: ChannelModel,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    The create_channel function creates a new channel in the database.
        It takes a ChannelModel object as input, which is validated by Pydantic.
        The function then checks if there already exists a channel with the same name, and if so it raises an HTTPException.
        If no such channel exists, it calls repository_channels' create_channel function to add the new channel to the database.

    :param body: ChannelModel: Get the channel name from the request body
    :param db: Session: Get the database session,
    :param _: User: Check if the user is authenticated
    :param : Get the channel by id
    :return: A channelmodel object
    :doc-author: Trelent
    """
    channel = await repository_channels.get_channel_by_name(body.name.value, db)
    if channel:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Channel with the name '" f"{body.name}' already exists",
        )
    return await repository_channels.create_channel(body, db)


@router.put(
    "/{channelId}",
    response_model=ChannelResponse,
    description=f"No more than {settings.rate_limit_requests_per_minute} requests per minute",
    dependencies=[Depends(rate_limiter)],
)
async def update_channel(
    channelId: int,
    body: ChannelModel,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    The update_channel function updates a channel in the database.
        It takes an id and a body as parameters, which are used to update the channel.
        The function returns the updated channel.

    :param channelId: int: Find the channel to delete
    :param body: ChannelModel: Pass in the data that will be used to update the channel
    :param db: Session: Get the database session
    :param _: User: Check if the user is logged in
    :param : Get the channelid from the url
    :return: A channelmodel object
    :doc-author: Trelent
    """
    channel = await repository_channels.update_channel(channelId, body, db)
    if channel is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found"
        )
    return channel


@router.delete(
    "/{channelId}",
    response_model=ChannelResponse,
    description=f"No more than {settings.rate_limit_requests_per_minute} requests per minute",
    dependencies=[Depends(rate_limiter)],
)
async def delete_channel(
    channelId: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)
):
    """
    The delete_channel function deletes a channel from the database.
        It takes in a channelId and returns the deleted channel.

    :param channelId: int: Specify the channel to be deleted
    :param db: Session: Access the database
    :param _: User: Check if the user is authenticated
    :return: A channel object
    :doc-author: Trelent
    """
    channel = await repository_channels.remove_channel(channelId, db)
    if channel is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found"
        )
    return channel
