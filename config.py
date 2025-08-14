import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'uploads'
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 1073741824))  # 1GB по умолчанию
    STORAGE_LIMIT_DEFAULT = int(os.environ.get('STORAGE_LIMIT_DEFAULT', 1073741824))  # 1GB по умолчанию
    
    # Database configurations
    DATABASE_TYPE = os.environ.get('DATABASE_TYPE', 'sqlite').lower()
    
    # SQLite configuration
    SQLITE_DATABASE_URI = os.environ.get('SQLITE_DATABASE_URI') or 'sqlite:///cloud_storage.db'
    
    # MySQL configuration
    MYSQL_HOST = os.environ.get('MYSQL_HOST') or 'localhost'
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT') or 3306)
    MYSQL_USER = os.environ.get('MYSQL_USER') or 'root'
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD') or ''
    MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE') or 'cloud_storage'
    
    # PostgreSQL configuration
    POSTGRES_HOST = os.environ.get('POSTGRES_HOST') or 'localhost'
    POSTGRES_PORT = int(os.environ.get('POSTGRES_PORT') or 5432)
    POSTGRES_USER = os.environ.get('POSTGRES_USER') or 'postgres'
    POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD') or ''
    POSTGRES_DATABASE = os.environ.get('POSTGRES_DATABASE') or 'cloud_storage'
    
    # MariaDB configuration
    MARIADB_HOST = os.environ.get('MARIADB_HOST') or 'localhost'
    MARIADB_PORT = int(os.environ.get('MARIADB_PORT') or 3306)
    MARIADB_USER = os.environ.get('MARIADB_USER') or 'root'
    MARIADB_PASSWORD = os.environ.get('MARIADB_PASSWORD') or ''
    MARIADB_DATABASE = os.environ.get('MARIADB_DATABASE') or 'cloud_storage'
    
    @classmethod
    def get_database_uri(cls):
        """Get database URI based on DATABASE_TYPE"""
        if cls.DATABASE_TYPE == 'mysql':
            return f"mysql+pymysql://{cls.MYSQL_USER}:{cls.MYSQL_PASSWORD}@{cls.MYSQL_HOST}:{cls.MYSQL_PORT}/{cls.MYSQL_DATABASE}"
        elif cls.DATABASE_TYPE == 'postgresql':
            return f"postgresql://{cls.POSTGRES_USER}:{cls.POSTGRES_PASSWORD}@{cls.POSTGRES_HOST}:{cls.POSTGRES_PORT}/{cls.POSTGRES_DATABASE}"
        elif cls.DATABASE_TYPE == 'mariadb':
            return f"mysql+pymysql://{cls.MARIADB_USER}:{cls.MARIADB_PASSWORD}@{cls.MARIADB_HOST}:{cls.MARIADB_PORT}/{cls.MARIADB_DATABASE}"
        else:  # Default to SQLite
            return cls.SQLITE_DATABASE_URI

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

class TestingConfig(Config):
    TESTING = True
    DATABASE_TYPE = 'sqlite'
    SQLITE_DATABASE_URI = 'sqlite:///:memory:'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
