# Тест-кейсы функциональных требований

1. TC-FR-001 — Парсинг корректного Markdown
Приоритет: High. Предусловия: существует .md файл с заголовками и списками.
Шаги:
1. Запустить generate requirements.md
2. Дождаться завершения
Ожидаемый результат: ошибок нет, парсинг завершён

2. TC-FR-002 — Парсинг пустого файла
Приоритет: Medium. Предусловия: существует пустой .md файл.
Шаги:
1. Запустить generate empty.md
Ожидаемый результат: система выводит сообщение "Parsing requirements" и "File not found" или "No requirements found" и завершается

3. TC-FR-003 — Парсинг файла не в формате Markdown
Приоритет: Low. Предусловия: существует .txt файл с произвольным текстом.
Шаги:
1. Запустить generate input.txt
Ожидаемый результат: система выводит сообщение и завершается

4. TC-FR-004 — Парсинг файла с вложенными заголовками
Приоритет: Medium. Предусловия: существует .md с заголовками уровней 1-3.
Шаги:
1. Запустить generate requirements.md
2. Проверить в структуре Requirements наличие вложенных секций
Ожидаемый результат: иерархия заголовков сохранена

5. TC-FR-005 — Генерация: LLM доступна, ответ валидный
Приоритет: High. Предусловия: Ollama запущен, модель Phi-4 Mini загружена.
Шаги:
1. Запустить generate requirements.md
2. Дождаться завершения
Ожидаемый результат: получен массив TestCase, каждый содержит id, title, steps, expectedResult

6. TC-FR-006 — Генерация: LLM недоступна
Приоритет: High. Предусловия: Ollama не запущен или порт недоступен.
Шаги:
1. Запустить generate requirements.md
Ожидаемый результат: сообщение "LLM connection failed" в stderr, код возврата 1

7. TC-FR-007 — Генерация: LLM ответ невалидный JSON
Приоритет: Medium. Предусловия: настроена симуляция некорректного ответа.
Шаги:
1. Запустить generate requirements.md
Ожидаемый результат: сообщение "Failed to parse LLM response" в stderr, код возврата 1

8. TC-FR-008 — Экспорт: запись в ./output/
Приоритет: High. Предусловия: тест-кейсы сгенерированы.
Шаги:
1. Запустить generate requirements.md
2. Проверить наличие ./output/requirements.json
Ожидаемый результат: файл создан, содержит валидный JSON

9. TC-FR-009 — Экспорт: превышение 10 МБ
Приоритет: Medium. Предусловия: большой объём требований.
Шаги:
1. Запустить generate large.md
Ожидаемый результат: сообщение "Result size exceeds 10 MB" в stderr

10. TC-FR-010 — Экспорт: CSV создан
Приоритет: Medium. Предусловия: тест-кейсы сгенерированы.
Шаги:
1. Запустить generate requirements.md
2. Проверить наличие ./output/requirements.csv
Ожидаемый результат: CSV с разделителем ;, столбцы id;title;preconditions;step0;...;expectedResult

11. TC-FR-011 — CLI: generate с корректным input
Приоритет: High. Предусловия: корректный .md файл.
Шаги:
1. Запустить generate requirements.md
Ожидаемый результат: JSON + CSV созданы, pipeline выполнен без ошибок

12. TC-FR-012 — CLI: generate без input (неверный путь)
Приоритет: Medium. Предусловия:
Шаги:
1. Запустить generate nonexistent.md
Ожидаемый результат: сообщение "File not found" в stderr, код возврата 1

13. TC-FR-013 — Docker: сборка образа
Приоритет: High. Предусловия: Docker установлен.
Шаги:
1. docker compose build
2. Проверить успешное завершение сборки
Ожидаемый результат: образ собран, контейнер запускается

14. TC-FR-014 — Docker: compose up с ollama sidecar
Приоритет: High. Предусловия: docker-compose.yml существует.
Шаги:
1. docker compose up -d
2. Проверить, что оба контейнера (app + ollama) запущены
Ожидаемый результат: app подключается к ollama на localhost:11434

15. TC-FR-015 — run.sh: полный цикл generate-and-stop
Приоритет: High. Предусловия: требования в input/.
Шаги:
1. ./run.sh requirements.md
Ожидаемый результат: скрипт запускает ollama, генерирует кейсы, останавливает всё

16. TC-FR-016 — run.ps1: полный цикл generate-and-stop
Приоритет: High. Предусловия: требования в input/.
Шаги:
1. .\run.ps1 requirements.md
Ожидаемый результат: скрипт запускает ollama, генерирует кейсы, останавливает всё

17. Результаты
17.1. TC-FR-001 — Пройден — parser unit test test_parse_basic_markdown
17.2. TC-FR-002 — Пройден — parser unit test test_parse_empty_file
17.3. TC-FR-003 — Не реализован — валидация .md/.txt не добавлена в парсер
17.4. TC-FR-004 — Пройден — parser unit test test_parse_nested_headings
17.5. TC-FR-005 — Пройден — generator unit test test_generate_with_mock (мок)
17.6. TC-FR-006 — Пройден — generator unit test test_ollama_provider_connection_error
17.7. TC-FR-007 — Пройден — generator unit test test_ollama_provider_bad_json
17.8. TC-FR-008 — Пройден — serializer unit test test_to_json_basic, CLI test
17.9. TC-FR-009 — Пройден — serializer unit test test_to_json_exceeds_10mb
17.10. TC-FR-010 — Пройден — serializer unit test test_to_csv_equal_steps
17.11. TC-FR-011 — Пройден — CLI end-to-end smoke test
17.12. TC-FR-012 — Пройден — cli unit test test_generate_file_not_found
17.13. TC-FR-013 — Готов к выполнению — Dockerfile создан, сборка проверена
17.14. TC-FR-014 — Готов к выполнению — docker-compose.yml создан
17.15. TC-FR-015 — Готов к выполнению — run.sh создан, проверен
17.16. TC-FR-016 — Готов к выполнению — run.ps1 создан, проверен
