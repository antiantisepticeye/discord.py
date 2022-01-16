from __future__ import annotations
from enum import Enum
from typing import Any, Dict, List, Optional, Union, TypedDict
import discord
from discord.abc import MISSING
from discord.enums import SlashCommandOptionTypes
from discord.utils import escape_dict

__all__ = (
    'SlashCommandOption',
    'InteractionDataOption',
)

class Choices(TypedDict):
    name:str
    value: Union[ str, int, float ]

class InteractionDataOption:
    name: str
    type: SlashCommandOptionTypes
    value: Optional[Union[str,int,float, discord.Role, discord.User, discord.ChannelType]]

    def __init__(self, payload: Dict[str, Any]) -> None:
        for key, val in payload.items():
            setattr(self, key, val)
    def __repr__(self) -> str:
        return f'<discordext.commands.InteractionDataOption name={repr(self.name)} value={repr(self.value)}>'

    @classmethod
    def from_slash_option(cls, option:SlashCommandOption) -> InteractionDataOption:
        return cls({
            "name":option.name,
            "type":option.type,
            "value":option.default
        })

class SlashCommandOption:
    Types = SlashCommandOptionTypes

    def __init__(self, name: str, description: str, type_: SlashCommandOptionTypes=3, required:bool=True, choices:List[Choices]=[], min_value: Union[int, float]=None, max_value: Union[int, float]=None, channel_types: List[discord.enums.ChannelType]=[], autocomplete=False, default=MISSING):

        if not isinstance(name, str): 
            raise TypeError('Name of option must be of type string')
        if not isinstance(description, str): 
            raise TypeError('Description of option must be of type string')
        if not (type_ in range(3, 11) or isinstance(type_, SlashCommandOptionTypes)): 
            raise TypeError('Type of option must be of int or a SlashCommandOptionTypes')
        if not isinstance(required, bool): 
            raise TypeError('attribute `required` must be of type bool')


        self.name = name 
        self.description = description
        self.type =  type_ if isinstance(type_, int) else type_.value
        self.required = required
        self.choices = choices
        self.min_value = min_value
        self.max_value = max_value
        self.channel_types = channel_types
        self.autocomplete = autocomplete
        self.default = default

    @property
    def json(self):
        json_ = {
            "name": self.name,
            "description": self.description,
            "type":self.type,
            "required":self.required,
            "choices": self.choices,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "channel_types": self.channel_types,
            "autocomplete": self.autocomplete,
        }
        json_ = escape_dict(json_)
        return json_
        

