# arayuru-py
Python3/PyQtGraph(PyQt5)/PyAudioで作った読み上げ音声収録ツール

## Requirement

   - Python 3.7.x
   - PyQt5
   - pyqtgraph
   - pyaudio

## Installation

### Native envritonment

    $ pip install pyqt5 pyqtgraph
    $ pip install pyaudio

### Via venv module (recommended)

    $ python -mvenv .py
    $ .py/bin/activate
    (.py)$ pip install pyqt5 pyqtgraph
    (.py)$ pip install pyaudio

- Note: If you use Windows, `.py/bin/activate` should be replaced with `.py\Script\activate`

### Troubleshooting

- If you use Python>=3.7.x on Windows 10:
  - Please install `PyAudio-0.2.11-cp37-cp37m-win_amd64.whl` using [Unofficial package](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio)

## Usage

### Native python

    $ python arayuru.py sample.txt

### Via venv module (recommended)

    $ .py/bin/python arayuru.py sample.txt

- Note: If you use Windows, `.py/bin/python` should be replaced with `.py\Script\python`

## Windows 10 Executable

Google Driveにexeファイルと関連DLLをパッケージングしたzipファイルが置いてあります．
  - https://drive.google.com/drive/folders/0B4VPoQXZgUWHMng4OW43N3phMjA?usp=sharing
