"""
The MIT License (MIT)

Copyright (c) 2015-present Rapptz

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

from __future__ import annotations

from typing import Callable, Dict, Iterable, List, Optional, Union, TYPE_CHECKING, Sequence
import time
import asyncio


from .mixins import Hashable
from .abc import Messageable
from .user import User as UserPayload
from .user import User
from .channel import StageChannel, VoiceChannel
from .enums import EventStatusType, EventEntityType, try_enum
from .errors import ClientException, InvalidData
from .utils import MISSING, parse_time, _get_as_snowflake
import datetime
__all__ = (
    'ScheduledEvent'
)

if TYPE_CHECKING:
    from .types.schedule_event import ScheduledEvent as ScheduledEventPayload
    from .types.snowflake import SnowflakeList
    from .guild import Guild
    from .channel import TextChannel, CategoryChannel
    from .member import Member
    from .message import Message, PartialMessage
    from .abc import Snowflake, SnowflakeTime
    from .role import Role
    from .user import User
    from .permissions import Permissions
    from .state import ConnectionState


class ScheduledEvent(Hashable):
#region to be checked
    """Represents a Discord guild's scheduled Event.

    .. container:: operations

        .. describe:: x == y

            Checks if two threads are equal.

        .. describe:: x != y

            Checks if two threads are not equal.

        .. describe:: hash(x)

            Returns the thread's hash.

        .. describe:: str(x)

            Returns the thread's name.
    .. versionadded:: 2.0

    Attributes
    -----------
    name: :class:`str`
        The thread name.
    guild: :class:`Guild`
        The guild the thread belongs to.
    id: :class:`int`
        The thread ID.
    parent_id: :class:`int`
        The parent :class:`TextChannel` ID this thread belongs to.
    owner_id: :class:`int`
        The user's ID that created this thread.
    last_message_id: Optional[:class:`int`]
        The last message ID of the message sent to this thread. It may
        *not* point to an existing or valid message.
    slowmode_delay: :class:`int`
        The number of seconds a member must wait between sending messages
        in this thread. A value of `0` denotes that it is disabled.
        Bots and users with :attr:`~Permissions.manage_channels` or
        :attr:`~Permissions.manage_messages` bypass slowmode.
    message_count: :class:`int`
        An approximate number of messages in this thread. This caps at 50.
    member_count: :class:`int`
        An approximate number of members in this thread. This caps at 50.
    me: Optional[:class:`ThreadMember`]
        A thread member representing yourself, if you've joined the thread.
        This could not be available.
    archived: :class:`bool`
        Whether the thread is archived.
    locked: :class:`bool`
        Whether the thread is locked.
    invitable: :class:`bool`
        Whether non-moderators can add other non-moderators to this thread.
        This is always ``True`` for public threads.
    archiver_id: Optional[:class:`int`]
        The user's ID that archived this thread.
    auto_archive_duration: :class:`int`
        The duration in minutes until the thread is automatically archived due to inactivity.
        Usually a value of 60, 1440, 4320 and 10080.
    archive_timestamp: :class:`datetime.datetime`
        An aware timestamp of when the thread's archived status was last updated in UTC.
    """
#endregion
    __slots__ = (
        'name',
        'description',
        '_state',
        'start_time',
        'end_time',
        'status',
        'id',
        'guild',
        'user_count',
        'is_guild_only',
        'creator_id',
        'type',
        'channel_id',
        'entity_metadata',
        'location'
    )

    def __init__(self, *, data: ScheduledEventPayload, guild: Guild, state: ConnectionState):
        self._state: ConnectionState = state
        self.guild = guild

        self.id = int(data['id'])
        self.name: str = data['name']
        self.start_time: datetime.datetime = parse_time(data['scheduled_start_time'])
        self.status: EventStatusType = try_enum(EventStatusType, data['status'])
        self.is_guild_only: bool = data.get('privacy_level') == 2 or False

        self.description: str = data.get('description', None)
        self.user_count: int = data.get('user_count', None)
        self.end_time: Optional[datetime.datetime] = parse_time(data['scheduled_end_time'])
        self.creator_id: int = int(data['creator_id']) 
        self.type: EventEntityType = try_enum(EventEntityType, data['entity_type'])
        channel_id = data.get('channel_id', None)
        
        self.channel_id: Optional[int] = int(channel_id) if channel_id else None
        self.entity_metadata: Dict[str, str] = data.get('entity_metadata', None)

        # set location if any
        self.location: Optional[str] = None
        if self.type == EventEntityType.external:
            if self.entity_metadata.get('location', None):
               self.location = self.entity_metadata.get('location', None)

    def _update(self, data: ScheduledEventPayload):
        self.name: str = data['name']
        self.description: str = data.get('description', None)
        self.user_count: int = data.get('user_count', None)
        self.end_time: Optional[datetime.datetime] = parse_time(data['scheduled_end_time'])
        self.start_time: datetime.datetime = parse_time(data['scheduled_start_time'])
        self.status: EventStatusType = try_enum(EventStatusType, data['status'])
        self.type: EventEntityType = try_enum(EventEntityType, data['entity_type'])
        channel_id = data.get('channel_id', None)
             
        self.channel_id: Optional[int] = int(channel_id) if channel_id else None
        self.entity_metadata: Dict[str, str] = data.get('entity_metadata', None)

        # set location if any
        self.location: Optional[str] = None
        if self.type == EventEntityType.external:
            if self.entity_metadata.get('location', None):
               self.location = self.entity_metadata.get('location', None)   
        pass

    async def delete(self) -> None:
        self._state.http.delete_scheduled_event(self.guild.id, self.id)

    def __repr__(self) -> str:
        return f'<ScheduledEvent id={self.id!r} name={self.name!r}>'

    def __str__(self) -> str:
        return self.name

    @property
    def creator(self) -> Optional[User]:
        return self.guild.get_member(self.creator_id)

    @property
    def channel(self) -> Optional[Union[StageChannel, VoiceChannel]]:
        if self.type in (EventEntityType.stage, EventEntityType.voice):
            return self._state.get_channel(self.channel_id)

    async def fetch_users(self) -> Sequence[User]:
        """|coro|

        Retrieves all :class:`discord.User` subscribed to the event .

        .. note::

            This method is an API call.

        Raises
        -------
        HTTPException
            Retrieving the users failed.

        Returns
        -------
        Sequence[:class:`discord.User`]
            All users subscribed to the event.
        """
        data = await self._state.http.get_scheduled_event_users(self.guild.id, self.id)


        return [User(state=self._state, data=d['user']) for d in data]



