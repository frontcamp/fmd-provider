
Financial Market Data Provider (FMD Provider)
=============================================

Документ содержит вводную информацию:

- назначение проекта
- установка и запуск
- варианты использования
- правовая информация

Технические спецификации: `docs/SPECIFICATION.md`


Назначение проекта
------------------

FMD Provider предназначен для сбора рыночных данных из разрозненных источников, их нормализации и передачи другим подсистемам программного комплекса FMD Trader.

Информация по сбору исходных данных: `docs/market-data-collection.md`
Информация по нормализации данных: `docs/market-data-normalization.md`

Общая схема работы FMD Provider:
1. Исходные рыночные данные накапливаются в `data/sources/`.
2. `normalize.cmd` нормализует, фильтрует и переносит данные из `data/sources/` в симметричные каталоги `data/normalized/`.
3. `fmd-provider.py` предоставляет запрошенные данные в требуемом формате.


Установка и запуск
------------------






---

Copyright (c) 2026 Maksym Plaksin. All rights reserved.
This project and all its contents are provided for demo and review only.
No license is granted for reuse, modification, or redistribution.
The author disclaims all responsibility.

