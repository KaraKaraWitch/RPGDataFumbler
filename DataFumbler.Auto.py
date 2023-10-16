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


class LanguageModel:
    def __init__(self, **kwargs) -> None:
        pass

    def batch_translate(self, text: list):
        """Runs a batch translation over a list of text.

        Args:
            text (list): A list of strings to be translated.

        Raises:
            NotImplementedError: The class does not support batch_translate as a function.
        """
        raise NotImplementedError()

    def translate(self, text: str):
        """Runs a translation over text.

        Args:
            text (str): A string to be translated.

        Raises:
            NotImplementedError: The class does not support batch_translate as a function.
        """
        raise NotImplementedError()

    def configure(self, **kwargs):
        raise NotImplementedError()


class Googled(LanguageModel):
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


class OpenAI(LanguageModel):
    pass


class MToolMapped(LanguageModel):
    def __init__(self, **kwargs) -> None:
        self.translated_data = orjson.loads(
            pathlib.Path(kwargs["manualTransFile"]).read_bytes()
        )
        self.per_line = kwargs.get("per_line", True)

    def batch_translate(self, text: list):
        """Runs a batch translation over a list of text.

        MTool sometimes translates

        Args:
            text (list): A list of strings to be translated.

        Raises:
            NotImplementedError: The class does not support batch_translate as a function.
        """
        results = []
        composite = "\n".join(text)
        composite_result = self.translated_data.get(composite, composite)
        if self.per_line:
            # For some MTool translators, it does not like new lines.
            for line in text:
                results.append(self.translated_data.get(line, line))
        else:
            return composite_result
        return results

    def translate(self, text):
        return self.translated_data.get(text, text)


app = typer.Typer()


class Services(enum.Enum):

    GOOGLE = "Google"
    MTOOL = "MTool"


class ServicesMapping(enum.Enum):

    GOOGLE = Googled
    MTOOL = MToolMapped


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
    jp_rgx = re.compile(r"[一-龠]+|[ぁ-ゔ]+|[ァ-ヴー]+", flags=re.UNICODE)

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
                for key, event_data in map_events.items():
                    for idx, orig_line in enumerate(event_data):

                        # skip empty lines
                        if orig_line == "<>":
                            continue
                        if not orig_line:
                            continue
                        # Skip Non-Japanese lines.
                        if not jp_rgx.search(orig_line):
                            # print("JPRGX", orig_line)
                            continue
                        print(idx, orig_line)
                        # Check for MTool undesirables.

                        # Check if quotes are wrapped.
                        braces_in = orig_line.count("「")
                        braces_out = orig_line.count("」")
                        if (braces_in != braces_out) and braces_in > 0:
                            print("Braces")
                            continue

                        # Skip lines with varying punctuations.
                        # MTool seems to dislike it.

                        if orig_line.count("。") > 1:
                            # print("Puncts 1")
                            continue
                        # Exclaimation
                        collapesed = (
                            orig_line.replace("！", "*")
                            .replace("？", "*")
                            .replace("。", "*")
                        )
                        punct_exclaims = [i for i in collapesed.split("*") if i]
                        if len(punct_exclaims) > 1:
                            # print("Puncts 2")
                            continue

                        # Get the translation
                        translated = translator_instance.translate(orig_line)
                        # Skip same text.
                        if orig_line == translated:
                            # print("Orgline same as TL")
                            continue

                        # Check for translation length, if it is too short, it doesn't get replaced.
                        if len(translated) < len(orig_line) * 1.5:
                            if not len(orig_line) < 10:
                                continue
                                # It's probably worth keeping

                            # print("SizeScaling")
                            # continue
                        # print(event_data[idx], translated, orig_line)
                        event_data[idx] = translated
                    map_events[key] = event_data
                file.write_text(nestedtext.dumps(map_events), encoding="utf-8")


@app.command("Google")
def do_translate(
    game_exec: pathlib.Path,
    service: Services,
    config: typing.Optional[pathlib.Path] = None,
):
    pass


if __name__ == "__main__":
    app()
