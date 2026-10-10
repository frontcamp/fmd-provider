
import csv
import os
import sys

# Add project root to module search path
_project_dir_abspath = os.path.dirname(os.path.abspath(__file__))
while not os.path.isdir(os.path.join(_project_dir_abspath, "libs")):
    _parent_dir_abspath = os.path.dirname(_project_dir_abspath)
    if _parent_dir_abspath == _project_dir_abspath:
        raise ImportError("Project root containing libs was not found.")
    _project_dir_abspath = _parent_dir_abspath
sys.path.insert(0, _project_dir_abspath)

from libs.normalizer import CustomNormalizer, parse_price, parse_time_XEQT


class Normalizer(CustomNormalizer):

    def _get_script_dir_abspath(self) -> str:
        return os.path.dirname(os.path.abspath(__file__))

    def _get_yyyymmdd(self, src_file_name: str) -> bool|str:

        # Filename example:
        # equiduct_trades_2026-09-17.csv

        if not (src_file_name.startswith('equiduct_trades_')
                and src_file_name.endswith('.csv')):
            return False

        date_part = src_file_name.removesuffix('.csv')[-10:]
        yyyymmdd = date_part.replace('-', '')

        if len(yyyymmdd) != 8 or not yyyymmdd.isdigit():
            return False

        return yyyymmdd

    def _process_line(self, line: str) -> bool:

        # Data example:
        # timestamp,symbol,isin,currency,home_market,tvtic,price,quantity,trade_type,flags
        # "20260917-07:00:00.394966","A3Me","ES0109427734","EUR","XMAD","EXE0XSE1M8NGKCA3FFCG","5.33","1","O",="--"

        # parse data

        if not line.strip():  # skip empty lines
            return True

        field_names = (
            'timestamp', 'symbol', 'isin', 'currency', 'home_market',
            'tvtic', 'price', 'quantity', 'trade_type', 'flags',
        )
        source_record = next(csv.DictReader(
            [line],
            fieldnames=field_names,
            delimiter=',',
            skipinitialspace=True,
        ))

        # reject incomplete records
        if None in source_record or None in source_record.values():
            return False

        # skip headline
        if source_record['isin'] == 'isin':
            return True

        flags = source_record['flags'].removeprefix('="').removesuffix('"')
        if flags == 'C-':
            self._buff_trans = [
                record for record in self._buff_trans
                if record['__tid'][1:] != source_record['tvtic'][1:]
            ]
            return True

        if flags not in ('--', '-H'):
            return False

        if (not source_record['isin']
                or not source_record['currency']
                or not source_record['quantity'].isdigit()):
            return False

        time_utc = parse_time_XEQT(source_record['timestamp'])
        price = parse_price(source_record['price'])
        if time_utc is None or price is None:
            return False

        transaction = {
            'source': 'XEQT',
            'mic': 'XEQT',
            'isin': source_record['isin'],
            'trade_time': time_utc,
            'price': price,
            'currency': source_record['currency'],
            'quantity': int(source_record['quantity']),
            'quantity_unit': '',
            '__tid': source_record['tvtic'],
        }

        self._buff_trans.append(transaction)
        return True


if __name__ == '__main__':

    normalizer = Normalizer()
    normalizer.process()

    if '--hold' in sys.argv[1:]:
        input("Press Enter to exit...")
