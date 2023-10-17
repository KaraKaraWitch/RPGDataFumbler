
import pathlib
import typing


class AutoTranslator:

    def translate_events(self, nested_text:dict) -> dict:
        raise NotImplementedError()
    
    def translate_exports(self, exports:typing.Union[typing.List[pathlib.Path], typing.Generator[pathlib.Path,None,None]],events:bool, weapons:bool,armor:bool,items:bool,actors:bool):