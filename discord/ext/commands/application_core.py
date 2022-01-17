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

from typing import (
    Any,
    Callable,
    Dict,
    Generator,
    Generic,
    Literal,
    List,
    Optional,
    Union,
    Set,
    Tuple,
    TypeVar,
    Type,
    TYPE_CHECKING,
    overload,
)
import asyncio
import functools
import inspect
import datetime

import discord
from discord import utils
from discord.abc import User

from .errors import *

from discord.interactions import Interaction
from .message_command import MessageCommand
from .slash_command import SlashCommand
from .slash_command_group import SlashCommandGroup
from .user_command import UserCommand
from .slash_options import SlashCommandOption


if TYPE_CHECKING:
    from typing_extensions import Concatenate, ParamSpec

    from discord.message import Message

    from ._types import (
        Coro,
    )


__all__ = (
    'Command',
    'Group',
    'GroupMixin',
    'SlashCommand',
    'SlashCommandOption',
    'SlashCommandGroup',
)

MISSING: Any = discord.utils.MISSING


if TYPE_CHECKING:
    P = ParamSpec('P')
else:
    P = TypeVar('P')


T = TypeVar('T')
SlashCommandT = TypeVar('SlashCommandT', bound='SlashCommand')
MessageCommandT = TypeVar('MessageCommandT', bound='MessageCommand')
UserCommandT = TypeVar('UserCommandT', bound='UserCommand')
InteractionT = TypeVar('InteractionT', bound='Interaction')




def slash_command(
    name: str = MISSING,
    description: str = MISSING,
    cls: Type[SlashCommandT] = MISSING,
    **attrs: Any
) -> Callable[
    [
        Callable[Concatenate[InteractionT, P], Coro[T]]
    ]
, Union[SlashCommand[P, T], SlashCommandT]]:
    """A decorator that transforms a function into a :class:`.SlashCommand`

    By default the ``help`` attribute is received automatically from the
    docstring of the function and is cleaned up with the use of
    ``inspect.cleandoc``. If the docstring is ``bytes``, then it is decoded
    into :class:`str` using utf-8 encoding.


    Parameters
    -----------
    name: :class:`str`
        The name to create the command with. By default this uses the
        function name unchanged.
    cls
        The class to construct with. By default this is :class:`.SlashCommand`.
        You usually do not change this.
    attrs
        Keyword arguments to pass into the construction of the class denoted
        by ``cls``.

    Raises
    -------
    TypeError
        If the function is not a coroutine or is already a command.
    """
    if cls is MISSING:
        cls = SlashCommand  # type: ignore

    def decorator(func:
            Callable[Concatenate[InteractionT, P], Coro[Any]]
        ) -> SlashCommandT:
        if isinstance(func, SlashCommand):
            raise TypeError('Callback is already a command.')
        return cls(func, name=name, description=description, **attrs)

    return decorator

def message_command(
    name: str = MISSING,
    cls: Type[MessageCommandT] = MISSING,
    **attrs: Any
) -> Callable[
    [
        Callable[Concatenate[InteractionT, P], Coro[T]]
    ]
, Union[MessageCommand[P, T], MessageCommandT]]:
    """A decorator that transforms a function into a :class:`.MessageCommand`

    By default the ``help`` attribute is received automatically from the
    docstring of the function and is cleaned up with the use of
    ``inspect.cleandoc``. If the docstring is ``bytes``, then it is decoded
    into :class:`str` using utf-8 encoding.


    Parameters
    -----------
    name: :class:`str`
        The name to create the command with. By default this uses the
        function name unchanged.
    cls
        The class to construct with. By default this is :class:`.MessageCommand`.
        You usually do not change this.
    attrs
        Keyword arguments to pass into the construction of the class denoted
        by ``cls``.

    Raises
    -------
    TypeError
        If the function is not a coroutine or is already a command.
    """
    if cls is MISSING:
        cls = MessageCommand  # type: ignore

    def decorator(func:
            Callable[Concatenate[InteractionT, P], Coro[Any]]
        ) -> MessageCommandT:
        if isinstance(func, MessageCommand):
            raise TypeError('Callback is already a command.')
        return cls(func, name=name, **attrs)

    return decorator


