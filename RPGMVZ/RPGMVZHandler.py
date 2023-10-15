

import logging
import pathlib
import typing
import orjson

from .RPGMVZItems import ItemMVFungler
from .RPGMVZEvents import CommonEventMVFungler, MapsMVFungler
from .RPGMVZSystem import SystemMVfungler

class MVZHandler:
    def __init__(self, game_file:pathlib.Path, config:dict, project_name:str="tl_workspace"):
        self.config = config
        self.game_file =game_file
        self.project_name = project_name
        self.game_type = self.config["General"]["type"]
        self.logger = logging.getLogger("MVZ|Handler")
        self._project_folders:typing.Optional[typing.Dict] = None


    @property
    def game_folder(self):
        if self._project_folders:
            return self._project_folders
        tl_folder = self.game_file.resolve().parent / self.project_name
        patch = tl_folder / "patched"
        exports = tl_folder / "export"
        
        if self.game_type == "MV":
            www = self.game_file.resolve().parent / "www"
            
            if not (www).exists():
                self.logger.error("missing `www` folder in game directory!")
                self.logger.error("Are you sure it is a MV game?")
                self.logger.error("If expecting a MZ game (data folder in root folder with game.exe)")
                self.logger.error("Set [type = \"MZ\"] value in DataFumbler.toml.")
                return
            self._project_folders = {
                "data":www/"data",
                "scripts":www/"js",
                "tl_root": tl_folder,
                "patch": patch,
                "export":exports
            }
        elif self.game_type == "MZ":
            data_folder = self.game_file.resolve().parent / "data"
            scripts_folder = self.game_file.resolve().parent / "js"
            
            if not (data_folder).exists():
                self.logger.error("missing `www` folder in game directory!")
                self.logger.error("Are you sure it is a MV game?")
                self.logger.error("If expecting a MV game (data folder in root folder with game.exe)")
                self.logger.error("Set [type = \"MV\"] value in DataFumbler.toml.")
                return
            self._project_folders = {
                "data":data_folder,
                "scripts":scripts_folder,
                "tl_root": tl_folder,
                "patch": patch,
                "export":exports
            }
        else:
            self.logger.error(f"Unknown game type: {self.game_type}")
            return {}
        return self._project_folders

    def resolve_file(self, orig_file: pathlib.Path, map_file:pathlib.Path, export_file:pathlib.Path):
        content = orjson.loads(orig_file.read_bytes())
        # print("[Check]", file_url.name)
        if isinstance(content, list):
            if len(content) < 2:
                return None
            item = content[1]
            actor_tests = ["characterIndex", "characterName", "name", "note", "profile"]
            weapon_tests = ["description", "name", "note"]
            # event_tests = ["characterIndex", "characterName", "name", "note", "profile"]
            if sum([act_test in actor_tests for act_test in item]) == len(actor_tests):
                return ActorMVFungler(orig_file, map_file, export_file, self.config)
            if (
                sum([weapon_test in weapon_tests for weapon_test in item])
                == len(weapon_tests)
                and "weapon" in orig_file.name.lower()
            ):
                return ItemMVFungler(orig_file, map_file, export_file, self.config)
            if (
                sum([weapon_test in weapon_tests for weapon_test in item])
                == len(weapon_tests)
                and "item" in orig_file.name.lower()
            ):
                return ItemMVFungler(orig_file, map_file, export_file, self.config)
            if (
                sum([weapon_test in weapon_tests for weapon_test in item])
                == len(weapon_tests)
                and "armors" in orig_file.name.lower()
            ):
                return ItemMVFungler(orig_file, map_file, export_file, self.config)
            if "commonevents" in orig_file.name.lower():
                return CommonEventMVFungler(orig_file, map_file, export_file, self.config)

            # else:
            #     print()
        elif isinstance(content, dict):
            if "Map" in orig_file.name and content.get("events"):
                return MapsMVFungler(orig_file, map_file, export_file, self.config)
            if content.get("armorTypes"):
                return SystemMVfungler(orig_file, map_file, export_file, self.config)
        # Events stuff


    def create_maps(self):
        # folders:typing.Dict[str, pathlib.Path], config_dict
        if not self.game_folder:
            return
        for json_file in self.game_folder["data"].rglob("*.json"):
            rel = json_file.relative_to(self.game_folder["data"])
            tl_folder = self.game_folder["tl_root"] / "data"
            export_folder = self.game_folder["export"]
            map_file = tl_folder / rel
            export_file = export_folder / rel
            cls = self.resolve_file(json_file, map_file, export_file)
            if cls:
                if (tl_folder / rel).exists() and not config_dict["General"]["replace"]:
                    pass
                    # logger.info(f"Skip dump for: {rel.name}")
                else:
                    logger.info(f"Dumping: {rel.name}")
                    cls.create_maps()
        for script_file in folders["scripts"].rglob("*.js"):
            rel = script_file.relative_to(folders["scripts"])
            tl_folder = folders["tl_root"] / "script"
            (tl_folder / rel).parent.mkdir(parents=True, exist_ok=True)
            if not (tl_folder / rel).exists() and not config_dict["General"]["replace_scripts"]:
                logger.info(f"Dumping: {rel.name}")
                shutil.copy(script_file, tl_folder / rel)
        # Marking folder / I hope someone doesn't delete this...
        (folders["tl_root"] / ".TLPROJECT").touch()

    def extract(self, override:bool=False):
        """Extracts the translatable components into the project folder
        """
        game_folders = self.game_folder
        folders = self.game_folder
        if not folders:
            return
        for json_file in folders["data"].rglob("*.json"):
            rel = json_file.relative_to(folders["data"])
            tl_folder = folders["tl_root"] / "data"
            
            cls = resolve_file(json_file, config_dict)