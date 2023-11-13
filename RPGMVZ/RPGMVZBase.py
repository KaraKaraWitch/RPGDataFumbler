import logging
import pathlib
import re
import typing
import nestedtext

import orjson

try:
    import pandas
except ImportError:
    pandas = None


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
            mapped_file (pathlib.Path): The mapped file to write to.
            export_file (pathlib.Path): The export file to write to.
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
    jp_rgx = re.compile(r"[一-龠]+|[ぁ-ゔ]+|[ァ-ヴー]+", flags=re.UNICODE)

    def apply_maps(self, patch_file: pathlib.Path) -> bool:
        raise NotImplementedError()

    def create_maps(self) -> bool:
        """Creates the mapping dictionary and writes it to the file specified for mapping.

        Raises:
            NotImplementedError: _description_

        Returns:
            bool: _description_
        """
        raise NotImplementedError()

    def import_map(self, format="nested") -> bool:
        """Imports the data from "exported" file.

        Raises:
            NotImplementedError: _description_

        Returns:
            bool: _description_
        """
        raise NotImplementedError()

    def export_map(self, format="nested") -> bool:
        """Exports the mapped data to a more human readable format.

        Args:
            map_file (pathlib.Path): _description_

        Raises:
            NotImplementedError: _description_

        Returns:
            typing.Union[list, dict]: _description_
        """
        raise NotImplementedError()

    def export_excel(self, values: typing.Dict[str, typing.List[str]]) -> bool:
        """Exports the file to an Excel Sheet

        Args:
            values (typing.Dict[str, typing.List[str]]): A list of values to use

        Raises:
            ImportError: _description_
        """
        if not pandas:
            raise ImportError(
                "export_excel needs `pandas` and `XlsxWriter` to be installed."
            )
        with pandas.ExcelWriter(
            str(self.export_file),
        ) as writer:
            for sheet_name, list_values in values.items():
                formatted = {
                    "Original": list_values,
                    "Inital": [""] * len(list_values),
                    "Edited": [""] * len(list_values),
                    "Final": [""] * len(list_values),
                }

                pandas.DataFrame.from_dict(formatted).to_excel(
                    writer, sheet_name=sheet_name
                )
        return True

    def export_nested(
        self,
        value: typing.Union[
            typing.Dict[typing.Any, typing.Any], typing.List[typing.Any]
        ],
    ) -> bool:
        self.export_file.write_text(nestedtext.dumps(value), encoding="utf-8")
        return True

    def import_nested(self, type_shed: typing.Type) -> typing.Optional[typing.Any]:
        try:
            raw_data = self.export_file.read_text("utf-8")
            if raw_data == "{}":
                return False
            data = nestedtext.loads(raw_data)
            if not isinstance(data, type_shed):
                self.logger.error(
                    f"Unable to import NestedText for file: {self.export_file.name}. Invalid Type Check"
                )
                return None
            return data

        except nestedtext.NestedTextError as e:
            # self.logger.error(f"")
            self.logger.error(
                f"Unable to import NestedText for file: {self.export_file.name}. {e}"
            )
            return None

    def import_excel(self, type_shed: typing.Type) -> typing.Optional[typing.Any]:
        if not pandas:
            raise ImportError("import_excel needs `pandas` to be installed.")
        data = {}
        for sheet_name, data_frame in pandas.read_excel(
            self.export_file, sheet_name=None
        ).items():
            data[sheet_name] = []
            for idx, row in data_frame.iterrows():
                text_value = None
                if row["Final"]:
                    text_value = row["Final"]
                elif row["Edited"]:
                    text_value = row["Final"]
                elif row["Inital"]:
                    text_value = row["Inital"]
                elif row["Original"]:
                    text_value = row["Original"]
                data[sheet_name].append(text_value)
        if not isinstance(data, type_shed):
            self.logger.error(
                f"Unable to import xlsx for file: {self.export_file.name}. Invalid Type Check"
            )
            return None
        return data

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
        do_dtext = self.config.get("Events", {}).get("dtext", False)
        dtext_rgx = re.compile(r"D_TEXT (.+) (\d+)")
        dtext_rgx_fallback = re.compile(r"D_TEXT (.+)")

        var_122 = self.config.get("Events", {}).get("code_122", None)
        auto_var_122 = self.config.get("Events", {}).get("auto_code_122", None)
        tile_name_pop = self.config.get("Events", {}).get("tile_name_pop", None)
        if var_122 is None or auto_var_122 is None:
            raise Exception("code_122/auto_code_122 is missing.")

        def process_code356(base_i):
            event = page_list_data[base_i]
            if do_dtext:
                if len(event["parameters"]) > 1:
                    return
                event_param = event["parameters"][0]
                d_text_check = event_param.startswith(
                    "D_TEXT"
                ) and not event_param.startswith("D_TEXT_SETTING")
                if not d_text_check:
                    return
                if event_param.strip() == "D_TEXT":
                    return
                dtext_param = event["parameters"][0]
                fi = dtext_rgx.findall(dtext_param)
                fallback = False
                if not fi:
                    fi = dtext_rgx_fallback.findall(dtext_param)
                    if isinstance(fi[0], str):
                        fi = [[fi[0], "_"]]
                    fallback = True
                if not fi:
                    self.logger.info("Regex failed to match DText.")
                    return
                    # raise Exception("Regex failed to match DText.")
                
                text_data = {
                    "type": "d_text",
                    "text": [fi[0][0]],
                    "pointer": [base_i],
                    "meta": dtext_rgx.sub(f"D_TEXT {{DTEXT}} {fi[0][1]}", dtext_param),
                }
                if fallback:
                    text_data["meta"] = f"D_TEXT {{DTEXT}}"
                page_list_events.append(text_data)

        def process_code122(base_i):
            if not var_122 and not auto_var_122:
                return
            event = page_list_data[base_i]

            # Sanity check
            if (
                event["parameters"][0] != event["parameters"][1]
                or not event["parameters"][0] in var_122
            ):
                if not auto_var_122:
                    # print("not autovar")
                    return
            # String sanity check
            string_param = event["parameters"][-1]
            
            if isinstance(string_param, str):
                if self.jp_rgx.search(string_param):
                    text_data = {
                        "type": "c12_text",
                        "text": [event["parameters"][-1].strip("'")],
                        "pointer": [base_i],
                    }
                    page_list_events.append(text_data)
            else:
                return

        def process_code320(base_i):
            event = page_list_data[base_i]
            if isinstance(event["parameters"][1], str):
                text_data = {
                    "type": "text_name_change",
                    "text": [event["parameters"][1]],
                    "pointer": [base_i],
                    "meta": "",
                }
                page_list_events.append(text_data)

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
                # MZ appears to no need processing for 102 codes...
                bse_event = page_list_data[base_i]
                text_data["text"] = bse_event["parameters"][0]
                text_data["pointer"] = [base_i]
                page_list_events.append(text_data)
            else:

                pointer = base_i + 1
                nx_event = page_list_data[pointer]
                nx_code = nx_event["code"]
                text_data["pointer"].append(base_i)
                while len(link_words) > 0 and pointer < t_pages:
                    if nx_code == 402 and nx_event["parameters"][1] == link_words[0]:
                        text_data["text"].append(nx_event["parameters"][1])
                        text_data["pointer"].append(pointer)
                        link_words.pop(0)
                    pointer += 1
                    if pointer > t_pages:
                        break
                    nx_event = page_list_data[pointer]
                    nx_code = nx_event["code"]
                if len(link_words) > 0:
                    self.logger.warning(f"trailing link_words. Report to Github.")
                page_list_events.append(text_data)

        for t_idx in range(t_pages):
            page_data = page_list_data[t_idx]
            if page_data["code"] == 101:
                process_code101(t_idx)
            elif page_data["code"] == 102:
                process_code102(t_idx)
            elif page_data["code"] == 356:
                process_code356(t_idx)
            elif page_data["code"] == 122:
                process_code122(t_idx)
            elif page_data["code"] == 320:
                process_code320(t_idx)
        return page_list_events

    @property
    def original_data(
        self,
    ) -> typing.Union[typing.Dict[str, typing.Any], typing.List[typing.Any]]:
        if not self._cached_orig_data:
            self._cached_orig_data = orjson.loads(self.original_file.read_bytes())
        return self._cached_orig_data
