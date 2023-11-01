import pathlib
import re
import typing
import nestedtext
from translatepy.translators.google import GoogleTranslateV2

import orjson
import textwrap
from .AFCore import AutoTranslator


class GoogleTranslator(AutoTranslator):
    def __init__(self, config: dict, game_config:dict) -> None:
        super().__init__(config, game_config)
        self.collapse_event_newlines = config["Google"].get(
            "collapse_event_newlines", True
        )
        self.force_collapse = config["Google"].get("force_collapse", False)
        # self.
        self.google_instance = GoogleTranslateV2()

    def translate_actors(
        self, names: typing.Dict[int, typing.List[str]]
    ) -> typing.Dict[int, typing.List[str]]:

        for actor_idx, actor_data in names.items():
            name, profile, nickname = actor_data
            profile_lines = len(profile.split("\n"))
            profile = "".join(profile.split("\n"))
            google_packed = "\n".join([name, nickname, profile])
            r = self.google_instance.translate("===\n{google_packed}\n===", "en", "jp")
            try:
                name, profile, nickname = r.result.strip().split("\n")
            except Exception as e:
                print(e)
                return {}
            wrapped_chars = len(profile) // profile_lines
            profile = textwrap.wrap(profile, width=wrapped_chars)
            names[actor_idx] = [name, profile, nickname]
        return names

    def translate_events(
        self, events: typing.List[typing.List[str]]
    ) -> typing.List[typing.List[str]]:
        # pass
        collapse = self.config["Google"]["collapse_event_newlines"]
        punctuations = self.config["Google"]["punctuations"]
        max_event_lines = self.config["Google"]["max_event_lines"]
        collapse_length = self.config["Google"]["collapse_length"]
        for event_section in events:
            for event in self.unpack_list_like(event_section):
                # Google is quite robust in terms of translation formatting. Unlike ChatGPT.
                if collapse:
                    if (len(event) > max_event_lines and len(event) > 1) or len(event[1]) < collapse_length:
                        # Don't collapse, likely is choices or very short text.
                        translated_lines = "\n".join(event)
                    else:
                        translated_lines = ""
                        expected_lines = 0
                        for line in event[:1]:
                            if line[-1] in punctuations:
                                translated_lines += line + "\n"
                                expected_lines += 1
                            else:
                                translated_lines += line
                                expected_lines += 1
                        translated_lines = translated_lines.strip()
                    event[:1]

    def translate_exports(self, exports: typing.List[pathlib.Path] | typing.Generator[pathlib.Path, None, None], actors: bool, events: bool, items: bool, names: bool):
        for export in exports:
            export_name = export.name.lower()
            if actors and "actors" in export_name:
                data = self.read_nested(export)
                if not isinstance(data,dict):
                    return
                translate_data = {

                }
                rd = {}
                for idx, actor in enumerate(self.unpack_list_like(data["Actors"])):
                    name, note, nick, profile = actor
                    translate_data[idx] = [name, profile, nick]
                    rd[idx] = [name, note, nick, profile]
                translate_data = self.translate_actors(translate_data)
                for idx, actor in enumerate(self.unpack_list_like(data["Actors"])):
                    rd[idx][0] = actor[0]
                    rd[idx][2] = actor[3]
                    rd[idx][3] = actor[2]
                z = []
                for value in rd.values():
                    z.extend(value)
                    z.append("<>")
                self.write_nested({"Actors":z}, export)