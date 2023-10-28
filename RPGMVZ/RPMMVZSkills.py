import pathlib
import typing

import orjson
from .RPGMVZBase import MVZFungler

class SkillsMVfungler(MVZFungler):

    fungler_type = "skill"

    def create_maps(self):
        self.read_mapped(create=True)
        mapping: typing.Dict[str, typing.Any] = {"type": self.fungler_type, "skills":{}}
        skill_data = self.original_data
        if not isinstance(skill_data, list):
            raise Exception("SkillData not in correct format.")

        for skill in skill_data:
            if not skill:
                continue

            fmt_data = {
                "name": skill["name"],
                "msgs": [skill["message1"], skill["message2"]]
            }
            if skill["description"]:
                fmt_data["desc"] = skill["description"]
            mapping["skills"][str(skill["id"])] = fmt_data

    def apply_maps(self, patch_file: pathlib.Path) -> bool:
        mapping = self.read_mapped()
        if not mapping:
            raise Exception(f"Cannot read Mappings?")
        if mapping.get("type", "") not in ["skill"]:
            print(
                f"[ERR] Failed applying, {patch_file.name} does not match required type."
            )
            return False

        skills = self.original_data

        for k,v in mapping["skills"].items():
            skills[int(k)]["name"] = v["name"]
            skills[int(k)]["message1"] = v["msgs"][0]
            skills[int(k)]["message2"] = v["msgs"][1]
            if "desc" in v:
                skills[int(k)]["description"] = v["desc"]
        patch_file.write_bytes(orjson.dumps(skills))
        return True
    
    def import_map(self, format="nested") -> bool:
        return super().import_map(format)
    
    def export_map(self, format="nested") -> bool:
        if format == "nested":
            
        return super().export_map(format)