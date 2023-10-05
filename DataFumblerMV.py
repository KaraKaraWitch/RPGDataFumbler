# =================================================== #
# DataFumbler: RPGMakerMV localization python scripts
# Built for Gehenna but works for MV related games.
# =================================================== #
# Code relating the the MV/MZ variants of the game engine.
# =================================================== #

import pathlib
import typing
import tqdm

import orjson
from DataFumblerCommons import terms_patch


class MVFungler:
    def __init__(self, file: pathlib.Path, config: dict) -> None:
        """Base class that implements MV Related classes

        Args:
            file (pathlib.Path): Input file
            config (dict): Configuration for the project
        """
        self.file: pathlib.Path = file
        self.config = config

    def apply_maps(self, map_file: pathlib.Path):
        raise NotImplementedError()

    def create_maps(self, export_file: pathlib.Path):
        raise NotImplementedError()


class SystemMVfungler(MVFungler):
    def create_maps(self, export_file: pathlib.Path):
        mapping: typing.Dict[str, typing.Any] = {"type": "system"}
        system_data = orjson.loads(self.file.read_text(encoding="utf-8"))
        if self.config["System"]["armor_types"]:
            mapping["armor_types"] = []
            for idx, armor in enumerate(system_data["armorTypes"]):
                if armor:
                    mapping["armor_types"].append([idx, armor])
        if self.config["System"]["equip_types"]:
            mapping["equip_types"] = []
            for idx, equip in enumerate(system_data["equipTypes"]):
                if equip:
                    mapping["equip_types"].append([idx, equip])
        if self.config["System"]["skill_types"]:
            mapping["skill_types"] = []
            for idx, skill in enumerate(system_data["skillTypes"]):
                if skill:
                    mapping["skill_types"].append([idx, skill])
        if self.config["System"]["terms"]:
            mapping["terms"] = system_data["terms"]
            terms = terms_patch["basic"]
            for k, v in enumerate(mapping["terms"]["basic"]):
                if v in terms:
                    print(f"[SystemCommon|Basic] Found common term for: {k}")
                    mapping["terms"]["basic"][k] = terms[v]
            terms = terms_patch["commands"]
            for k, v in enumerate(mapping["terms"]["commands"]):
                if v in terms:
                    print(f"[SystemCommon|Commands] Found common term for: {k}")
                    mapping["terms"]["commands"][k] = terms[v]
            terms = terms_patch["params"]
            for k, v in enumerate(mapping["terms"]["params"]):
                if v in terms:
                    print(f"[SystemCommon|Params] Found common term for: {k}")
                    mapping["terms"]["params"][k] = terms[v]
            terms = terms_patch["messages"]
            for k, v in mapping["terms"]["messages"].items():
                if v == terms.get(k,["",""])[0]:
                    print(f"[SystemCommon|Messages] Found common term for: {k}")
                    mapping["terms"]["messages"][k] = terms.get(k,["",""])[1]
        # 
        export_file.write_bytes(orjson.dumps(mapping, option=orjson.OPT_INDENT_2))


class ActorMVFungler(MVFungler):
    def apply_maps(self, map_file: pathlib.Path):
        mapping = orjson.loads(map_file.read_text(encoding="utf-8"))
        actors = orjson.loads(self.file.read_text(encoding="utf-8"))

        export_actors = []
        for actor in actors:

            if not actor:
                export_actors.append(actor)
                continue
            if not actor["name"]:
                export_actors.append(actor)
                continue
            # print(actor, mapping["actors"])
            actor_data = mapping["actors"].get(str(actor["id"]), {})
            if not actor_data:
                export_actors.append(actor)
                continue
            actor["name"] = actor_data["name"]
            actor["note"] = actor_data["note"]
            actor["nickname"] = actor_data["nickname"]
            actor["profile"] = actor_data["profile"]
            export_actors.append(actor)
        return export_actors

    def create_maps(self, export_file: pathlib.Path):
        mapping = {"type": "actors", "actors": {}}
        actors = orjson.loads(self.file.read_text(encoding="utf-8"))
        for actor in actors:
            if not actor:
                continue
            if not actor["name"]:
                continue
            mapping["actors"][str(actor["id"])] = {
                "name": actor["name"],
                "note": actor["note"],
                "nickname": actor["nickname"],
                "profile": actor["profile"],
            }

        export_file.write_bytes(orjson.dumps(mapping, option=orjson.OPT_INDENT_2))


