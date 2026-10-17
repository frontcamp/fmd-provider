
How to update ISIN the registry
===============================

The registry is stored in libs/isinreg/_registry.sqlite3. Its records contain
an ISIN, a full instrument name, and a short instrument name.

Preparing the source data
-------------------------

1. Download a complete ESMA snapshot using the instructions in `libs/isinreg/_sources/esma/readme.txt`. Remove ZIP files from the previous snapshot and place all ZIP files from the new snapshot in `libs/isinreg/_sources/esma/latest-snapshot/`.

2. Run `data/normalized/collect-instrument-isins.py` script. Move the resulting `data/normalized/collected-instrument-isins.csv` to `libs/isinreg/_sources/collected-instrument-isins.csv`.

Updating the registry
---------------------

3. Run `libs/isinreg/_update.py`. Be happy :)

For a complete rebuild, the registry database can be removed before step 3. Keep the existing database until the new update procedure is implemented and verified.