def user_command(
    name: str = MISSING,
    cls: Type[UserCommandT] = MISSING,
    **attrs: Any
) -> Callable[
    [
        Callable[Concatenate[InteractionT, P], Coro[T]]
    ]
, Union[UserCommand[P, T], UserCommandT]]:
    """A decorator that transforms a function into a :class:`.UserCommand`

    By default the ``help`` attribute is received automatically from the
    docstring of the function and is cleaned up with the use of
    ``inspect.cleandoc``. If the docstring is ``bytes``, then it is decoded
    into :class:`str` using utf-8 encoding.


    Parameters
    -----------
    name: :class:`str`
        The name to create the command with. By default this uses the
        function name unchanged.
    cls
        The class to construct with. By default this is :class:`.UserCommand`.
        You usually do not change this.
    attrs
        Keyword arguments to pass into the construction of the class denoted
        by ``cls``.

    Raises
    -------
    TypeError
        If the function is not a coroutine or is already a command.
    """
    if cls is MISSING:
        cls = UserCommand  # type: ignore

    def decorator(func:
            Callable[Concatenate[InteractionT, P], Coro[Any]]
        ) -> UserCommandT:
        if isinstance(func, UserCommand):
            raise TypeError('Callback is already a command.')
        return cls(func, name=name, **attrs)

    return decorator


class ApplicationCommandsDict():
    def __init__(self) -> None:
        self.__data: List[Union[UserCommand, MessageCommand, SlashCommand, SlashCommandGroup]] = []

    def add_command(self, command: Union[UserCommand, MessageCommand, SlashCommand, SlashCommandGroup]):
        self.__data.append(command)

    def __getitem__(self, __key: Union[str, int]):
        try:
            self.all_commands_mapping_by_names[__key]
        except KeyError:
            return self.all_commands_mapping_by_ids[__key]

    def __repr__(self) -> str:
        type_ = type(self)
        module = type_.__module__
        qualname = type_.__qualname__
        return f"<{module}.{qualname} {repr(self.__data)}>"

    def get(self, __key: Union[str, int], __default:Any=None) -> Optional[Union[UserCommand, MessageCommand, SlashCommand, SlashCommandGroup]]:
        try:
            self[__key]
        except KeyError:
            return __default
    def get_by_name(self, __key: str, __default:Any=None) -> Optional[Union[UserCommand, MessageCommand, SlashCommand, SlashCommandGroup]]:
            return self.all_commands_mapping_by_names.get(__key, __default)

    def get_by_id(self, __key: int, __default:Any=None) -> Optional[Union[UserCommand, MessageCommand, SlashCommand, SlashCommandGroup]]:
        return self.all_commands_mapping_by_ids.get(__key, __default)

    def get_by_id_deep(self, __key:int, __default:Any=None) -> Optional[Union[UserCommand, MessageCommand, SlashCommand, SlashCommandGroup]]:
        try:
            return self.all_commands_mapping_by_ids[__key]
        except KeyError:
            try:
                return discord.utils.get(self.all_slash_command_group, id=__key)
            except KeyError:
                return __default

    @property
    def all_commands(self):
        return self.__data

    @property
    def all_commands_mapping_by_ids(self):
        return { i.id : i for i in self.__data }

    @property
    def all_commands_mapping_by_names(self):
        return { i.name : i for i in self.__data }

    @property
    def all_message_commands(self):
        return [i for i in self.__data if isinstance(i, MessageCommand)]

    @property
    def all_user_commands(self):
        return [i for i in self.__data if isinstance(i, UserCommand)]

    @property
    def all_slash_commands(self):
        return [i for i in self.__data if isinstance(i, SlashCommand)]

    @property
    def all_slash_command_group(self):
        return [i for i in self.__data if isinstance(i, SlashCommandGroup)]
    



