import json
import os
import pathlib
from typing import Any


class TranslationError(RuntimeError):
    pass


class Messages:
    lang = None
    messages = None

    def __init__(self, path_to_messages, lang='en'):
        assert os.path.isfile(path_to_messages)
        self._data = json.load(open(path_to_messages))
        self.set_lang(lang)

    def set_lang(self, lang):
        if lang not in self._data.keys():
            raise TranslationError(f"Language `{lang}` not found, available: {list(self._data.keys())}")
        self.lang = lang
        self.messages = self._data[self.lang]
    
    def __getattribute__(self, __name: str) -> Any:
        try:
            mes = self.messages[__name]
        except Exception as e:
            mes = super().__getattribute__(__name)
        return mes


translations = Messages(pathlib.Path(__file__).parent / 'translations.json', 'en')
