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
    config: typing.Optional[pathlib.Path] = None,
    bypass_multiline: bool = False,
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
    tl_events = events
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

    handler = MVZHandler(game_exec, config_dict)
    mantransfile = game_exec.parent / "ManualTransFile.json"
    if not mantransfile.exists():
        print(f"Unable to find ManualTransFile.json @ {mantransfile}")
        return
    translator_instance = MToolMapped(manualTransFile=mantransfile)
    

    # translator_instance:LanguageModel = getattr(ServicesMapping, service.name).value()
    # print(list())
    # terminals = "？！"
    for file in handler.export_files:
        if not file.exists():
            continue
        fn = file.name.lower()
        if "map" in fn or "commonevents" in fn:
            if tl_events:
                print(f"Translating: {file.name}")
                try:
                    map_events: typing.Dict[str, typing.List[str]] = nestedtext.loads(
                        file.read_text(encoding="utf-8")
                    )
                except nestedtext.NestedTextError as e:
                    print(f"[NestedTextError]: {e}")
                    continue
                file.write_text(nestedtext.dumps(map_events), encoding="utf-8")


@app.command("Google")
def google_translator(
    game_exec: pathlib.Path,
    service: Services,
    config: typing.Optional[pathlib.Path] = None,
):
    


if __name__ == "__main__":
    app()
