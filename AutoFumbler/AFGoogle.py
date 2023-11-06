import pathlib
import typing
from translatepy.translators.google import GoogleTranslateV2
import concurrent.futures

import textwrap
from .AFCore import AutoTranslator


class GoogleTranslator(AutoTranslator):
    def __init__(self, config: dict, game_config: dict) -> None:
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
        self, events: typing.Dict[str,typing.List[str]]
    ) -> typing.List[typing.List[str]]:
        # pass
        # collapse = self.config["Google"]["collapse_event_newlines"]
        punctuations = self.config["Google"]["punctuations"]
        max_event_lines = self.config["Google"]["max_event_lines"]
        collapse_length = self.config["Google"]["collapse_length"]
        sep = "\n<===>\n"
        
        for event_section in events.items():
            chunk = []
            tl_events = []
            unpacked_list_events = self.unpack_list_like(event_section)
            for idx, event_data in enumerate(unpacked_list_events):
                if not self.jp_rgx.search(event_data["txt"]):
                    continue
                if event_data["typ"] == "choice":
                    translated = self.google_instance.translate(event_data["text"],"jp","en").result
                    orig_count = len(event_data["text"].split("\n"))
                    event_data["text"] = translated.strip()
                    nw_lines = event_data["text"].split("\n")
                    if len(nw_lines) < orig_count:
                        print("[Pad due to text]: ", orig_count, event_data["text"], )
                        event_data["text"] += "\n" * (orig_count - len(nw_lines))
                    unpacked_list_events[idx] = event_data
                else:
                    orig_lines = event_data["text"].split("\n")
                    if punctuations and len(orig_lines) > 2:
                        concat_lines = orig_lines[0]
                        if len(concat_lines) <= collapse_length:
                            concat_lines += "\n"
                        for line in orig_lines[1:]:
                            if line[-1] in punctuations:
                                concat_lines += line + "\n"
                            else:
                                concat_lines += line
                            line.rstrip()
                    else:
                        # Keep it as is.
                        concat_lines = "\n".join(orig_lines)
                    translated = self.google_instance.translate(concat_lines,"jp","en").result
                    print("translated:\n", concat_lines, "\n\n",translated)
                    orig_count = len(event_data["text"].split("\n"))
                    event_data["text"] = translated.strip()
                    nw_lines = event_data["text"].split("\n")
                    if len(nw_lines) < orig_count:
                        print("[Pad due to text]: ", orig_count, event_data["text"], )
                        event_data["text"] += "\n" * (orig_count - len(nw_lines))
        
                            


                        
    def translate_exports(
        self,
        exports: typing.List[pathlib.Path] | typing.Generator[pathlib.Path, None, None],
        actors: bool,
        events: bool,
        items: bool,
        names: bool,
    ):
        for export in exports:
            export_name = export.name.lower()
            if actors and "actors" in export_name:
                data = self.read_nested(export)
                if not isinstance(data, dict):
                    return
                translate_data = {}
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
                self.write_nested({"Actors": z}, export)
            if events and "commonevents" in export_name:
                data = self.read_nested(export)
                if not isinstance(data, dict):
                    return
                self.translate_events(data)