import pathlib
import re
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

    def apply_maps(self, patch_file: pathlib.Path):
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
                elif text_data["type"] == "text_name_change":
                    ptr = text_data["pointer"][0]
                    txt_event = old_map[int(idx)]["list"][ptr]
                    txt_event["parameters"][1] = text_data["text"][0]
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
                # D_TEXT
                elif text_data["type"] == "d_text":
                    d_pointer = text_data["pointer"][0]
                    formatted = text_data["meta"].format(DTEXT=text_data["text"][0])
                    txt_event = old_map[int(idx)]["list"][d_pointer]
                    txt_event["parameters"][0] = formatted
                    old_map[int(idx)]["list"][d_pointer] = txt_event
                elif text_data["type"] == "c12_text":
                    c12_pointer = text_data["pointer"][0]
                    txt_event = old_map[int(idx)]["list"][c12_pointer]
                    has_wrong_escape = False
                    for rgx_match in re.finditer("'", text_data["text"][0]):
                        if text_data["text"][0][rgx_match.start() - 1] != "\\":
                            self.logger.warning(
                                f"\"{text_data['text'][0]}\" does not have an escape sequence for >'<. Refusing to use it. File name: {patch_file.name}"
                            )
                            has_wrong_escape = True
                            break
                    if not has_wrong_escape:
                        txt_event["parameters"][-1] = f"'{text_data['text'][0]}'"
                        old_map[int(idx)]["list"][c12_pointer] = txt_event
        patch_file.write_bytes(orjson.dumps(old_map, option=orjson.OPT_INDENT_2))

    def export_map(self, format="nested") -> bool:
        mapping = self.read_mapped()
        if not mapping:
            return False
        if format == "nested":
            # print(self.mapped_file)
            z = {}
            for evidx, event in mapping["events"].items():
                events = []
                for text_data in event:
                    events.extend(text_data["text"])
                    if text_data["type"] == "text_choice":
                        # hack to work around detection of <>
                        events.append("<>c")
                    else:
                        events.append("<>")
                z[evidx] = events
            return self.export_nested(z)
        elif format == "xlsx":
            z = {}
            for evidx, event in mapping["events"].items():
                events = []
                for text_data in event:
                    events.extend(text_data["text"])
                    events.append("<>")
                z[evidx] = events
            return self.export_excel(z)
        else:
            raise Exception(f"Unknown format: {format}")

    def import_map(self, format="nested") -> bool:
        mapping = self.read_mapped()
        if mapping is None:
            return False
        if format == "nested":
            nesttext_data = self.import_nested(dict)
        elif format == "xlsx":
            nesttext_data = self.import_excel(dict)
        else:
            raise Exception(f"Unknown format: {format}")
        if not nesttext_data:
            return False
        parsed_events = {}
        for event_idx, lines in nesttext_data.items():
            reconstruct_events = []
            event_data = []
            for line in lines:
                if line.startswith("<>") and len(line) in [2, 3]:
                    reconstruct_events.append(event_data)
                    event_data = []
                else:
                    event_data.append(line)
            parsed_events[event_idx] = reconstruct_events
        for k, map_events in mapping["events"].items():
            if len(map_events) != len(parsed_events[k]):
                self.logger.error(
                    f"Mismatched key size: {k}. Expecting: {len(map_events)}. Got: {len(parsed_events[k])}"
                )
                return False
            for idx, event in enumerate(map_events):
                if len(event["text"]) != len(parsed_events[k][idx]):
                    self.logger.error(
                        f"Mismatched key size: {event}. Expecting: {len(event['text'])}. Got: {len(parsed_events[k][idx])}"
                    )
                    return False
                event["text"] = parsed_events[k][idx]
                map_events[idx] = event
            mapping["events"][k] = map_events
        self.mapped_file.write_bytes(orjson.dumps(mapping, option=orjson.OPT_INDENT_2))
        return True


