# Cloud Storage Server

Сервер облачного хранилища на Python, в первую очередь ориентированный на запуск на ARMv8l 32-bit архитектуре. Предоставляет веб-интерфейс для управления файлами с поддержкой множественных баз данных.

## Возможности

- Веб-интерфейс на Flask с Bootstrap 5
- Поддержка баз данных: SQLite, MySQL, PostgreSQL, MariaDB
- Система аутентификации с хешированием паролей bcrypt
- Управление пользователями через административную панель
- Иерархическая организация файлов в папках
- Поиск по имени файла и содержимому
- REST API для интеграции с внешними системами
- Webhook уведомления о событиях
- Система логирования с ротацией файлов
- Оптимизация для ARM архитектуры

## Системные требования

- Python 3.8+
- Минимум 512MB RAM
- 1GB свободного места на диске


## Установка

### 1. Клонирование репозитория
```bash
git clone <repository-url>
cd cloud-storage
```

### 2. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 3. Создание конфигурации
```bash
python run.py --create-env
```

### 4. Настройка базы данных
```bash
# Для SQLite (по умолчанию)
python run.py --setup-db

# Для MySQL
python run.py --setup-db --database mysql

# Для PostgreSQL
python run.py --setup-db --database postgresql

# Для MariaDB
python run.py --setup-db --database mariadb
```



## Запуск

### Быстрый запуск (SQLite)
```bash
python run.py
```

### Запуск на определенном порту
```bash
python run.py --port 8080
```

### Запуск с определенной базой данных
```bash
python run.py --database mysql --port 5000
```

### Запуск в режиме отладки
```bash
python run.py --debug
```

### Запуск с SSL (временно не работает)
```bash
python run.py --ssl --cert cert.pem --key key.pem
```



## Конфигурация

### Переменные окружения (.env файл)

```env
# Тип базы данных
DATABASE_TYPE=sqlite

# Настройки сервера
PORT=5000
SECRET_KEY=your-secret-key
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=1073741824
DEBUG=False
FLASK_ENV=production

# SSL настройки
SSL_CERT_PATH=cert.pem
SSL_KEY_PATH=key.pem
SSL_ENABLED=False

# Безопасность
SESSION_COOKIE_SECURE=False
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax
PASSWORD_MIN_LENGTH=8
LOGIN_ATTEMPTS_LIMIT=5
LOGIN_BLOCK_TIME=300

# Файловые настройки
ALLOWED_EXTENSIONS=txt,pdf,png,jpg,jpeg,gif,doc,docx,xls,xlsx,zip,rar
MAX_FILE_SIZE=16777216
ENABLE_FILE_VERSIONING=True
ENABLE_FILE_ENCRYPTION=False

# Уведомления
ENABLE_WEBHOOKS=False
WEBHOOK_URL=
SLACK_WEBHOOK_URL=
EMAIL_NOTIFICATIONS=False
SMTP_SERVER=
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=

# SQLite
SQLITE_DATABASE_URI=sqlite:///cloud_storage.db

# MySQL
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=
MYSQL_DATABASE=cloud_storage

# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=
POSTGRES_DATABASE=cloud_storage

# MariaDB
MARIADB_HOST=localhost
MARIADB_PORT=3306
MARIADB_USER=root
MARIADB_PASSWORD=
MARIADB_DATABASE=cloud_storage

# Redis (для кеширования)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
```

## Базы данных

### SQLite (рекомендуется для ARM устройств)
- Встроенная база данных без внешних зависимостей
- Автоматическое резервное копирование
- Оптимальна для устройств с ограниченными ресурсами

### MySQL/MariaDB
- Высокая производительность для многопользовательских сценариев
- Поддержка репликации и кластеризации
- Требует установки сервера БД

### PostgreSQL
- Расширенные возможности и ACID совместимость
- Поддержка JSON и геоданных
- Требует установки сервера БД

## REST API

### Аутентификация
```bash
# Получение токена
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "password"}'

# Использование токена
curl -H "Authorization: Bearer <token>" \
  http://localhost:5000/api/files
```

