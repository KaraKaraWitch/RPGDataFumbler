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