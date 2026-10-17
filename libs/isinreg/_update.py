import csv
from collections.abc import Iterator
from pathlib import Path
from typing import IO
from xml.etree import ElementTree
from zipfile import ZipFile

if __package__:
    from libs.isinreg._registry import ISINRegistry
else:
    from _registry import ISINRegistry


_ESMA_DATA_DIR_ABSPATH = (
    Path(__file__).resolve().parent / "_sources" / "esma" / "latest-snapshot"
)
_REQUIRED_ISINS_FILE_ABSPATH = (
    Path(__file__).resolve().parent / "_sources" / "collected-instrument-isins.csv"
)
_ESMA_MISSING_ISINS_FILE_ABSPATH = (
    Path(__file__).resolve().parent / "_sources" / "absent-isins.csv"
)
_XML_NS = "{urn:iso:std:iso:20022:tech:xsd:auth.017.001.02}"
_TAG_REF_DATA = _XML_NS + "RefData"
_TAG_ATTRIBUTES = _XML_NS + "FinInstrmGnlAttrbts"
_TAG_ID = _XML_NS + "Id"
_TAG_TITLE = _XML_NS + "FullNm"
_TAG_SHORT = _XML_NS + "ShrtNm"


def _read_records(xml_file_obj: IO[bytes]) -> Iterator[tuple[str, str, str]]:
    # Keep parent references so processed records can be removed from the XML tree.
    parents: list[ElementTree.Element] = []
    for event, element in ElementTree.iterparse(
        xml_file_obj, events=("start", "end")
    ):
        if event == "start":
            parents.append(element)
            continue

        parents.pop()
        if element.tag != _TAG_REF_DATA:
            continue

        attributes = element.find(_TAG_ATTRIBUTES)
        record = None
        if attributes is not None:
            isin = (attributes.findtext(_TAG_ID) or "").strip()
            if isin:
                record = (
                    isin,
                    attributes.findtext(_TAG_TITLE) or "",
                    attributes.findtext(_TAG_SHORT) or "",
                )

        parents[-1].remove(element)
        element.clear()
        if record is not None:
            yield record


def collect() -> None:

    # load required ISINs
    with _REQUIRED_ISINS_FILE_ABSPATH.open("r", encoding="utf-8", newline="") as isins_file_obj:
        reader = csv.reader(isins_file_obj)
        if next(reader, None) != ["isin"]:
            raise ValueError(f"Unexpected CSV header in {_REQUIRED_ISINS_FILE_ABSPATH}")
        isin_codes = {row[0].strip() for row in reader if row and row[0].strip()}

    zip_files = sorted(_ESMA_DATA_DIR_ABSPATH.glob("*.zip"))
    if not zip_files:
        raise FileNotFoundError(f"No ZIP archives in {_ESMA_DATA_DIR_ABSPATH}")

    total = 0
    matched = 0
    skipped = 0
    missing = isin_codes.copy()
    for zip_file_abspath in zip_files:
        with ZipFile(zip_file_abspath) as zip_file_obj:
            for xml_file_name in zip_file_obj.namelist():
                if not xml_file_name.lower().endswith(".xml"):
                    continue

                # Read each XML directly from its archive, one record at a time.
                with zip_file_obj.open(xml_file_name) as xml_file_obj:
                    for isin, title, short in _read_records(xml_file_obj):

                        total += 1

                        if isin not in isin_codes:  # skip unknown ISINs
                            skipped += 1
                            if skipped % 1000000 == 0:
                                print("X", end="", flush=True)
                            elif skipped % 100000 == 0:
                                print("=", end="", flush=True)
                            elif skipped % 20000 == 0:
                                print("-", end="", flush=True)
                            continue

                        ISINRegistry.upsert_isin_info_batch(isin, title, short)
                        missing.discard(isin)

                        matched += 1
                        if matched % 1000000 == 0:
                            print("#", end="", flush=True)
                        elif matched % 100000 == 0:
                            print("*", end="", flush=True)
                        elif matched % 20000 == 0:
                            print("+", end="", flush=True)

    ISINRegistry.upsert_isin_info_batch("", "", "")  # flush batch cache

    # save missing ISINs
    if missing:
        with _ESMA_MISSING_ISINS_FILE_ABSPATH.open(
            "w", encoding="utf-8", newline=""
        ) as missing_file_obj:
            writer = csv.writer(missing_file_obj)
            writer.writerow(["isin"])
            writer.writerows((isin,) for isin in missing)
    else:
        _ESMA_MISSING_ISINS_FILE_ABSPATH.unlink(missing_ok=True)

    # summary
    print(f"\nProcessed: {total}; "
          f"matched: {matched}; "
          f"skipped: {skipped}; "
          f"missing: {len(missing)}")


if __name__ == "__main__":
    collect()
    input("\nPress Enter to finish...")
