# Тест-кейсы нефункциональных требований

1. TC-NFR-001 — Приватность: отсутствие исходящих запросов внешним сервисам
Приоритет: High. Предусловия: запущен генератор с корректными требованиями.
Шаги:
1. Перехватить весь исходящий HTTP-трафик
2. Запустить generate requirements.md
3. Дождаться завершения
Ожидаемый результат: нет HTTP-запросов за пределы localhost:11434 (Ollama)

2. TC-NFR-002 — Приватность: LLM-запросы в контуре
Приоритет: High. Предусловия: Ollama на localhost:11434.
Шаги:
1. Проверить, что все запросы к LLM идут на localhost:11434
Ожидаемый результат: ни один запрос не уходит на внешний IP/домен

3. TC-NFR-003 — Установка одной командой
Приоритет: High. Предусловия: чистая машина с Docker.
Шаги:
1. ./run.sh requirements.md (Linux) или .\run.ps1 requirements.md (Windows)
Ожидаемый результат: скрипт запускает ollama, генерирует кейсы, останавливает всё

4. TC-NFR-004 — Работа на Windows через Docker
Приоритет: Medium. Предусловия: Windows с Docker Desktop.
Шаги:
1. .\run.ps1 requirements.md
Ожидаемый результат: pipeline выполняется без ошибок

5. TC-NFR-005 — Работа на Linux через Docker
Приоритет: Medium. Предусловия: Linux с Docker Engine.
Шаги:
1. ./run.sh requirements.md
Ожидаемый результат: pipeline выполняется без ошибок

6. TC-NFR-006 — Работа на macOS через Docker
Приоритет: Medium. Предусловия: macOS с Docker Desktop.
Шаги:
1. ./run.sh requirements.md
Ожидаемый результат: pipeline выполняется без ошибок

7. TC-NFR-007 — Лимит 10 МБ: превышение
Приоритет: High. Предусловия: большой объём требований.
Шаги:
1. Запустить generate large.md
Ожидаемый результат: сообщение "Result size exceeds 10 MB" в stderr, JSON не создан

8. TC-NFR-008 — Индикация прогресса в stdout
Приоритет: Medium. Предусловия: корректный .md файл.
Шаги:
1. Запустить generate requirements.md
2. Наблюдать stdout
Ожидаемый результат: в stdout последовательно отображаются "Parsing requirements" → "Generating: ... (X/Y)" → "Saving results" → "Results saved in:"

9. Результаты
9.1. TC-NFR-001 — Пройден — генератор шлёт запросы только на localhost:11434
9.2. TC-NFR-002 — Пройден — OllamaProvider сконфигурирован на localhost:11434
9.3. TC-NFR-003 — Готов к выполнению — run.sh/run.ps1 созданы, проверены
9.4. TC-NFR-004 — Готов к выполнению — run.ps1 создан, проверен
9.5. TC-NFR-005 — Готов к выполнению — run.sh создан, проверен
9.6. TC-NFR-006 — Готов к выполнению — run.sh создан, проверен
9.7. TC-NFR-007 — Пройден — serializer unit test test_to_json_exceeds_10mb
9.8. TC-NFR-008 — Пройден — cli unit test test_generate_progress_messages
