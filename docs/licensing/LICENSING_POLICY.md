# H-S-Tool Licensing Policy

**Версия:** 1.0.0  
**Дата:** 2026-10-11  
**Статус:** Draft  
**Автор:** Technical Lead  

---

## 1. ОБЩИЕ ПРИНЦИПЫ

Проект H-S-Tool — это локальная система поддержки принятия решений для специалиста по охране труда.

Продукт разрабатывается с учетом будущей коммерциализации как proprietary-совместимый продукт.

**Основные принципы:**

1. **Local-first**: Все ключевые функции работают без интернета.
2. **License-clean by design**: Архитектура и зависимости должны быть пригодны для коммерческой продажи.
3. **Transparency**: Все зависимости должны быть задокументированы с указанием лицензий.
4. **Compliance**: Соблюдение лицензионных требований всех используемых компонентов.
5. **Auditability**: Возможность проверки лицензионной чистоты на любом этапе.

---

## 2. РАЗРЕШЁННЫЕ ЛИЦЕНЗИИ

### 2.1. Разрешенные по умолчанию (Permissive)

Эти лицензии могут использоваться в runtime-ядре без дополнительного approval:

| Лицензия | Описание | Пример |
|----------|----------|--------|
| MIT | Простая разрешительная лицензия | `streamlit`, `pandas` |
| BSD-2-Clause | BSD с 2 пунктами | `numpy` |
| BSD-3-Clause | BSD с 3 пунктами | `pdfplumber` |
| Apache-2.0 | Apache License 2.0 | `rich`, `pydantic` |
| ISC | ISC License | `requests` |
| Python-2.0 | Python Software Foundation License | `sqlite3` (stdlib) |
| Zlib | Zlib License | `zlib` |
| Unlicense | Public Domain | Различные утилиты |
| CC0-1.0 | Creative Commons Zero | Данные/ассеты |

### 2.2. Требуют юридического review

Эти лицензии требуют явного approval перед использованием:

| Лицензия | Описание | Риски |
|----------|----------|-------|
| LGPL-2.1-only | Lesser GPL 2.1 | Обязательства по предоставлению исходников изменений |
| LGPL-3.0-only | Lesser GPL 3.0 | Обязательства по предоставлению исходников изменений |
| MPL-2.0 | Mozilla Public License 2.0 | Файловое заражение |
| EPL-1.0 | Eclipse Public License 1.0 | Патентные обязательства |
| EPL-2.0 | Eclipse Public License 2.0 | Патентные обязательства |
| CDDL-1.0 | Common Development and Distribution License | Патентные обязательства |

### 2.3. Запрещённые для runtime-ядра

Эти лицензии **ЗАПРЕЩЕНЫ** для использования в ядре продукта и распространяемых компонентах:

| Лицензия | Описание | Причина запрета |
|----------|----------|-----------------|
| GPL-2.0-only | GNU General Public License 2.0 | Вирусное заражение |
| GPL-2.0-or-later | GNU GPL 2.0 или новее | Вирусное заражение |
| GPL-3.0-only | GNU GPL 3.0 | Вирусное заражение |
| GPL-3.0-or-later | GNU GPL 3.0 или новее | Вирусное заражение |
| AGPL-3.0-only | Affero GPL 3.0 | Сетевое вирусное заражение |
| AGPL-3.0-or-later | Affero GPL 3.0 или новее | Сетевое вирусное заражение |
| SSPL-1.0 | Server Side Public License | Запрещает коммерческое использование |
| BSL-1.1 | Business Source License 1.1 | Ограничения на коммерческое использование |
| Commons Clause | Commons Clause | Запрещает коммерческое использование |
| Любые non-commercial | Non-commercial лицензии | Запрещают коммерческое использование |
| Unknown | Неизвестная лицензия | Неопределённый статус |

**Правило:**
> **Unknown = Forbidden until reviewed**

---

## 3. ПРОЦЕСС ДОБАВЛЕНИЯ ЗАВИСИМОСТЕЙ

### 3.1. Перед добавлением зависимости

**ОБЯЗАТЕЛЬНЫЕ ШАГИ:**

