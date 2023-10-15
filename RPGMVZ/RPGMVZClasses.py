import pathlib

import orjson
from .RPGMVZBase import MVZFungler


class ClassesMVFungler(MVZFungler):
    def create_maps(self):
        mapping = {"type": "classes", "classes": {}}
        classes_data = orjson.loads(self.file.read_bytes())

        for mv_idx, mv_class in enumerate(classes_data):
            if mv_class["name"]:
                mapping["classes"][mv_idx] = mv_class["name"]

    def apply_maps(self):
        self.original_data
