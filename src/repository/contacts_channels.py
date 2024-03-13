from __future__ import annotations

from typing import Type

from sqlalchemy import and_
from sqlalchemy.orm import Session

from src.database.models import ContactChannel, Channel, Contact
from src.schemas import ContactChannelModel


async def get_contacts_channels(
    skip: int, limit: int, db: Session, user_id: int
) -> list[Type[ContactChannel]]:
    """
    The get_contacts_channels function returns a list of ContactChannel objects.

    :param skip: int: Skip a number of records in the database
    :type skip: int
    :param limit: Limit the number of results returned
    :type limit: int
    :param db: Pass the database session to the function
    :type db: Session
    :param user_id: Filter the results to only show channels created by that user
    :type user_id: int
    :return: A list of contact channels
    :rtype: list[Type[ContactChannel]]
    """
    return (
        db.query(ContactChannel)
        .filter(ContactChannel.created_by == user_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


async def create_contacts_channels(
    body: ContactChannelModel, db: Session, user_id: int
) -> (ContactChannel | int):
    """
    The create_contacts_channels function creates a new contact channel in the database.
    :param body: ContactChannelModel: Create a new contact channel
    :type body: ContactChannelModel
    :param db: Session: Pass the database session to the function
    :type db: Session
    :param user_id: Check if the user is authorized to create a contact channel
    :type user_id: int
    :return: Either a ContactChannel object, an int of 1 or 2
    :rtype: (ContactChannel | int)
    """
    contact_channel = (
        db.query(ContactChannel)
        .filter(
            and_(
                ContactChannel.channel_value == body.channel_value,
                ContactChannel.created_by == user_id,
            )
        )
        .first()
    )
    if contact_channel:
        return 1
    channel = db.query(Channel).filter(Channel.id == body.channel_id).first()
    contact = db.query(Contact).filter(Contact.id == body.contact_id).first()
    if channel and contact:
        contact_channel = ContactChannel(
            contact_id=body.contact_id,
            channel_id=channel.id,
            channel_value=body.channel_value,
        )
        db.add(contact_channel)
        db.commit()
        db.refresh(contact_channel)
        return contact_channel
    else:
        return 2


async def update_contact_channel(
    contact_channel_id: int, body: ContactChannelModel, db: Session, user_id: int
) -> [ContactChannel]:
    """
    The update_contact_channel function updates a contact channel in the database.

    :param contact_channel_id: Find the contact channel to be updated
    :type contact_channel_id: int
    :param body: Pass the data that will be used to update the contact channel
    :type body: ContactChannelModel
    :param db: Create a session with the database
    :type db: Session
    :param user_id: Check if the user is authorized to delete the contact_channel
    :type user_id: int
    :return: The updated contact channel
    :rtype: ContactChannel
    """
    contact_channel = (
        db.query(ContactChannel)
        .filter(
            and_(
                ContactChannel.id == contact_channel_id,
                ContactChannel.created_by == user_id,
            )
        )
        .first()
    )
    if contact_channel:
        contact_channel.contact_id = body.contact_id
        contact_channel.channel_id = body.channel_id
        contact_channel.channel_value = body.channel_value
        db.commit()
        db.refresh(contact_channel)
        return contact_channel


async def remove_contact_channel(
    contact_channel_id: int,
    db: Session,
    user_id: int,
) -> ContactChannel | None:
    """
    The remove_contact_channel function removes a contact channel from the database.

    :param contact_channel_id: Specify the id of the contact channel to be removed
    :type contact_channel_id: int
    :param db: Pass the database session to the function
    :type db: Session
    :param user_id: Make sure that the user is authorized to delete the contact channel
    :type user_id: int
    :return: A contactchannel object
    :rtype: ContactChannel | None
    """
    contact_channel = (
        db.query(ContactChannel)
        .filter(
            and_(
                ContactChannel.id == contact_channel_id,
                ContactChannel.created_by == user_id,
            )
        )
        .first()
    )
    if contact_channel:
        db.delete(contact_channel)
        db.commit()
    return contact_channel
