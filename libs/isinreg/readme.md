
How to update the ISIN registry
===============================

The registry is stored in libs/isinreg/_registry.sqlite3. Its records contain an ISIN, a full instrument name, and a short instrument name.

Preparing the source data
-------------------------

1. Download a complete ESMA snapshot using the instructions in `libs/isinreg/_sources/esma/readme.txt`. Remove ZIP files from the previous snapshot and place all ZIP files from the new snapshot in `libs/isinreg/_sources/esma/latest-snapshot/`.

2. Run `data/normalized/collect-instrument-isins.py` script. Move the resulting `data/normalized/collected-instrument-isins.csv` to `libs/isinreg/_sources/collected-instrument-isins.csv`.

Updating the registry
---------------------

3. Run `libs/isinreg/_update.py`. Be happy :)

For a complete rebuild, the registry database can be removed before step 3.

Information
-----------

The updater reads the required ISINs from the CSV prepared in step 2, then processes every XML record in the complete ESMA snapshot. Records whose ISINs are not required are skipped. Required instruments with a defined maturity or expiry date are also skipped: they are time-limited and are not needed in this project. ESMA's 9999-12-31 date means that no end date is defined.

For each remaining record, the updater adds its ISIN, full name, and short name to the registry or updates the existing entry. After processing the snapshot, it compares the registry with the current required ISINs and deletes entries that are no longer required. A required ISIN absent from the ESMA snapshot is reported, but an existing registry entry for it is left unchanged. The updater therefore keeps useful instrument names across runs while removing entries that have dropped out of this project's required list.

Reporting
---------

The updater writes these CSV reports to `libs/isinreg/_reports/`:

- `limited-isins.csv`: required ISINs found in ESMA with a defined maturity or expiry date and therefore skipped.
- `absent-isins.csv`: required ISINs not found in the ESMA snapshot.
- `deleted-isins.csv`: ISINs removed from the registry because they are no longer in the required list.

Each report has an `isin` header and unique ISINs. A report is written only when its list is nonempty; an old report is removed when its list becomes empty. The `_reports` directory is created only when there is something to report. The final console summary counts ESMA XML records for `processed`, `matched`, `skipped`, and `limited`; `missing` and `deleted` count unique ISINs.

To inspect the current registry without running the updater, run `python libs/isinreg/_registry.py`. It prints the database path and size, the number of records, and counts of empty full and short names. This command does not change existing registry entries.

