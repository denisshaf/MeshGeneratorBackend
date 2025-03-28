#! /bin/bash

sudo apt install ninja-build
sudo apt install cmake -y

git clone --recurse-submodules https://github.com/ggerganov/llama.cpp.git
cd llama.cpp

cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=build -DLLAMA_BUILD_TESTS=OFF -DLLAMA_BUILD_EXAMPLES=ON -DLLAMA_BUILD_SERVER=ON -DBUILD_SHARED_LIBS=OFF
cmake --build build --config Release -j 2
cmake --install build --config Release
export PATH="~/llama.cpp/build/bin:$PATH"