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


def ensure_dir(dir_path):
    '''Ensure that the path's directories are exists, create them otherwise.'''
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)


class CustomNormalizer(ABC):

    def __init__(self):
        print(_APP_INTRO)

        # initialize source & destination folders
        self._source_dir: str = self._get_script_dir()
        self._normalized_dir: str = self._get_normalized_dir(self._source_dir)
        ensure_dir(self._normalized_dir)

        # initialize data buffers
        self._buff_trans: list = []
        self._buff_log: list = []

        print(f'Source location: {self._source_dir}')

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

    def _reset_buffers(self):
        self._buff_trans = []
        self._buff_log = []

    #
    # Abstract methods

    @abstractmethod
    def _get_script_dir(self) -> str:
        pass

    @abstractmethod
    def _get_yyyymmdd(self, filename) -> bool|str:
        pass

    @abstractmethod
    def _process_line(self, line: str) -> bool:
        pass

    #
    # Process methods

    def _process_file(self, file_name: str) -> None:

        # define source file path
        file_path = os.path.join(self._source_dir, file_name)
        if not os.path.isfile(file_path):
            return

        # define source date
        proc_date = self._get_yyyymmdd(file_name)
        if not isinstance(proc_date, str):  # check type
            return

        #define destination files
        log_root = os.path.join(self._normalized_dir, proc_date + '.log')
        archive_root = os.path.join(self._normalized_dir, proc_date + '.zip')

        # TODO: check if resulting file already exists - then return from function

        # show what's going on..
        print('-' * 20)
        print(f'File: {file_name}; date: {proc_date}')

        with ExitStack() as stack:

            # read data
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

            # parse data lines
            self._reset_buffers()
            for line in text_file:
                if not self._process_line(line):
                    self._buff_log.append(f'Undefined: {line.rstrip('\r\n')}')

            # save log (if non empty)
            if len(self._buff_log):
                # TODO: delete old log if it exists before write new
                with open(log_root, 'w', encoding='utf-8', newline='') as file:
                    file.write('\r\n'.join(self._buff_log))

            # compile transactions
            transactions = ''

            # compile instruments
            instruments = ''

            # save transactions & instruments to zip archive
            with zipfile.ZipFile(
                archive_root,
                mode='w',
                compression=zipfile.ZIP_DEFLATED,
                compresslevel=9,
            ) as archive:
                archive.writestr('transactions.csv', transactions)
                archive.writestr('instruments.csv', instruments)

            # TODO: remove source file if all successfully done

            # show results
            report = f'Transactions: {len(self._buff_trans)}; ' \
                   + f'instruments: {instruments.strip().count('\n')}; ' \
                   + f'undefined: {len(self._buff_log)}'
            print(report)

    def process(self) -> None:
        file_names = os.listdir(self._source_dir)

        file_names = list(filter(self._get_yyyymmdd, file_names))
        file_names.sort(key=self._get_yyyymmdd)

        for file_name in file_names:
            self._process_file(file_name)

