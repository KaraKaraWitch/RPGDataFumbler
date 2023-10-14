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

from ctypes import resize
import enum
import pathlib
import orjson
import typer


class LanguageModel:

    def __init__(self, **kwargs) -> None:
        pass

    def batch_translate(self, text:list):
        """Runs a batch translation over a list of text.

        Args:
            text (list): A list of strings to be translated.

        Raises:
            NotImplementedError: The class does not support batch_translate as a function.
        """
        raise NotImplementedError()

    def translate(self, text:str):
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
            raise NotImplementedError(f"Google Translation requires translatepy package to be installed. run: `pip install translatepy` if on windows.")
        self.translator = GoogleTranslate()
    def batch_translate(self, text: list):
        print(f"[DF|GTrans] Translating: {len(text)}")
        lines = "\n".join(text)
        translated = self.translator.translate(lines, "English")
        txt_result= translated.result
        
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
        self.translated_data = orjson.loads(pathlib.Path(kwargs["manualTransFile"]).read_bytes())
        self.per_line = kwargs.get("per_line",True)
        
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
        composite_result = self.translated_data.get(composite,composite)
        if self.per_line:
            # For some MTool translators, it does not like new lines. 
            for line in text:
                results.append(self.translated_data.get(line,line))
        else:
            return composite_result
        return results

    def translate(self, text):
        return self.translated_data.get(text,text)

app = typer.Typer()

class Services(enum.Enum):

    GOOGLE = Googled
    MTOOL = MToolMapped

@app.command(name="translate")
def do_translate(game_executable:pathlib.Path, service:Services):
