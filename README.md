# arayuru-py
Python3/PyQtGraph(PySide6)/PyAudioで作った読み上げ音声収録ツール

## Requirement

   - Python >= 3.11
   - PySide6 < 6.9
   - pyqtgraph
   - pyaudio

## Installation

### a) uv (recommended)

- Install `uv`: https://docs.astral.sh/uv/getting-started/installation/
- Install packages

    $ uv sync

### b) Native envrinment

    $ pip install "pyside6<6.9" pyqtgraph
    $ pip install pyaudio

### b) venv module

    $ python -mvenv --prompt arayuru .env
    $ .env/bin/activate
    (arayuru)$ pip install "pyside6<6.9" pyqtgraph
    (arayuru)$ pip install pyaudio

- Note: If you use Windows, `.env/bin/activate` should be replaced with `.env\Script\activate`

### Troubleshooting

- If you use Python>=3.7.x on Windows 10:
  - Please install `PyAudio-0.2.11-cp37-cp37m-win_amd64.whl` using [Unofficial package](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio)

## Usage

### a) uv (recommended)

    $ uv run arayuru.py sample.txt

### b) Native python

    $ python arayuru.py sample.txt

### c) venv module

    $ .env/bin/python arayuru.py sample.txt

- Note: If you use Windows, `.env/bin/python` should be replaced with `.env\Script\python`

## Windows 10 Executable

~Google Driveにexeファイルと関連DLLをパッケージングしたzipファイルが置いてあります．~
  - https://drive.google.com/drive/folders/0B4VPoQXZgUWHMng4OW43N3phMjA?usp=sharing