class WeaponsMVFungler(MVFungler):
    def create_maps(self, export_file: pathlib.Path):
        mapping = {"type": "weapons", "weapon": {}}
        weapons_data = orjson.loads(self.file.read_bytes())
        for weapon in weapons_data:
            if not weapon or not weapon["name"]:
                continue
            mapping["weapon"][str(weapon["id"])] = {
                "name": weapon["name"],
                "desc": weapon["description"],
                "note": weapon["note"],
            }
        if mapping["weapon"]:
            export_file.write_bytes(orjson.dumps(mapping, option=orjson.OPT_INDENT_2))
        else:
            print("No Exportable Weapons:", self.file.name)

class CommonEventMVFungler(MVFungler):

    def parse_page_lists(self, page_list_data: list):
        page_list_events = []
        t_pages = len(page_list_data)

        def process_code101(base_i):
            pointer = base_i + 1
            nx_event = page_list_data[pointer]
            nx_code = nx_event["code"]
            text_data = {"type": "text", "text": [], "pointer": []}
            while nx_code == 401:
                text_data["text"].append(nx_event["parameters"][0])
                text_data["pointer"].append(pointer)
                # text_data.append([pointer, ])
                pointer += 1
                nx_event = page_list_data[pointer]
                nx_code = nx_event["code"]
            unwarp_start_line = self.config.get("unwrap_text", None)
            to_unwrap = text_data["text"][unwarp_start_line:]
            page_list_events.append(text_data)

        def process_code402(base_i):
            link_words = page_data["parameters"][0]
            text_data = {"type": "text_choice", "text": [], "pointer": []}
            pointer = base_i + 1
            nx_event = page_list_data[pointer]
            nx_code = nx_event["code"]
            text_data["pointer"].append(base_i)
            while len(link_words) > 0 and pointer < t_pages:
                if nx_code == 402:
                    text_data["text"].append(nx_event["parameters"][1])
                    text_data["pointer"].append(pointer)
                    link_words.pop(0)
                pointer += 1
                if pointer > t_pages:
                    break
                nx_event = page_list_data[pointer]
                nx_code = nx_event["code"]
            page_list_events.append(text_data)

        for t_idx in range(t_pages):
            page_data = page_list_data[t_idx]
            if page_data["code"] == 101:
                process_code101(t_idx)

                continue
            elif page_data["code"] == 102:
                process_code402(t_idx)
        return page_list_events

    def create_maps(self, export_file: pathlib.Path):
        mapping = {"type": "common_event", "events": {}}
        events_list = orjson.loads(self.file.read_bytes())
        # events = []
        pbar = tqdm.tqdm()
        print("Parsing Common event page. Have some patience...")
        for idx, event in enumerate(
            events_list,
        ):
            if not event:
                pbar.update(1)
                continue
            # pages = []
            page_list_data = event.get("list", [])
            if not page_list_data:
                continue
            if page_list_data[0]["code"] == 0:
                continue
            page_list_events = self.parse_page_lists(page_list_data)
            pbar.update(1)
            if page_list_events:
                mapping["events"][str(idx)] = page_list_events
        if mapping["events"]:
            export_file.write_bytes(orjson.dumps(mapping, option=orjson.OPT_INDENT_2))
        pbar.close()
            

