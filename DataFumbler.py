# =================================================== #
# DataFumbler: RPGMakerMV localization python scripts
# Built for Gehenna but works for MV related games.
# =================================================== #

import pathlib
import typing
import typer
import tomli
import json
import logging

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger("DF|Cmmd")

# from DataFumblerUtils import get_folders, extract


app = typer.Typer()

from RPGMVZ import MVZHandler

project_folder_name = "tl_workspace"


@app.command(name="map")
def mapping(
    game_exec: pathlib.Path,
    config: typing.Optional[pathlib.Path] = None,
    overwrite: bool = False,
):

    if not game_exec.is_file() or not game_exec.suffix.endswith(".exe"):
        raise FileNotFoundError("Expecting a game executable.")

    if config:
        try:
            config_dict = tomli.loads(config.read_text(encoding="utf-8"))
        except tomli.TOMLDecodeError:
            raise Exception("Config Read Error. Decode Error.")
    else:
        config = game_exec.resolve().parent / "DataFumbler.toml"
        if not config.exists():
            raise Exception("Config Read Error. Config not found.")
        try:
            config_dict = tomli.loads(config.read_text(encoding="utf-8"))
        except tomli.TOMLDecodeError:
            raise Exception("Config Read Error. Decode Error.")
    MVZHandler(game_exec, config_dict).create_maps(replace=overwrite)


@app.command(name="export")
def export_data(
    game_exec: pathlib.Path,
    config: typing.Optional[pathlib.Path] = None,
    overwrite: bool = False,
):

    if not game_exec.is_file() or not game_exec.suffix.endswith(".exe"):
        raise FileNotFoundError("Expecting a game executable.")

    if config:
        try:
            config_dict = tomli.loads(config.read_text(encoding="utf-8"))
        except tomli.TOMLDecodeError:
            raise Exception("Config Read Error. Decode Error.")
    else:
        config = game_exec.resolve().parent / "DataFumbler.toml"
        if not config.exists():
            raise Exception("Config Read Error. Config not found.")
        try:
            config_dict = tomli.loads(config.read_text(encoding="utf-8"))
        except tomli.TOMLDecodeError:
            raise Exception("Config Read Error. Decode Error.")
    MVZHandler(game_exec, config_dict).export(replace=overwrite)


@app.command(name="apply")
def apply_data(
    data: pathlib.Path,
    config: typing.Optional[pathlib.Path] = None,
):
    if not data.is_file() or not data.suffix.endswith(".exe"):
        raise FileNotFoundError("Expecting a game executable.")

    www = data.resolve().parent / "www"
    tl_folder = data.resolve().parent / "trans"
    apply_folder = data.resolve().parent / "apply"
    if not (www).exists():
        raise FileNotFoundError("missing `www` folder in game directory!")
    if config:
        try:
            config_dict = tomli.loads(config.read_text(encoding="utf-8"))
        except tomli.TOMLDecodeError:
            raise Exception("Config Read Error. Decode Error.")
    else:
        config = data.resolve().parent / "DataFumbler.toml"
        if not config.exists():
            raise Exception("Config Read Error. Config not found.")
        try:
            config_dict = tomli.loads(config.read_text(encoding="utf-8"))
        except tomli.TOMLDecodeError:
            raise Exception("Config Read Error. Decode Error.")
    # Parse JSON files.
    for json_file in www.rglob("*.json"):
        # Solve for data/*.json
        # print(json_file.parent.name)
        if not json_file.parent.name == "data":
            continue
        rel = json_file.relative_to(www)
        # print(rel)
        cls = resolve_file(json_file, config_dict)
        if cls:
            if (tl_folder / rel).exists():
                (apply_folder / rel).parent.mkdir(parents=True, exist_ok=True)
                print(f"[Apply] {(tl_folder / rel)}")
                try:
                    # For some reason, saving it as unscaled unicode can cause images to not load?
                    (apply_folder / rel).write_bytes(
                        json.dumps(cls.apply_maps(tl_folder / rel)).encode(
                            encoding="utf-8"
                        )
                    )
                except NotImplementedError:
                    print(f"[TODO]: {rel.name}")


if __name__ == "__main__":
    app()
