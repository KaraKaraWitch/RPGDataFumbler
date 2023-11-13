import pathlib
import nestedtext

import orjson

from .RPGMVZBase import MVZFungler


class EnemyMVFungler(MVZFungler):

    fungler_type = "enemy"

    def create_maps(self):
        enemy_data = self.original_data
        mapping = self.read_mapped(create=True)
        if not mapping:
            raise Exception("Failed to create?")
        mapping["enemy"] = {}
        if not mapping:
            raise Exception(f"Cannot create Mappings?")
        for enemy in enemy_data:
            if not enemy or not enemy["name"]:
                continue
            mapping["enemy"][str(enemy["id"])] = enemy["name"]
        if mapping["enemy"]:
            self.mapped_file.write_bytes(
                orjson.dumps(mapping, option=orjson.OPT_INDENT_2)
            )
        else:
            print("No Exportable Items:", self.mapped_file.name)

    def apply_maps(self, patch_file: pathlib.Path):
        mapping = self.read_mapped()
        if not mapping:
            raise Exception(f"Cannot read Mappings?")
        if mapping.get("type", "") not in ["enemy"]:
            print(
                f"[ERR] Failed applying, {patch_file.name} does not match required type."
            )
            return
        enemy = self.original_data
        for enemy_idx_s, trans_data in mapping["enemy"].items():
            enemy_idx = int(enemy_idx_s)
            enemy[enemy_idx]["name"] = trans_data
        patch_file.write_bytes(orjson.dumps(enemy))
        return True

    def export_map(self, format="nested") -> bool:
        mapping = self.read_mapped()
        if not mapping:
            raise Exception(f"Cannot read Mappings?")
        if format == "nested":
            items = {}
            for enemy_idx_s, trans_data in mapping["enemy"].items():
                items[enemy_idx_s] = trans_data
            self.export_nested(items)
            return True
        elif format == "xlsx":
            items = []
            for _, trans_data in mapping["enemy"].items():
                items.extend([trans_data,"<>"])
            self.export_excel({"enemy":items})
        return False

    def import_map(self, format="nested") -> bool:
        mapping = self.read_mapped()
        if mapping is None:
            return False
        if format == "nested":
            nesttext_data = self.import_nested(dict)
            if not nesttext_data:
                return False
            for enemy_idx_s, name in nesttext_data.items():
                mapping["enemy"][enemy_idx_s] = name
        elif format == "xlsx":
            nesttext_data = self.import_excel(dict)
            if not nesttext_data:
                return False
        # We assume it is a map file.
        
        self.mapped_file.write_bytes(orjson.dumps(mapping, option=orjson.OPT_INDENT_2))
        return True
