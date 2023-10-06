# =================================================== #
# DataFumbler: RPGMakerMV localization python script
# Built for Gehenna but works for MV related games.
# The "Automated Translation" bit for DataFumbler.
# =================================================== #
# Personal Opinion: OpenAI or LLM based translations
# may not be accurate while stricter translators like
# DeepL or Google Translate may be a bit too stiff
# It's recommended that translators play the game to
# check on the translations.
# =================================================== #

class LanguageModel:

    def __init__(self) -> None:
        pass

    async def batch_translate(self, text:list):
        raise NotImplementedError()

    async def translate(self, text):
        raise NotImplementedError()
    
class Googled:
    pass