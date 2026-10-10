
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

from libs.normalizer import CustomNormalizer


class Normalizer(CustomNormalizer):

    def _get_script_dir_abspath(self) -> str:
        return os.path.dirname(os.path.abspath(__file__))

    def _get_yyyymmdd(self, src_file_name: str) -> bool|str:

        # Filename example:
        # DFRA-posttrade-daily-2026-09-18.json.gz

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
        # {"messageId":"posttrade","instrumentIdentificationCode":"SE0000108656","tradingSystem":"9","mmtTradingMode":"U","mmtModificationInd":"-","mmtPubModeDefReason":"-","tradingDateAndTime":"2026-09-18T06:00:03.007066917Z","price":8.934,"quantity":15.0,"priceCurrency":"EUR","venueOfPublication":"XCEF","priceNotation":1,"publicationDateAndTime":"2026-09-18T06:00:03.014895000Z","transactionIdentificationCode":"3000000000000000076460178971120300706691700000000001","venueOfExecution":"FRAB","notionalCurrency":"EUR","mmtAlgoInd":"H"}

        # Data fields:
        # messageId: message type; posttrade or pretrade observed.
        # instrumentIdentificationCode: instrument identifier; 12-character ISIN.
        # tradingSystem: MMT market mechanism; 9 observed for posttrade records.
        # mmtTradingMode: MMT mode; U = unscheduled auction, I = intraday auction.
        # mmtModificationInd: MMT status; - = new trade, C = cancellation, A = amendment.
        # mmtPubModeDefReason: MMT publication delay reason; - = immediate publication.
        # mmtAlgoInd: MMT algorithmic indicator; H = algorithmic trade, - = no flag.
        # priceNotation: price quotation type; 1 and 2 observed in DFRA posttrade.
        # quantity: traded quantity or nominal amount; numeric.
        # notionalAmount: nominal amount; present with priceNotation 2.
        # price: execution price in the units specified by priceNotation; numeric.
        # priceCurrency: price currency; e.g. EUR, USD, GBP, CHF.
        # notionalCurrency: nominal currency; e.g. EUR, USD, GBP, CHF.
        # tradingDateAndTime: execution timestamp; ISO 8601 UTC with fractional seconds.
        # publicationDateAndTime: publication timestamp; ISO 8601 UTC with fractional seconds.
        # transactionIdentificationCode: transaction ID; numeric string, also used for cancellations.
        # venueOfExecution: execution venue MIC; FRAA, FRAB, FRAS observed for posttrade.
        # venueOfPublication: publication venue MIC; XCEF in DFRA records.

        # parse data

        if not line.strip():  # skip empty lines
            return True

        try:
            source_record = json.loads(line)
        except json.JSONDecodeError:
            return False

        if not isinstance(source_record, dict):
            return False

        if source_record.get('messageId') == 'pretrade':
            return True

        is_price_event = (
            source_record.get('messageId') == 'posttrade'
            and source_record.get('mmtModificationInd') == '-'  # new transaction
            and source_record.get('venueOfExecution') is not None
            and source_record.get('instrumentIdentificationCode') is not None
            and source_record.get('tradingDateAndTime') is not None
            and source_record.get('price') is not None  # zero allowed
            and source_record.get('priceCurrency') is not None
            and source_record.get('quantity') is not None  # zero allowed
            and source_record.get('transactionIdentificationCode') is not None
        )

        if is_price_event:

            # convert to unified record
            transaction = {
                'source': 'DFRA', # data source ID
                'mic': source_record['venueOfExecution'], # trade execution venue
                'isin': source_record['instrumentIdentificationCode'], # instrument ID
                'trade_time': source_record['tradingDateAndTime'], # trade execution time (UTC)
                'price': source_record['price'],
                'currency': source_record['priceCurrency'],
                'quantity': source_record['quantity'],
                'quantity_unit': '',
                '__tid': source_record['transactionIdentificationCode'], # transaction ID
            }

            self._buff_trans.append(transaction)
            return True

        is_amendment = (
            source_record.get('messageId') == 'posttrade'
            and source_record.get('mmtModificationInd') == 'A'
        )

        if is_amendment:  # update existing transaction
            return False  # save to log..

        is_cancellation = (
            source_record.get('messageId') == 'posttrade'
            and source_record.get('mmtModificationInd') == 'C'
            and source_record.get('transactionIdentificationCode')
        )

        if is_cancellation:  # handle cancellation events
            self._buff_trans = [
                record for record in self._buff_trans
                if record['__tid'] != source_record['transactionIdentificationCode']
            ]
            return True

        return False


if __name__ == '__main__':

    normalizer = Normalizer()
    normalizer.process()

    if '--hold' in sys.argv[1:]:
        input("Press Enter to exit...")
