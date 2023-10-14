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
import nestedtext
from DataFumblerCommons import terms_patch
import logging

logger = logging.getLogger("DF|MVZ")

class MVZFungler:
    def __init__(self, file: pathlib.Path, config: dict) -> None:
        """Base class that implements MV Related classes

        Args:
            file (pathlib.Path): Input file
            config (dict): Configuration for the project
        """
        self.file: pathlib.Path = file
        self.config = config
        self.game_type = self.config["General"].get("type", "MV")

    def apply_maps(self, map_file: pathlib.Path):
        raise NotImplementedError()

    def create_maps(self, export_file: pathlib.Path):
        raise NotImplementedError()

    def export_map(self, map_file: pathlib.Path):
        raise NotImplementedError()

    def import_map(self, translated_file: pathlib.Path, inter_json:pathlib.Path):
        raise NotImplementedError()

    def parse_page_lists(self, page_list_data: list):
        """Processes MV/MZ Pages found in maps.json and CommonEvents.json

        Args:
            page_list_data (list): A list of pages

        Returns:
            _type_: _description_
        """
        page_list_events = []
        t_pages = len(page_list_data)

        def process_code101(base_i):
            pointer = base_i + 1
            nx_event = page_list_data[pointer]
            if self.game_type == "MZ":
                # MZ has an additional param to code 101, which stores the character name.
                params101 = page_list_data[base_i]["parameters"]
                if len(params101) == 5:
                    chara_name = params101[4]
                    text_data = {
                        "type": "text",
                        "text": [
                            chara_name,
                        ],
                        "pointer": [base_i],
                        "meta": "101code",
                    }
                else:
                    text_data = {"type": "text", "text": [], "pointer": [], "meta": ""}
            else:
                text_data = {"type": "text", "text": [], "pointer": [], "meta": ""}
            nx_code = nx_event["code"]
            while nx_code == 401:
                text_data["text"].append(nx_event["parameters"][0])
                text_data["pointer"].append(pointer)
                # text_data.append([pointer, ])
                pointer += 1
                nx_event = page_list_data[pointer]
                nx_code = nx_event["code"]
            page_list_events.append(text_data)

        def process_code102(base_i):
            link_words = page_data["parameters"][0]
            text_data = {"type": "text_choice", "text": [], "pointer": []}
            if self.game_type == "MZ":
                bse_event = page_list_data[base_i]
                text_data["text"] = bse_event["parameters"]
                text_data["pointer"] = base_i
                page_list_events.append(text_data)
                return
                # MZ appears to no need processing for 102 codes...
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
            elif page_data["code"] == 102:
                process_code102(t_idx)
        return page_list_events


class SystemMVfungler(MVZFungler):
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
                    logger.info(f'[SystemCommon|Basic] Found common term for: {mapping["terms"]["basic"][k]}')
                    mapping["terms"]["basic"][k] = terms[v]
            terms = terms_patch["commands"]
            for k, v in enumerate(mapping["terms"]["commands"]):
                if v in terms:
                    logger.info(f'[SystemCommon|Commands] Found common term for: {mapping["terms"]["commands"][k]}')
                    mapping["terms"]["commands"][k] = terms[v]
            terms = terms_patch["params"]
            for k, v in enumerate(mapping["terms"]["params"]):
                if v in terms:
                    logger.info(f'[SystemCommon|Params] Found common term for: {mapping["terms"]["params"][k]}')
                    mapping["terms"]["params"][k] = terms[v]
            terms = terms_patch["messages"]
            for k, v in mapping["terms"]["messages"].items():
                if v == terms.get(k, ["", ""])[0]:
                    logger.info(f'[SystemCommon|Messages] Found common term for: {mapping["terms"]["messages"][k]}')
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


