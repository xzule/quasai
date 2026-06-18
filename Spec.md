# Spec — Спецификация проекта

Оглавление
1. Обзор
2. Пользовательский сценарий
3. Функциональные требования
4. Нефункциональные требования
5. Архитектура

1. Обзор
Сервис представляет собой локальное развертывание системы, принимающей на вход артефакты, содержащие описание поведения системы клиента в виде функциональных и нефункциональных требований.
На основе этих данных система разрабатывает тестовые box-сценарии в формате, доступном для обработки клиентом вручную или для импорта в TMS системы.

2. Пользовательский сценарий
2.1. Пользователь клонирует репозиторий и запускает скрипт генерации:
2.1.1. run.sh (Linux/macOS): ./run.sh requirements.md
2.1.2. run.ps1 (Windows): .\run.ps1 requirements.md
2.1.3. Файл .md должен находиться в папке input/
2.1.4. Скрипт запускает Ollama, ожидает готовности модели, генерирует тест-кейсы, останавливает все сервисы
2.2. Система обрабатывает артефакт, генерирует тестовые box-сценарии через LLM. Ход выполнения отображается в stdout (на английском)
2.3. Система сохраняет результат в JSON и CSV в папку output/:
2.3.1. ./output/{filename}.json — для импорта в TMS
2.3.2. ./output/{filename}.csv — для просмотра в Excel (разделитель ;, столбцы step0..stepN до expectedResult)
2.4. Пользователь загружает JSON в TMS или открывает CSV в Excel

3. Функциональные требования
Требования описаны в [docs/FunctionalRequirements.md](docs/FunctionalRequirements.md). Чек-лист ревью — [docs/RequirementsReview.md](docs/RequirementsReview.md). Тест-кейсы — [docs/FunctionalRequirementsTests.md](docs/FunctionalRequirementsTests.md).

4. Нефункциональные требования
Требования описаны в [docs/NonFunctionalRequirements.md](docs/NonFunctionalRequirements.md). Тест-кейсы — [docs/NonFunctionalRequirementsTests.md](docs/NonFunctionalRequirementsTests.md).

5. Архитектура
5.1. Pipeline
CLI → Parser → Generator → Serializer
Error handling: LLM errors → stdout, без retry/circuit breaker

5.2. LLM
Провайдер: Ollama (localhost:11434). Развёртывание: sidecar (docker compose: app + ollama). Режим: CPU-only (GPU if available — автоматически). Типы: LLMProvider { generate(Requirements) → TestCase[] }

5.3. Типы данных
Requirements { title, sections[] }
Section { heading, content, subsections[] }
TestCase { id, title, preconditions, steps[], expectedResult }

5.4. Стек
Язык: Python. LLM-модели: Phi-4 Mini (стартовая). Кандидаты: Mistral 7B, Llama 3.1 8B, Qwen2.5 7B