class MapsMVFungler(MVZFungler):
    fungler_type = "maps"

    def apply_maps(self, patch_file: pathlib.Path):
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
            for page_code_idx, page in page_maps.items():
                page_code_idx = int(page_code_idx)
                # Get thge current page_data
                page_data = old_events[evnt_id]["pages"][page_code_idx]
                for trans in page:
                    if trans["type"] == "text":
                        for txt_idx, ptr in enumerate(trans["pointer"]):
                            if txt_idx == 0 and "101code" in trans["meta"]:
                                text_event = page_data["list"][ptr]
                                text_event["parameters"][4] = trans["text"][txt_idx]
                                page_data["list"][ptr] = text_event
                            else:
                                text_event = page_data["list"][ptr]
                                text_event["parameters"][0] = trans["text"][txt_idx]
                                page_data["list"][ptr] = text_event
                    elif trans["type"] == "text_name_change":
                        ptr = trans["pointer"][0]
                        text_event = page_data["list"][ptr]
                        text_event["parameters"][1] = trans["text"][0]
                        page_data["list"][ptr] = text_event
                    elif trans["type"] == "text_choice":
                        # For Code 402
                        for txt_idx, ptr in enumerate(trans["pointer"][1:]):
                            text_event = page_data["list"][ptr]
                            text_event["parameters"][1] = trans["text"][txt_idx]
                            page_data["list"][ptr] = text_event
                            # print(events[page_idx], ptr, trans[txt_idx])
                        # Write back to code 102
                        text_event = old_events[evnt_id]["pages"][page_code_idx][
                            "list"
                        ][trans["pointer"][0]]
                        text_event["parameters"][0] = trans["text"]
                        page_data["list"][trans["pointer"][0]] = text_event
                    elif trans["type"] == "d_text":
                        d_pointer = trans["pointer"][0]
                        formatted = trans["meta"].format(DTEXT=trans["text"][0])
                        txt_event = page_data["list"][d_pointer]
                        txt_event["parameters"][0] = formatted
                        page_data["list"][d_pointer] = txt_event
                    elif trans["type"] == "c12_text":
                        c12_pointer = trans["pointer"][0]
                        txt_event = page_data["list"][c12_pointer]
                        has_wrong_escape = False
                        for rgx_match in re.finditer("'", trans["text"][0]):
                            if trans["text"][0][rgx_match.start() - 1] != "\\":
                                self.logger.warning(
                                    f"\"{trans['text'][0]}\" does not have an escape sequence for >'<. Refusing to use it."
                                )
                                has_wrong_escape = True
                                break
                        if not has_wrong_escape:
                            txt_event["parameters"][4] = f"'{trans['text'][0]}'"
                            page_data["list"][c12_pointer] = txt_event
                # Set back the page data
                old_events[evnt_id]["pages"][page_code_idx] = page_data
            old_events[evnt_id] = event_data
        old_map["events"] = old_events
        old_map["displayName"] = mapping["name"]
        patch_file.write_bytes(orjson.dumps(old_map, option=orjson.OPT_INDENT_2))
        return True

        # return super().apply_maps(map_file)

    def export_map(self, format="nested") -> bool:
        mapping = self.read_mapped()
        if not mapping:
            return False
        if format == "nested":
            # print(self.mapped_file)
            z = {}
            for evidx, event in mapping["events"].items():
                events = []
                for page_idx, page_events in event.items():
                    # print(page)
                    # for _, text_data in page:
                    for event in page_events:
                        # print(text_data)
                        events.extend(event["text"])
                        if event["type"] == "text_choice":
                            # hack to work around detection of <>
                            events.append("<>c")
                        else:
                            events.append("<>")
                z[evidx] = events
            self.export_nested(z)
            return True
        elif format == "xlsx":
            z = {}
            for evidx, event in mapping["events"].items():
                events = []
                for page_idx, text_data in event.items():
                    # print(page)
                    # for _, text_data in page:
                    for event in events:
                        # print(text_data)
                        events.extend(event["text"])
                        events.append("<>")
                z[evidx] = events
            self.export_excel(z)
            return True
        else:
            raise Exception(f"{format} Not Supported")

    def import_map(self, format="nested") -> bool:
        mapping = self.read_mapped()
        if mapping is None:
            return False
        if format == "nested":
            nesttext_data = self.import_nested(dict)
            if not nesttext_data:
                return False
        elif format == "xlsx":
            nesttext_data = self.import_excel(dict)
            if not nesttext_data:
                return False
        else:
            print(format, "Not Supported.")
            return False
        parsed_events = {}
        for event_idx, lines in nesttext_data.items():
            reconstruct_events = []
            event_data = []
            for line in lines:
                if line.startswith("<>") and len(line) in [2, 3]:
                    reconstruct_events.append(event_data)
                    event_data = []
                else:
                    event_data.append(line)
            parsed_events[event_idx] = reconstruct_events

        for evidx, map_event in mapping["events"].items():
            events: list = parsed_events[evidx]
            # idx = 0
            for pgidx, page in map_event.items():
                for idx, text_data in enumerate(page):
                    if len(events[0]) != len(text_data["text"]):
                        self.logger.error(
                            "Mismatch import for events. Text data does not match reconstructed events"
                        )
                        self.logger.error(events[0])
                        self.logger.error(text_data["text"])
                        self.logger.error(self.export_file.name)
                        return False
                    self.logger.debug(f"{text_data['text']} {events[0]}")
                    text_data["text"] = events[0]
                    events.pop(0)
                    page[idx] = text_data
                    # idx += 1
                map_event[pgidx] = page
            mapping["events"][evidx] = map_event
            if len(events) != 0:
                self.logger.error("Mismatch import for events.")
                self.logger.error(len(events))
                self.logger.error(self.export_file.name)
                return False
        self.mapped_file.write_bytes(orjson.dumps(mapping, option=orjson.OPT_INDENT_2))
        return True

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
