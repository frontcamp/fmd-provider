from pathlib import Path
from typing import BinaryIO, Iterator
from xml.etree import ElementTree
from zipfile import ZipFile

if __package__:
    from libs.isinreg._registry import ISINRegistry
else:
    from _registry import ISINRegistry


_SOURCE_DIR_ABSPATH = (
    Path(__file__).resolve().parent / "_sources" / "esma" / "latest-snapshot"
)
_XML_NS = "{urn:iso:std:iso:20022:tech:xsd:auth.017.001.02}"
_REF_DATA_TAG = _XML_NS + "RefData"
_ATTRIBUTES_TAG = _XML_NS + "FinInstrmGnlAttrbts"
_ID_TAG = _XML_NS + "Id"
_TITLE_TAG = _XML_NS + "FullNm"
_SHORT_TAG = _XML_NS + "ShrtNm"


def _read_records(xml_file_obj: BinaryIO) -> Iterator[tuple[str, str, str]]:
    # Keep parent references so processed records can be removed from the XML tree.
    parents: list[ElementTree.Element] = []
    for event, element in ElementTree.iterparse(
        xml_file_obj, events=("start", "end")
    ):
        if event == "start":
            parents.append(element)
            continue

        parents.pop()
        if element.tag != _REF_DATA_TAG:
            continue

        attributes = element.find(_ATTRIBUTES_TAG)
        record = None
        if attributes is not None:
            isin = (attributes.findtext(_ID_TAG) or "").strip()
            if isin:
                record = (
                    isin,
                    attributes.findtext(_TITLE_TAG) or "",
                    attributes.findtext(_SHORT_TAG) or "",
                )

        parents[-1].remove(element)
        element.clear()
        if record is not None:
            yield record


def collect() -> None:
    zip_files = sorted(_SOURCE_DIR_ABSPATH.glob("*.zip"))
    if not zip_files:
        raise FileNotFoundError(f"No ZIP archives in {_SOURCE_DIR_ABSPATH}")

    total = 0
    for zip_file_abspath in zip_files:
        with ZipFile(zip_file_abspath) as zip_file_obj:
            for xml_file_name in zip_file_obj.namelist():
                if not xml_file_name.lower().endswith(".xml"):
                    continue

                # Read each XML directly from its archive, one record at a time.
                with zip_file_obj.open(xml_file_name) as xml_file_obj:
                    for isin, title, short in _read_records(xml_file_obj):
                        ISINRegistry.upsert_isin_info_batch(isin, title, short)
                        total += 1

                        if total % 1000000 == 0:
                            print("|", end="", flush=True)
                        elif total % 100000 == 0:
                            print("*", end="", flush=True)
                        elif total % 20000 == 0:
                            print(".", end="", flush=True)

    ISINRegistry.upsert_isin_info_batch("", "", "")  # flush batch cache
    print(f"\nProcessed: {total} records")


if __name__ == "__main__":
    collect()
    input("\nPress Enter to finish...")
