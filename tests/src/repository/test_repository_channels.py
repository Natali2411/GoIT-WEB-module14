import unittest
from unittest.mock import MagicMock

from sqlalchemy.orm import Session

from src.database.models import Channel, User
from src.schemas import ChannelModel, ChannelType
from src.repository.channels import (
    get_channel, get_channels, get_channel_by_name, create_channel, update_channel,
    remove_channel
)


class TestChannels(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.session = MagicMock(spec=Session)
        self.user = User(id=1)

    async def test_get_channels(self):
        channels = [Channel(), Channel(), Channel()]
        self.session.query().all.return_value = channels
        result = await get_channels(db=self.session)
        self.assertEqual(result, channels)

    async def test_get_channel_found(self):
        channel = Channel()
        self.session.query().filter().first.return_value = channel
        result = await get_channel(channel_id=1, db=self.session)
        self.assertEqual(result, channel)

    async def test_get_channel_not_found(self):
        self.session.query().filter().first.return_value = None
        result = await get_channel(channel_id=1, db=self.session)
        self.assertIsNone(result)

    async def test_get_channel_by_name_found(self):
        channel = Channel()
        self.session.query().filter().first.return_value = channel
        result = await get_channel_by_name(channel_name=channel.name, db=self.session)
        self.assertEqual(result, channel)

    async def test_get_channel_by_name_not_found(self):
        channel = Channel()
        self.session.query().filter().first.return_value = None
        result = await get_channel_by_name(channel_name=channel.name, db=self.session)
        self.assertIsNone(result)

    async def test_create_channel(self):
        body = ChannelModel(name=ChannelType.PHONE.value)
        result = await create_channel(body=body, db=self.session)
        self.assertEqual(result.name, body.name.value)
        self.assertTrue(hasattr(result, "id"))

    async def test_update_channel(self):
        body = ChannelModel(name=ChannelType.PHONE.value)
        new_channel = await create_channel(body=body, db=self.session)
        new_body = ChannelModel(name=ChannelType.EMAIL.value)
        updated_channel = await update_channel(channel_id=new_channel.id,
                                               body=new_body, db=self.session)
        self.assertEqual(updated_channel.name, new_body.name.value)
        self.assertTrue(hasattr(updated_channel, "id"))

    async def test_delete_channel(self):
        body = ChannelModel(name=ChannelType.PHONE.value)
        new_channel = await create_channel(body=body, db=self.session)

        self.session.query().filter().first.return_value = new_channel

        result = await remove_channel(channel_id=new_channel.id, db=self.session)
        self.assertEqual(result.name, body.name.value)
        self.assertTrue(hasattr(result, "id"))


if __name__ == "__main__":
    unittest.main()
