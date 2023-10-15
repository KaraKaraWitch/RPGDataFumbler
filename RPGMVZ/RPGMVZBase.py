import logging
import pathlib
import typing

import orjson


class MVZFungler:
    def __init__(
        self,
        original_file: pathlib.Path,
        mapped_file: pathlib.Path,
        export_file: pathlib.Path,
        config: dict,
    ) -> None:
        """Base class that implements MV Related classes.

        You will need to extend the following classes:

        - create_maps (Creates/Extracts the mapping from the game)
        - apply_maps (Applies the mapping back to base game)


        The following are optional but recommended.

        - export_map
        - import_map

        Args:
            original_file (pathlib.Path): The Input file from the game.
            mapped_file (pathlib.Path): _description_
            export_file (pathlib.Path): _description_
            config (dict): Configuration for the project
        """
        self.original_file: pathlib.Path = original_file
        self.mapped_file: pathlib.Path = mapped_file
        self.export_file: pathlib.Path = export_file
        self.config = config
        self.game_type = self.config["General"].get("type", "MV")
        self.logger = logging.getLogger("DF|MVZ")
        self._cached_orig_data = None

    fungler_type = None

    def apply_maps(self) -> bool:
        raise NotImplementedError()

    def export_map(self) -> bool:
        """Exports the map fil

        Args:
            map_file (pathlib.Path): _description_

        Raises:
            NotImplementedError: _description_

        Returns:
            typing.Union[list, dict]: _description_
        """
        raise NotImplementedError()

    def create_maps(self) -> bool:
        """Creates the mapping file and writes it the

        Raises:
            NotImplementedError: _description_

        Returns:
            bool: _description_
        """
        raise NotImplementedError()

    def import_map(self) -> bool:
        """Imports the data from "exported" file.

        Raises:
            NotImplementedError: _description_

        Returns:
            bool: _description_
        """
        raise NotImplementedError()

    def type_check(self, map_file: pathlib.Path, mapping: dict, type: str):
        if mapping.get("type", "") != type:
            print(
                f"[ERR] Failed applying, {map_file.name} does not match required type."
            )
            return False
        return True

    def read_mapped(
        self, create: bool = False
    ) -> typing.Union[None, typing.Dict[str, typing.Any]]:
        """Reads the mapped file into a dictionary.

        Additionally, it does a simple type check (That can be spoofed).

        Args:
            type (str): The "type" to check against.
            create (bool, optional): _description_. Defaults to False.

        Returns:
            _type_: _description_
        """
        if self.fungler_type is None:
            raise Exception(f"fungler_type is missing an inheritence.")
        # self.logger.info(self.mapped_file)
        if self.mapped_file.exists():
            mapping = orjson.loads(self.mapped_file.read_bytes())
            if self.type_check(self.mapped_file, mapping, self.fungler_type):

                return mapping
            else:
                self.logger.error("Type Check failed")
                return None
        else:
            if create:
                return {"type": self.fungler_type}

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

    @property
    def original_data(
        self,
    ) -> typing.Union[typing.Dict[str, typing.Any], typing.List[typing.Any]]:
        if not self._cached_orig_data:
            self._cached_orig_data = orjson.loads(self.original_file.read_bytes())
        return self._cached_orig_data
