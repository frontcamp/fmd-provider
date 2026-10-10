
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

from libs.normalizer import CustomNormalizer, parse_price, parse_time_HAMX


class Normalizer(CustomNormalizer):

    def _get_script_dir_abspath(self) -> str:
        return os.path.dirname(os.path.abspath(__file__))

    def _get_yyyymmdd(self, src_file_name: str) -> bool|str:

        # Filename example:
        # lsx_posttrade_equity_previous_2026_09_17_stand_23_30_50.csv

        if not (src_file_name.startswith('lsx_posttrade_equity_')
                and src_file_name.endswith('.csv')
                and '_stand_' in src_file_name):
            return False

        date_part = src_file_name.split('_stand_', 1)[0][-10:]
        yyyymmdd = date_part.replace('_', '')

        if len(yyyymmdd) != 8 or not yyyymmdd.isdigit():
            return False

        return yyyymmdd

    def _process_line(self, line: str) -> bool:

        # Data example:
        # Trading date and time;ISIN;Price;Missing Price;Price currency;Price notation;Quantity;Venue of execution;Trading system;Publication date and time;Venue of Publication;Transaction identification code;Flags
        # "2026-09-17 05:30:00.667";"CA14071L1085";"8.5690";"";"EUR";"MONE";"500.0000";"HAMN";"OTHR";"2026-09-17 05:30:23.704";"HAMN";"HAMLCA14071L1085202609170530236910468A0000019";"ALGO"

        # parse data

        if not line.strip():  # skip empty lines
            return True

        field_names = (
            'Trading date and time', 'ISIN', 'Price', 'Missing Price',
            'Price currency', 'Price notation', 'Quantity',
            'Venue of execution', 'Trading system', 'Publication date and time',
            'Venue of Publication', 'Transaction identification code', 'Flags',
        )
        source_record = next(csv.DictReader(
            [line],
            fieldnames=field_names,
            delimiter=';',
            skipinitialspace=True,
        ))

        # reject incomplete records
        if None in source_record or None in source_record.values():
            return False

        # skip headline
        if source_record['ISIN'] == 'ISIN':
            return True

        flags = source_record['Flags']
        if 'AMND' in flags:  # update existing transaction
            return False  # save to log..

        if 'CANC' in flags and source_record['Transaction identification code']:
            self._buff_trans = [
                record for record in self._buff_trans
                if record['__tid'] != source_record['Transaction identification code']
            ]
            return True

        source_record['Quantity'] = int(float(source_record['Quantity']))

        if (not source_record['Venue of execution']
         or not source_record['ISIN']
         or not source_record['Price currency']
         or not source_record['Quantity']
         or not source_record['Transaction identification code']
         or source_record['Price notation'] != 'MONE'
         or source_record['Missing Price']):
            return False

        time_utc = parse_time_HAMX(source_record['Trading date and time'])
        price = parse_price(source_record['Price'])
        if time_utc is None or price is None:
            return False

        transaction = {
            'source': 'HAMN',
            'mic': source_record['Venue of execution'],
            'isin': source_record['ISIN'],
            'trade_time': time_utc,
            'price': price,
            'currency': source_record['Price currency'],
            'quantity': source_record['Quantity'],
            'quantity_unit': '',
            '__tid': source_record['Transaction identification code'],
        }

        self._buff_trans.append(transaction)
        return True


if __name__ == '__main__':

    normalizer = Normalizer()
    normalizer.process()

    if '--hold' in sys.argv[1:]:
        input("Press Enter to exit...")
