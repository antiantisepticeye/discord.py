from __future__ import annotations
import asyncio
import inspect
import discord
from typing import (
    Any,
    Callable,
    TYPE_CHECKING,
    Dict,
    Generic,
    Optional,
    Type,
    TypeVar
)

from discord.utils import escape_dict, escape_list
__all__ = (
    'MessageCommand'
)

from discord.interactions import Interaction

from .errors import *

if TYPE_CHECKING:
    from typing_extensions import Concatenate, ParamSpec, TypeGuard

    from discord.message import Message

    from ._types import (
        Coro,
        CoroFunc,
        Check,
        Hook,
        Error,
    )
    from .core import _CaseInsensitiveDict

if TYPE_CHECKING:
    P = ParamSpec('P')
else:
    P = TypeVar('P')


from ._types import _BaseMessageCommand



T = TypeVar('T')
MessageCommandT = TypeVar('MessageCommandT', bound='MessageCommand')
InteractionT = TypeVar('InteractionT', bound='Interaction')


class MessageCommand(_BaseMessageCommand, Generic[P, T]):

    r"""A class that implements the protocol for a bot message command.

    These are not created manually, instead they are created via the
    decorator or functional interface.

    Attributes
    -----------
    name: :class:`str`
        The name of the command.
    callback: :ref:`coroutine <coroutine>`
        The coroutine that is executed when the message command is called.
    help: Optional[:class:`str`]
        The long help text for the command.
    brief: Optional[:class:`str`]
        The short help text for the command.
    usage: Optional[:class:`str`]
        A replacement for arguments in the default help text.
    description: :class:`str`
        An optional description.
        This will not show with the command in the context menu.
    allowed_users: Optional[Dict[:class:`int`, :class:`bool`]]
        A mapping of user ids to a boolean value for wether they should be allowed to use the command or not 
    allowed_roles: Optional[Dict[:class:`int`, :class:`bool`]]
        A mapping of role ids to a boolean value for wether users with those roles should be allowed to use the command or not 
    extras: :class:`dict`
        A dict of user provided extras to attach to the MessageCommand. 
        
        
        .. note::
            This object may be copied by the library.


        .. versionadded:: 2.0
    """
    __original_kwargs__: Dict[str, Any]

    def __new__(cls: Type[MessageCommandT], *args: Any, **kwargs: Any) -> MessageCommandT:
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
        self.name: str = name
        
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
        description = kwargs.get('description') or self.name


        if not isinstance(description, str):
            raise TypeError('Description of a command must be a string.')
        if not 1 < len(description) < 100:
            raise ValueError("Description of slash command must be in range ( 1 - 100 )")

        self.description = inspect.cleandoc(description)

        self._id: int = 0
        


    @property
    def id(self):
        return self._id
    
    @property
    def options(self):
        return self._options

    @property 
    def json(self):
        json_ = {
            "type":3,
            "name":self.name
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





    # def __init__(self, attrs:dict, func: Callable):
    #     name = attrs['name']
    #     if not isinstance(name, str): raise TypeError('Name must be of type string')
    #     self.name: str = name

    #     if not isinstance(func, Callable):   raise TypeError('Function of a command must be a Coroutine.')
    #     self.func: Callable = func

    #     self.id =  ""
       