class ActorMVFungler(MVZFungler):
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

    def export_map(self, map_file: pathlib.Path):
        mapping = orjson.loads(map_file.read_bytes())
        # return super().exports_maps(map_file)
        if mapping.get("type", "") != "actors":
            print(
                f"[ERR] Failed exporting, {map_file.name} does not match required type."
            )
            return
        return nestedtext.dumps(mapping["actors"])


class ItemMVFungler(MVZFungler):
    def create_maps(self, export_file: pathlib.Path):
        mapping = {"type": "items", "item": {}}
        weapons_data = orjson.loads(self.file.read_bytes())
        for weapon in weapons_data:
            if not weapon or not weapon["name"]:
                continue
            mapping["item"][str(weapon["id"])] = {
                "name": weapon["name"],
                "desc": weapon["description"],
                "note": weapon["note"],
            }
        if mapping["item"]:
            export_file.write_bytes(orjson.dumps(mapping, option=orjson.OPT_INDENT_2))
        else:
            print("No Exportable Items:", self.file.name)

    def apply_maps(self, map_file: pathlib.Path):
        mapping = orjson.loads(map_file.read_text(encoding="utf-8"))
        weapons = orjson.loads(self.file.read_text(encoding="utf-8"))
        if mapping.get("type", "") not in ["weapons", "items"]:
            print(
                f"[ERR] Failed applying, {map_file.name} does not match required type."
            )
            return
        for weapon_idx_s, trans_data in mapping["item"].items():
            weapon_idx = int(weapon_idx_s)
            weapons[weapon_idx]["name"] = trans_data["name"]
            weapons[weapon_idx]["description"] = trans_data["desc"]
            weapons[weapon_idx]["note"] = trans_data["note"]
        return weapons

    def import_map(self, translated_item: pathlib.Path):
        try:
            rr = nestedtext.loads(translated_item.read_bytes().decode("utf-8"))
        except nestedtext.NestedTextError as e:
            raise e
        return rr

    def export_map(self, map_file: pathlib.Path):
        mapping = orjson.loads(map_file.read_bytes())
        # return super().exports_maps(map_file)
        if mapping.get("type", "") != "items":
            print(
                f"[ERR] Failed exporting, {map_file.name} does not match required type."
            )
            return
        export_item = {i["name"]: i["desc"] for i in mapping["item"].values()}
        return nestedtext.dumps(export_item)


class CommonEventMVFungler(MVZFungler):
    def __init__(self, file: pathlib.Path, config: dict) -> None:
        super().__init__(file, config)

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
                        if txt_idx == 0 and "101code" in text_data["meta"]:
                            txt_event = old_map[int(idx)]["list"][ptr]
                            txt_event["parameters"][4] = text_data["text"][txt_idx]
                        else:
                            txt_event = old_map[int(idx)]["list"][ptr]
                            txt_event["parameters"][0] = text_data["text"][txt_idx]
                            old_map[int(idx)]["list"][ptr] = txt_event
                elif text_data["type"] == "text_choice":
                    # Note for MZ that this for loop should not execute since the list is empty.
                    for txt_idx, ptr in enumerate(text_data["pointer"][1:]):
                        txt_event = old_map[int(idx)]["list"][ptr]
                        txt_event["parameters"][1] = text_data["text"][txt_idx]
                        old_map[int(idx)]["list"][ptr] = txt_event
                    zero_ptr = text_data["pointer"][0]
                    txt_event = old_map[int(idx)]["list"][zero_ptr]
                    txt_event["parameters"][0] = text_data["text"]
                    old_map[int(idx)]["list"][zero_ptr] = txt_event
        return old_map


