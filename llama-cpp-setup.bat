@echo off
echo Установка необходимых компонентов...

REM Установка Ninja и CMake (требуется иметь chocolatey)
REM Если у вас нет chocolatey, установите его или скачайте ninja и cmake вручную
choco install ninja -y
choco install cmake -y

REM Клонирование репозитория
git clone --recurse-submodules https://github.com/ggerganov/llama.cpp.git
cd llama.cpp

REM Сборка проекта
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=build -DLLAMA_BUILD_TESTS=OFF -DLLAMA_BUILD_EXAMPLES=ON -DLLAMA_BUILD_SERVER=ON -DBUILD_SHARED_LIBS=OFF
cmake --build build --config Release -j 2
cmake --install build --config Release

REM Добавление пути в PATH для текущей сессии
set PATH=%CD%\build\bin;%PATH%

echo Сборка завершена! Путь к бинарным файлам добавлен в PATH текущей сессии.
echo Полный путь: %CD%\build\bin
pause