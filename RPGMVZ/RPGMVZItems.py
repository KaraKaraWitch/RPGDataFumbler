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

    def export_map(self, format="nested") -> bool:
        mapping = self.read_mapped()
        if not mapping:
            raise Exception(f"Cannot read Mappings?")
        if format == "nested":
            items = {}
            for weapon_idx_s, trans_data in mapping["item"].items():
                items[weapon_idx_s] = [
                    trans_data["name"],
                    trans_data["desc"],
                    trans_data["note"],
                ]
            self.export_nested(items)
            return True
        elif format == "xlsx":
            items = []
            for _, trans_data in mapping["item"].items():
                items.extend([
                    trans_data["name"],
                    trans_data["desc"],
                    trans_data["note"],
                    "<>"
                ])
            self.export_excel({"items":items})
        return False

    def import_map(self, format="nested") -> bool:
        mapping = self.read_mapped()
        if mapping is None:
            return False
        if format == "nested":
            nesttext_data = self.import_nested(dict)
            if not nesttext_data:
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
        elif format == "xlsx":
            nesttext_data = self.import_excel(dict)
            if not nesttext_data:
                return False
        # We assume it is a map file.
        
        self.mapped_file.write_bytes(orjson.dumps(mapping, option=orjson.OPT_INDENT_2))
        return True