class MapsMVFungler(MVZFungler):
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
                            if txt_idx == 0 and "101code" in trans["meta"]:
                                text_event = old_events[evnt_id]["pages"][
                                    page_code_idx
                                ]["list"][ptr]
                                text_event["parameters"][4] = trans["text"][txt_idx]
                                old_events[evnt_id]["pages"][page_code_idx]["list"][
                                    ptr
                                ] = text_event
                            else:
                                text_event = old_events[evnt_id]["pages"][
                                    page_code_idx
                                ]["list"][ptr]
                                text_event["parameters"][0] = trans["text"][txt_idx]
                                old_events[evnt_id]["pages"][page_code_idx]["list"][
                                    ptr
                                ] = text_event
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

    def export_map(self, map_file: pathlib.Path):
        mapping = orjson.loads(map_file.read_bytes())
        # return super().exports_maps(map_file)
        if mapping.get("type", "") != "map":
            print(
                f"[ERR] Failed exporting, {map_file.name} does not match required type."
            )
            return
        # for evidx, event in mapping['events'].items():
        #     for pgidx, page in event.items():
        #         zz2 = []
        #         for text_data in page:
        #             if text_data["type"] == "text":
        #                 compo = text_data["text"]
        #                 for idx, i in enumerate(compo):
        #                     if not i.strip():
        #                         compo[idx] = "<Empty String>"
        #                 zz = "\n"+"\n".join(compo)
        #                 zz = f"\n{zz}"
        #             elif text_data["type"] == "text_choice":
        #                 compo = text_data["text"]
        #                 for idx, i in enumerate(compo):
        #                     if not i.strip():
        #                         compo[idx] = "<Empty String>"
        #                 zz = "\n".join(compo)
        #                 zz = f"\nChoices:\n{zz}"
        #             else:
        #                 raise Exception("???")
        #             zz2.append(zz)
        #         export.append(f"### {evidx}-{pgidx}\n\n" + "\n".join(zz2))
        # export_item = [[i["name"], i['desc']] for i in mapping['items'].values()]
        z = {}
        for evidx, event in mapping["events"].items():
            events = []
            for pgidx, page in event.items():
                for text_data in page:
                    events.extend(text_data["text"])
                    events.append("<>")
            z[evidx] = events
        return nestedtext.dumps(z)
    
    def import_map(self, translated_file: pathlib.Path, inter_json:pathlib.Path):
        try:
            map_data = nestedtext.loads(translated_file.read_text("utf-8"))
        except nestedtext.NestedTextError as e:
            logger.error("Unable to import MapsMVFungler NestedText. {e}")
            return 
        # We assume it is a map file.
        if not isinstance(map_data, dict):
            logger.error("Unable to use MapsMVFungler NestedText. Expecting dictionary.")
            return
        mapping = orjson.loads(inter_json.read_bytes())
        if mapping.get("type", "") != "map":
            print(
                f"[ERR] Failed exporting, {inter_json.name} does not match required type."
            )
            return
        for event_idx, lines in map_data.items():
            reconstruct_events = []
            event_data = []
            for line in lines:
                if line == "<>":
                    reconstruct_events.append(event_data)
                    event_data = []
                else:
                    event_data.append(line)
                
        for evidx, event in mapping["events"].items():
            events = []
            for pgidx, page in event.items():
                for text_data in page:
                    pass
                    
                


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
        if len(content) < 2:
            return None
        item = content[1]
        actor_tests = ["characterIndex", "characterName", "name", "note", "profile"]
        weapon_tests = ["description", "name", "note"]
        # event_tests = ["characterIndex", "characterName", "name", "note", "profile"]
        if sum([act_test in actor_tests for act_test in item]) == len(actor_tests):
            return ActorMVFungler(file_url, config)
        if (
            sum([weapon_test in weapon_tests for weapon_test in item])
            == len(weapon_tests)
            and "weapon" in file_url.name.lower()
        ):
            return ItemMVFungler(file_url, config)
        if (
            sum([weapon_test in weapon_tests for weapon_test in item])
            == len(weapon_tests)
            and "item" in file_url.name.lower()
        ):
            return ItemMVFungler(file_url, config)
        if (
            sum([weapon_test in weapon_tests for weapon_test in item])
            == len(weapon_tests)
            and "armors" in file_url.name.lower()
        ):
            return ItemMVFungler(file_url, config)
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