class MapsMVFungler(MVFungler):
    def parse_page_lists(self, page_list_data: list):
        page_list_events = []
        t_pages = len(page_list_data)

        def process_code101(base_i):
            pointer = base_i + 1
            nx_event = page_list_data[pointer]
            nx_code = nx_event["code"]
            text_data = {"type": "text", "text": [], "pointer": []}
            while nx_code == 401:
                text_data["text"].append(nx_event["parameters"][0])
                text_data["pointer"].append(pointer)
                # text_data.append([pointer, ])
                pointer += 1
                nx_event = page_list_data[pointer]
                nx_code = nx_event["code"]
            unwarp_start_line = self.config.get("unwrap_text", None)
            to_unwrap = text_data["text"][unwarp_start_line:]
            page_list_events.append(text_data)

        def process_code402(base_i):
            link_words = page_data["parameters"][0]
            text_data = {"type": "text_choice", "text": [], "pointer": []}
            pointer = base_i + 1
            nx_event = page_list_data[pointer]
            nx_code = nx_event["code"]
            text_data["pointer"].append(base_i)
            while len(link_words) > 0 and pointer < t_pages:
                if nx_code == 402:
                    text_data["text"].append(nx_event["parameters"][1])
                    text_data["pointer"].append(pointer)
                    link_words.pop(0)
                pointer += 1
                if pointer > t_pages:
                    break
                nx_event = page_list_data[pointer]
                nx_code = nx_event["code"]
            page_list_events.append(text_data)

        for t_idx in range(t_pages):
            page_data = page_list_data[t_idx]
            if page_data["code"] == 101:
                process_code101(t_idx)

                continue
            elif page_data["code"] == 102:
                process_code402(t_idx)
        return page_list_events

    def apply_maps(self, map_file: pathlib.Path):
        old_events = orjson.loads(self.file.read_bytes())
        mapping = orjson.loads(map_file.read_bytes())
        if mapping.get("type","") != "map":
            print(f"[ERR] Failed applying, {map_file.name} does not match required type.")
            return
        for k,v in mapping["events"].items():
            k = int(k)
            events = old_events[k]
            for idx, page in v.items():
                page_idx = int(idx)
                for trans in page:
                    for txt_idx, ptr in trans["pointer"]:
                        events[page_idx][ptr][1] = trans[txt_idx]
            old_events[k] = events
        return old_events


        # return super().apply_maps(map_file)

    def create_maps(self, export_file: pathlib.Path):
        mapping = {"type": "map", "events": {}}
        events_data = orjson.loads(self.file.read_bytes())
        # events = []

        for idx, event in enumerate(
            events_data.get("events", []),
        ):
            if not event:
                continue
            pages = {}
            for idx, page in enumerate(event.get("pages", [])):
                page_list_data = page.get("list", [])
                if not page_list_data:
                    continue
                if page_list_data[0]["code"] == 0:
                    continue
                page_list_events = self.parse_page_lists(page_list_data)
                if page_list_events:
                    pages[str(idx)] = page_list_events

            if pages:
                mapping["events"][str(idx)] = pages
        if mapping["events"]:
            export_file.write_bytes(orjson.dumps(mapping, option=orjson.OPT_INDENT_2))
        else:
            print("No Exportable Events:", self.file.name)


def resolve_file(file_url: pathlib.Path, config: dict):
    content = orjson.loads(file_url.read_bytes())
    # print("[Check]", file_url.name)
    if isinstance(content, list):

        item = content[1]
        actor_tests = ["characterIndex", "characterName", "name", "note", "profile"]
        weapon_tests = ["traits", "iconIndex", "name", "note"]
        # event_tests = ["characterIndex", "characterName", "name", "note", "profile"]
        if sum([act_test in actor_tests for act_test in item]) == len(actor_tests):
            return ActorMVFungler(file_url, config)
        if (
            sum([weapon_test in weapon_tests for weapon_test in item])
            == len(weapon_tests)
            and "weapon" in file_url.name.lower()
        ):
            return WeaponsMVFungler(file_url, config)
        if "commonevents" in file_url.name.lower():
            return CommonEventMVFungler(file_url, config)

        # else:
        #     print()
    elif isinstance(content, dict):
        if "Map" in file_url.name and content.get("events"):
            return MapsMVFungler(file_url, config)
        if content.get("armorTypes"):
            return SystemMVfungler(file_url, config)
    # Events stuff
