import logging
import pathlib
import shutil
import typing
import orjson

from .RPGMVZItems import ItemMVFungler
from .RPGMVZEvents import CommonEventMVFungler, MapsMVFungler
from .RPGMVZSystem import SystemMVfungler
from .RPMMVZActors import ActorMVFungler
from .RPGMVZClasses import ClassesMVFungler
from .RPMMVZSkills import SkillsMVfungler


class MVZHandler:
    def __init__(
        self, game_file: pathlib.Path, config: dict, project_name: str = "tl_workspace"
    ):
        self.config = config
        self.game_file = game_file
        self.project_name = project_name
        self.game_type = self.config["General"].get("type", "MV")
        self.logger = logging.getLogger("MVZ|Handler")
        self._project_folders: typing.Optional[typing.Dict] = None

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
                self.logger.error(
                    "If expecting a MZ game (data folder in root folder with game.exe)"
                )
                self.logger.error('Set [type = "MZ"] value in DataFumbler.toml.')
                return
            self._project_folders = {
                "data": www / "data",
                "scripts": www / "js",
                "tl_root": tl_folder,
                "patch": patch,
                "export": exports,
            }
        elif self.game_type == "MZ":
            data_folder = self.game_file.resolve().parent / "data"
            scripts_folder = self.game_file.resolve().parent / "js"

            if not (data_folder).exists():
                self.logger.error("missing `www` folder in game directory!")
                self.logger.error("Are you sure it is a MV game?")
                self.logger.error(
                    "If expecting a MV game (data folder in root folder with game.exe)"
                )
                self.logger.error('Set [type = "MV"] value in DataFumbler.toml.')
                return
            self._project_folders = {
                "data": data_folder,
                "scripts": scripts_folder,
                "tl_root": tl_folder,
                "patch": patch,
                "export": exports,
            }
        else:
            self.logger.error(f"Unknown game type: {self.game_type}")
            return {}
        return self._project_folders

    def resolve_file(
        self, orig_file: pathlib.Path, map_file: pathlib.Path, export_file: pathlib.Path
    ):
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
                return CommonEventMVFungler(
                    orig_file, map_file, export_file, self.config
                )
            if "classes" in orig_file.name.lower():
                return ClassesMVFungler(
                    orig_file, map_file, export_file, self.config
                )
            if "skills" in orig_file.name.lower():
                return SkillsMVfungler(
                    orig_file, map_file, export_file, self.config
                )

            # else:
            #     print()
        elif isinstance(content, dict):
            if "Map" in orig_file.name and content.get("events"):
                return MapsMVFungler(orig_file, map_file, export_file, self.config)
            if content.get("armorTypes"):
                return SystemMVfungler(orig_file, map_file, export_file, self.config)
        # Events stuff

    @property
    def mapping_files(
        self,
    ) -> typing.Union[
        typing.Generator[pathlib.Path, None, None], typing.List[pathlib.Path]
    ]:
        if not self.game_folder:
            return []
        tl_folder = self.game_folder["tl_root"] / "data"
        for json_file in self.game_folder["data"].rglob("*.json"):
            rel = json_file.relative_to(self.game_folder["data"])
            map_file = tl_folder / rel
            yield map_file

    @property
    def export_files(
        self,
    ) -> typing.Union[
        typing.Generator[pathlib.Path, None, None], typing.List[pathlib.Path]
    ]:
        if not self.game_folder:
            return []
        export_folder = self.game_folder["export"] / "data"
        # export_folder = export_folder / rel
        for json_file in self.game_folder["data"].rglob("*.json"):
            rel = json_file.relative_to(self.game_folder["data"])
            export_file = (export_folder / rel).with_suffix(".nt.txt")
            yield export_file

    def create_maps(self, replace: bool = False):
        # folders:typing.Dict[str, pathlib.Path], config_dict
        if not self.game_folder:
            return
        tl_folder = self.game_folder["tl_root"] / "data"
        export_folder = self.game_folder["export"]
        for json_file in self.game_folder["data"].rglob("*.json"):
            rel = json_file.relative_to(self.game_folder["data"])

            map_file = tl_folder / rel
            export_file = (export_folder / rel).with_suffix(".nt.txt")
            cls = self.resolve_file(json_file, map_file, export_file)
            if cls:
                self.logger.debug(f"Dumping: {rel.name}")
                if not (tl_folder / rel).parent.exists():
                    (tl_folder / rel).parent.mkdir(parents=True, exist_ok=True)
                # print( (tl_folder / rel).exists())
                if (tl_folder / rel).exists():
                    if not replace:
                        self.logger.debug(f"Skip dump for: {rel.name}")
                        continue
                    else:
                        cls.create_maps()
                else:
                    cls.create_maps()

        tl_folder = self.game_folder["tl_root"] / "script"
        for script_file in self.game_folder["scripts"].rglob("*.js"):
            rel = script_file.relative_to(self.game_folder["scripts"])
            # print(script_file, (tl_folder / rel))
            self.logger.debug(f"Dumping: {rel.name}")
            if not (tl_folder / rel).parent.exists():
                (tl_folder / rel).parent.mkdir(parents=True, exist_ok=True)
            # print( (tl_folder / rel).exists())
            if (tl_folder / rel).exists():
                if not replace:
                    self.logger.debug(f"Skip dump for: {rel.name}")
                    continue
                else:
                    shutil.copy(script_file, tl_folder / rel)
            else:
                shutil.copy(script_file, tl_folder / rel)
        # Marking folder / I hope someone doesn't delete this...
        (self.game_folder["tl_root"] / ".TLPROJECT").touch()

    def export(self, replace: bool = False,format:str="nested"):
        """Exports the translatable components into the project folder"""
        if not self.game_folder:
            return
        tl_folder = self.game_folder["tl_root"] / "data"
        export_folder = self.game_folder["export"] / "data"
        for json_file in self.game_folder["data"].rglob("*.json"):
            rel = json_file.relative_to(self.game_folder["data"])

            map_file = tl_folder / rel
            export_file: pathlib.Path = export_folder / rel
            export_file = export_file.with_suffix(".nt.txt")
            cls = self.resolve_file(json_file, map_file, export_file)
            if cls:
                if (tl_folder / rel).exists() and replace:
                    pass
                    # logger.info(f"Skip dump for: {rel.name}")
                else:
                    self.logger.info(f"Exporting: {rel.name}")
                    if not (export_folder / rel).parent.exists():
                        (export_folder / rel).parent.mkdir(parents=True, exist_ok=True)
                    try:
                        if map_file.exists():
                            cls.export_map()
                            if format == "nested":
                                orig_export = export_file.with_suffix(".ORIG.nt.txt")
                                if export_file.exists() and not orig_export.exists():
                                    self.logger.info("Creating original copy...")
                                    shutil.copy(export_file, orig_export)
                    except NotImplementedError:
                        self.logger.warning(f"TODO: {rel.name}")

    def import_maps(self):
        """imports the translatable components into the project folder"""
        if not self.game_folder:
            return
        tl_folder = self.game_folder["tl_root"] / "data"
        export_folder = self.game_folder["export"] / "data"
        for json_file in self.game_folder["data"].rglob("*.json"):
            rel = json_file.relative_to(self.game_folder["data"])

            map_file = tl_folder / rel
            export_file: pathlib.Path = export_folder / rel
            export_file = export_file.with_suffix(".nt.txt")
            cls = self.resolve_file(json_file, map_file, export_file)
            if cls:
                if (export_file).exists():
                    try:
                        cls.import_map()
                    except NotImplementedError:
                        self.logger.warning(f"TODO: {rel.name}")

    def patch(self, skip_copy:bool=True):
        """Patches a game.

        To be more precise, it creates a copy of the entire game directory and then patches over it.

        This ensures that the original game being translated doesn't get overwritten by it.
        """

        

        if not self.game_folder:
            return
        tl_folder: pathlib.Path = self.game_folder["tl_root"] / "data"
        patched_folder: pathlib.Path = self.game_folder["patch"].resolve()
        do_copy = False
        if not patched_folder.is_dir() or not skip_copy:
            do_copy = True
        if do_copy:
            if not self.game_folder["patch"].is_dir():
                self.game_folder["patch"].mkdir(parents=True, exist_ok=True)
            for item in self.game_file.parent.iterdir():
                if item.resolve() == self.game_folder["tl_root"]:
                    continue
                if item.is_file():
                    rel = item.relative_to(self.game_file.parent)
                    shutil.copy(item, self.game_folder["patch"] / rel)
                elif item.is_dir():
                    rel = item.relative_to(self.game_file.parent)
                    shutil.copytree(item, self.game_folder["patch"] / rel)

        export_folder = self.game_folder["export"] / "data"
        data_rel = (
            self.game_folder["data"]
            .resolve()
            .relative_to(self.game_file.parent.resolve())
        )
        for json_file in self.game_folder["data"].rglob("*.json"):
            rel = json_file.relative_to(self.game_folder["data"])

            map_file = tl_folder / rel
            export_file: pathlib.Path = export_folder / rel
            export_file = export_file.with_suffix(".nt.txt")
            patch_file = patched_folder / data_rel / rel
            # print(patch_file)
            cls = self.resolve_file(json_file, map_file, export_file)
            print(patch_file, "patching", map_file)
            if cls:
                if map_file.exists():
                    try:
                        cls.apply_maps(patch_file)
                    except NotImplementedError:
                        self.logger.warning(f"TODO: {rel.name}")
        script_rel = (
            self.game_folder["scripts"]
            .resolve()
            .relative_to(self.game_file.parent.resolve())
        )
        for script_file in self.game_folder["scripts"].rglob("*.js"):
            rel = script_file.relative_to(self.game_folder["scripts"])
            nsp = self.game_folder["tl_root"] / "script" / rel
            patch_file = patched_folder / script_rel / rel
            # print(patch_file, nsp)
            if patch_file.exists():
                patch_file.unlink()
            shutil.copy(nsp, patch_file)
