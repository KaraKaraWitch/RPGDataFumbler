import logging
import pathlib
import typing

import orjson


class MVZFungler:
    def __init__(self, file: pathlib.Path, config: dict) -> None:
        """Base class that implements MV Related classes

        Args:
            file (pathlib.Path): The Input file from the game.
            config (dict): Configuration for the project
        """
        self.file: pathlib.Path = file
        self.config = config
        self.game_type = self.config["General"].get("type", "MV")
        self.logger = logging.getLogger("DF|MVZ")

    def type_check(self, map_file:pathlib.Path, mapping:dict, type:str):
        if mapping.get("type", "") != type:
            print(
                f"[ERR] Failed applying, {map_file.name} does not match required type."
            )
            return False
        return True
    
    def load_raw(self, init_dict:dict, init_type:str):
        """Loads and initalizes a dictionary from the raw file and mapping data...

        Args:
            init_dict (dict): Inital Dict
            init_type (str): The type for the said class.

        Returns:
            _type_: _description_
        """
        mapping: typing.Dict[str, typing.Any] = {"type": init_type, **init_dict}
        raw_data = orjson.loads(self.file.read_text(encoding="utf-8"))
        return mapping, raw_data

    def apply_maps(self, map_file: pathlib.Path):
        raise NotImplementedError()

    def create_maps(self, export_file: pathlib.Path):
        raise NotImplementedError()

    def export_map(self, map_file: pathlib.Path):
        raise NotImplementedError()

    def import_map(self, translated_file: pathlib.Path, inter_json: pathlib.Path):
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
                text_data["text"] = bse_event["parameters"][0]
                text_data["pointer"] = base_i
                page_list_events.append(text_data)
            else:
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