#!/usr/bin/env python3
"""
Cloud Storage Server - Запуск сервера
Поддерживает различные базы данных и настройки порта
"""

import os
import sys
import argparse
from dotenv import load_dotenv
from app import create_app, db
from models import User

def create_env_file():
    """Создает файл .env с настройками по умолчанию"""
    env_content = """# Cloud Storage Server Configuration

# Тип базы данных (sqlite, mysql, postgresql, mariadb)
DATABASE_TYPE=sqlite

# SQLite настройки
SQLITE_DATABASE_URI=sqlite:///cloud_storage.db

# MySQL настройки
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=
MYSQL_DATABASE=cloud_storage

# PostgreSQL настройки
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=
POSTGRES_DATABASE=cloud_storage

# MariaDB настройки
MARIADB_HOST=localhost
MARIADB_PORT=3306
MARIADB_USER=root
MARIADB_PASSWORD=
MARIADB_DATABASE=cloud_storage

# Настройки сервера
PORT=5000
SECRET_KEY=your-secret-key-change-in-production
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=1073741824
STORAGE_LIMIT_DEFAULT=1073741824

# Окружение
FLASK_ENV=development
"""
    
    with open('.env', 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print("Файл .env создан с настройками по умолчанию")
    print("Отредактируйте его перед запуском в продакшене")

def setup_database(database_type):
    """Настройка базы данных"""
    print(f"Настройка базы данных: {database_type}")
    
    if database_type == 'mysql':
        print("Убедитесь, что MySQL сервер запущен и доступен")
        print("Создайте базу данных 'cloud_storage' если она не существует")
    elif database_type == 'postgresql':
        print("Убедитесь, что PostgreSQL сервер запущен и доступен")
        print("Создайте базу данных 'cloud_storage' если она не существует")
    elif database_type == 'mariadb':
        print("Убедитесь, что MariaDB сервер запущен и доступен")
        print("Создайте базу данных 'cloud_storage' если она не существует")
    else:
        print("Используется SQLite (встроенная база данных)")

def main():
    parser = argparse.ArgumentParser(description='Cloud Storage Server')
    parser.add_argument('--port', '-p', type=int, default=5000, help='Порт для запуска сервера')
    parser.add_argument('--host', default='0.0.0.0', help='Хост для запуска сервера')
    parser.add_argument('--database', '-d', choices=['sqlite', 'mysql', 'postgresql', 'mariadb'], 
                       help='Тип базы данных')
    parser.add_argument('--create-env', action='store_true', help='Создать файл .env')
    parser.add_argument('--setup-db', action='store_true', help='Настроить базу данных')
    parser.add_argument('--debug', action='store_true', help='Запустить в режиме отладки')
    
    args = parser.parse_args()
    
    # Создание .env файла
    if args.create_env:
        create_env_file()
        return
    
    # Загрузка переменных окружения
    load_dotenv()
    
    # Переопределение порта из аргументов командной строки
    if args.port != 5000:
        os.environ['PORT'] = str(args.port)
    
    # Переопределение типа базы данных
    if args.database:
        os.environ['DATABASE_TYPE'] = args.database
    
    # Настройка базы данных
    if args.setup_db:
        database_type = args.database or os.environ.get('DATABASE_TYPE', 'sqlite')
        setup_database(database_type)
        return
    
    # Создание приложения
    app = create_app()
    
    # Создание таблиц базы данных
    with app.app_context():
        print("Создание таблиц базы данных...")
        db.create_all()
        
        # Создание администратора по умолчанию
        admin = User.query.filter_by(is_admin=True).first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@example.com',
                is_admin=True,
                storage_limit=10 * 1024 * 1024 * 1024  # 10GB
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("✓ Администратор создан: username=admin, password=admin123")
        else:
            print("✓ Администратор уже существует")
    
    # Получение настроек
    port = int(os.environ.get('PORT', args.port))
    database_type = os.environ.get('DATABASE_TYPE', 'sqlite')
    upload_folder = os.environ.get('UPLOAD_FOLDER', 'uploads')
    
    # Создание папки для загрузок
    os.makedirs(upload_folder, exist_ok=True)
    
    print("\n" + "="*50)
    print("Cloud Storage Server")
    print("="*50)
    print(f"Порт: {port}")
    print(f"База данных: {database_type}")
    print(f"Папка загрузок: {upload_folder}")
    print(f"Режим отладки: {'Включен' if args.debug else 'Выключен'}")
    print("="*50)
    print(f"Сервер доступен по адресу: http://localhost:{port}")
    print(f"Веб-интерфейс: http://localhost:{port}")
    print("="*50)
    
    # Запуск сервера
    try:
        app.run(
            host=args.host, 
            port=port, 
            debug=args.debug or app.config['DEBUG'],
            use_reloader=False  # Отключаем автоперезагрузку для ARM устройств
        )
    except KeyboardInterrupt:
        print("\nСервер остановлен пользователем")
    except Exception as e:
        print(f"Ошибка запуска сервера: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
