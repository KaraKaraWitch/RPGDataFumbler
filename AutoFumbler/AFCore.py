import pathlib
import typing
import dataclasses

class AutoTranslator:
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