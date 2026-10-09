
import json
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
        # DETR-posttrade-daily-2026-09-18.json.gz

        if not src_file_name.endswith('.json.gz'):
            return False

        src_file_name = src_file_name.removesuffix('.json.gz')
        date_part = src_file_name[-10:]
        yyyymmdd = date_part.replace('-', '')

        if len(yyyymmdd) != 8 or not yyyymmdd.isdigit():
            return False

        return yyyymmdd

    def _process_line(self, line: str) -> bool:

        # Data example:
        # {"messageId":"posttrade","instrumentIdentificationCode":"DE000TLX1005","priceCurrency":"EUR","lastTradeIndicator":"R","tradingSystem":"1","mmtTradingMode":"4","mmtModificationInd":"-","mmtBenchmarkRefprcInd":"-","mmtPubModeDefReason":"-","mmtAlgoInd":"-","priceNotation":1,"quantity":15.00,"price":123.30,"tradingDateAndTime":"2026-09-18T06:00:00.761054622Z","publicationDateAndTime":"2026-09-18T06:00:00.768851000Z","transactionIdentificationCode":"1000000000000025048540178971120076105462200000000001","venueOfExecution":"XETA","venueOfPublication":"XCEF"}
        # {"messageId":"posttrade","instrumentIdentificationCode":"DE0008232125","priceCurrency":"EUR","tradingSystem":"1","mmtTradingMode":"O","mmtModificationInd":"-","mmtBenchmarkRefprcInd":"-","mmtPubModeDefReason":"-","mmtAlgoInd":"H","priceNotation":1,"quantity":79160.00,"price":7.718,"tradingDateAndTime":"2026-09-18T07:00:00.141024183Z","publicationDateAndTime":"2026-09-18T07:00:00.148843000Z","transactionIdentificationCode":"1000000000000025051300178971480014102418300000000050","venueOfExecution":"XETA","venueOfPublication":"XCEF"}
        # {"messageId":"posttrade","instrumentIdentificationCode":"DE0008232125","priceCurrency":"EUR","tradingSystem":"1","mmtTradingMode":"2","mmtModificationInd":"-","mmtBenchmarkRefprcInd":"-","mmtPubModeDefReason":"-","mmtAlgoInd":"H","priceNotation":1,"quantity":2410.00,"price":7.72,"tradingDateAndTime":"2026-09-18T07:00:00.157335613Z","publicationDateAndTime":"2026-09-18T07:00:00.158721000Z","transactionIdentificationCode":"1000000000000025051300178971480015733561300000000051","venueOfExecution":"XETA","venueOfPublication":"XCEF"}
        # {"messageId":"posttrade","instrumentIdentificationCode":"DE000KBX1006","priceCurrency":"EUR","lastTradeIndicator":"P","tradingSystem":"3","mmtTradingMode":"2","mmtModificationInd":"-","mmtBenchmarkRefprcInd":"S","mmtPubModeDefReason":"-","mmtAlgoInd":"H","priceNotation":1,"quantity":61.00,"price":105.60,"tradingDateAndTime":"2026-09-18T07:00:06.137633065Z","publicationDateAndTime":"2026-09-18T07:00:06.138746000Z","transactionIdentificationCode":"1000000000000035027440178971480613763306500000000077","venueOfExecution":"XEMA","venueOfPublication":"XCEF"}

        # parse data

        if not line.strip():  # skip empty lines
            return True

        try:
            source_record = json.loads(line)
        except json.JSONDecodeError:
            return False

        if not isinstance(source_record, dict):
            return False

        # convert to unified record
        transaction = {
            'source': 'DETR', # data source ID
            'mic': source_record['venueOfExecution'], # trade execution venue
            'isin': source_record['instrumentIdentificationCode'], # instrument ID
            'trade_time': source_record['tradingDateAndTime'], # trade execution time (UTC)
            'price': source_record['price'],
            'currency': source_record['priceCurrency'],
            'quantity': source_record['quantity'],
            'quantity_unit': '',
            '__tid': source_record['transactionIdentificationCode'], # transaction ID
        }

        record_type = (
            source_record.get('messageId'),
            source_record.get('mmtTradingMode'),
            source_record.get('mmtModificationInd'),
            source_record.get('priceNotation'),
        )

        match record_type:
            case ('posttrade', '4' | 'O' | '2' | 'U' | '5' | 'I' | 'K' | '3', '-', 1):
                self._buff_trans.append(transaction)
                return True

            case ('posttrade', '4' | 'O' | '2' | 'U' | '5' | 'I' | 'K' | '3', 'C', 1):
                self._buff_trans = [
                    record for record in self._buff_trans
                    if record['__tid'] != transaction['__tid']
                ]
                return True

            case _:
                return False


if __name__ == '__main__':

    normalizer = Normalizer()
    normalizer.process()

    if '--hold' in sys.argv[1:]:
        input("Press Enter to exit...")
