import pathlib
import typing
from .AFCore import AutoTranslator
import httpx

try:
    import ctranslate2
    import huggingface_hub
except ImportError as e:
    ctranslate2 = None
    huggingface_hub = None

class CTranslate(AutoTranslator):
    
    models = {
        "sugoi-v4": [
            "https://huggingface.co/JustFrederik/sugoi-v4-ja-en-ct2-int8/resolve/main/config.json",
            "https://huggingface.co/JustFrederik/sugoi-v4-ja-en-ct2-int8/resolve/main/model.bin",
            "https://huggingface.co/JustFrederik/sugoi-v4-ja-en-ct2-int8/resolve/main/source_vocabulary.txt",
            "https://huggingface.co/JustFrederik/sugoi-v4-ja-en-ct2-int8/resolve/main/target_vocabulary.txt",
            "https://huggingface.co/JustFrederik/sugoi-v4-ja-en-ct2-int8/resolve/main/spm.en.nopretok.model",
            "https://huggingface.co/JustFrederik/sugoi-v4-ja-en-ct2-int8/resolve/main/spm.en.nopretok.vocab",
            "https://huggingface.co/JustFrederik/sugoi-v4-ja-en-ct2-int8/resolve/main/spm.ja.nopretok.model",
            "https://huggingface.co/JustFrederik/sugoi-v4-ja-en-ct2-int8/resolve/main/spm.ja.nopretok.vocab",
        ]
    }

    def download_models(self, root:pathlib.Path, model_urls:typing.List[str]):
        for url in model_urls:
            filepath = root / url.split("/")[-1]
            if not filepath.parent.is_dir():
                filepath.parent.mkdir(exist_ok=True, parents=True)
                session = httpx.Client()
                session.headers["user-agent"] = "Mozilla/5.0 (compatible; AutoFumberModelDownloader/1.0.0; +http://github.com/KaraKaraWitch/RPGDataFumbler)"

    def __init__(self, hugging_model) -> None:
        if not ctranslate2:
            raise ImportError("ctranslate package not found. Install ctranslate2 with `pip install ctranslate2`. ")
        
        if hugging_model == "sugoi-v4":
            model_path:pathlib.Path = pathlib.Path(__file__).resolve() / ".."  / pathlib.Path("models") / hugging_model
            model_path= model_path.resolve()
            if model_path.exists():
                fns = self.models["sugoi-v4"]
                fns = [i.split("/")[-1].lower() for i in fns]
                seens = []
                for file in model_path.iterdir():
                    if file.is_file():
                        seens.append(file.name.lower())
                # print(seens)
                needs = set(fns) - set(seens)
                print(needs)
                # print(f"Downloading file: {file}")
            else:
                model_path.mkdir(parents=True,exist_ok=True)
            self.instance = ctranslate2.Translator(model_path)

    def translate_text(self, text:str):



    def translate_events(self, nested_text: dict) -> dict:
        for event_idx, text_list in nested_text.items():
            text_sections = []
            section_buffer = []
            for text in text_list:
                if text == "<>":
                    text_sections.append(section_buffer)
                    section_buffer = []
                    continue
                section_buffer.append(text)
        # return super().translate_events(nested_text)