### Основные эндпоинты

#### Файлы
```bash
# Список файлов
GET /api/files

# Загрузка файла
POST /api/files/upload

# Скачивание файла
GET /api/files/<file_id>/download

# Удаление файла
DELETE /api/files/<file_id>

# Поиск файлов
GET /api/files/search?q=<query>
```

#### Папки
```bash
# Создание папки
POST /api/folders

# Список папок
GET /api/folders

# Содержимое папки
GET /api/folders/<folder_id>/contents
```

#### Пользователи
```bash
# Список пользователей (только админ)
GET /api/users

# Создание пользователя (только админ)
POST /api/users

# Обновление профиля
PUT /api/users/profile
```

### Webhook события
```bash
# Настройка webhook
POST /api/webhooks

# События:
# - file.uploaded
# - file.deleted
# - file.downloaded
# - user.login
# - user.created
```

## Первый запуск

1. Запустите сервер: `python run.py`
2. Откройте браузер: `http://localhost:5000`
3. Войдите с учетными данными по умолчанию:
   - Логин: `admin`
   - Пароль: `admin123`


## Администрирование

### Создание пользователей
- Только администраторы могут создавать новые аккаунты
- Настройка лимитов хранилища для каждого пользователя
- Управление правами доступа и ролями

### Мониторинг системы
- Статистика использования хранилища
- Логи всех действий пользователей
- Мониторинг производительности и ресурсов
- Алерты при превышении лимитов

### Настройки сервера
- Выбор типа базы данных
- Настройка максимального размера файлов
- Конфигурация портов и хостов
- Настройка SSL/TLS

### Резервное копирование
```bash
# Автоматическое резервное копирование
python run.py --backup

# Восстановление из резервной копии
python run.py --restore backup_2024-01-01.zip

# Настройка cron для автоматических бэкапов
0 2 * * * cd /path/to/cloud-storage && python run.py --backup
```


## Безопасность

- Хеширование паролей с bcrypt (cost factor 12)
- Контроль доступа к файлам на уровне пользователя
- Валидация загружаемых файлов по расширению и размеру
- Логирование всех действий с временными метками
- Защита от CSRF атак
- Rate limiting для API (100 запросов/минуту)
- Блокировка после неудачных попыток входа (5 попыток, блокировка на 5 минут)
- Шифрование файлов AES-256 (опционально)

## Структура проекта

```
cloud-storage/
├── app.py              # Основное приложение Flask
├── config.py           # Конфигурация и настройки
├── models.py           # Модели базы данных SQLAlchemy
├── forms.py            # Формы веб-интерфейса WTForms
├── run.py              # Скрипт запуска с аргументами командной строки
├── requirements.txt    # Зависимости Python
├── .env                # Переменные окружения
├── templates/          # HTML шаблоны Jinja2
│   ├── base.html
│   ├── login.html
│   ├── index.html
│   ├── upload.html
│   ├── search.html
│   ├── settings.html
│   └── admin/
│       ├── users.html
│       ├── settings.html
│       ├── user_files.html
│       ├── user_storage.html
│       └── edit_user.html
├── static/             # Статические файлы
│   ├── css/
│   ├── js/
│   └── images/
├── uploads/            # Папка для загруженных файлов
├── logs/               # Логи приложения с ротацией
├── backups/            # Резервные копии БД и файлов
└── tests/              # Модульные и интеграционные тесты

```

## Развертывание в продакшене

### 1. Настройка безопасности
```bash
# Измените SECRET_KEY в .env файле
SECRET_KEY=your-very-long-random-secret-key

# Отключите режим отладки
FLASK_ENV=production

# Включите HTTPS
SSL_ENABLED=True
```

### 2. Использование Gunicorn
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 --timeout 120 --keep-alive 2 app:app
```



## Мониторинг и логирование

### Логирование
```python
# Настройка логирования в config.py
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/app.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'standard'
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard'
        }
    },
    'loggers': {
        '': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True
        }
    }
}
```

### Мониторинг с Prometheus
```python
# requirements.txt
prometheus-flask-exporter==0.22.4

