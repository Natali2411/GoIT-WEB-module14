from __future__ import annotations

from typing import List, Type

from sqlalchemy import and_, extract, cast, Integer
from sqlalchemy.orm import Session

from src.database.models import Contact, ContactChannel
from src.schemas import ContactModel
from src.utils.dates import get_future_dates


async def get_contacts(
    db: Session,
    user_id: int,
    first_name: str = None,
    last_name: str = None,
    email: str = None,
) -> List[Type[Contact]]:
    """
    Method retrieves a list of contacts filtered by input parameters.
    :param db: DB object.
    :type db: Session
    :param user_id: User identifier.
    :type user_id: int
    :param first_name: Contact first name.
    :type first_name: str
    :param last_name: Contact last name.
    :type last_name: str
    :param email: Contact email.
    :type email: str
    :return: The list of contacts.
    :rtype: List[Type[Contact]]
    """
    conditions = [Contact.created_by == user_id]
    if first_name:
        conditions.append(Contact.first_name == first_name)
    if last_name:
        conditions.append(Contact.last_name == last_name)
    if email:
        conditions.append(ContactChannel.channel_value == email)
    contacts = (
        db.query(Contact).outerjoin(ContactChannel).filter(and_(*conditions)).all()
    )
    return contacts


async def get_contacts_birthdays(
    db: Session, days: int, user_id: int
) -> List[Type[Contact]]:
    """
    Method retrieves the list of contacts with birthdays in a range from now till
    future date.
    :param db: DB object.
    :type db: Session
    :param days: Days that should be added to current date to get a future date.
    :type days: int
    :param user_id: User identifier.
    :type user_id: int
    :return: The list of contacts who have birthdays in a range from now to a future
    date (now + days).
    :rtype: List[Type[Contact]]
    """
    dates = get_future_dates(days)
    contacts = (
        db.query(Contact)
        .filter(
            (Contact.birthdate.isnot(None))
            & cast((extract("month", Contact.birthdate)), Integer).in_(dates["month"])
            & cast(extract("day", Contact.birthdate), Integer).in_(dates["day"])
            & (Contact.created_by == user_id)
        )
        .all()
    )
    return contacts


async def get_contact(
    contact_id: int, db: Session, user_id: int
) -> Type[Contact] | None:
    """
    Method retrieves the contact by contact identifier and user identifier.
    :param contact_id: Contact identifier.
    :type contact_id: int
    :param db: DB object.
    :type db: Session
    :param user_id: User identifier.
    :type user_id: int
    :return: Contact.
    :rtype: Type[Contact] | None
    """
    return (
        db.query(Contact)
        .filter(and_(Contact.id == contact_id, Contact.created_by == user_id))
        .first()
    )


async def create_contact(body: ContactModel, db: Session, user_id: int) -> Contact:
    """
    Method creates a contact by specific user.
    :param body: Request body for creating contact.
    :type body: ContactModel
    :param db: DB object.
    :type db: Session
    :param user_id: User identifier.
    :type user_id: int
    :return: Created contact.
    :rtype: Contact
    """
    contact = Contact(
        first_name=body.first_name,
        last_name=body.last_name,
        birthdate=body.birthdate,
        gender=body.gender,
        persuasion=body.persuasion,
        created_by=user_id,
        created_at=body.created_at,
    )
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


async def update_contact(
    contact_id: int, body: ContactModel, db: Session, user_id: int
) -> Contact | None:
    """
    Method updates a contact by specific user.
    :param contact_id: Contact identifier.
    :type contact_id: int
    :param body: Request body for updating contact.
    :type body: ContactModel
    :param db: DB object.
    :type db: Session
    :param user_id: User identifier.
    :type user_id: int
    :return: Updated contact.
    :rtype: Contact | None

    """
    contact = (
        db.query(Contact)
        .filter(and_(Contact.id == contact_id, Contact.created_by == user_id))
        .first()
    )
    if contact:
        contact.first_name = body.first_name
        contact.last_name = body.last_name
        contact.persuasion = body.persuasion
        contact.gender = body.gender
        contact.birthdate = body.birthdate
        db.commit()
    return contact


async def remove_contact(contact_id: int, db: Session, user_id: int) -> Contact | None:
    """
    Method removes the contact by contact identifier.
    :param contact_id: Contact identifier.
    :type contact_id: int
    :param db: DB object.
    :type db: Session
    :param user_id: User identifier.
    :type user_id: int
    :return: Deleted contact.
    :rtype: Contact | None
    """
    contact = (
        db.query(Contact)
        .filter(and_(Contact.id == contact_id, Contact.created_by == user_id))
        .first()
    )
    if contact:
        db.delete(contact)
        db.commit()
    return contact
