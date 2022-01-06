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

from discord.utils import escape_dict
__all__ = (
    'UserCommand'
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

from ._types import _BaseUserCommand



T = TypeVar('T')
UserCommandT = TypeVar('UserCommandT', bound='UserCommand')
InteractionT = TypeVar('InteractionT', bound='Interaction')


class UserCommand(_BaseUserCommand, Generic[P, T]):

    r"""A class that implements the protocol for a bot user command.

    These are not created manually, instead they are created via the
    decorator or functional interface.

    Attributes
    -----------
    name: :class:`str`
        The name of the command.
    callback: :ref:`coroutine <coroutine>`
        The coroutine that is executed when the user command is called.
    help: Optional[:class:`str`]
        The long help text for the command.
    brief: Optional[:class:`str`]
        The short help text for the command.
    usage: Optional[:class:`str`]
        A replacement for arguments in the default help text.
    description: :class:`str`
        An optional description.
        This will not show with the command in the context menu.
    extras: :class:`dict`
        A dict of user provided extras to attach to the UserCommand. 
        
        
        .. note::
            This object may be copied by the library.


        .. versionadded:: 2.0
    """
    __original_kwargs__: Dict[str, Any]

    def __new__(cls: Type[UserCommandT], *args: Any, **kwargs: Any) -> UserCommandT:
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
            "type":2,
            "name":self.name
        }
        return escape_dict(json_)


