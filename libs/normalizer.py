'''Utilities for normalizing exchange trade records.'''

import gzip
import io
import os
import sys
import zipfile
from abc import ABC, abstractmethod
from contextlib import ExitStack

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
        self._normalized_dir: str = self._get_normalized_dir(self._source_dir)

        print(f'{self._source_dir = }')

    #
    # Common methods

    def _get_normalized_dir(self, source_dir: str) -> str:
        search_path = source_dir.replace('\\', '/')
        index = search_path.find('/sources/')
        if index == -1:
            raise ValueError('Source path does not contain a sources directory')

        return source_dir[:index + 1] \
             + 'normalized' \
             + source_dir[index + 8:]

    #
    # Abstract methods

    @abstractmethod
    def _get_script_dir(self) -> str:
        pass

    @abstractmethod
    def _process_line(self, line: str) -> dict | None:
        pass

    #
    # Process methods

    def _process_file(self, file_name: str) -> None:
        file_path = os.path.join(self._source_dir, file_name)

        if not os.path.isfile(file_path):
            return

        print(f'Process file: {file_path}')

        with ExitStack() as stack:
            if file_name.lower().endswith('.zip'):
                archive = stack.enter_context(zipfile.ZipFile(file_path))
                member = next(
                    member for member in archive.infolist()
                    if not member.is_dir()
                )
                text_file = stack.enter_context(
                    io.TextIOWrapper(archive.open(member), encoding='utf-8')
                )
            elif file_name.lower().endswith('.gz'):
                text_file = stack.enter_context(
                    gzip.open(file_path, 'rt', encoding='utf-8')
                )
            else:
                text_file = stack.enter_context(
                    open(file_path, 'rt', encoding='utf-8')
                )

            count = 0
            for line in text_file:
                count += 1
                if count <= 5:
                    self._process_line(line)

    def process(self) -> None:
        file_names = os.listdir(self._source_dir)

        file_names.sort()

        for file_name in file_names:
            if file_name in ('normalize.py', '.', '..'):
                continue

            file_path = os.path.join(self._source_dir, file_name)
            if not os.path.isfile(file_path):
                continue

            self._process_file(file_name)

