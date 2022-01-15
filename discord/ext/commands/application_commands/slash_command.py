from __future__ import annotations
import asyncio
import inspect
import discord
from typing import (
    Any,
    Callable,
    ClassVar,
    Dict,
    Generic,
    List,
    Literal,
    Optional,
    overload,
    Type,
    TypeVar,
    TYPE_CHECKING,
    Union,

)


from discord.interactions import Interaction
from discord.utils import escape_dict, escape_list
from .slash_options import SlashCommandOption


from ..errors import *

if TYPE_CHECKING:
    from typing_extensions import Concatenate, ParamSpec, TypeGuard

    from discord.message import Message

    from .._types import (
        Coro,
        CoroFunc,
        Check,
        Hook,
        Error,
    )
    from ..core import _CaseInsensitiveDict

if TYPE_CHECKING:
    P = ParamSpec('P')
else:
    P = TypeVar('P')

from enum import Enum

from .._types import _BaseSlashCommand

__all__ = (
    'SlashCommand',
    'SlashCommandOption'
)


MISSING: Any = discord.utils.MISSING


T = TypeVar('T')
SlashCommandT = TypeVar('SlashCommandT', bound='SlashCommand')
InteractionT = TypeVar('InteractionT', bound='Interaction')



class SlashCommand(_BaseSlashCommand, Generic[P, T]):
    r"""A class that implements the protocol for a bot slash command.

    These are not created manually, instead they are created via the
    decorator or functional interface.

    Key word arguments
    -----------
    name: :class:`str`
        The name of the command.
    description: :class:`str`
        The description to appear with the slash command.
        The message prefixed into the default help command.
    callback: :ref:`coroutine <coroutine>`
        The coroutine that is executed when the slash command is called.

    help: Optional[:class:`str`]
        The long help text for the command.
    brief: Optional[:class:`str`]
        The short help text for the command.
    usage: Optional[:class:`str`]
        A replacement for arguments in the default help text.
    allowed_users: Optional[Dict[:class:`int`, :class:`bool`]]
        A mapping of user ids to a boolean value for wether they should be allowed to use the command or not 
    allowed_roles: Optional[Dict[:class:`int`, :class:`bool`]]
        A mapping of role ids to a boolean value for wether users with those roles should be allowed to use the command or not 
    extras: :class:`dict`
        A dict of user provided extras to attach to the SlashCommand. 

        .. note::
            This object may be copied by the library.


        .. versionadded:: 2.0
    """
    __original_kwargs__: Dict[str, Any]

    def __new__(cls: Type[SlashCommandT], *args: Any, **kwargs: Any) -> SlashCommandT:
        self = super().__new__(cls)
        self.__original_kwargs__ = kwargs.copy()
        return self



    def __init__(self, func: 
            Callable[Concatenate[InteractionT, P], Coro[T]],
            **kwargs: Any):

        if not asyncio.iscoroutinefunction(func):
            raise TypeError('Callback must be a coroutine.')

        name = kwargs.get('name') or func.__name__
        if not isinstance(name, str):
            raise TypeError('Name of a command must be a string.')
        self.name: str = name.lower()

        self.callback = func

        help_doc = kwargs.get('help')
        if help_doc is not None:
            help_doc = inspect.cleandoc(help_doc)
        else:
            help_doc = inspect.getdoc(func)
            if isinstance(help_doc, bytes):
                help_doc = help_doc.decode('utf-8')

        self.help: Optional[str] = help_doc

        self.brief: Optional[str] = kwargs.get('brief')
        self.usage: Optional[str] = kwargs.get('usage')
        self.extras: Dict[str, Any] = kwargs.get('extras', {})
        self.allowed_users: Dict[int, bool] = kwargs.get('allowed_users', {})
        self.allowed_roles: Dict[int, bool] = kwargs.get('allowed_roles', {})
        self._is_sub_command: bool = kwargs.get('is_sub', False)
        self._is_sub_sub_command: bool = kwargs.get('is_sub_sub', False)
        self.autocomplete_callback = None
        
        description = kwargs.get('description') or self.name


        if not isinstance(description, str):
            raise TypeError('Description of a command must be a string.')
        if not 1 < len(description) < 100:
            raise ValueError("Description of slash command must be in range ( 1 - 100 )")

        self.description = inspect.cleandoc(description)


        self._options: List[SlashCommandOption] = []

        options = kwargs.get('options')
        if options:
            if not isinstance(options, list):
                raise TypeError('Options must be a list of discord.SlashCommandOptions')
            
            if not all(isinstance(x, SlashCommandOption) for x in options):
                raise TypeError('Options must be a list of discord.SlashCommandOptions')
            
            self._options = options
        self._id: int = 0
        

    def on_autocomplete(self) -> Callable:
        def inner(func: Callable) -> SlashCommand:
            self.autocomplete_callback = func
        return inner
    
    @overload
    def raw_command(cls, name:str, **attrs) -> SlashCommand: ...

    @classmethod
    def raw_command(cls, **kwargs) -> Callable:
        def inner(func: Callable) -> SlashCommand:
            command = SlashCommand(func, is_sub=True, **kwargs)
            return command

        return inner

    @property
    def id(self):
        return self._id
    
    @property
    def options(self):
        return self._options
    
    @property
    def json(self):
        json_ = {
            "type":1,
            "name": self.name,
            "description": self.description,
            "options": [i.json for i in self.options]
        }
        return escape_dict(json_)

    @property
    def permissions_json(self):
        json_ = []
        
        for id_, allow_ in self.allowed_users.items():
            json_.append(
                {
                    "id": int(id_),
                    "type": 2,
                    "permission": int(allow_),
                }
            ) 
        
        for id_, allow_ in self.allowed_roles.items():
            json_.append(
                {
                    "id": int(id_),
                    "type": 1,
                    "permission": int(allow_),
                }
            ) 
        
        

        if len(json_): return escape_list(json_)
        else: return None 
