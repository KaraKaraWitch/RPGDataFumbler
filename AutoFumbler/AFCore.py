import pathlib
import typing
import dataclasses

import nestedtext

class AutoTranslator:

    def __init__(self, config: dict, game_config:dict) -> None:
        self.config = config
        self.game_config = game_config

    def translate_actors(
        self, names: typing.Dict[int, typing.List[str]]
    ) -> typing.Dict[int, typing.List[str]]:
        """Translates a dictionary of actors

        Args:
            names (typing.Dict[int, typing.List[str]]): The key is defined as the actor index while the list should contain: [name, profile, nickname]

        Returns:
            typing.Dict[int, typing.List[str]]: A dictioanry with the translated results.
        """
        raise NotImplementedError()

    def translate_events(
        self, events: typing.List[typing.List[str]]
    ) -> typing.List[typing.List[str]]:
        """Translates a list of events (Map & CommonEvents)

        Args:
            events (list[list[str]]): Translates a list of events. Main list is each "Group" of event while sub lists are

        Raises:
            NotImplementedError: _description_

        Returns:
            dict: _description_
        """
        raise NotImplementedError()

    def translate_items(
        self, items: typing.Dict[str, typing.List[str]]
    ) -> typing.Dict[str, typing.List[str]]:
        """Translates a dictionary of items (Armors, Items, Weapons)

        Notes are handled strangely since they typically are not displayed in the game. Instead, they are used as metadata.

        Args:
            items (typing.Dict[str, typing.List[str]]): The key is defined as the item index whille the list should contain: [name, description, [note, note_2]]



        Raises:
            NotImplementedError: The function is not implemented by the translator

        Returns:
            typing.Dict[str, typing.List[str]]: _description_
        """
        raise NotImplementedError()

    def translate_name(
        self,
        names: typing.Dict[str, str],
        name_meta: typing.Optional[typing.Any] = None,
    ) -> typing.Dict[str, str]:
        """Translates a dictionary of "Names" (Map Names, Classes, Enemies, etc)

        Notes are handled strangely since they typically are not displayed in the game. Instead, they are used as metadata.

        Args:
            items (typing.Dict[str, str]): The key is defined as the class index while the value is the class name itself.
            name_meta (typing.Optional[typing.Any]): Defaults to None. The meta infomation on how to "Handle" the name in question (context stuff.)



        Raises:
            NotImplementedError: The function is not implemented by the translator

        Returns:
            typing.Dict[str, typing.List[str]]: _description_
        """
        raise NotImplementedError()
    
    def read_nested(self, nested:pathlib.Path) -> typing.Union[typing.List[str], typing.Dict[str,typing.Any], None]:
        try:
            r = nestedtext.loads(nested.read_text(encoding="utf-8"))
            if isinstance(r,(int, dict)):
                return r
            else:
                return None
        except nestedtext.NestedTextError:
            return None
        
    def write_nested(self, data:typing.Dict[str, typing.List[str]], nested:pathlib.Path) -> typing.Union[typing.List[str], typing.Dict[str,typing.Any], None]:
        nested.write_text(nestedtext.dumps(data),encoding="utf-8")
        
    def unpack_list_like(self, list_data:typing.List[str], sep:str="<>") -> typing.List[typing.List[str]]:
        data = []
        buffer = []
        for item in list_data:
            if item == sep:
                data.append(buffer)
                buffer = []
            else:
                buffer.append(item)
        if buffer:
            data.append(buffer)
        return buffer
        

    def translate_exports(
        self,
        exports: typing.Union[
            typing.List[pathlib.Path], typing.Generator[pathlib.Path, None, None]
        ],
        actors: bool,
        events: bool,
        items: bool,
        names: bool,
    ):
        """Translates a list of exports

        Args:
            exports (typing.Union[ typing.List[pathlib.Path], typing.Generator[pathlib.Path, None, None] ]): _description_
            actors (bool): _description_
            events (bool): _description_
            items (bool): _description_
            names (bool): _description_

        Raises:
            NotImplementedError: _description_
        """
        raise NotImplementedError()