class ApplicationGroupMixin:
    """A mixin that implements common functionality for classes that behave
    similar to :class:`.Group` and are allowed to register commands.

    Attributes
    -----------
    all_commands: :class:`dict`
        A mapping of command name to :class:`.Command`
        objects.
    all_global_application_commands: :class:`ApplicationCommandsDict`
        A mapping of slash command name to :class:`.SlashCommand`
        objects.
    all_guild_application_commands: :class:`dict`
        A mapping of guild specific guild id to a mapping of slash command name to :class:`.SlashCommand`
        objects.
    case_insensitive: :class:`bool`
        Whether the commands should be case insensitive. Defaults to ``False``.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        case_insensitive = kwargs.get('case_insensitive', False)
        self.all_global_application_commands: ApplicationCommandsDict = ApplicationCommandsDict()
        self.all_guild_application_commands:  Dict[int, ApplicationCommandsDict] = {}
        super().__init__(*args, **kwargs)

    def slash_command(
        self,
        name: str = MISSING,
        description: str = MISSING,
        cls: Type[SlashCommandT] = MISSING,
        *args: Any,
        **kwargs: Any,
    ) -> Callable[[Callable[Concatenate[InteractionT, P], Coro[Any]]], SlashCommandT]:
        """A shortcut decorator that invokes :func:`.slash_command` and adds it to
        the internal command list via :meth:`~.GroupMixin.add_global_slash_command`.

        Returns
        --------
        Callable[..., :class:`SlashCommand`]
            A decorator that converts the provided method into a SlashCommand, adds it to the bot, then returns it.
        """
        def decorator(func: Callable[Concatenate[InteractionT, P], Coro[Any]]) -> SlashCommandT:
            kwargs.setdefault('parent', self)
            guild=kwargs.get('guild', None)
            result = slash_command(name=name, description=description, cls=cls, *args, **kwargs)(func)
            self.add_slash_command(result, guild=guild)

            return result

        return decorator

    def add_slash_command(self, command: SlashCommand, guild:int=None) -> None:
        """Adds a :class:`.SlashCommand` into the internal list of slash commands.


        Parameters
        -----------
        command: :class:`SlashCommand`
            The command to add.

        guild: :class:`Optional[int]`
            The id of guild to add the command to. If `None`, then slash command is added to global scope instead.

        Raises
        -------
        :exc:`.CommandRegistrationError`
            If the slash command is already registered by different command.
        TypeError
            If the command passed is not a subclass of :class:`.SlashCommand`.
        """

        if not isinstance(command, SlashCommand):
            raise TypeError('The command passed must be a subclass of SlashCommand')

        if isinstance(self, SlashCommand):
            command.parent = self

        if command.name in self.all_global_application_commands.all_commands_mapping_by_names.keys():
            raise CommandRegistrationError(command.name)

        if guild is None:
            self.all_global_application_commands.add_command(command)
            
        else:
            if guild in self.all_guild_application_commands:
                if command.name in self.all_guild_application_commands[guild].all_slash_commands:
                    raise CommandRegistrationError(command.name)


            if self.all_guild_application_commands.get(guild):
                self.all_guild_application_commands[guild].add_command(command)
            else:
                self.all_guild_application_commands[guild] = ApplicationCommandsDict()
                self.all_guild_application_commands[guild].add_command(command)


    def get_global_slash_command(self, name: str) -> Optional[SlashCommand]:
        """Get a :class:`.SlashCommand` from the internal list
        of slash commands.

        Parameters
        -----------
        name: :class:`str`
            The name of the slash command to get.

        Returns
        --------
        Optional[:class:`SlashCommand`]
            The slash command that was requested. If not found, returns ``None``.
        """

        # fast path, no space in name.
        if ' ' not in name:
            return self.all_global_application_commands.get(name)

        names = name.split()
        if not names:
            return None
        obj = self.all_global_application_commands.get(names[0])
        if not isinstance(obj, ApplicationGroupMixin):
            return obj

        for name in names[1:]:
            try:
                obj = obj.all_global_application_commands[name]  # type: ignore
            except (AttributeError, KeyError):
                return None

        return obj




    def message_command(
        self,
        name: str = MISSING,
        cls: Type[MessageCommandT] = MISSING,
        *args: Any,
        **kwargs: Any,
    ) -> Callable[[Callable[Concatenate[InteractionT, P], Coro[Any]]], MessageCommandT]:
        """A shortcut decorator that invokes :func:`.message_command` and adds it to
        the internal command list via :meth:`~.GroupMixin.add_message_command`.

        Returns
        --------
        Callable[..., :class:`MessageCommand`]
            A decorator that converts the provided method into a user application command, adds it to the bot, then returns it.
        """
        def decorator(func: Callable[Concatenate[InteractionT, P], Coro[Any]]) -> MessageCommandT:
            guild=kwargs.get('guild')
            result = message_command(name=name,cls=cls, *args, **kwargs)(func)
            self.add_message_command(result, guild=guild)
            return result

        return decorator

    def add_message_command(self, command: MessageCommand, guild:int=None) -> None:
        """Adds a :class:`.MessageCommand` to the internal list of message commands.


        Parameters
        -----------
        command: :class:`MessageCommand`
            The command to add.

        guild: :class:`Optional[int]`
            The id of guild to add the command to. If `None`, then slash command is added to global scope instead.

        Raises
        -------
        :exc:`.CommandRegistrationError`
            If the message command is already registered by different command.
        TypeError
            If the command passed is not a subclass of :class:`.MessageCommand`.
        
        """
        
        if not isinstance(command, MessageCommand):
            raise TypeError('The command passed must be a subclass of MessageCommand')

        if isinstance(self, MessageCommand):
            command.parent = self


        if guild != None:
            if self.all_guild_application_commands.get(guild):
                self.all_guild_application_commands[guild].add_command(command)
            else:
                self.all_guild_application_commands[guild] = ApplicationCommandsDict()
                self.all_guild_application_commands[guild].add_command(command)
        else:
            self.all_global_application_commands.add_command(command)

    def user_command(
        self,
        name: str = MISSING,
        cls: Type[UserCommandT] = MISSING,
        *args: Any,
        **kwargs: Any,
    ) -> Callable[[Callable[Concatenate[InteractionT, P], Coro[Any]]], UserCommandT]:
        """A shortcut decorator that invokes :func:`.message_command` and adds it to
        the internal command list via :meth:`~.GroupMixin.add_message_command`.

        Returns
        --------
        Callable[..., :class:`MessageCommand`]
            A decorator that converts the provided method into a user application command, adds it to the bot, then returns it.
        """
        def decorator(func: Callable[Concatenate[InteractionT, P], Coro[Any]]) -> UserCommandT:
            guild=kwargs.get('guild')
            result = user_command(name=name,cls=cls, *args, **kwargs)(func)
            self.add_user_command(result, guild=guild)
            return result

        return decorator

    def add_user_command(self, command: UserCommand, guild:int=None) -> None:
        """Adds a :class:`.UserCommand` to the internal list of message commands.


        Parameters
        -----------
        command: :class:`UserCommand`
            The command to add.

        guild: :class:`Optional[int]`
            The id of guild to add the command to. If `None`, then slash command is added to global scope instead.

        Raises
        -------
        :exc:`.CommandRegistrationError`
            If the user command is already registered by different command.
        TypeError
            If the command passed is not a subclass of :class:`.UserCommand`.
        
        """
        
        if not isinstance(command, UserCommand):
            raise TypeError('The command passed must be a subclass of UserCommand')

        if isinstance(self, UserCommand):
            command.parent = self

        if command.name in self.all_message_commands:
            raise CommandRegistrationError(command.name)
        
        if guild:
            if self.all_guild_application_commands.get(guild):
                self.all_guild_application_commands[guild].add_command(command)
            else:
                self.all_guild_application_commands[guild] = ApplicationCommandsDict()
                self.all_guild_application_commands[guild].add_command(command)
        else:
            self.all_global_application_commands.add_command(command)
