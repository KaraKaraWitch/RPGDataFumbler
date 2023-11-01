import pathlib

import orjson
from .RPGMVZBase import MVZFungler


class ClassesMVFungler(MVZFungler):

    fungler_type = "classes"

    def create_maps(self):
        classes_data = self.original_data
        mapping = self.read_mapped(create=True)
        if not mapping:
            raise Exception("Unknown Mapping?")
        if not isinstance(classes_data, list):
            raise Exception("Expected Classes to be a list.")
        mapping = {**mapping, "classes":{}}

        for mv_idx, mv_class in enumerate(classes_data):
            if not mv_class:
                continue
            if mv_class["name"]:
                mapping["classes"][str(mv_idx)] = mv_class["name"]
        self.mapped_file.write_bytes(orjson.dumps(mapping, option=orjson.OPT_INDENT_2))

    def apply_maps(self, patch_file: pathlib.Path):
        classes_data = self.original_data
        if not isinstance(classes_data, list):
            raise Exception("Expected Classes to be a list.")
        mapping = self.read_mapped(create=True)
        if not mapping:
            return
        if mapping["classes"]:
            for k,v in mapping["classes"].items():
                class_id = int(k)
                classes_data[class_id]["name"] = v
        patch_file.write_bytes(orjson.dumps(classes_data, option=orjson.OPT_INDENT_2))
        return True