# app.py
from prometheus_flask_exporter import PrometheusMetrics

metrics = PrometheusMetrics(app)
metrics.info('app_info', 'Application info', version='1.0.0')
```

### Grafana дашборд
```json
{
  "dashboard": {
    "title": "Cloud Storage Metrics",
    "panels": [
      {
        "title": "Active Users",
        "type": "stat",
        "targets": [
          {
            "expr": "cloud_storage_active_users",
            "legendFormat": "Users"
          }
        ]
      },
      {
        "title": "File Uploads",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(cloud_storage_file_uploads_total[5m])",
            "legendFormat": "Uploads/sec"
          }
        ]
      }
    ]
  }
}
```

## Резервное копирование

### Автоматические бэкапы
```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y-%m-%d_%H-%M-%S)
BACKUP_DIR="/backups"
PROJECT_DIR="/path/to/cloud-storage"

# Создание бэкапа
cd $PROJECT_DIR
python run.py --backup --output $BACKUP_DIR/backup_$DATE.zip

# Удаление старых бэкапов (старше 30 дней)
find $BACKUP_DIR -name "backup_*.zip" -mtime +30 -delete

# Отправка уведомления
curl -X POST $WEBHOOK_URL \
  -H "Content-Type: application/json" \
  -d "{\"text\":\"Backup completed: backup_$DATE.zip\"}"
```

### Восстановление
```bash
# Восстановление из бэкапа
python run.py --restore backup_2024-01-01.zip

# Проверка целостности
python run.py --verify-backup backup_2024-01-01.zip

# Список доступных бэкапов
python run.py --list-backups
```

## Устранение неполадок

### Проблемы с базой данных
```bash
# Проверьте подключение к БД
python run.py --setup-db --database mysql

# Создайте базу данных вручную
mysql -u root -p
CREATE DATABASE cloud_storage;

# Проверьте права пользователя
GRANT ALL PRIVILEGES ON cloud_storage.* TO 'user'@'localhost';
FLUSH PRIVILEGES;
```

### Проблемы с портами
```bash
# Проверьте занятые порты
netstat -tulpn | grep :5000

# Используйте другой порт
python run.py --port 8080

# Проверьте firewall
sudo ufw status
```

### Проблемы с правами доступа
```bash
# Создайте папку uploads
mkdir uploads
chmod 755 uploads

# Измените владельца
sudo chown -R www-data:www-data uploads/
sudo chown -R www-data:www-data logs/
sudo chown -R www-data:www-data backups/
```

### Проблемы с SSL
```bash
# Проверьте сертификат
openssl x509 -in cert.pem -text -noout

# Проверьте приватный ключ
openssl rsa -in key.pem -check

# Обновите Let's Encrypt сертификат
sudo certbot renew
```

### Проблемы с производительностью
```bash
# Проверьте использование памяти
htop
free -h

# Проверьте диск
df -h
iostat -x 1

# Оптимизируйте базу данных
python run.py --optimize-db
```


## Лицензия

MIT License - см. файл LICENSE для деталей.

## Поддержка

- Создайте Issue в GitHub
- Опишите проблему подробно
- Укажите версию Python и архитектуру устройства
- Приложите логи ошибок
- Опишите шаги для воспроизведения

### Каналы поддержки
- Email: RinKirsan@rkir.ru


## Обновления

```bash
# Обновите код
git pull origin main

# Обновите зависимости
pip install -r requirements.txt --upgrade

# Примените миграции БД
python run.py --migrate

# Перезапустите сервер
python run.py

# Проверьте работоспособность
python run.py --health-check
```

### Автоматические обновления
```bash
#!/bin/bash
# update.sh

cd /path/to/cloud-storage
git pull origin main
pip install -r requirements.txt --upgrade
python run.py --migrate
sudo systemctl restart cloud-storage
```



---

**Cloud Storage Server** - решение для облачного хранилища на ARM устройствах

*Последнее обновление: август 2025*
