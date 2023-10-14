
import pathlib

import orjson
from .RPGMVZBase import MVZFungler

class ClassesMVFungler(MVZFungler):

    def create_maps(self, export_file: pathlib.Path):
        mapping = {"type": "classes", "classes": {}}
        classes_data = orjson.loads(self.file.read_bytes())

        for mv_idx, mv_class in enumerate(classes_data):
            if mv_class["name"]:
                mapping["classes"][mv_idx] = mv_class["name"]

    def apply_maps(self, map_file: pathlib.Path):
        old_map = orjson.loads(self.file.read_bytes())
        mapping = orjson.loads(map_file.read_bytes())