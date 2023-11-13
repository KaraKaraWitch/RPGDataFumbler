import math
import pathlib
import typing
from translatepy.translators.google import GoogleTranslateV2

import textwrap, tqdm
from .AFCore import AutoTranslator


class GoogleTranslator(AutoTranslator):
    def __init__(self, config: dict, game_config: dict) -> None:
        super().__init__(config, game_config)
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
            r = self.google_instance.translate(
                "===\n{google_packed}\n===", "English", source_language="Japanese"
            )
            try:
                name, profile, nickname = r.result.strip().split("\n")
            except Exception as e:
                print(e)
                return {}
            wrapped_chars = len(profile) // profile_lines
            profile = textwrap.wrap(profile, width=wrapped_chars)
            names[actor_idx] = [name, profile, nickname]
        return names

    def collapse_chars(
        self,
        text: str,
    ):
        orig_tol = self.config["Google"]["collapse_chars_tolerance"]
        if orig_tol:
            last_char = None
            buffer = ""
            tolerance = orig_tol
            for char in text:
                if char == "\n":
                    buffer += char
                    last_char = char
                    continue
                if last_char != char:
                    buffer += char
                    last_char = char
                    tolerance = orig_tol
                else:
                    if tolerance > 1:
                        buffer += char
                        tolerance -= 1
            return buffer
        else:
            return text
        
    def text_replace(self, text:str, replacements:typing.Dict[str,typing.List[str]]):
        for k,v in replacements.items():
            if k == "start":
                for (orig, repl) in v:
                    if text.startswith(orig):
                        text = repl + text.removeprefix(orig)
            elif k == "any":
                for (orig, repl) in v:
                    if orig in text:
                        text = text.replace(orig,repl)
            elif k == "end":
                for (orig, repl) in v:
                    if text.endswith(orig):
                        text = text.removesuffix(orig) + repl
        return text


    def translate_events(
        self, events: typing.Dict[str, typing.List[str]]
    ) -> typing.Dict[str, typing.List[str]]:
        # pass
        name_collapse = self.config["Google"]["collapse_event_newlines"]
        punctuations = self.config["Google"]["punctuations"]
        wrap_max = self.config["Google"]["wrap_max"]
        replacements = self.config["Google"]["replacements"]
        replace_compiled = {"start": [], "any": [], "ends": []}
        for replacement in replacements:
            find_type, orig, replaced = replacement
            if find_type not in replace_compiled:
                raise Exception(f"{find_type} does not exist. [start, any, ends]")
            replace_compiled[find_type].append((orig,replaced))
        
        # max_event_lines = self.config["Google"]["max_event_lines"]

        for ev_idx, event_section in events.items():
            unpacked_list_events = self.unpack_list_like(event_section)
            translated_data = []
            pbar = tqdm.tqdm(total=len(unpacked_list_events), desc=f"ev_idx: {ev_idx}")
            for idx, event_data in enumerate(unpacked_list_events):
                if not self.jp_rgx.search(event_data["txt"]):
                    translated_data.append(event_data)
                    pbar.update(1)
                    continue
                if event_data["typ"] == "choice":
                    event_data["txt"] = self.collapse_chars(event_data["txt"])
                    translated = self.google_instance.translate(
                        event_data["txt"], "English", source_language="Japanese"
                    ).result
                    orig_count = len(event_data["txt"].split("\n"))
                    event_data["txt"] = translated.strip()
                    nw_lines = event_data["txt"].split("\n")
                    if len(nw_lines) < orig_count:
                        # print("[Pad due to text]: ", orig_count, event_data["txt"], )
                        event_data["txt"] += "\n" * (orig_count - len(nw_lines))
                    # unpacked_list_events[idx] = event_data
                    translated_data.append(event_data)
                    pbar.update(1)
                else:
                    event_data["txt"] = self.collapse_chars(event_data["txt"])
                    event_data["txt"] = self.text_replace(event_data["txt"], replace_compiled)
                    orig_lines = event_data["txt"].split("\n")
                    rewrap = False
                    name_detect = False
                    if punctuations and len(orig_lines) > 2:
                        concat_lines = orig_lines[0]
                        if len(concat_lines) <= name_collapse:
                            name_detect = True
                            concat_lines += "\n"
                        # concat_lines += "\n"
                        for line in orig_lines[1:]:
                            if not line:
                                concat_lines += line + "\n"
                                continue
                            if line[-1] in punctuations:
                                concat_lines += line + "\n"
                            else:
                                concat_lines += line
                        concat_lines = concat_lines.rstrip()
                        rewrap = True
                    else:
                        # Keep it as is.
                        concat_lines = "\n".join(orig_lines)
                    translated = self.google_instance.translate(
                        concat_lines, "English", source_language="Japanese"
                    ).result

                    # Repad and rewrap tests.
                    orig_count = len(event_data["txt"].split("\n"))
                    if "aaaaaaaaaaaaaaaaaaaaaaaa" in translated.strip():
                        print([translated.strip(), concat_lines])
                    event_data["txt"] = translated.strip()
                    nw_lines = event_data["txt"].split("\n")
                    
                    # Number of lines shorter than original.
                    if len(nw_lines) < orig_count:
                        # Probably a rewrap, test to confirm
                        # if it's an actual rewrap and
                        # we have the space for it.
                        if rewrap and orig_count - 2 > 0:
                            wrapping_lines = orig_count
                            wrapped_text = event_data["txt"].split("\n")
                            # Check if there is a name detected.
                            # If so, deduct 1 count from lines to wrap.
                            top = ""
                            if name_detect:
                                # 1 lines reserved
                                wrapping_lines -= 1
                                top = wrapped_text[0]
                                wrapped_text = wrapped_text[1:]

                            # Concat and count how much chars we need to wrap
                            wrapped_text = " ".join(wrapped_text)
                            wrapped_chars = math.floor(len(wrapped_text) / wrapping_lines)
                            if wrapped_chars <= wrap_max:
                                # print(wrapped_chars, wrapping_lines, wrapped_text, wrap_max, "padcheck")
                                # Line is too short and we don't need to rewrap, just pad it.
                                event_data["txt"] += "\n" * (orig_count - len(nw_lines))
                            else:
                                if name_detect:
                                    # TODO: Fix this hack.
                                    temp_wrapped_text = textwrap.wrap(wrapped_text, width=wrapped_chars)
                                    while len(temp_wrapped_text) > wrapping_lines:
                                        wrapped_chars += 5
                                        temp_wrapped_text = textwrap.wrap(wrapped_text, width=wrapped_chars)
                                    # Do wrapping for Name + Text
                                    event_data["txt"] = (
                                        top
                                        + "\n"
                                        + "\n".join(temp_wrapped_text)
                                    )
                                else:
                                    # do wrapping for Text [No name.]
                                    # TODO: Fix this hack.
                                    temp_wrapped_text = textwrap.wrap(wrapped_text, width=wrapped_chars)
                                    while len(temp_wrapped_text) > wrapping_lines:
                                        wrapped_chars += 5
                                        temp_wrapped_text = textwrap.wrap(wrapped_text, width=wrapped_chars)
                                    event_data["txt"] = "\n".join(temp_wrapped_text)
                            if len(event_data["txt"].split("\n")) != orig_count:
                                print(orig_count, name_detect, wrapped_chars)
                                print(orig_count, event_data["txt"].split("\n"))
                                raise Exception()
                        else:
                            #
                            event_data["txt"] += "\n" * (orig_count - len(nw_lines))
                        # print("[Pad due to text]: ", orig_count, len(nw_lines))
                    translated_data.append(event_data)
                    pbar.update(1)
            # print(event_section)
            events[ev_idx] = self.pack_translated(translated_data)
        return events

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
            if not export.exists():
                continue
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
                self.write_nested(self.translate_events(data), export)
            elif events and export_name.startswith("map"):
                data = self.read_nested(export)
                if not isinstance(data, dict):
                    return
                self.write_nested(self.translate_events(data), export)
