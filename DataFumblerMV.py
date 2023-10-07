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

    def export_maps(self, map_file: pathlib.Path):
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
                if v == terms.get(k, ["", ""])[0]:
                    print(f"[SystemCommon|Messages] Found common term for: {k}")
                    mapping["terms"]["messages"][k] = terms.get(k, ["", ""])[1]
        mapping["game_title"] = system_data["gameTitle"]
        export_file.write_bytes(orjson.dumps(mapping, option=orjson.OPT_INDENT_2))

    def apply_maps(self, map_file: pathlib.Path):
        mapping = orjson.loads(map_file.read_text(encoding="utf-8"))
        system_data = orjson.loads(self.file.read_text(encoding="utf-8"))

        if mapping.get("type", "") != "system":
            print(
                f"[ERR] Failed applying, {map_file.name} does not match required type."
            )
            return

        if self.config["System"]["armor_types"]:
            for idx, value in mapping["armor_types"]:
                system_data["armorTypes"][idx] = value
        if self.config["System"]["equip_types"]:
            for idx, value in mapping["equip_types"]:
                system_data["equipTypes"][idx] = value
        if self.config["System"]["skill_types"]:
            for idx, value in mapping["skill_types"]:
                system_data["skillTypes"][idx] = value
        if self.config["System"]["terms"]:
            system_data["terms"] = mapping["terms"]
        system_data["gameTitle"] = mapping["game_title"]
        return system_data


class ActorMVFungler(MVFungler):
    def apply_maps(self, map_file: pathlib.Path):
        mapping = orjson.loads(map_file.read_text(encoding="utf-8"))
        actors = orjson.loads(self.file.read_text(encoding="utf-8"))

        if mapping.get("type", "") != "actors":
            print(
                f"[ERR] Failed applying, {map_file.name} does not match required type."
            )
            return

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
    
    def apply_maps(self, map_file: pathlib.Path):
        mapping = orjson.loads(map_file.read_text(encoding="utf-8"))
        weapons = orjson.loads(self.file.read_text(encoding="utf-8"))
        if mapping.get("type", "") != "weapons":
            print(
                f"[ERR] Failed applying, {map_file.name} does not match required type."
            )
            return
        for weapon_idx_s,trans_data in mapping["weapon"].items():
            weapon_idx = int(weapon_idx_s)
            weapons[weapon_idx]["name"] = trans_data["name"]
            weapons[weapon_idx]["description"] = trans_data["desc"]
            weapons[weapon_idx]["note"] = trans_data["note"]
        return weapons


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


    def apply_maps(self, map_file: pathlib.Path):
        old_map = orjson.loads(self.file.read_bytes())
        mapping = orjson.loads(map_file.read_bytes())
        if mapping.get("type", "") != "common_event":
            print(
                f"[ERR] Failed applying, {map_file.name} does not match required type."
            )
            return
        for idx, map_event in mapping["events"].items():
            for text_data in map_event:
                if text_data["type"] == "text":
                    for txt_idx, ptr in enumerate(text_data["pointer"]):
                        txt_event = old_map[int(idx)]["list"][ptr]
                        txt_event["parameters"][0] = text_data["text"][txt_idx]
                        old_map[int(idx)]["list"][ptr] = txt_event
                elif text_data["type"] == "text_choice":
                    for txt_idx, ptr in enumerate(text_data["pointer"][1:]):
                        txt_event = old_map[int(idx)]["list"][ptr]
                        txt_event["parameters"][0] = text_data["text"][txt_idx]
                        old_map[int(idx)]["list"][ptr] = txt_event
                    zero_ptr = text_data["pointer"][0]
                    txt_event = old_map[int(idx)]["list"][zero_ptr]
                    txt_event["parameters"][0] = text_data["text"]
                    old_map[int(idx)]["list"][zero_ptr] = txt_event
        return old_map
                    
                

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
        old_map = orjson.loads(self.file.read_bytes())
        mapping = orjson.loads(map_file.read_bytes())
        if mapping.get("type", "") != "map":
            print(
                f"[ERR] Failed applying, {map_file.name} does not match required type."
            )
            return
        old_events = old_map["events"]
        for evnt_id, page_maps in mapping["events"].items():
            evnt_id = int(evnt_id)

            event_data = old_events[evnt_id]

            for page_code_idx, page in page_maps.items():
                page_code_idx = int(page_code_idx)
                for trans in page:
                    if trans["type"] == "text":
                        # print(page, page_code_idx, old_events[evnt_id]['pages'])
                        #
                        # print([page_code_idx])
                        for txt_idx, ptr in enumerate(trans["pointer"]):
                            # print(old_events[evnt_id]['pages'][page_code_idx])
                            text_event = old_events[evnt_id]["pages"][page_code_idx][
                                "list"
                            ][ptr]
                            text_event["parameters"][0] = trans["text"][txt_idx]
                            old_events[evnt_id]["pages"][page_code_idx]["list"][
                                ptr
                            ] = text_event
                            # print()
                            pass
                            # event_data[]
                            # events[page_idx][ptr][1] = trans[txt_idx]
                    elif trans["type"] == "text_choice":
                        # For Code 402
                        for txt_idx, ptr in enumerate(trans["pointer"][1:]):
                            text_event = old_events[evnt_id]["pages"][page_code_idx][
                                "list"
                            ][ptr]
                            text_event["parameters"][1] = trans["text"][txt_idx]
                            old_events[evnt_id]["pages"][page_code_idx]["list"][
                                ptr
                            ] = text_event
                            # print(events[page_idx], ptr, trans[txt_idx])
                        # Write back to code 102
                        text_event = old_events[evnt_id]["pages"][page_code_idx][
                            "list"
                        ][trans["pointer"][0]]
                        text_event["parameters"][0] = trans["text"]
                        old_events[evnt_id]["pages"][page_code_idx]["list"][
                            trans["pointer"][0]
                        ] = text_event
            old_events[evnt_id] = event_data
        old_map["events"] = old_events
        return old_map

        # return super().apply_maps(map_file)

    def export_maps(self, map_file: pathlib.Path):
        mapping = orjson.loads(map_file.read_bytes())
        # return super().exports_maps(map_file)
        if mapping.get("type", "") != "map":
            print(
                f"[ERR] Failed exporting, {map_file.name} does not match required type."
            )
            return
        export = []
        for evidx, event in mapping['events'].items():
            for pgidx, page in event.items():
                zz2 = []
                for text_data in page:
                    if text_data["type"] == "text":
                        compo = text_data["text"]
                        for idx, i in enumerate(compo):
                            if not i.strip():
                                compo[idx] = "<Empty String>"
                        zz = "\n"+"\n".join(compo)
                        zz = f"\n{zz}"
                    elif text_data["type"] == "text_choice":
                        compo = text_data["text"]
                        for idx, i in enumerate(compo):
                            if not i.strip():
                                compo[idx] = "<Empty String>"
                        zz = "\n".join(compo)
                        zz = f"\nChoices:\n{zz}"
                    else:
                        raise Exception("???")
                    zz2.append(zz)
                export.append(f"### {evidx}-{pgidx}\n\n" + "\n".join(zz2))
        return "\n\n".join(export)
                

    def create_maps(self, export_file: pathlib.Path):
        mapping = {"type": "map", "events": {}}
        events_data = orjson.loads(self.file.read_bytes())
        # events = []

        for evidx, event in enumerate(
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
                mapping["events"][str(evidx)] = pages
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
