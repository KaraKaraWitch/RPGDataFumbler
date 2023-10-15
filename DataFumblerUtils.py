# =================================================== #
# DataFumblerUtils: RPGMakerMV localization python scripts
# Built for Gehenna but works for MV related games.
# Utils: Utility Functions(?)
# =================================================== #

import pathlib
import shutil
import typing
import typer
import logging

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger("DF|Util")

app = typer.Typer()



def get_folders(game_exec:pathlib.Path, game_type: str):
    tl_folder = game_exec.resolve().parent / project_folder_name
    patch = tl_folder / "patched"
    exports = tl_folder / "export"
    if game_type == "MV":
        www = game_exec.resolve().parent / "www"
        
        if not (www).exists():
            logging.error("missing `www` folder in game directory!")
            logging.error("Are you sure it is a MV game?")
            logging.error("If expecting a MZ game (data folder in root folder with game.exe)")
            logging.error("Set [type = \"MZ\"] value in DataFumbler.toml.")
            return
        return {
            "data":www/"data",
            "scripts":www/"js",
            "tl_root": tl_folder,
            "patch": patch,
            "export":exports
        }
    elif game_type == "MZ":
        data_folder = game_exec.resolve().parent / "data"
        scripts_folder = game_exec.resolve().parent / "js"
        
        if not (data_folder).exists():
            logging.error("missing `www` folder in game directory!")
            logging.error("Are you sure it is a MV game?")
            logging.error("If expecting a MV game (data folder in root folder with game.exe)")
            logging.error("Set [type = \"MV\"] value in DataFumbler.toml.")
            return
        return {
            "data":data_folder,
            "scripts":scripts_folder,
            "tl_root": tl_folder,
            "patch": patch,
            "export":exports
        }
    else:
        logging.error(f"Unknown game type: {game_type}")
        return

def extract(folders:typing.Dict[str, pathlib.Path], config_dict):
    for json_file in folders["data"].rglob("*.json"):
        rel = json_file.relative_to(folders["data"])
        tl_folder = folders["tl_root"] / "data"
        
        cls = resolve_file(json_file, config_dict)
        if cls:
            if (tl_folder / rel).exists():
                logger.info(f"Dumping: {rel.name}")
                try:
                    maps = cls.export_map(tl_folder / rel)
                except NotImplementedError:
                    print("[TODO]",rel.name)
                    continue
                if maps:
                    if (folders["export"] / rel).with_suffix(".nt.txt").exists():
                        continue
                    (folders["export"] / rel).parent.mkdir(exist_ok=True,parents=True)
                    (folders["export"] / rel).with_suffix(".nt.txt").write_text(maps, encoding="utf-8")
                

def create_maps(folders:typing.Dict[str, pathlib.Path], config_dict):
    for json_file in folders["data"].rglob("*.json"):
        rel = json_file.relative_to(folders["data"])
        tl_folder = folders["tl_root"] / "data"
        (tl_folder / rel).parent.mkdir(parents=True, exist_ok=True)
        cls = resolve_file(json_file, config_dict)
        if cls:
            if (tl_folder / rel).exists() and not config_dict["General"]["replace"]:
                pass
                # logger.info(f"Skip dump for: {rel.name}")
            else:
                logger.info(f"Dumping: {rel.name}")
                cls.create_maps(tl_folder / rel)
    for script_file in folders["scripts"].rglob("*.js"):
        rel = script_file.relative_to(folders["scripts"])
        tl_folder = folders["tl_root"] / "script"
        (tl_folder / rel).parent.mkdir(parents=True, exist_ok=True)
        if not (tl_folder / rel).exists() and not config_dict["General"]["replace_scripts"]:
            logger.info(f"Dumping: {rel.name}")
            shutil.copy(script_file, tl_folder / rel)
    # Marking folder / I hope someone doesn't delete this...
    (folders["tl_root"] / ".TLPROJECT").touch()

def patch(game_exec:pathlib.Path, folders:typing.Dict[str, pathlib.Path], config_dict):
    for file in game_exec.iterdir():
        if file.is_dir() and (file.name == project_folder_name or (file/ ".TLPROJECT").exists()):
            folders["to_root"] = file
            folders["patched"] = file / "patched"
            continue
        # if file.is_dir()
    for file in game_exec.iterdir():
        if file.is_dir() and file != folders["to_root"]:
            if file == folders["scripts"]:
                continue
            print(f"Copy folder: {file.name}")
            shutil.copytree(file, folders["patched"] / file.name, dirs_exist_ok=True)
        elif file.is_file():
            print(f"Copy file: {file.name}")
            shutil.copy(file, folders["patched"] / file.name)