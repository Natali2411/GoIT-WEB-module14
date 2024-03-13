from __future__ import annotations

from typing import Type

from sqlalchemy.orm import Session

from src.database.models import Channel
from src.schemas import ChannelModel


async def get_channels(db: Session) -> list[Type[Channel]]:
    """
    Method retrieves the list  of channels type.
    :param db: DB object.
    :type db: Session
    :return: List of channel types
    :rtype: list[Type[Channel]]
    """
    return db.query(Channel).all()


async def get_channel(channel_id: int, db: Session) -> Type[Channel] | None:
    """
    Method retrieves the channel type by channel identifier.
    :param channel_id: Channel identifier.
    :type channel_id: int
    :param db: DB object.
    :type db: Session
    :return: Channel type.
    :rtype: Type[Channel] | None
    """
    return db.query(Channel).filter(Channel.id == channel_id).first()


async def get_channel_by_name(channel_name: str, db: Session) -> Type[Channel] | None:
    """
    Method retrieves the channel type by channel name.
    :param channel_name: Channel name.
    :type channel_name: str
    :param db: DB object.
    :type db: Session
    :return: Channel type.
    :rtype: Type[Channel] | None
    """
    return db.query(Channel).filter(Channel.name == channel_name).first()


async def create_channel(body: ChannelModel, db: Session) -> Channel:
    """
    Method creates a channel type.
    :param body: Request body for creating channel type.
    :type body: ChannelModel
    :param db: DB object.
    :type db: Session
    :return: Channel type.
    :rtype: Channel
    """
    channel = Channel(name=body.name.value)
    db.add(channel)
    db.commit()
    db.refresh(channel)
    return channel


async def update_channel(
    channel_id: int, body: ChannelModel, db: Session
) -> (Channel | None):
    """
    Method updates the channel type by channel identifier.
    :param channel_id: Channel identifier.
    :type channel_id: int
    :param body: Request body for updating channel type.
    :type body: ChannelModel
    :param db: DB object.
    :type db: Session
    :return: Channel type.
    :rtype: Channel | None
    """
    channel = db.query(Channel).filter(Channel.id == channel_id).first()
    if channel:
        channel.name = body.name.value
        db.commit()
    return channel


async def remove_channel(channel_id: int, db: Session) -> Channel | None:
    """
    Method removes channel type by channel identifier.
    :param channel_id: Channel identifier.
    :type channel_id: int
    :param db: DB object.
    :type db: Session
    :return: Channel type.
    :rtype: Channel | None
    """
    channel = db.query(Channel).filter(Channel.id == channel_id).first()
    if channel:
        db.delete(channel)
        db.commit()
    return channel