1. ✅ **Проверить лицензию**
   - Найти лицензию в репозитории зависимости (LICENSE, COPYING)
   - Проверить на [choosealicense.com](https://choosealicense.com/)
   - Проверить на [SPDX](https://spdx.org/licenses/)

2. ✅ **Определить категорию**
   - Runtime (включается в финальную сборку)
   - Dev-only (используется только для разработки)
   - Build (используется для сборки)
   - Vendor (включается как сторонний компонент)

3. ✅ **Проверить совместимость**
   - Разрешена ли лицензия по п.2.1?
   - Требует ли review по п.2.2?
   - Запрещена ли по п.2.3?

4. ✅ **Обновить артефакты**
   - Добавить в `requirements.txt` (runtime) или `requirements-dev.txt` (dev)
   - Добавить в `pyproject.toml` (если используется)
   - Обновить `sbom/cyclonedx.json`
   - Обновить `sbom/spdx.json`
   - Обновить `third_party/NOTICES`

5. ✅ **Проверить redistribution**
   - Разрешено ли redistribution?
   - Требуется ли attribution?
   - Есть ли ограничения на коммерческое использование?

6. ✅ **Запустить license gate**
   ```bash
   python tools/license_report.py --check
   ```

7. ✅ **Создать PR с полным отчётом**
   - Указать лицензию зависимости
   - Указать категорию (runtime/dev/build)
   - Указать статус redistribution
   - Указать требования attribution

### 3.2. Если лицензия неизвестна или запрещена

**ДЕЙСТВИЯ:**

1. ❌ **НЕ ДОБАВЛЯТЬ** зависимость в проект
2. 🛑 **ОСТАНОВИТЬСЯ** и запросить решение у Technical Lead
3. 📝 **Создать issue** с запросом на review лицензии
4. ⏳ **ЖДАТЬ** approval перед продолжением

---

## 4. SBOM (SOFTWARE BILL OF MATERIALS)

### 4.1. Форматы

Продукт поддерживает генерацию SBOM в следующих форматах:

1. **CycloneDX JSON** (основной)
2. **SPDX JSON** (опционально)

### 4.2. Содержимое SBOM

Каждый компонент в SBOM должен содержать:

| Поле | Описание | Пример |
|------|----------|--------|
| `name` | Имя пакета | `streamlit` |
| `version` | Версия | `1.65.0` |
| `license` | Лицензия (SPDX ID) | `Apache-2.0` |
| `purl` | Package URL | `pkg:pypi/streamlit@1.65.0` |
| `sha256` | Hash пакета | `a1b2c3...` |
| `origin` | Источник | `PyPI` |
| `purpose` | Назначение | `runtime` / `dev` / `build` |
| `distribution_status` | Статус распространения | `allowed` / `restricted` / `forbidden` |

### 4.3. Генерация SBOM

```bash
# Генерация CycloneDX
python tools/sbom_generate.py --format cyclonedx --output sbom/cyclonedx.json

# Генерация SPDX
python tools/sbom_generate.py --format spdx --output sbom/spdx.json

# Проверка SBOM
python tools/sbom_generate.py --validate
```

### 4.4. Хранение SBOM

- `sbom/cyclonedx.json` — основной SBOM в формате CycloneDX
- `sbom/spdx.json` — опциональный SBOM в формате SPDX
- `sbom/history/` — история изменений SBOM

---

## 5. LICENSE REPORT

### 5.1. Генерация отчёта

```bash
# Полный отчёт
python tools/license_report.py --output reports/license_report.md

# Проверка лицензий
python tools/license_report.py --check

# JSON формат
python tools/license_report.py --format json --output reports/license_report.json
```

### 5.2. Содержимое отчёта

Отчёт должен содержать:

1. **Список всех зависимостей**
   - Имя
   - Версия
   - Лицензия
   - Категория (runtime/dev/build)
   - Статус (allowed/requires_review/forbidden)

2. **Статистика**
   - Общее количество зависимостей
   - Количество runtime-зависимостей
   - Количество dev-зависимостей
   - Количество запрещённых зависимостей

3. **Рекомендации**
   - Зависимости, требующие review
   - Зависимости, которые нужно заменить
   - Отсутствующие attribution

---

## 6. NOTICE FILE

### 6.1. Структура

Файл `third_party/NOTICES` должен содержать:

```text
================================================================================
NOTICE FOR H-S-Tool
================================================================================

This product includes software developed by third parties.

--------------------------------------------------------------------------------
STREAMLIT (Apache-2.0)
--------------------------------------------------------------------------------
Copyright 2021-2024 Streamlit Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

--------------------------------------------------------------------------------
PANDAS (BSD-3-Clause)
--------------------------------------------------------------------------------
Copyright (c) 2008-2024, the pandas development team

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice,
   this list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its
   contributors may be used to endorse or promote products derived from
   this software without specific prior written permission.

--------------------------------------------------------------------------------
... (и так далее для всех зависимостей)
================================================================================
```

### 6.2. Генерация NOTICE

```bash
python tools/license_report.py --generate-notice --output third_party/NOTICES
```

---

## 7. LICENSE GATE (АВТОМАТИЧЕСКАЯ ПРОВЕРКА)

### 7.1. Интеграция с CI/CD

License gate должен запускаться:

1. **Перед коммитом** (pre-commit hook)
2. **В CI/CD пайплайне**
3. **Перед сборкой**

### 7.2. Правила gate

| Условие | Действие |
|---------|----------|
| Есть forbidden зависимости | ❌ **FAIL** (блокировать) |
| Есть unknown зависимости | ⚠️ **WARN** (предупреждать) |
| Есть зависимости, требующие review | ⚠️ **WARN** (предупреждать) |
| Все зависимости разрешены | ✅ **PASS** |

### 7.3. Пример интеграции

```yaml
# .github/workflows/license-check.yml
name: License Check

on: [push, pull_request]

jobs:
  license-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run license check
        run: python tools/license_report.py --check
```

---

## 8. ОБНОВЛЕНИЕ ЗАВИСИМОСТЕЙ

### 8.1. Процесс обновления

1. **Проверить изменения лицензии**
   - Не изменилась ли лицензия на новую версию?
   - Не стала ли она более ограничительной?

2. **Проверить совместимость**
   - Работает ли новая версия с текущим кодом?
   - Нет ли breaking changes?

3. **Обновить артефакты**
   - Обновить версию в `requirements.txt`
   - Обновить SBOM
   - Обновить license report
   - Обновить NOTICE (если изменилась лицензия)

4. **Запустить тесты**
   - Unit-тесты
   - Integration-тесты
   - License gate

5. **Создать PR**
   - Указать изменения
   - Указать проверку лицензии
   - Указать результаты тестов

---

## 9. ИСКЛЮЧЕНИЯ

### 9.1. Dev-only зависимости

Dev-only зависимости (тестирование, разработка, сборка) могут использовать более разрешительные лицензии, если:

1. Они не включаются в финальную сборку
2. Они не распределяются вместе с продуктом
3. Они явно помечены как `dev` в SBOM

**Пример:**
- `pytest` (MIT) — разрешено
- `black` (MIT) — разрешено
- `mypy` (MIT) — разрешено

### 9.2. Системные зависимости

Системные библиотеки (stdlib) не требуют проверки:
- `sqlite3` (Python-2.0)
- `json` (Python-2.0)
- `pathlib` (Python-2.0)

---

## 10. МОДЕЛИ LLM

### 10.1. Реестр моделей

Файл `models.lock.json` должен содержать:

```json
{
  "models": [
    {
      "id": "llama-3-8b",
      "name": "Llama 3 8B",
      "source": "Meta",
      "sha256": "a1b2c3...",
      "size": "4.7GB",
      "license": "LLAMA3",
      "commercial_use_allowed": true,
      "redistribution_allowed": false,
      "attribution_required": true,
      "restrictions": "Non-commercial redistribution prohibited",
      "review_status": "approved"
    }
  ]
}
```

### 10.2. Правила для моделей

1. **Commercial Use Allowed**
   - Модель должна разрешать коммерческое использование
   - Если `commercial_use_allowed = false`, модель **ЗАПРЕЩЕНА**

2. **Redistribution**
   - Если `redistribution_allowed = false`, модель **НЕ ВКЛЮЧАЕТСЯ** в сборку
   - Пользователь должен установить её самостоятельно

3. **Attribution**
   - Если `attribution_required = true`, добавить в NOTICE

4. **Review Status**
   - `approved` — модель разрешена
   - `pending` — требует review
   - `rejected` — модель запрещена

---

## 11. ПРИМЕРЫ

### 11.1. Пример добавления новой зависимости

**Задача:** Добавить `requests` для HTTP-запросов

**Шаги:**

1. Проверить лицензию `requests`:
   ```bash
   pip show requests | grep License
   # License: Apache-2.0
   ```

2. Apache-2.0 разрешена (п.2.1)

3. Добавить в `requirements.txt`:
   ```
   requests==2.31.0
   ```

4. Обновить SBOM:
   ```bash
   python tools/sbom_generate.py --update
   ```

5. Запустить license gate:
   ```bash
   python tools/license_report.py --check
   ```

6. Создать PR с отчётом:
   ```markdown
   ## Add requests dependency
   
   - License: Apache-2.0 (allowed)
   - Purpose: runtime (HTTP client)
   - Redistribution: allowed
   - Attribution: required (in NOTICE)
   
   ### Checks
   - [x] License check passed
   - [x] SBOM updated
   - [x] NOTICE updated
   - [x] Tests passed
   ```

---

### 11.2. Пример запрещённой зависимости

**Задача:** Добавить `gnuplot-py` для графиков

**Шаги:**

1. Проверить лицензию `gnuplot-py`:
   ```bash
   pip show gnuplot-py | grep License
   # License: GPL-3.0
   ```

2. GPL-3.0 **ЗАПРЕЩЕНА** (п.2.3)

3. ❌ **НЕ ДОБАВЛЯТЬ** зависимость
4. 🛑 **ОСТАНОВИТЬСЯ**
5. 📝 Создать issue:
   ```markdown
   ## License Review: gnuplot-py
   
   **License:** GPL-3.0
   **Status:** FORBIDDEN
   **Reason:** Viral licensing (p.2.3)
   
   **Alternatives:**
   - matplotlib (BSD-compatible)
   - plotly (MIT)
   ```

---

## 12. КОНТАКТЫ

Вопросы по лицензионной политике:
- Technical Lead: [email]
- Legal Team: [email]

---

**Документ утверждён:** _______________________  
**Дата:** _______________
