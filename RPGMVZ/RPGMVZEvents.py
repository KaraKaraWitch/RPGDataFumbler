import pathlib
import nestedtext

import orjson
from .RPGMVZBase import MVZFungler


class CommonEventMVFungler(MVZFungler):
    fungler_type = "common_event"

    def create_maps(self):
        mapping = self.read_mapped(create=True)
        if not mapping:
            raise Exception("Mapping failed to create?")
        mapping["events"] = {}
        mapping = {"type": "common_event", "events": {}}
        if not isinstance(self.original_data, list):
            raise Exception("Wrong type?")
        # events = []
        for idx, event in enumerate(
            self.original_data,
        ):
            if not event:
                continue
            # pages = []
            page_list_data = event.get("list", [])
            if not page_list_data:
                continue
            if page_list_data[0]["code"] == 0:
                continue
            page_list_events = self.parse_page_lists(page_list_data)
            if page_list_events:
                mapping["events"][str(idx)] = page_list_events
        if mapping["events"]:
            self.mapped_file.write_bytes(
                orjson.dumps(mapping, option=orjson.OPT_INDENT_2)
            )

    def apply_maps(self):
        mapping = self.read_mapped(create=False)
        if not mapping:
            raise Exception("Mapping failed to read?")
        old_map = self.original_data
        if not old_map or not isinstance(old_map, list):
            raise Exception("original_data failed to read?")
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
        self.original_file.write_bytes(
            orjson.dumps(old_map, option=orjson.OPT_INDENT_2)
        )


class MapsMVFungler(MVZFungler):

    fungler_type = "maps"

    def apply_maps(self, map_file: pathlib.Path):
        old_map = self.original_data
        if not isinstance(old_map, dict):
            raise Exception("Maps in wrong format?")
        mapping = self.read_mapped()
        if not mapping:
            raise Exception("Mapping missing?")
        old_events = old_map["events"]
        for evnt_id, page_maps in mapping["events"].items():
            evnt_id = int(evnt_id)

            event_data = old_events[evnt_id]
            # TODO: Eventually refactor these bits
            for page_code_idx, page in page_maps.items():
                page_code_idx = int(page_code_idx)
                for trans in page:
                    if trans["type"] == "text":
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
        self.original_file.write_bytes(
            orjson.dumps(old_map, option=orjson.OPT_INDENT_2)
        )
        return True

        # return super().apply_maps(map_file)

    def export_map(self):
        mapping = self.read_mapped()
        if not mapping:
            return False
        # print(self.mapped_file)
        z = {}
        for evidx, event in mapping["events"].items():
            events = []
            for _, page in event.items():
                for text_data in page:
                    events.extend(text_data["text"])
                    events.append("<>")
            z[evidx] = events
        self.export_file.write_text(nestedtext.dumps(z), encoding="utf-8")

    def import_map(self, translated_file: pathlib.Path, inter_json: pathlib.Path):
        try:
            map_data = nestedtext.loads(translated_file.read_text("utf-8"))
        except nestedtext.NestedTextError as e:
            self.logger.error("Unable to import MapsMVFungler NestedText. {e}")
            return
        # We assume it is a map file.
        if not isinstance(map_data, dict):
            self.logger.error(
                "Unable to use MapsMVFungler NestedText. Expecting dictionary."
            )
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

    def create_maps(self):
        mapping = self.read_mapped(create=True)
        if not mapping:
            raise Exception("Mapping missing?")
        mapping["events"] = {}
        map_data = self.original_data
        # events = []
        if not isinstance(map_data, dict):
            raise Exception("Maps in wrong format?")
        for evidx, event in enumerate(
            map_data.get("events", []),
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
        mapping["name"] = map_data["displayName"]
        if mapping["events"] or mapping["name"]:
            self.mapped_file.write_bytes(
                orjson.dumps(mapping, option=orjson.OPT_INDENT_2)
            )
