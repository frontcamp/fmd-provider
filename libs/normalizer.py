'''Utilities for normalizing exchange trade records.'''

# File/folder role prefixes:
#   arc_* - archive
#   log_* - log
#   src_* - source

import csv
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


def ensure_dir(dir_abspath):
    '''Ensure that the path's directories are exists, create them otherwise.'''

    if not os.path.exists(dir_abspath):
        os.makedirs(dir_abspath)


class CustomNormalizer(ABC):

    def __init__(self):
        print(_APP_INTRO)

        # initialize source & destination folders
        self._src_dir_abspath: str = self._get_script_dir_abspath()
        self._normalized_dir_abspath: str = self._get_normalized_dir_abspath(self._src_dir_abspath)
        ensure_dir(self._normalized_dir_abspath)

        # initialize data buffers
        self._buff_trans: list = []
        self._buff_log: list = []

        print(f'Source location: {self._src_dir_abspath}')

    #
    # Common methods

    def _get_normalized_dir_abspath(self, src_dir_abspath: str) -> str:
        search_dir_abspath = src_dir_abspath.replace('\\', '/')
        index = search_dir_abspath.find('/sources/')
        if index == -1:
            raise ValueError('Source path does not contain a sources directory')

        return src_dir_abspath[:index + 1] \
             + 'normalized' \
             + src_dir_abspath[index + 8:]

    #
    # Abstract methods

    @abstractmethod
    def _get_script_dir_abspath(self) -> str:
        pass

    @abstractmethod
    def _get_yyyymmdd(self, src_file_name) -> bool|str:
        pass

    @abstractmethod
    def _process_line(self, line: str) -> bool:
        pass

    #
    # Process methods

    def _verify_zip(self, arc_file_abspath: str) -> bool:
        try:
            with zipfile.ZipFile(arc_file_abspath, 'r') as arc_file_obj:
                if set(arc_file_obj.namelist()) != {
                    'transactions.csv',
                    'instruments.csv',
                }:
                    raise zipfile.BadZipFile(f'Error: Invalid structure: {arc_file_abspath}')

                bad_file_name = arc_file_obj.testzip()
                if bad_file_name is not None:
                    raise zipfile.BadZipFile(f'Error: Corrupted file: {bad_file_name}')

        except Exception as exc:
            print(f'Error: The archive failed verification: {arc_file_abspath}: {exc}',
                  file=sys.stderr)
            os.remove(arc_file_abspath)
            return False
        return True

    def _reset_buffers(self):
        self._buff_trans = []
        self._buff_log = []

    def _parse_source(self, src_file_name, src_file_abspath):
        with ExitStack() as stack:

            # read data
            if src_file_name.lower().endswith('.zip'):
                src_arc_file_obj = stack.enter_context(zipfile.ZipFile(src_file_abspath))
                member = next(
                    member for member in src_arc_file_obj.infolist()
                    if not member.is_dir()
                )
                src_file_obj = stack.enter_context(
                    io.TextIOWrapper(src_arc_file_obj.open(member), encoding='utf-8')
                )
            elif src_file_name.lower().endswith('.gz'):
                src_file_obj = stack.enter_context(
                    gzip.open(src_file_abspath, 'rt', encoding='utf-8')
                )
            else:
                src_file_obj = stack.enter_context(
                    open(src_file_abspath, 'rt', encoding='utf-8')
                )

            # parse data lines
            self._reset_buffers()
            for line in src_file_obj:
                if not self._process_line(line):
                    self._buff_log.append(f'Undefined: {line.rstrip('\r\n')}')

    def _unload_log(self, log_file_abspath):

        # delete old log in any case
        if os.path.isfile(log_file_abspath):
            os.remove(log_file_abspath)

        # save log (if non empty)
        if len(self._buff_log):
            with open(log_file_abspath, 'w', encoding='utf-8', newline='') as log_file_obj:
                log_file_obj.write('\r\n'.join(self._buff_log))

    def _buff_trans_sort_by_time(self):
        '''Sort transactions by datetime'''

        self._buff_trans.sort(
            key=lambda transaction: (
                transaction['trade_time'][:19],
                transaction['trade_time'][20:].rstrip('Z').ljust(9, '0'),
            )
        )

    def _buff_trans_filter_by_date(self, date):
        '''Remove transactions out of processing date'''

        self._buff_trans = [
            transaction for transaction in self._buff_trans
            if transaction['trade_time'][:10].replace('-', '') == date
        ]

    def _compile_transactions(self) -> str:
        '''Compile transactions CSV'''

        temp_trans_file_obj = io.StringIO(newline='')
        writer = csv.DictWriter(
            temp_trans_file_obj,
            fieldnames=(
                'source', 'mic', 'isin', 'title', 'trade_time',
                'price', 'currency', 'quantity', 'quantity_unit',
            ),
            delimiter=';',
        )
        writer.writeheader()
        writer.writerows(self._buff_trans)
        return temp_trans_file_obj.getvalue()

    def _collect_instruments(self):
        instruments = []
        seen_isins = set()

        for transaction in self._buff_trans:
            isin = transaction['isin']
            if isin not in seen_isins:
                seen_isins.add(isin)
                instruments.append({
                    'isin': isin,
                    'title': transaction['title'],
                })

        instruments.sort(key=lambda record: record['isin'])
        return instruments

    def _compile_instruments(self, _buff_instr) -> str:
        temp_instr_file_obj = io.StringIO(newline='')
        writer = csv.DictWriter(
            temp_instr_file_obj,
            fieldnames=(
                'isin', 'title',
            ),
            delimiter=';',
        )
        writer.writeheader()
        writer.writerows(_buff_instr)
        return temp_instr_file_obj.getvalue()

    def _save_archive(self, arc_file_abspath, transactions, instruments):
        '''Save transactions & instruments to zip archive'''

        with zipfile.ZipFile(
            arc_file_abspath,
            mode='w',
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=9,
        ) as arc_file_obj:
            arc_file_obj.writestr('transactions.csv', transactions)
            arc_file_obj.writestr('instruments.csv', instruments)

    def _process_file(self, src_file_name: str) -> None:

        # define source file path
        src_file_abspath = os.path.join(self._src_dir_abspath, src_file_name)
        if not os.path.isfile(src_file_abspath):
            return

        # define source date
        proc_date = self._get_yyyymmdd(src_file_name)
        if not isinstance(proc_date, str):  # check type
            return

        #define destination files
        log_file_abspath = os.path.join(self._normalized_dir_abspath, proc_date + '.log')
        arc_file_abspath = os.path.join(self._normalized_dir_abspath, proc_date + '.zip')

        # show what's going on..
        print('-' * 20)
        print(f'File: {src_file_name}; date: {proc_date}')

        # if archive already exists..
        if os.path.isfile(arc_file_abspath):
            print(f'Already exists: {arc_file_abspath}')
            if self._verify_zip(arc_file_abspath) and not os.path.isfile(log_file_abspath):
                #os.remove(src_file_abspath)  # DELETING SOURCE!
                #print(f'Deleted: {src_file_name}')
                return

        self._parse_source(src_file_name, src_file_abspath)
        self._unload_log(log_file_abspath)

        self._buff_trans_sort_by_time()
        self._buff_trans_filter_by_date(proc_date)
        transactions = self._compile_transactions()

        _buff_instr = self._collect_instruments()
        instruments = self._compile_instruments(_buff_instr)

        self._save_archive(arc_file_abspath, transactions, instruments)

        # check if archive exists and valid, delete otherwise
        self._verify_zip(arc_file_abspath)

        # show results
        report = f'Transactions: {len(self._buff_trans)}; ' \
                + f'instruments: {len(_buff_instr)}; ' \
                + f'undefined: {len(self._buff_log)}'
        print(report)

        # if archive successfully created and log is empty..
        if os.path.isfile(arc_file_abspath) and not self._buff_log:
            #os.remove(src_file_abspath)  # DELETING SOURCE!
            #print(f'Deleted: {src_file_name}')
            pass

    def process(self) -> None:
        src_file_names = os.listdir(self._src_dir_abspath)

        src_file_names = list(filter(self._get_yyyymmdd, src_file_names))
        src_file_names.sort(key=self._get_yyyymmdd)

        for src_file_name in src_file_names:
            self._process_file(src_file_name)

