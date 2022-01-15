from __future__ import annotations

from discord.utils import escape_dict
from .slash_command import SlashCommand
from typing import (
    Any,
    Optional,
    Type,
    TypeVar,
    Callable,
    ClassVar,
    Union,
    overload,
    Dict,
    List
)


SlashCommandGroupT = TypeVar('SlashCommandGroupT', bound='SlashCommandGroup')

__all__ = (
    'SlashCommandGroup',
    'SlashSubGroup',
)

class SlashSubGroup:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._slash_commands = {}
        self.name = kwargs['name']
        self.description = kwargs.get('description')

    @overload
    def command(self, name:str, **attrs) -> SlashCommand: ...

    def command(self, **kwargs) -> Callable:
        def inner(func: Callable) -> SlashCommand:
            command = SlashCommand(func, is_sub=True, **kwargs)
            if not getattr(self, '_slash_commands', None): self._slash_commands = {}
            self._slash_commands[command.name] = command
            return command

        return inner

    @property
    def commands(self):
        return self._slash_commands

    @property
    def json(self):
        json_ = {
                "type": 2,
                "name": self.name,
                "description": self.description,
                "options": [ i.json for i in self.commands.values() ]
        }

        return escape_dict(json_)

class GroupMeta(type):

    __group_name__: str
    __group_description__: str
    __group_commands__: list[SlashCommand]
    _slash_commands: dict[str, SlashCommand]
    _slash_command_subgroups: dict[str, SlashSubGroup]
    id: str

    def __new__(cls: Type[GroupMeta], *args: Any, **kwargs: Any) -> GroupMeta:
        name, description, attrs = args
        attrs['__group_name__'] = kwargs.pop('name', name)
        attrs['__group_description__'] = kwargs.pop('description', description)
        attrs['guild_id'] = kwargs.pop('guild_id', None)
        initial_commands: List[Union[SlashCommand, SlashSubGroup]] = kwargs.pop('commands', [])

        
        commands = {}
        groups = {}

        for i in initial_commands:
            if isinstance(i, SlashCommand):
                commands[i.name] = i
            elif isinstance(i, SlashSubGroup):
                groups[i.name] = i

        new_cls = super().__new__(cls, name, description, attrs, **kwargs)
        for base in reversed(new_cls.__mro__):
            for elem, value in base.__dict__.items():
    
                is_static_method = isinstance(value, staticmethod)
                if is_static_method:
                    value = value.__func__
                if isinstance(value, SlashCommand):
                    if is_static_method:
                        raise TypeError(f'Command in method {base}.{elem!r} must not be staticmethod.')
                    if not getattr(value, '_is_sub_command', False):
                        value._is_sub_command = True
                        commands[elem] = value
                elif isinstance(value, SlashSubGroup):
                    if is_static_method:
                        raise TypeError(f'Group in method {base}.{elem!r} must not be staticmethod.')
                    groups[elem] = value
                    
                    

        new_cls.__group_commands__ = list(commands.values()) # this will be copied in Cog.__new__
        new_cls._slash_commands = {i.name: i for i in list(commands.values())}
        new_cls._slash_command_subgroups = {i.name: i for i in list(groups.values())}
        new_cls.id = 0

        return new_cls

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args)


    @overload
    def command(self, name:str, **attrs) -> SlashCommand: ...

    def command(self, **kwargs) -> Callable:
        def inner(func: Callable) -> SlashCommand:
            command = SlashCommand(func, is_sub=True, **kwargs)
            if not getattr(self, '_slash_commands', None): self._slash_commands = {}
            self._slash_commands[command.name] = command
            return command

        return inner

    @overload
    def sub_group(self, name:str, **attrs) -> SlashCommand: ...

    def sub_group(self, **kwargs) -> Callable:
        def inner(func: Callable) -> SlashSubGroup:
            name = (kwargs["name"] or func.__name__).lower()
            description = kwargs.get("description")
            command = SlashSubGroup(name=name, description=description)
            if not getattr(self, '_slash_commands', None): self._slash_commands = {}
            self._slash_command_subgroups[command.name] = command
            return command

        return inner







class SlashCommandGroup(metaclass=GroupMeta):
    

    __group_name__: ClassVar[str]
    __group_description__: ClassVar[str]
    __group_commands__: ClassVar[List[SlashCommand]]
    _slash_commands: ClassVar[Dict[str, SlashCommand]]
    _slash_command_subgroups: ClassVar[Dict[str, SlashSubGroup]]
    id: ClassVar[int]
    guild_id: ClassVar[Optional[int]]



    def __new__(cls: Type[SlashCommandGroupT], *args: Any, **kwargs: Any) -> SlashCommandGroupT:
    
        self = super().__new__(cls)

        self.__group_commands__ = cls.__group_commands__  
        self._slash_commands = cls._slash_commands
        self._slash_command_subgroups = cls._slash_command_subgroups
        self.id = cls.id
        

        # Update the Command instances dynamically as well
        for command in self.__group_commands__:
            setattr(self, command.name, command)

        return self

    @property
    def name(self):
        return (self.__group_name__ or self.__class__.__name__).lower()

    @property
    def commands(self):
        return self._slash_commands

    @property
    def groups(self):
        return self._slash_command_subgroups

    @property
    def description(self):
        return self.__group_description__.lower()
    @property
    def is_guild(self):
        return (not self.guild_id is None)
    
    @property
    def json(self):
        json_ = {
                "type": 1,
                "name": self.name,
                "description": self.description,
                "options": [ i.json for i in self.commands.values() ] + [ i.json for i in self.groups.values() ]
        }

        return escape_dict(json_)

