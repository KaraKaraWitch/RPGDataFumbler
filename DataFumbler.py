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


@app.command(name="import")
def import_data(
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
    MVZHandler(game_exec, config_dict).import_maps()


@app.command(name="patch")
def patch_data(
    game_exec: pathlib.Path,
    config: typing.Optional[pathlib.Path] = None,
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
    MVZHandler(game_exec, config_dict).patch()


if __name__ == "__main__":
    app()
