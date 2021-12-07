from __future__ import annotations
from enum import Enum



class SlashCommandOption:
    class TYPES(Enum):
        STRING = 3
        INTEGER = 4
        BOOLEAN = 5
        USER = 6
        CHANNEL = 7
        ROLE = 8
        MENTIONABLE = 9
        FLOAT = 10
      
    def __init__(self, name: str, description: str, type: SlashCommandOption.TYPES=3, required:bool=True, choices:List[dict]=None):

        if not isinstance(name, str): 
            raise TypeError('Name of option must be of type string')
        if not isinstance(description, str): 
            raise TypeError('Description of option must be of type string')
        if not isinstance(type, int) or (3 > type >= 10): 
            raise TypeError('Type of option must be of int or a SlashCommandOption.Types')
        if not isinstance(required, bool): 
            raise TypeError('attribute `required` must be of type bool')
        if choices and not isinstance(choices, list): 
            raise TypeError('choices must be a list of dicts( name: str, value: str | int | float )')
        

        self.name = name 
        self.description = description
        self.type = type
        self.required = required
        self.choices = choices
        self.json = {
            "name": self.name,
            "description": self.description,
            "type":self.type,
            "required":self.required,
            "choices": choices
        }

