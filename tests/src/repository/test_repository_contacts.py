import datetime
import unittest
from unittest.mock import MagicMock

from sqlalchemy.orm import Session

from src.database.models import Contact, User
from src.schemas import ContactModel
from src.repository.contacts import (
    get_contact, get_contacts_birthdays, get_contacts, get_future_dates,
    create_contact, update_contact, remove_contact
)


class TestContacts(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.session = MagicMock(spec=Session)
        self.user = User(id=1)

    async def test_get_contacts(self):
        contacts = [Contact(), Contact(), Contact()]
        self.session.query().outerjoin().filter().all.return_value = contacts
        result = await get_contacts(user_id=self.user.id, first_name="Nataliia",
                                    last_name="Tiutiunnyk", email="test@test.com",
                                    db=self.session)
        self.assertEqual(result, contacts)

    async def test_get_contact_found(self):
        contact = Contact()
        self.session.query().filter().first.return_value = contact
        result = await get_contact(contact_id=1, user_id=self.user.id, db=self.session)
        self.assertEqual(result, contact)

    async def test_get_contact_not_found(self):
        self.session.query().filter().first.return_value = None
        result = await get_contact(contact_id=1, user_id=self.user.id, db=self.session)
        self.assertIsNone(result)

    async def test_create_contact(self):
        body = ContactModel(first_name="Nataliia", last_name="Tiutiunnyk",
                            birthdate="1992-03-12", gender="F", persuasion="Orthodox",
                            created_at=datetime.datetime.now())
        result = await create_contact(body=body, user_id=self.user.id, db=self.session)
        self.assertTrue(hasattr(result, "id"))
        self.assertEqual(result.first_name, body.first_name), (
            result.first_name, body.first_name)
        self.assertEqual(result.last_name, body.last_name), (
            result.last_name, body.last_name)
        self.assertEqual(result.created_at, body.created_at), (
            result.created_at, body.created_at)
        self.assertEqual(result.gender, body.gender), (
            result.gender, body.gender)
        self.assertEqual(result.persuasion, body.persuasion), (
            result.persuasion, body.persuasion)
        self.assertEqual(result.birthdate, body.birthdate), (
            result.birthdate, body.birthdate)
        self.assertEqual(result.created_by, self.user.id), (
            result.created_by, self.user.id)
        self.assertEqual(result.channels, []), (
            result.channels, [])

    async def test_update_contact(self):
        body = ContactModel(first_name="Nataliia", last_name="Tiutiunnyk",
                            birthdate="1992-11-24", gender="F", persuasion="Orthodox",
                            created_at=datetime.datetime.now())
        result1 = await create_contact(body=body, user_id=self.user.id, db=self.session)
        body.first_name = "Valentyna"
        body.birthdate = "1970-04-14"
        self.session.query().filter().first.return_value = result1
        result = await update_contact(contact_id=result1.id, body=body,
                                      user_id=self.user.id, db=self.session)
        self.assertTrue(hasattr(result, "id"))
        self.assertEqual(result.first_name, body.first_name), (
            result.first_name, body.first_name)
        self.assertEqual(result.last_name, body.last_name), (
            result.last_name, body.last_name)
        self.assertEqual(result.created_at, body.created_at), (
            result.created_at, body.created_at)
        self.assertEqual(result.gender, body.gender), (
            result.gender, body.gender)
        self.assertEqual(result.persuasion, body.persuasion), (
            result.persuasion, body.persuasion)
        self.assertEqual(result.birthdate, body.birthdate), (
            result.birthdate, body.birthdate)
        self.assertEqual(result.created_by, self.user.id), (
            result.created_by, self.user.id)
        self.assertEqual(result.channels, []), (
            result.channels, [])

    async def test_delete_contact(self):
        body = ContactModel(first_name="Nataliia", last_name="Tiutiunnyk",
                            birthdate="1992-11-24", gender="F", persuasion="Orthodox",
                            created_at=datetime.datetime.now())
        result1 = await create_contact(body=body, user_id=self.user.id, db=self.session)
        self.session.query().filter().first.return_value = result1
        result = await remove_contact(contact_id=result1.id, user_id=self.user.id,
                                      db=self.session)
        self.assertTrue(hasattr(result, "id"))
        self.assertEqual(result.first_name, body.first_name), (
            result.first_name, body.first_name)
        self.assertEqual(result.last_name, body.last_name), (
            result.last_name, body.last_name)
        self.assertEqual(result.created_at, body.created_at), (
            result.created_at, body.created_at)
        self.assertEqual(result.gender, body.gender), (
            result.gender, body.gender)
        self.assertEqual(result.persuasion, body.persuasion), (
            result.persuasion, body.persuasion)
        self.assertEqual(result.birthdate, body.birthdate), (
            result.birthdate, body.birthdate)
        self.assertEqual(result.created_by, self.user.id), (
            result.created_by, self.user.id)
        self.assertEqual(result.channels, []), (
            result.channels, [])

    def test_future_days(self):
        result = get_future_dates(days=5)
        assert len(result["day"]) == 6

    async def test_get_contacts_birthdays(self):
        contacts = [Contact(birthdate="1992-03-13"), Contact(birthdate="1992-03-18"),
                    Contact(birthdate="1993-03-19"), Contact(birthdate="1993-04-19")]
        self.session.query().filter().all.return_value = contacts
        result = await get_contacts_birthdays(db=self.session, days=10,
                                              user_id=self.user.id)
        self.assertEqual(result, contacts)
