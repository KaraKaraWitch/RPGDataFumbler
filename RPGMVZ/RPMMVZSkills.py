import pathlib
import typing

import orjson
from .RPGMVZBase import MVZFungler


class SkillsMVfungler(MVZFungler):

    fungler_type = "skill"

    def create_maps(self):
        self.read_mapped(create=True)
        mapping: typing.Dict[str, typing.Any] = {
            "type": self.fungler_type,
            "skills": {},
        }
        skill_data = self.original_data
        if not isinstance(skill_data, list):
            raise Exception("SkillData not in correct format.")

        for skill in skill_data:
            if not skill:
                continue
            if not skill["name"]:
                continue

            fmt_data = {
                "name": skill["name"],
                "msgs": [skill["message1"], skill["message2"]],
            }
            if skill["description"]:
                fmt_data["desc"] = skill["description"]
            mapping["skills"][str(skill["id"])] = fmt_data
        self.mapped_file.write_bytes(orjson.dumps(mapping, option=orjson.OPT_INDENT_2))

    def apply_maps(self, patch_file: pathlib.Path) -> bool:
        mapping = self.read_mapped()
        if not mapping:
            raise Exception(f"Cannot read Mappings?")
        if mapping.get("type", "") not in ["skill"]:
            print(
                f"[ERR] Failed applying, {patch_file.name} does not match required type."
            )
            return False

        skill_data = self.original_data

        if not isinstance(skill_data, list):
            raise Exception("SkillData not in correct format.")

        for k, v in mapping["skills"].items():
            skill_data[int(k)]["name"] = v["name"]
            skill_data[int(k)]["message1"] = v["msgs"][0]
            skill_data[int(k)]["message2"] = v["msgs"][1]
            if "desc" in v:
                skill_data[int(k)]["description"] = v["desc"]
        patch_file.write_bytes(orjson.dumps(skill_data))
        return True

    def import_map(self, format="nested") -> bool:
        # self.import_nested()

        mappings = self.read_mapped()
        if not mappings:
            return False
        if format == "nested":
            skills = []
            buffer = []
            data = self.import_nested(dict)
            if not data:
                return False
            for skill in data["Skills"]:
                if skill == "<>":
                    skills.append(buffer)
                    buffer = []
                else:
                    buffer.append(skill)
            ctr = 0
            for k, _ in mappings["skills"].items():
                mappings["skills"][k]["name"] = skills[ctr][0]
                mappings["skills"][k]["msgs"][0] = skills[ctr][1]
                mappings["skills"][k]["msgs"][1] = skills[ctr][2]
                if "desc" in mappings["skills"][k]:
                    mappings["skills"][k]["desc"] = skills[ctr][3]
                ctr += 1
        elif format == "xlsx":
            skills = []
            buffer = []
            data = self.import_excel(dict)
            if not data:
                return False
            for skill in data["Skills"]:
                if skill == "<>":
                    skills.append(buffer)
                    buffer = []
                else:
                    buffer.append(skill)
            if buffer:
                skills.append(buffer)
            ctr = 0
            for k, _ in mappings["skills"].items():
                mappings[k]["name"] = skills[ctr][0]
                mappings[k]["msgs"][0] = skills[ctr][1]
                mappings[k]["msgs"][1] = skills[ctr][2]
                if "desc" in mappings[k]:
                    mappings[k]["desc"] = skills[ctr][3]
        else:
            raise Exception(f"Unknown format: {format}")
        self.mapped_file.write_bytes(orjson.dumps(mappings, option=orjson.OPT_INDENT_2))
        return True
        # return super().import_map(format)

    def export_map(self, format="nested") -> bool:
        mappings = self.read_mapped()
        if not mappings:
            return False
        if format == "nested":
            export_actors = {"Skills": []}
            for skill in mappings["skills"].values():
                export_actors["Skills"].append(skill["name"])
                export_actors["Skills"].append(skill["msgs"][0])
                export_actors["Skills"].append(skill["msgs"][1])
                if "desc" in skill:
                    export_actors["Skills"].append(skill["desc"])
                export_actors["Skills"].append("<>")
            self.export_nested(export_actors)
            return True
        elif format == "xlsx":
            export_actors = {"Skills": []}
            for skill in mappings["skills"].values():
                export_actors["Skills"].append(skill["name"])
                export_actors["Skills"].append(skill["msgs"][0])
                export_actors["Skills"].append(skill["msgs"][1])
                if "desc" in skill:
                    export_actors["Skills"].append(skill["desc"])
                export_actors["Skills"].append("<>")
            self.export_excel(export_actors)
            return True
        raise NotImplementedError(f"Format: {format} is not Implemented.")
