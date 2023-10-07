# =================================================== #
# DataFumbler: RPGMakerMV localization python scripts
# Built for Gehenna but works for MV related games.
# =================================================== #

import pathlib
import shutil
import typing
import orjson
import typer
import tomli

app = typer.Typer()

from DataFumblerMV import resolve_file


@app.command(name="map")
def mapping(data: pathlib.Path, config: typing.Optional[pathlib.Path] = None):
    if not data.is_file() or not data.suffix.endswith(".exe"):
        raise FileNotFoundError("Expecting a game executable.")

    www = data.resolve().parent / "www"
    tl_folder = data.resolve().parent / "trans"
    if not (www).exists():
        raise FileNotFoundError("missing `www` folder in game directory!")
    if config:
        try:
            config_dict = tomli.loads(config.read_text(encoding="utf-8"))
        except tomli.TOMLDecodeError:
            raise Exception("Config Read Error. Decode Error.")
    else:
        config = (data.resolve().parent / "DataFumbler.toml")
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
        (tl_folder / rel).parent.mkdir(parents=True, exist_ok=True)
        cls = resolve_file(json_file, config_dict)
        if cls:
            if (tl_folder / rel).exists() and not config_dict["General"]["replace"]:
                print("[SkipDump]", rel.name)
            else:
                print("[Dump]", rel.name)
                cls.create_maps(tl_folder / rel)
    # Copy JS files.
    for js_file in www.rglob("*.js"):
        rel = js_file.relative_to(www)
        # print(rel)
        (tl_folder / rel).parent.mkdir(parents=True, exist_ok=True)
        if (tl_folder / rel).exists() and not config_dict["General"]["replace"]:
            print("[SkipDump]", rel.name)
        else:
            shutil.copy(js_file, (tl_folder / rel))
            print("[Copy]", rel.name)

@app.command(name="export")
def export_data(data: pathlib.Path, format:str="markdown", config: typing.Optional[pathlib.Path] = None):
    if not data.is_file() or not data.suffix.endswith(".exe"):
        raise FileNotFoundError("Expecting a game executable.")

    www = data.resolve().parent / "www"
    tl_folder = data.resolve().parent / "trans"
    export_folder = data.resolve().parent / "export"

    if config:
        try:
            config_dict = tomli.loads(config.read_text(encoding="utf-8"))
        except tomli.TOMLDecodeError:
            raise Exception("Config Read Error. Decode Error.")
    else:
        config = (data.resolve().parent / "DataFumbler.toml")
        if not config.exists():
            raise Exception("Config Read Error. Config not found.")
        try:
            config_dict = tomli.loads(config.read_text(encoding="utf-8"))
        except tomli.TOMLDecodeError:
            raise Exception("Config Read Error. Decode Error.")

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
                (export_folder / rel).parent.mkdir(parents=True, exist_ok=True)
                try:
                    (export_folder / rel).write_text(cls.export_maps(tl_folder / rel), encoding="utf-8")
                except NotImplementedError:
                    print(f"[TODO]: {rel.name}")

@app.command(name="convert")
def conv_data(data: pathlib.Path, file: pathlib.Path):
    if file.is_file() and "ManualTransFile" in file.name:
        print("Apply file seems to be")


@app.command(name="apply")
def apply_data(data: pathlib.Path, config: typing.Optional[pathlib.Path] = None):
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
        config = (data.resolve().parent / "DataFumbler.toml")
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
                    (apply_folder / rel).write_bytes(orjson.dumps(cls.apply_maps(tl_folder / rel)))
                except NotImplementedError:
                    print(f"[TODO]: {rel.name}")



if __name__ == "__main__":
    app()
