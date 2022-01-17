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


import asyncio
import aiohttp
import collections
import collections.abc
import inspect
import importlib.util
import sys
import traceback
import types
import logging
from typing import Any, Callable, Mapping, List, Dict, TYPE_CHECKING, Optional, Tuple, TypeVar, Type, Union

import discord
from .message_command import MessageCommand
from .slash_command import SlashCommand
from .slash_command_group import SlashCommandGroup, SlashSubGroup
from .user_command import UserCommand
from .slash_options import SlashCommandOption, InteractionDataOption
from discord.enums import try_enum, SlashCommandOptionTypes


from .application_core import ApplicationGroupMixin, ApplicationCommandsDict
from .view import StringView

from . import errors
from discord.http import Route


if TYPE_CHECKING:
    import importlib.machinery

    from discord.message import Message
    from ._types import (
        Check,
        CoroFunc,
    )

__all__ = (
    'ApplicationBot',
)

MISSING: Any = discord.utils.MISSING

T = TypeVar('T')
CFT = TypeVar('CFT', bound='CoroFunc')



class ApplicationBotBase(ApplicationGroupMixin):
    def __init__(self, **options):
        super().__init__(**options)        
        self.extra_events: Dict[str, List[CoroFunc]] = {}
        self.description = inspect.cleandoc(options.get('description')) if options.get('description') else ''
        self.owner_id = options.get('owner_id')
        self.owner_ids = options.get('owner_ids', set())
        self.log_app_commands = options.get('log_app_commands', False)
        
        self.add_listener( self._deploy_application_commands, 'on_connect')
        self.add_listener( self._listen_application_commands, 'on_interaction')
        

        if self.owner_id and self.owner_ids:
            raise TypeError('Both owner_id and owner_ids are set.')

        if self.owner_ids and not isinstance(self.owner_ids, collections.abc.Collection):
            raise TypeError(f'owner_ids must be a collection not {self.owner_ids.__class__!r}')
        

    # internal helpers

    def dispatch(self, event_name: str, *args: Any, **kwargs: Any) -> None:
        # super() will resolve to Client
        super().dispatch(event_name, *args, **kwargs)  # type: ignore
        ev = 'on_' + event_name
        for event in self.extra_events.get(ev, []):
            self._schedule_event(event, ev, *args, **kwargs)  # type: ignore


    async def _listen_application_commands(self, interaction: discord.Interaction):
            # check interaction type
            if interaction.type is discord.InteractionType.application_command:
                
                command_type = int(interaction.data['type'])
                if command_type == 1:
                    command, group = self.__resolve_slash_command(interaction)
                    args = []
                    if group is None:
                        if command.options:
                            
                            opts = self.__parse_slash_options(command, interaction)
                            args = [interaction] + opts

                        else:
                            args = [interaction] 
                    else:
                        if command.options:
                            
                            opts = self.__parse_slash_options(command, interaction)
                            args = [group, interaction] + opts

                        else:
                            args = [group, interaction]  
                    try:
                        await command.callback(*args)
                    except Exception as e:                    
                        self.dispatch('interaction_command_error', interaction, e)

                elif command_type == 2:
                    command = self.__resolve_user_command(interaction) 
                    user = self.get_user(int(interaction.data['target_id'])) 
                    await command.callback(interaction, user)

                elif command_type == 3:
                    command = self.__resolve_message_command(interaction)
                    message = await interaction.channel.fetch_message(int(interaction.data['target_id']))
                    await command.callback(interaction, message)
            elif interaction.type is discord.InteractionType.autocomplete:
                command, group = self.__resolve_slash_command(interaction)
                if(command.autocomplete_callback):
                    await command.autocomplete_callback(interaction)


    def __resolve_slash_command(self, interaction:discord.Interaction) -> Tuple[SlashCommand, SlashCommandGroup]:
        group = None
        command = None
        id = int(interaction.data['id'])
        name = interaction.data['name']
        type = int(interaction.data['type'])
        res = discord.utils.get( self.all_global_application_commands.all_commands, name=name )
        if not res: res = discord.utils.get( self.all_guild_application_commands[int(interaction.guild_id)].all_commands, name=name )
        if isinstance(res, SlashCommand):
            return res, None
            
        elif isinstance(res, SlashCommandGroup):
            options = interaction.data["options"]
            
            res: SlashCommandGroup = res
            for o in options:
                if o["type"] == 1:
                    command = res.commands.get(o["name"])
                elif o["type"] == 2:
                    g: SlashSubGroup = res.groups.get(o["name"])
                    for o_2 in o["options"]:
                        command = g.commands.get(o_2["name"])
            group = res

        if not command: raise Exception("command not found")
        

        return command, group

    def __resolve_user_command(self, interaction:discord.Interaction) -> UserCommand:
        command = None
        id = int(interaction.data['id'])
        name = str(interaction.data['name'])
        command = discord.utils.get(self.all_global_application_commands.all_user_commands, id=id) or discord.utils.get(self.all_global_application_commands.all_user_commands, name=name)
        if command is None: 
            guild_commands = self.all_guild_application_commands.get(int(interaction.guild_id))
            if guild_commands:
                command = discord.utils.get(guild_commands.all_user_commands, id=id) or discord.utils.get(guild_commands.all_user_commands, name=name)
        
        if command is None: raise Exception("command not found")
        
        return command
    def __parse_slash_options(self, command: SlashCommand, interaction:discord.Interaction) -> List[Union[discord.User, discord.Role, discord.ChannelType, str, int, bool, MISSING]]:
    
        parsed_opts = {}
        
        options:List[Dict] = interaction.data.get('options', [])
        
        def parse_opts(options):
            for option in options:
                type =  option['type']

                if type == 1 or type == 2:
                    return parse_opts(option.get('options', []))

                
                option_value = option['value']
                
                if type == SlashCommandOptionTypes.user.value:

                    option_value = self.get_user(int(option_value))
                    
                elif type == SlashCommandOptionTypes.channel.value:
                    guild = interaction.guild
                    option_value = guild.get_channel(int(option_value))
                
                elif type == SlashCommandOptionTypes.role.value:
                    guild = interaction.guild
                    option_value = guild.get_role(int(option_value))

                option['type'] = try_enum(SlashCommandOptionTypes, type)
                option["value"]= option_value
                parsed_opts[option["name"]] = InteractionDataOption(option)
            final_opts = []
            for i in command.options:
                
                d =  InteractionDataOption.from_slash_option(i)
                final_opts.append(parsed_opts.get(i.name, d))

            return final_opts
        return parse_opts(options)


    async def _deploy_application_commands(self, *args,**kwargs):

        BASE_URL = Route.BASE
        header = {'Authorization' : 'Bot ' + self.http.token}
        
        all_global_commands = []   # make list to store commands when looping through them

        for command in self.all_global_application_commands.all_commands:     # looping through message commands
                all_global_commands.append(command.json)
        
        for group in self.all_global_application_commands.all_slash_command_group:
            if not group.is_guild:
                all_global_commands.append(group.json)
            

        if self.log_app_commands:
            print(f"Upserting Global  Commands now: {[i['name'] for i in all_global_commands]!r}")
        r = await self.http.bulk_upsert_global_commands(self.application_id, all_global_commands)
        for command_data in r:
            cmd_id   = int(command_data['id'])
            cmd_type = int(command_data['type'])
            cmd_name = str(command_data['name'])

            cmd_ = discord.utils.get(self.all_global_application_commands.all_commands, name=cmd_name)
            if(cmd_): cmd_._id = cmd_id

        if self.log_app_commands:
            print(f"Succcessfully upserted Global Commands: {[ (i['name'], i['id']) for i in r]!r}")


        for guild_id, commands in self.all_guild_application_commands.items():
            if self.log_app_commands:
                print(f"Upserting Guild Commands for guild={guild_id} now: {[i['name'] for i in all_global_commands]!r}")

            r = await self.http.bulk_upsert_guild_commands(self.application_id, guild_id, [i.json for i in commands.all_commands])
            for command_data in r:
                cmd_id   = int(command_data['id'])
                cmd_type = int(command_data['type'])
                cmd_name = str(command_data['name'])
        


                guild_commands = self.all_guild_application_commands[guild_id]
                cmd = guild_commands.get_by_name(cmd_name)
                cmd._id = cmd_id

            if self.log_app_commands:
                print(f"Succcessfully upserted Guild for guild={guild_id} Commands: {[ (i['name'], i['id']) for i in r]!r}")





    def add_slash_group(self, slash_cog: Type[SlashCommandGroup]):
        cog = slash_cog
        if cog.is_guild:
            if not self.all_guild_application_commands.get(cog.guild_id): self.all_guild_application_commands[cog.guild_id] = ApplicationCommandsDict()
            self.all_guild_application_commands[cog.guild_id].add_command(cog)
        else:
            self.all_global_application_commands.add_command(cog)


    def _resolve_name(self, name: str, package: Optional[str]) -> str:
        try:
            return importlib.util.resolve_name(name, package)
        except ImportError:
            raise errors.ExtensionNotFound(name)
 
    def _slash_load_from_module_spec(self, spec: importlib.machinery.ModuleSpec, key: str) -> None:

        lib = importlib.util.module_from_spec(spec)
        sys.modules[key] = lib
        try:
            spec.loader.exec_module(lib)  # type: ignore
        except Exception as e:
            del sys.modules[key]
            raise errors.ExtensionFailed(key, e) from e

        try:
            setup = getattr(lib, 'setup')
        except AttributeError:
            del sys.modules[key]
            raise errors.NoEntryPointError(key)

        try:
            setup(self)
        except Exception as e:
            del sys.modules[key]
            raise errors.ExtensionFailed(key, e) from e


    def load_slash_module(self, name: str, *, package: Optional[str] = None) -> None:
        name = self._resolve_name(name, package)
        if name in [i.name for i in self.all_global_application_commands.all_slash_command_group]:
            raise errors.ExtensionAlreadyLoaded(name)
        spec = importlib.util.find_spec(name)
        if spec is None:
            raise errors.ExtensionNotFound(name)

        self._slash_load_from_module_spec(spec, name)

    # listener registration

    def add_listener(self, func: CoroFunc, name: str = MISSING) -> None:
        """The non decorator alternative to :meth:`.listen`.

        Parameters
        -----------
        func: :ref:`coroutine <coroutine>`
            The function to call.
        name: :class:`str`
            The name of the event to listen for. Defaults to ``func.__name__``.

        Example
        --------

        .. code-block:: python3

            async def on_ready(): pass
            async def my_message(message): pass

            bot.add_listener(on_ready)
            bot.add_listener(my_message, 'on_message')

        """
        name = func.__name__ if name is MISSING else name

        if not asyncio.iscoroutinefunction(func):
            raise TypeError('Listeners must be coroutines')

        if name in self.extra_events:
            self.extra_events[name].append(func)
        else:
            self.extra_events[name] = [func]

    def remove_listener(self, func: CoroFunc, name: str = MISSING) -> None:
        """Removes a listener from the pool of listeners.

        Parameters
        -----------
        func
            The function that was used as a listener to remove.
        name: :class:`str`
            The name of the event we want to remove. Defaults to
            ``func.__name__``.
        """

        name = func.__name__ if name is MISSING else name

        if name in self.extra_events:
            try:
                self.extra_events[name].remove(func)
            except ValueError:
                pass

    def listen(self, name: str = MISSING) -> Callable[[CFT], CFT]:
        """A decorator that registers another function as an external
        event listener. Basically this allows you to listen to multiple
        events from different places e.g. such as :func:`.on_ready`

        The functions being listened to must be a :ref:`coroutine <coroutine>`.

        Example
        --------

        .. code-block:: python3

            @bot.listen()
            async def on_message(message):
                print('one')

            # in some other file...

            @bot.listen('on_message')
            async def my_message(message):
                print('two')

        Would print one and two in an unspecified order.

        Raises
        -------
        TypeError
            The function being listened to is not a coroutine.
        """

        def decorator(func: CFT) -> CFT:
            self.add_listener(func, name)
            return func

        return decorator

class ApplicationBot(ApplicationBotBase, discord.Client):
    pass


