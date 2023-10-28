import pathlib
import typing

import nestedtext
import rich
from .AFCore import AutoTranslator
import httpx

try:
    import ctranslate2
    import huggingface_hub
except ImportError as e:
    ctranslate2 = None
    huggingface_hub = None

class OobaModel(AutoTranslator):


    def __init__(self, prompt_config:dict) -> None:
        self.prompt:dict = prompt_config

    def translate_events(self, nested_text:dict) -> dict:
        def chunks(lst, n):
            for i in range(0, len(lst), n):
                yield lst[i:i + n]
        session = httpx.Client()
        final = {}
        for event_id, dialogues in nested_text.items():
            t_buffer = ""
            for c_dialogues in chunks(dialogues, 5):
                diags_concat = "\n\n".join(c_dialogues)
                if not diags_concat.strip():
                    continue
                dc = self.prompt["events"].replace("{dialogues}",diags_concat)
                request = {
                    'prompt': dc,
                    'max_new_tokens': 1024,
                    'auto_max_new_tokens': True,
                    'preset': 'None',
                    'do_sample': True,
                    'temperature': self.prompt.get("temp", 0.2),
                    'top_p': self.prompt.get("top_p", 0.2),
                    'top_k': self.prompt.get("top_k", 0.2),
                    'repetition_penalty': 1.0,
                    'repetition_penalty_range': 1024,
                    'seed': -1,
                    'add_bos_token': True,
                    'mirostat_mode': 2,
                    'mirostat_tau': 5,
                    'mirostat_eta': 0.1,
                    'stopping_strings': ["</s>"]
                }
                rich.print(request)
                # print(dc)
                session_url = self.prompt["ooba_url"]
                r = session.post(session_url, json=request, timeout=None)
                print(dc + r.json()["results"][0]["text"])
                t_buffer += dc + r.json()["results"][0]["text"] + "---\n"
            final[str(event_id)] = t_buffer
        return final
            

            
    
    def translate_exports(self, exports:typing.Union[typing.List[pathlib.Path], typing.Generator[pathlib.Path,None,None]],events:bool, weapons:bool,armor:bool,items:bool,actors:bool):
        
        for export in exports:
            export_name = export.name.lower()
            print(export_name)
            if "map" in export_name:
                
                if not export.is_file():
                    continue
                map_data = nestedtext.loads(export.read_text(encoding="utf-8"))
                compact_dialogue = {}
                for event_id, event_lines in map_data.items():
                    dialogues = []
                    buffer = ""
                    for line in event_lines:
                        if line == "<>":
                            dialogues.append(buffer.strip())
                            buffer = ""
                        else:
                            buffer += line + "\n"
                    compact_dialogue[int(event_id)] = dialogues
                translated = self.translate_events(compact_dialogue)
                export.with_suffix(".OOBA.nt.txt").write_text(nestedtext.dumps(translated),encoding="utf-8")
                # break