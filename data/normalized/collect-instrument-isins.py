import csv
from io import TextIOWrapper
from pathlib import Path
from zipfile import ZipFile


_DATA_DIR_ABSPATH = Path(__file__).resolve().parent
_OUTPUT_FILE_ABSPATH = _DATA_DIR_ABSPATH / "collected-instrument-isins.csv"


def extract() -> None:
    zip_files = sorted(_DATA_DIR_ABSPATH.rglob("*.zip"))
    if not zip_files:
        raise FileNotFoundError(f"No ZIP archives in {_DATA_DIR_ABSPATH}")

    # Read each archived instrument list into one set of ISINs.
    isin_codes: set[str] = set()
    for zip_file_abspath in zip_files:
        with ZipFile(zip_file_abspath) as zip_file_obj:
            member_names = [
                name for name in zip_file_obj.namelist()
                if Path(name).name.lower() == "instruments.csv"
            ]
            if not member_names:
                raise ValueError(f"No instruments.csv in {zip_file_abspath}")

            for member_name in member_names:
                with (
                    zip_file_obj.open(member_name) as binary_file_obj,
                    TextIOWrapper(binary_file_obj, encoding="utf-8-sig", newline="")
                    as text_file_obj,
                ):
                    reader = csv.reader(text_file_obj)
                    if next(reader, None) != ["isin"]:
                        raise ValueError(
                            f"Unexpected instruments.csv header in {zip_file_abspath}"
                        )

                    for row in reader:
                        if not row:
                            continue
                        isin = row[0].strip()
                        if isin and isin not in isin_codes:
                            isin_codes.add(isin)
                            if len(isin_codes) % 1000 == 0:
                                print(".", end="", flush=True)

    # Save the unique codes in a stable order.
    with _OUTPUT_FILE_ABSPATH.open("w", encoding="utf-8", newline="") as output_file_obj:
        writer = csv.writer(output_file_obj)
        writer.writerow(["isin"])
        writer.writerows((isin,) for isin in sorted(isin_codes))

    if len(isin_codes) >= 20_000:
        print()
    print(f"Extracted {len(isin_codes)} ISIN codes")


if __name__ == "__main__":
    extract()
    input("\nPress Enter to finish...")
