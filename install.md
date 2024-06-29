# Utayomiの動作環境構築
* 参考:福山大工学部情報工学科 金子邦彦研究室 (2024年6月9日閲覧)  
    * WSL2 上の Ubuntu での NVIDIA CUDA ツールキット, NVIDIA cuDNN, PyTorch, TensorFlow 2.11 のインストールと動作確認（Windows 上）   
        https://www.kkaneko.jp/tools/wsl/wsl_tensorflow2.html  

現在、以下の環境で動作を確認しています。GPUアクセスが可能なWSL(Ubuntu)でも動作すると思いますが、確認はしていません。
* Intel(R) Core(TM) i7-8559U CPU @ 2.70GHz
* DRAM 32GB
* NVIDIA RTX A4000 VRAM16GB
* Ubuntu 22.04.3 LTS

環境構築にはUbuntuなどのLinuxのCLI動作に関する知識がある程度必要になります。  
nvidia-driver, cuda, cudnn等のGPUにアクセスするための環境構築は使用機器によって大きく異なるので、ここでは説明しません。  
nvcc -V やnvidia-smiなどのコマンドが動作する環境が本リポジトリを動作させる前提になります。  
以下の環境構築は、cuda version 12が動作する前提のコマンドです。  
具体的なcuda環境構築の方法については上記リンクのwebページなどを参照してください。  

```bash
# aptで利用する基本パッケージ等のアップデート
sudo apt -y update && sudo apt -y upgrade
sudo apt -y install python3-dev python3-pip python3-setuptools

# minicondaのインストール(インストール済みの場合は不要)
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh
bash ~/miniconda.sh -b -p $HOME/miniconda

# terminalを再起動, condaコマンドが動作することを確認

# tankaAIの仮想環境を構築
conda create -n tankaAI python=3.11 jupyterlab
conda activate tankaAI

# GPUで動作するpytorchのインストール
conda install pytorch torchvision torchaudio pytorch-cuda=12.1 -c pytorch -c nvidia
# pytorchのversion動作確認
python3 -c "import torch; print( torch.__version__ )"
# 2.2.0+cu121
python3 -c "import torch; print(torch.__version__, torch.cuda.is_available())"
# 2.2.0+cu121 True 

# 本リポジトリをクローン
git clone https://github.com/ef-utakata/Utayomi.git
cd Utayomi
# 動作に必要なpythonライブラリのインストール
pip install -r ./requirements.txt

# llama-cpp-python(GPU対応)をインストール(cuda-12の場合)
export CUDACXX="/usr/local/cuda-12/bin/nvcc"
export CMAKE_ARGS="-DLLAMA_CUBLAS=on -DCMAKE_CUDA_ARCHITECTURES=all-major"
export FORCE_CMAKE=1 
pip install fsspec llama-cpp-python --no-cache-dir --force-reinstall --upgrade