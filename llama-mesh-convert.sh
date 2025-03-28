#! /bin/bash

MODEL_NAME='LLaMA-Mesh'

git clone https://huggingface.co/Zhengyi/LLaMA-Mesh

python -m venv ~/llama.cpp/llama-cpp-venv
source ~/llama.cpp/llama-cpp-venv/bin/activate
python -m pip install --upgrade pip wheel setuptools
pip install --upgrade -r ~/llama.cpp/requirements/requirements-convert_hf_to_gguf.txt

python convert_hf_to_gguf.py ~/$MODEL_NAME --outfile ~/$MODEL_NAME/$MODEL_NAME'.gguf'
