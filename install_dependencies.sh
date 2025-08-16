#!/bin/bash

echo "Установка зависимостей для Cloud Storage на Termux..."

# Обновляем пакеты
echo "Обновление пакетов..."
pkg update -y

# Устанавливаем Python и необходимые пакеты
echo "Установка Python и зависимостей..."
pkg install -y python python-pip

# Устанавливаем системные зависимости для Pillow
echo "Установка системных зависимостей для Pillow..."
pkg install -y libjpeg-turbo libpng zlib freetype

# Обновляем pip
echo "Обновление pip..."
pip install --upgrade pip

# Устанавливаем Python зависимости
echo "Установка Python зависимостей..."
pip install -r requirements.txt

echo "Установка завершена!"
echo "Теперь можно запускать приложение командой: python run.py"
