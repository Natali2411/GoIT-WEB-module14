import json
import random

import pytest
import sqlalchemy

from src.schemas import ChannelType


@pytest.mark.asyncio
@pytest.mark.parametrize("name", ([ChannelType.PHONE.value, ChannelType.EMAIL.value,
                                   ChannelType.POST.value]))
async def test_create_channel(name, session, client, user_login):
    response = client.post(
        "/api/channels/",
        data=json.dumps({"name": name}),
        headers={"Authorization": f"Bearer {user_login.get('access_token')}"}
    )
    assert response.status_code == 200, response.status_code
    assert response.json()["name"] == name, (response.json()["name"], name)
    assert response.json()["id"]


@pytest.mark.asyncio
@pytest.mark.parametrize("name", (["test", "11test2"]))
async def test_create_channel_w_invalid_name(name, session, client, user_login):
    response = client.post(
        "/api/channels/",
        data=json.dumps({"name": name}),
        headers={"Authorization": f"Bearer {user_login.get('access_token')}"}
    )
    assert response.status_code == 422, response.status_code

@pytest.mark.asyncio
async def test_read_all_channels(session, client, user_login, create_channels):
    response = client.get(
        "/api/channels/",
        headers={"Authorization": f"Bearer {user_login.get('access_token')}"}
    )
    assert response.status_code == 200, response.status_code
    channel_names = [channel.value for channel in list(ChannelType)]
    for channel in response.json():
        assert channel["name"] in channel_names, (channel["name"])
        assert channel["id"]


@pytest.mark.asyncio
async def test_read_existing_channel_by_id(session, client, user_login, create_channels):
    channels = client.get(
        "/api/channels/",
        headers={"Authorization": f"Bearer {user_login.get('access_token')}"}
    ).json()
    channel = random.choice(channels)
    response = client.get(
        f"/api/channels/{channel.get('id')}",
        headers={"Authorization": f"Bearer {user_login.get('access_token')}"}
    )
    assert response.status_code == 200, response.status_code
    assert response.json() == channel, (response.json(), channel)


@pytest.mark.asyncio
async def test_read_absent_channel_by_id(session, client, user_login, create_channels):
    response = client.get(
        f"/api/channels/{random.randint(1000, 10000)}",
        headers={"Authorization": f"Bearer {user_login.get('access_token')}"}
    )
    assert response.status_code == 404, response.status_code


@pytest.mark.asyncio
@pytest.mark.parametrize("name_old, name_new",
                         ([(ChannelType.PHONE.value, ChannelType.EMAIL.value),
                           (ChannelType.POST.value, ChannelType.PHONE.value)]))
async def test_update_channel(name_old, name_new, session, client, user_login):
    channel = client.post(
        "/api/channels/",
        data=json.dumps({"name": name_old}),
        headers={"Authorization": f"Bearer {user_login.get('access_token')}"}
    ).json()
    response = client.put(
        f"/api/channels/{channel.get('id')}",
        data=json.dumps({"name": name_new}),
        headers={"Authorization": f"Bearer {user_login.get('access_token')}"}
    )
    assert response.status_code == 200, response.status_code
    assert response.json()["name"] == name_new, (response.json()["name"], name_new)
    assert response.json()["id"]

@pytest.mark.asyncio
@pytest.mark.parametrize("name", [ChannelType.PHONE.value, ChannelType.EMAIL.value])
async def test_delete_channel(name, session, client, user_login):
    try:
        client.post(
            "/api/channels/",
            data=json.dumps({"name": name}),
            headers={"Authorization": f"Bearer {user_login.get('access_token')}"}
        ).json()
    except sqlalchemy.exc.IntegrityError:
        print(f"Channel with a name {name} already exist")
    get_channels = client.get(
        f"/api/channels/",
        headers={"Authorization": f"Bearer {user_login.get('access_token')}"}
    ).json()
    for channel in get_channels:
        response = client.delete(
            f"/api/channels/{channel.get('id')}",
            headers={"Authorization": f"Bearer {user_login.get('access_token')}"}
        )
        assert response.status_code == 200, response.status_code
        channel_get = client.get(
            f"/api/channels/{channel.get('id')}",
            headers={"Authorization": f"Bearer {user_login.get('access_token')}"}
        )
        assert channel_get.status_code == 404, channel_get.status_code
