'''Utilities for normalizing exchange trade records.'''

import io
import sys
from abc import ABC, abstractmethod

# Set UTF-8 encoding for stdout
if isinstance(sys.stdout, io.TextIOWrapper):
    sys.stdout.reconfigure(encoding="utf-8")

# Set UTF-8 encoding for stderr
if isinstance(sys.stderr, io.TextIOWrapper):
    sys.stderr.reconfigure(encoding="utf-8")

_APP_NAME = 'normalizer'
_APP_VERSION = '0.1.0'
_APP_TITLE = 'Financial market data normalizer'
_APP_COPYRIGHT = 'Copyright (C) 2026 Maksym Plaksin'

_APP_INTRO = f'''{_APP_NAME} {_APP_VERSION}
{_APP_TITLE}
{_APP_COPYRIGHT}'''


class CustomNormalizer(ABC):

    def __init__(self):
        print(_APP_INTRO)

        self._source_dir: str = self._get_script_dir()

        print(f'{self._source_dir = }')

    @abstractmethod
    def _get_script_dir(self) -> str:
        pass

    def process(self):
        pass

