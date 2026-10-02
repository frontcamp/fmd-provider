'''Utilities for normalizing exchange trade records.'''

import sys
from abc import ABC, abstractmethod

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

__app__ = 'normalizer'
__version__ = '0.1.0'
__author__ = 'Maksym Plaksin <maxim.plaksin@gmail.com>'

_INTRO = f'''{__app__} {__version__} - Financial market data normalizer.
Copyright (C) 2026 {__author__}'''


class CustomNormalizer(ABC):

    def __init__(self):
        print(_INTRO)

        self._source_dir: str = self._get_script_dir()

        print(f'_source_dir: "{self._source_dir}"')

    @abstractmethod
    def _get_script_dir(self) -> str:
        pass

    def process(self):
        pass

