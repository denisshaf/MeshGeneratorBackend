@echo off
setlocal enabledelayedexpansion

set MODEL_NAME=LLaMA-Mesh

echo Клонирование модели из Hugging Face...
git clone https://huggingface.co/Zhengyi/LLaMA-Mesh

echo Создание виртуальной среды Python...
python -m venv %USERPROFILE%\llama.cpp\llama-cpp-venv

echo Активация виртуальной среды...
call %USERPROFILE%\llama.cpp\llama-cpp-venv\Scripts\activate.bat

echo Обновление pip, wheel и setuptools...
python -m pip install --upgrade pip wheel setuptools

echo Установка зависимостей...
pip install --upgrade -r %USERPROFILE%\llama.cpp\requirements\requirements-convert_hf_to_gguf.txt

echo Конвертация модели в формат GGUF...
python convert_hf_to_gguf.py %USERPROFILE%\%MODEL_NAME% --outfile %USERPROFILE%\%MODEL_NAME%\%MODEL_NAME%.gguf

echo Конвертация завершена!
pause