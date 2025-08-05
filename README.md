## Быстрый старт

### Запуск проекта

1. **Клонирование репозитория:**
   ```bash
   git clone git@github.com:wladbelsky/generic_data_api.git
   cd generic_data_processor
   ```

2. **Запуск с помощью Docker Compose:**
   ```bash
   docker-compose up -d
   ```

3. **Проверка работы API:**
  - Откройте браузер и перейдите по адресу: http://localhost:8921/docs
  - Или выполните тестовый запрос:
   ```bash
   curl -X POST "http://localhost:8921/process_data" \
        -H "Content-Type: application/json" \
        -d '{"test": "data", "user": "example"}'
   ```

### Настройка окружения

- **CLICKHOUSE_URL** - URL подключения к ClickHouse (по умолчанию: `clickhouse+native://default:@clickhouse:9000`)
- **LOGGING_ENABLED** - включение/выключение логирования (по умолчанию: `true`)

### Порты

- **API сервис**: http://localhost:8921
- **ClickHouse HTTP**: http://localhost:8123
- **ClickHouse Native**: localhost:9000

---

## Техническое задание
### Название проекта
Асинхронный REST API-сервис обработки данных на FastAPI
### Цель
Разработать микросервис, обрабатывающий асинхронные HTTP-запросы и взаимодействующий с внешними API. Сервис должен быть контейнеризирован с помощью Docker.
Функциональные требования
1.	1. API-эндпоинт
POST /process_data/Принимает JSON с произвольной структурой.Описание поведения:- Выполняет асинхронную обработку данных.- Делает асинхронный HTTP-запрос к внешнему публичному API (например, https://catfact.ninja/fact).- Возвращает клиенту результат обработки, включая данные, полученные от внешнего API.
Технологические требования
- Язык: Python 3.11+
- Фреймворк: FastAPI
- Асинхронность: async/await, httpx
- Докеризация:  
  - Dockerfile для сборки образа  
   - docker-compose.yml для запуска с зависимостями- Контейнеризация: через Docker (возможность запуска через 1 команду)

Дополнительные пожелания (необязательно, но желательно)
- Логирование всех запросов и ответов- Обработка исключений и ошибок (try/except, FastAPI exception handlers)
- Использование Redis или другой БД для хранения истории запросов и ответов
- Покрытие основного функционала unit-тестами (например, pytest, httpx.AsyncClient)
- Файл .env и конфигурация проекта через Pydantic BaseSettings
- Swagger-документация (автоматически генерируется FastAPI)

### Репозиторий
Проект должен быть размещён в публичном GitHub/GitLab репозиторииСтруктура проекта:  
- app/    
  -    main.py    
  -    api/    
  -    services/    
  -    models/  
- tests/  
- Dockerfile  
- docker-compose.yml  
- requirements.txt / pyproject.toml  
- README.md

### Пример внешнего API
**GET** https://catfact.ninja/factВозвращает случайный факт о кошках в формате:
```json
{
  "fact": "Cats can rotate their ears 180 degrees.",
  "length": 42
}
```
