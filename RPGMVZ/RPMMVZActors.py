import pathlib
import orjson
from .RPGMVZBase import MVZFungler, pandas
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

    def export_map(self, format="nested") -> bool:
        mapping = self.read_mapped(create=False)
        if not mapping:
            return False
        if format == "nested":
            export_actors = {"Actors": []}
            for actor in mapping["actors"].values():
                export_actors["Actors"].append(actor["name"])
                export_actors["Actors"].append(actor["note"])
                export_actors["Actors"].append(actor["nickname"])
                export_actors["Actors"].append(actor["profile"])
                export_actors["Actors"].append("<>")
            self.export_nested(export_actors)
            return True
        elif format == "xlsx":
            export_actors = {"Actors": []}
            for actor in mapping["actors"].values():
                export_actors["Actors"].append(actor["name"])
                export_actors["Actors"].append(actor["note"])
                export_actors["Actors"].append(actor["nickname"])
                export_actors["Actors"].append(actor["profile"])
                export_actors["Actors"].append("<>")
            self.export_excel(export_actors)
            return True
        raise NotImplementedError(f"Format: {format} is not Implemented.")

    def import_map(self, format="nested") -> bool:
        mappings = self.read_mapped(create=False)
        if not mappings:
            return False
        # TODO: Fix actors
        if format == "nested":
            actors = []
            buffer = []
            data = self.import_nested(dict)
            if not data:
                return False
            for skill in data["Actors"]:
                if skill == "<>":
                    actors.append(buffer)
                    buffer = []
                else:
                    buffer.append(skill)
            ctr = 0
            for k,_ in mappings["actors"].items():
                # k = int(k)
                mappings['actors'][k]["name"] = actors[ctr][0]
                mappings['actors'][k]["note"] = actors[ctr][1]
                mappings['actors'][k]["nickname"] = actors[ctr][2]
                mappings['actors'][k]["profile"] = actors[ctr][3]
        elif format == "xlsx":
            actors = []
            buffer = []
            data = self.import_excel(dict)
            if not data:
                return False
            for skill in data["Actors"]:
                if skill == "<>":
                    actors.append(buffer)
                    buffer = []
                else:
                    buffer.append(skill)
            ctr = 0
            for k,_ in mappings["actors"].items():
                mappings[k]["name"] = actors[ctr][0]
                mappings[k]["note"] = actors[ctr][1]
                mappings[k]["nickname"] = actors[ctr][2]
                mappings[k]["profile"] = actors[ctr][3]
        self.mapped_file.write_bytes(orjson.dumps(mappings, option=orjson.OPT_INDENT_2))
        return True
