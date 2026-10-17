
ESMA Registers
==============

Howto Download
--------------

Source URL:
https://registers.esma.europa.eu/publication/searchRegister?core=esma_registers_firds_files#

1) Get %DATE% from this API request:
https://registers.esma.europa.eu/solr/esma_registers_firds_files/select?q=file_type%3AFULINS&sort=publication_date%20desc&rows=1&wt=json

2) set Publication date from/to to %DATE%
3) File type: Full File
4) Press [SEARCH]

All the links shown will point to parts of a single, unified register of financial instruments.


Data Fields
-----------

| Поле XML               | Значение на русском
| ---------------------- | -------------------------
| FinInstrmGnlAttrbts/Id | **ISIN** — международный идентификатор финансового инструмента.
| FullNm                 | Полное название инструмента. Свободный текст: единый формат и английский язык не обязательны.
| ShrtNm                 | Стандартизированное краткое название **FISN**, по ISO 18774.
| ClssfctnTp             | Шестисимвольный **CFI-код**: классификация типа и характеристик инструмента.
| NtnlCcy                | Валюта номинала инструмента. **Не обязательно валюта торгов** на конкретной площадке.
| CmmdtyDerivInd         | Признак **товарного дериватива**: `true` — является, `false` — не является. Это не общий признак любого дериватива.
| Issr                   | **LEI эмитента** — идентификатор юридического лица. В отдельных случаях, например для биржевых деривативов, указывается LEI оператора площадки.
| TradgVnRltdAttrbts/Id  | **MIC площадки или её сегмента**, к которому относится запись.
| IssrReq                | Запрашивал или одобрял ли эмитент торговлю либо допуск инструмента на эту площадку.
| FrstTradDt             | Дата и время допуска к торгам либо первой сделки, заявки или котировки **на этой площадке**.
| TermntnDt              | Дата и время прекращения торговли или допуска **на этой площадке**. Если дата неизвестна, поле отсутствует.
| ReqForAdmssnDt         | Дата и время подачи заявки на допуск к торгам.
| AdmssnApprvlDtByIssr   | Дата и время, когда **эмитент одобрил** допуск или торговлю на площадке. ([EUR-Lex][1])
| RlvntCmptntAuthrty     | Код страны компетентного регулятора, ответственного за инструмент. `DE` — Германия.
| FrDt                   | Начальная дата публикации **этой версии справочных данных** в FIRDS. В твоём примере — `2024-07-30`.
| RlvntTradgVn           | MIC площадки, чью запись ESMA использует как **эталон справочных данных** об инструменте. ([esma.europa.eu][2])

[1]: https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32017R0585&utm_source=chatgpt.com "Delegated regulation - 2017/585 - EN"
[2]: https://www.esma.europa.eu/sites/default/files/library/esma65-11-1193_firds_reference_data_reporting_instructions_v2.1.pdf?utm_source=chatgpt.com "https://www.esma.europa.eu/sites/default/files/library/esma65-11-1193_firds_reference_data_reporting_instructions_v2.1.pdf"











