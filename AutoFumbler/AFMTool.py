import pathlib
import re
import typing

import orjson
from .AFCore import AutoTranslator

class MToolTranslator2(AutoTranslator):
    
    def __init__(self, manualTransFile:pathlib.Path,config:dict) -> None:
        self.translated_data = orjson.loads(
            pathlib.Path(manualTransFile).read_bytes()
        )
        self.config = config
        self.undesire_check = config["MTool"].get("skip_undesirables", True)

    jp_rgx = re.compile(r"[一-龠]+|[ぁ-ゔ]+|[ァ-ヴー]+", flags=re.UNICODE)

    def desired_translation(self, orig:str, translated:str):
        if not self.undesire_check:
            return True
        
        if not self.jp_rgx.search(orig):
            return False
        braces_in = orig.count("「")
        braces_out = orig.count("」")
        if (braces_in != braces_out) and braces_in > 0:
            return False
        
        if orig.count("。") > 1:
            # print("Puncts 1")
            return False
        # Collapse punctuations to singular characters.
        collapesed = (
            orig.replace("！", "*")
            .replace("？", "*")
            .replace("。", "*")
        )
        punct_exclaims = [i for i in collapesed.split("*") if i]
        if len(punct_exclaims) > 1:
            # print("Puncts 2")
            return False
        # Skip same text.
        if orig == translated:
            # print("Orgline same as TL")
            return False

        # Check for translation length, if it is too short, it doesn't get replaced.
        if len(translated) < len(orig) * 1.5:
            # It's probably worth keeping very short lines.
            if not len(orig) < 10:
                return True
            return False
        return True
        


    def translate_actors(self, names: typing.Dict[typing.List[str]]) -> typing.Dict[int, typing.List[str]]:
        for actor_idx, actor_data in names.items():
            name, profile, nick = actor_data
            repacked = [
                self.translated_data.get(name,name),
                self.translated_data.get(profile,profile),
                self.translated_data.get(nick,nick),
                ]
            for idx, value in enumerate(repacked):
                if not self.desired_translation(actor_data[idx], value):
                    repacked[idx] = actor_data[idx]
            names[actor_idx] = repacked
        return names
    
    def translate_events(self, events: typing.Dict[str, typing.List[str]]) -> typing.Dict[str, typing.List[str]]:
        for event in 