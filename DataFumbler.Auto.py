# =================================================== #
# DataFumbler: RPGMakerMV localization python script
# Built for Gehenna but works for MV related games.
# The "Automated Translation" bit for DataFumbler.
# =================================================== #
# Personal Opinion: OpenAI or LLM based translations
# may not be accurate while stricter translators like
# DeepL or Google Translate may be a bit too stiff.
# It's recommended that translators play the game to
# check on the translations.
# =================================================== #
# Script Requirements:
# translatepy
# =================================================== #

import enum
import pathlib
import re
import typing
import orjson
import typer
import tomli
import nestedtext
from RPGMVZ import MVZHandler
from AutoFumbler import AFMTool





class Googled:
    def __init__(self, **kwargs) -> None:
        try:
            from translatepy.translators.google import GoogleTranslate
        except ImportError:
            raise NotImplementedError(
                f"Google Translation requires translatepy package to be installed. run: `pip install translatepy` if on windows."
            )
        self.translator = GoogleTranslate()

    def batch_translate(self, text: list):
        print(f"[DF|GTrans] Translating: {len(text)}")
        lines = "\n".join(text)
        translated = self.translator.translate(lines, "English")
        txt_result = translated.result

        if len(text) != len(txt_result.split("\n")):
            # Try translate each line on it's own as fallback.
            results = []
            for line in text:
                results.append(self.translate(line))
        else:
            results = [i.strip() for i in txt_result.split("\n")]
        return results

    def translate(self, text: str):
        translated = self.translator.translate(text, "English")
        return translated.result.strip()
        # return super().translate(text)








app = typer.Typer()

@app.command(name="MTool")
def mtool_translate(
    game_exec: pathlib.Path,
    events: bool = True,
    weapons: bool = True,
    armor: bool = True,
    items: bool = True,
    actors: bool = True,
):
    typer.secho(
        '[NOTE] This command will only pull translations that are "Complete".', fg="red"
    )
    typer.secho(
        '"Complete". Essentially meaning that it will not attempt to pull MTool multi-line translations.',
        fg="red",
    )
    typer.secho(
        "Use the flag: --bypass-multiline to disable detection for multiline sectiion",
        fg="red",
    )
    if not game_exec.is_file() or not game_exec.suffix.endswith(".exe"):
        raise FileNotFoundError("Expecting a game executable.")

    config = game_exec.resolve().parent / "DataFumbler.toml"
    if not config.exists():
        raise Exception("Config Read Error. Config not found.")
    try:
        config_dict = tomli.loads(config.read_text(encoding="utf-8"))
    except tomli.TOMLDecodeError:
        raise Exception("Config Read Error. Decode Error.")

    handler = MVZHandler(game_exec, config_dict)
    mantransfile = game_exec.parent / "ManualTransFile.json"
    if not mantransfile.exists():
        print(f"Unable to find ManualTransFile.json @ {mantransfile}")
        return
    
    from .AutoFumbler.AFMTool import MToolTranslator

    instance = MToolTranslator(mantransfile)
    instance.translate_exports(handler.export_files,events, weapons, armor, items, actors)


@app.command("Ooba")
def Ooba_translator(
    game_exec: pathlib.Path,
    events: bool = True,
    weapons: bool = True,
    armor: bool = True,
    items: bool = True,
    actors: bool = True,
):
    if not game_exec.is_file() or not game_exec.suffix.endswith(".exe"):
        raise FileNotFoundError("Expecting a game executable.")

    config = game_exec.resolve().parent / "DataFumbler.toml"
    config_auto = game_exec.resolve().parent / "DataFumblerAuto.toml"
    if not config.exists():
        raise Exception("Config Read Error. Config not found.")
    if not config_auto.exists():
        raise Exception("ooba needs a DataFumblerAuto.toml with a \"prompt\" written inside it.")
    try:
        config_dict = tomli.loads(config.read_text(encoding="utf-8"))
    except tomli.TOMLDecodeError:
        raise Exception("Config Read Error. Decode Error.")
    
    try:
        config_auto_dict = tomli.loads(config_auto.read_text(encoding="utf-8"))
    except tomli.TOMLDecodeError:
        raise Exception("ConfigAuto Read Error. Decode Error.")
    
    handler = MVZHandler(game_exec, config_dict)

    from AutoFumbler.AFooba import OobaModel

    if "Prompt" not in config_auto_dict or "events" not in config_auto_dict["Prompt"]:
        raise Exception("ConfigAuto Is missing either events or prompt file.")

    model = OobaModel(config_auto_dict["Prompt"]["events"])
    model.translate_exports(handler.export_files, events,weapons, armor, items, actors)



if __name__ == "__main__":
    app()
