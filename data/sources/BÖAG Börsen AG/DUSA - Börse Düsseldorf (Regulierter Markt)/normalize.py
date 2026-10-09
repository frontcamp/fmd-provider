
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

from libs.normalizer import CustomNormalizer, parse_price, parse_time_DUSX


class Normalizer(CustomNormalizer):

    def _get_script_dir_abspath(self) -> str:
        return os.path.dirname(os.path.abspath(__file__))

    def _get_yyyymmdd(self, src_file_name: str) -> bool|str:

        # Filename example:
        # Mifir13DelayedData_DUSA_0000001B_202610010000000000.csv

        if not src_file_name.endswith('.csv'):
            return False

        src_file_name = src_file_name.removesuffix('.csv')
        date_part = src_file_name.rsplit('_', 1)[-1]
        yyyymmdd = date_part[:8]

        if len(yyyymmdd) != 8 or not yyyymmdd.isdigit():
            return False

        return yyyymmdd

    def _process_line(self, line: str) -> bool:

        # Data example:
        # MIC; ISIN; displayName; time; price; size; supplement
        # DUSA;DE000BASF111;"BASF SE Namens-Aktien o.N.";01.10.2026 08:00:11;50,04;50;"bez "

        # parse data

        if not line.strip():  # skip empty lines
            return True

        field_names = ('MIC','ISIN','displayName','time','price','size','supplement')
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
        if source_record['MIC'] == 'MIC':
            return True

        # convert source-local time to UTC
        time_utc = parse_time_DUSX(source_record['time'])
        if time_utc is None:
            return False

        # parse and validate the price
        price = parse_price(source_record['price'])
        if price is None:
            return False

        # convert to unified record
        transaction = {
            'source': 'DUSA',                   # data source ID
            'mic': source_record['MIC'],        # trade execution venue
            'isin': source_record['ISIN'],      # instrument ID
            'trade_time': time_utc,             # trade execution time (UTC)
            'price': price,                     # price
            'currency': '',                     # currency
            'quantity': source_record['size'],  # quantity
            'quantity_unit': '',                # quantity units
        }

        # recognize record types
        record_type = source_record['supplement'].strip()

        match record_type:

            case 'bez' if source_record['size'] != '0':  # bez = bezahlt
                self._buff_trans.append(transaction)
                return True

            case '' if source_record['size'] == '0':  # price update with zero size
                self._buff_trans.append(transaction)
                return True

            case _:  # unsupported supplement/size combination
                return False


if __name__ == '__main__':

    normalizer = Normalizer()
    normalizer.process()

    if '--hold' in sys.argv[1:]:
        input("Press Enter to exit...")
