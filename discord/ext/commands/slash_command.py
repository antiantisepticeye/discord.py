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
from discord.slash_options import SlashCommandOption


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

from enum import Enum

from ._types import _BaseSlashCommand

__all__ = (
    'SlashCommand',
    'SlashCommandOption',
    'SlashCommandGroup'
)


MISSING: Any = discord.utils.MISSING


T = TypeVar('T')
SlashCommandT = TypeVar('SlashCommandT', bound='SlashCommand')
InteractionT = TypeVar('InteractionT', bound='Interaction')



class SlashCommand(_BaseSlashCommand, Generic[P, T]):
    r"""A class that implements the protocol for a bot slash command.

    These are not created manually, instead they are created via the
    decorator or functional interface.

    Attributes
    -----------
    name: :class:`str`
        The name of the command.
    callback: :ref:`coroutine <coroutine>`
        The coroutine that is executed when the slash command is called.
    help: Optional[:class:`str`]
        The long help text for the command.
    brief: Optional[:class:`str`]
        The short help text for the command.
    usage: Optional[:class:`str`]
        A replacement for arguments in the default help text.
    description: :class:`str`
        The description to appear with the slash command.
        The message prefixed into the default help command.
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
        


    @property
    def id(self):
        return self._id
    
    @property
    def options(self):
        return self._options


class SlashCommandGroup: 
    def __init__(self) -> None:
        pass

