import pathlib
import re
import typing

import orjson
class MToolInstance:
    def __init__(self, manualTransFile:pathlib.Path,per_line:bool=True) -> None:
        self.translated_data = orjson.loads(
            pathlib.Path(manualTransFile).read_bytes()
        )
        self.per_line = per_line

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

class MToolTranslator:

    jp_rgx = re.compile(r"[一-龠]+|[ぁ-ゔ]+|[ァ-ヴー]+", flags=re.UNICODE)

    def __init__(self, mtool:pathlib.Path):
        self.mtool_file = mtool
        self.instance = MToolInstance(manualTransFile=self.mtool_file)
    def translate_events(self, nested_text:dict):
        for key, event_data in nested_text.items():
            for idx, orig_line in enumerate(event_data):
                # skip empty lines
                if orig_line == "<>":
                    continue
                if not orig_line:
                    continue
                # Skip Non-Japanese lines.
                if not self.jp_rgx.search(orig_line):
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
                # Collapse punctuations to singular characters.
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
                translated = self.instance.translate(orig_line)
                # Skip same text.
                if orig_line == translated:
                    # print("Orgline same as TL")
                    continue

                # Check for translation length, if it is too short, it doesn't get replaced.
                if len(translated) < len(orig_line) * 1.5:
                    # It's probably worth keeping very short lines.
                    if not len(orig_line) < 10:
                        continue
                event_data[idx] = translated
            nested_text[key] = event_data
        return nested_text
    
    def translate_exports(self, exports:typing.Union[typing.List[pathlib.Path], typing.Generator[pathlib.Path,None,None]],events:bool, weapons:bool,armor:bool,items:bool,actors:bool):
        for file in exports:
            if not file.exists():
                continue
            filename = file.name.lower()
            if ("map" in filename or "commonevents" in filename) and events: