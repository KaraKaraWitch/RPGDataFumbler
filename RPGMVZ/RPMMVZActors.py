import pathlib
import orjson
from .RPGMVZBase import MVZFungler
import nestedtext


class ActorMVFungler(MVZFungler):

    fungler_type = "actors"

    def apply_maps(self, patch_file: pathlib.Path):
        mapping = self.read_mapped()
        if not mapping:
            return
        actors = self.original_data
        if not isinstance(actors, list):
            raise Exception("Wrong type?")
        export_actors = []
        for actor in actors:

            if not actor:
                export_actors.append(actor)
                continue
            if not actor["name"]:
                export_actors.append(actor)
                continue
            # print(actor, mapping["actors"])
            actor_data = mapping["actors"].get(str(actor["id"]), {})
            if not actor_data:
                export_actors.append(actor)
                continue
            actor["name"] = actor_data["name"]
            actor["note"] = actor_data["note"]
            actor["nickname"] = actor_data["nickname"]
            actor["profile"] = actor_data["profile"]
            export_actors.append(actor)
        patch_file.write_bytes(orjson.dumps(export_actors, option=orjson.OPT_INDENT_2))
        return True

    def create_maps(self):
        mapping = self.read_mapped(create=True)
        if not mapping:
            return
        mapping["actors"] = {}
        actors = self.original_data
        if not isinstance(actors, list):
            raise Exception("Wrong type?")
        for actor in actors:
            if not actor:
                continue
            if not actor["name"]:
                continue
            mapping["actors"][str(actor["id"])] = {
                "name": actor["name"],
                "note": actor["note"],
                "nickname": actor["nickname"],
                "profile": actor["profile"],
            }
        self.mapped_file.write_bytes(orjson.dumps(mapping, option=orjson.OPT_INDENT_2))
        return True

    def export_map(self):
        mapping = self.read_mapped(create=False)
        if not mapping:
            return False
        self.export_file.write_text(
            nestedtext.dumps(mapping["actors"]), encoding="utf-8"
        )
        return True

    def import_map(self) -> bool:
        mapping = self.read_mapped(create=False)
        if not mapping:
            return False
        try:
            imports = nestedtext.loads(self.export_file.read_text(encoding="utf-8"))
        except nestedtext.NestedTextError as e:
            self.logger.error(f"Failed to load export file for Actors: {e}")
            return False
        mapping["actors"] = imports
        self.mapped_file.write_bytes(orjson.dumps(mapping, option=orjson.OPT_INDENT_2))
        return True
