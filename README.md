# Cloud Storage Server

Современный сервер облачного хранилища на Python, аналог Google Drive и Яндекс.Диск. Разработан специально для работы на ARMv8l 32-bit устройствах (телефоны, планшеты, одноплатные компьютеры).

## 🚀 Возможности

- **Веб-интерфейс** - современный и адаптивный дизайн
- **Множественные базы данных** - SQLite, MySQL, PostgreSQL, MariaDB
- **Управление пользователями** - создание аккаунтов только администратором
- **Безопасность** - хеширование паролей, контроль доступа
- **Организация файлов** - папки, поиск, публичные ссылки
- **Статистика** - мониторинг использования хранилища
- **Логирование** - отслеживание всех действий пользователей
- **ARM оптимизация** - специально для мобильных устройств

## 📋 Требования

- Python 3.8+
- ARMv8l 32-bit архитектура (совместимо с ARM64)
- Минимум 512MB RAM
- 1GB свободного места на диске

## 🛠 Установка

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

## 🚀 Запуск

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

## ⚙️ Конфигурация

### Переменные окружения (.env файл)

```env
# Тип базы данных
DATABASE_TYPE=sqlite

# Настройки сервера
PORT=5000
SECRET_KEY=your-secret-key
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=1073741824

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
```

## 🗄️ Базы данных

### SQLite (рекомендуется для ARM устройств)
- Встроенная база данных
- Не требует дополнительных серверов
- Оптимальна для мобильных устройств

### MySQL/MariaDB
- Высокая производительность
- Поддержка множественных пользователей
- Требует установки сервера БД

### PostgreSQL
- Расширенные возможности
- Надежность и ACID совместимость
- Требует установки сервера БД

## 👤 Первый запуск

1. Запустите сервер: `python run.py`
2. Откройте браузер: `http://localhost:5000`
3. Войдите с учетными данными по умолчанию:
   - **Логин:** `admin`
   - **Пароль:** `admin123`

⚠️ **Важно:** Измените пароль администратора после первого входа!

## 🔧 Администрирование

### Создание пользователей
- Только администраторы могут создавать новые аккаунты
- Настройка лимитов хранилища для каждого пользователя
- Управление правами доступа

### Мониторинг системы
- Статистика использования хранилища
- Логи всех действий пользователей
- Мониторинг производительности

### Настройки сервера
- Выбор типа базы данных
- Настройка максимального размера файлов
- Конфигурация портов и хостов

## 📱 Оптимизация для ARM устройств

- Отключен автоперезагрузчик Flask
- Оптимизированные зависимости
- Минимальное потребление ресурсов
- Поддержка мобильных браузеров

## 🔒 Безопасность

- Хеширование паролей с bcrypt
- Контроль доступа к файлам
- Валидация загружаемых файлов
- Логирование всех действий
- Защита от CSRF атак

## 📁 Структура проекта

```
cloud-storage/
├── app.py              # Основное приложение Flask
├── config.py           # Конфигурация
├── models.py           # Модели базы данных
├── forms.py            # Формы веб-интерфейса
├── run.py              # Скрипт запуска
├── requirements.txt    # Зависимости Python
├── .env                # Переменные окружения
├── templates/          # HTML шаблоны
│   ├── base.html
│   ├── login.html
│   ├── index.html
│   ├── upload.html
│   └── admin/
├── uploads/            # Папка для загруженных файлов
└── cloud_storage.db    # База данных SQLite
```

## 🚀 Развертывание в продакшене

### 1. Настройка безопасности
```bash
# Измените SECRET_KEY в .env файле
SECRET_KEY=your-very-long-random-secret-key

# Отключите режим отладки
FLASK_ENV=production
```

### 2. Использование Gunicorn
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### 3. Настройка Nginx (опционально)
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 🐛 Устранение неполадок

### Проблемы с базой данных
```bash
# Проверьте подключение к БД
python run.py --setup-db --database mysql

# Создайте базу данных вручную
mysql -u root -p
CREATE DATABASE cloud_storage;
```

### Проблемы с портами
```bash
# Проверьте занятые порты
netstat -tulpn | grep :5000

# Используйте другой порт
python run.py --port 8080
```

### Проблемы с правами доступа
```bash
# Создайте папку uploads
mkdir uploads
chmod 755 uploads
```

## 📊 Производительность

### Рекомендуемые настройки для ARM устройств
- **SQLite** для устройств с < 1GB RAM
- **MySQL/MariaDB** для устройств с > 2GB RAM
- **PostgreSQL** для устройств с > 4GB RAM

### Оптимизация памяти
- Максимальный размер файла: 16MB (настраивается)
- Лимит хранилища по умолчанию: 1GB на пользователя
- Автоочистка временных файлов

## 🤝 Вклад в проект

1. Форкните репозиторий
2. Создайте ветку для новой функции
3. Внесите изменения
4. Создайте Pull Request

## 📄 Лицензия

MIT License - см. файл LICENSE для деталей.

## 🆘 Поддержка

- Создайте Issue в GitHub
- Опишите проблему подробно
- Укажите версию Python и архитектуру устройства

## 🔄 Обновления

```bash
# Обновите код
git pull origin main

# Обновите зависимости
pip install -r requirements.txt --upgrade

# Перезапустите сервер
python run.py
```

---

**Cloud Storage Server** - надежное решение для облачного хранилища на ARM устройствах! 🚀
