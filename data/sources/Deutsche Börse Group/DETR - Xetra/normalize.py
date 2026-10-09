
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

        # Data fields:
        # messageId: message type; posttrade in the inspected DETR file.
        # instrumentIdentificationCode: instrument identifier; 12-character ISIN.
        # priceCurrency: price currency; e.g. EUR, USD, GBP, SEK, CHF, JPY, AUD.
        # lastTradeIndicator: optional exchange trade flag; observed R, P, C, D, k.
        #                     The meanings of these codes are not confirmed here.
        # tradingSystem: MMT market mechanism; 1 = order book, 3 = dark book, 6 = RFQ.
        # mmtTradingMode: MMT mode; O/K/I/U = opening/closing/intraday/unscheduled auction,
        #                 2 = continuous, 3 = at close, 4 = outside main session,
        #                 5 = on-exchange trade reporting.
        # mmtModificationInd: MMT status; - = new trade, C = cancellation, A = amendment.
        # mmtBenchmarkRefprcInd: MMT price reference; - = none, S = reference price,
        #                         B = benchmark price.
        # mmtPubModeDefReason: MMT publication delay reason; - = immediate publication.
        # mmtAlgoInd: MMT algorithmic indicator; H = algorithmic trade, - = no flag.
        # priceNotation: price quotation type; 1 observed in the inspected DETR file.
        # quantity: traded quantity; numeric number of instrument units.
        # price: execution price in the units specified by priceNotation; numeric.
        # tradingDateAndTime: execution timestamp; ISO 8601 UTC with fractional seconds.
        # publicationDateAndTime: publication timestamp; ISO 8601 UTC with fractional seconds.
        # transactionIdentificationCode: transaction ID; numeric string, also used for cancellations.
        # venueOfExecution: execution venue MIC; observed XETA, XETB, XEMA, XETS,
        #                   XEMB, XEMI, XETU.
        # venueOfPublication: publication venue MIC; XCEF in the inspected DETR file.

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
