import pathlib
import nestedtext

import orjson

from .RPGMVZBase import MVZFungler


class ItemMVFungler(MVZFungler):

    fungler_type = "items"

    def create_maps(self):
        weapons_data = self.original_data
        mapping = self.read_mapped(create=True)
        if not mapping:
            raise Exception("Failed to create?")
        mapping["item"] = {}
        if not mapping:
            raise Exception(f"Cannot create Mappings?")
        for weapon in weapons_data:
            if not weapon or not weapon["name"]:
                continue
            mapping["item"][str(weapon["id"])] = {
                "name": weapon["name"],
                "desc": weapon["description"],
                "note": weapon["note"],
            }
        if mapping["item"]:
            self.mapped_file.write_bytes(
                orjson.dumps(mapping, option=orjson.OPT_INDENT_2)
            )
        else:
            print("No Exportable Items:", self.mapped_file.name)

    def apply_maps(self, patch_file: pathlib.Path):
        mapping = self.read_mapped()
        if not mapping:
            raise Exception(f"Cannot read Mappings?")
        if mapping.get("type", "") not in ["weapons", "items"]:
            print(
                f"[ERR] Failed applying, {patch_file.name} does not match required type."
            )
            return
        weapons = self.original_data
        for weapon_idx_s, trans_data in mapping["item"].items():
            weapon_idx = int(weapon_idx_s)
            weapons[weapon_idx]["name"] = trans_data["name"]
            weapons[weapon_idx]["description"] = trans_data["desc"]
            weapons[weapon_idx]["note"] = trans_data["note"]
        patch_file.write_bytes(orjson.dumps(weapons))
        return True

    def export_map(self) -> bool:
        mapping = self.read_mapped()
        if not mapping:
            raise Exception(f"Cannot read Mappings?")
        items = {}
        for weapon_idx_s, trans_data in mapping["item"].items():
            items[weapon_idx_s] = [
                trans_data["name"],
                trans_data["desc"],
                trans_data["note"],
            ]
        self.export_file.write_text(nestedtext.dumps(items), encoding="utf-8")
        return True

    def import_map(self) -> bool:
        mapping = self.read_mapped()
        if mapping is None:
            return False
        try:
            raw_data = self.export_file.read_text("utf-8")
            if raw_data == "{}":
                return False
            nesttext_data = nestedtext.loads(raw_data)
        except nestedtext.NestedTextError as e:
            # self.logger.error(f"")
            self.logger.error(
                f"Unable to import MapsMVFungler NestedText for file: {self.export_file.name}. {e}"
            )
            return False
        # We assume it is a map file.
        if not isinstance(nesttext_data, dict):
            self.logger.error(
                "Unable to use MapsMVFungler NestedText. Expecting dictionary."
            )
            return False
        for weapon_idx_s, packed in nesttext_data.items():
            try:
                name, desc, note = packed
            except Exception:
                self.logger.error(
                    f"Unable to import NestedText for Items: {self.export_file.name}, Mismatch packed sizes for: {packed}"
                )
                return False
            mapping["item"][weapon_idx_s]["name"] = name
            mapping["item"][weapon_idx_s]["desc"] = desc
            mapping["item"][weapon_idx_s]["note"] = note
        self.mapped_file.write_bytes(orjson.dumps(mapping, option=orjson.OPT_INDENT_2))
        return True
