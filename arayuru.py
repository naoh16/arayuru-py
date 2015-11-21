# -*- coding: utf-8 -*-
# Recording application
#
# Requirement
#   PyQt4
#   pyqtgraph
#   pyaudio
#
# You can install them as below command:
#   $ conda install pyqt
#   $ python -m pip install pyqtgraph pyaudio
#
# Copyright (c) 2015 Sunao Hara, Okayama University.

import os
import sys
import codecs

#from PyQt4 import QtGui
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore

import pyaudio
import threading
import sys
import time
import wave

import numpy as np

DIRNAME = "record"
CHANNEL_NUM = 1
BIT_PER_SAMPLE = 16
SAMPLING_RATE  = 16000
BUFSIZE_SEC = 0.1

# create pyAudio Object
pa = pyaudio.PyAudio()

class MyWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent=parent)

        self.n = 0
        self.wave_recorder = WaveRecorder()
        self.wave_buffer = np.array([])

        self.init_ui()

        self.set_timer()

    def _init_plot_window(self):
        ### スペクトル表示用ウィジット
        wave_widget = pg.PlotWidget(name="audio signal")
        wave_widget.setLimits(xMin=0, minYRange=20001, minXRange=3)

        item = wave_widget.getPlotItem()
        item.setMouseEnabled(y = False) # y軸固定
        item.enableAutoRange()
        ax = item.getAxis("bottom")
        ax.setLabel("Time [s]")

        ### Plotしつつ後のためにキープ
        self.wave_widget = wave_widget.plot(np.array([0]), np.array([0]), pen='g')

        return wave_widget

    def set_timer(self):
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.onRecordData)
        self.timer.start(100)

    def onRecordData(self):
        frames = self.wave_recorder.get_data()

        if len(frames) > 0:
            self.wave_buffer = np.append(self.wave_buffer, frames)
            max_amp = np.amax(np.absolute(frames))

            self.pbar.setValue(max_amp)
            #print("> " + str(len(self.wave_buffer)) + '>'+ str(max_amp))
            x = np.linspace(start=0, stop=len(self.wave_buffer)/16000, num=len(self.wave_buffer))
            self.wave_widget.setData(x=x, y=self.wave_buffer)
            self.n += 1

    def init_ui(self):
        self.rec_button = QtGui.QPushButton("REC START", parent=self)
        self.play_button  = QtGui.QPushButton("PLAY", parent=self)

        self.previous_button = QtGui.QPushButton("<-", parent=self)
        self.next_button     = QtGui.QPushButton("->", parent=self)
        self.zoomup_button   = QtGui.QPushButton("+", parent=self)
        self.zoomdown_button = QtGui.QPushButton("-", parent=self)

        self.pbar = QtGui.QProgressBar(self)
        self.pbar.setTextVisible(0)
        self.pbar.setRange(0, 32768)

        self.reading_text = QtGui.QTextEdit(self)
        self.reading_text.setFontPointSize(20)
        self.reading_text.setText(u"あらゆる現実をすべて自分の方へねじ曲げたのだ。");

        self.datafile_text = QtGui.QLineEdit(self)
        self.datafile_text.setText("(null)");
        self.filenum_text = QtGui.QLineEdit(self)
        self.filenum_text.setText("0 / 0");
        self.filename_text = QtGui.QLineEdit(self)
        self.filename_text.setText("(null).wav");

        layout = QtGui.QGridLayout()

        layout.addWidget(self.datafile_text, 0, 0, 1, 1)
        layout.addWidget(self.filenum_text,  0, 1, 1, 1)
        layout.addWidget(self.filename_text, 0, 2, 1, -1)

        layout.addWidget(self.reading_text, 1, 0, 2, 4)

        layout.addWidget(self.previous_button, 3, 0, 1, 1)
        layout.addWidget(self.zoomup_button,   3, 1, 1, 1)
        layout.addWidget(self.zoomdown_button, 3, 2, 1, 1)
        layout.addWidget(self.next_button,     3, 3, 1, 1)

        layout.addWidget(self.rec_button, 4, 0, 1, 2)
        layout.addWidget(self.play_button,  4, 3, 1, 1)

        layout.addWidget(self.pbar,         5, 0, 1, 5)

        layout.addWidget(self._init_plot_window(), 6, 0, 4, 5)

        self.setLayout(layout)

    def load_datafile(self, filename):
        self.dataset_filename = filename;
        fp = codecs.open(self.dataset_filename, 'r', 'utf-8')
        self.dataset_texts = fp.readlines()
        fp.close()
        self.reset_datafile_view()

    def load_datafile_default(self):
        self.dataset_filename = "A";
        self.dataset_texts = ["A01 あらゆる現実をすべて自分の方へねじ曲げたのだ。"]
        self.reset_datafile_view()

    def reset_datafile_view(self):
        self.cur_line_num = 0;
        d = self.dataset_texts[0].split()

        self.datafile_text.setText(self.dataset_filename)
        self.filenum_text.setText('1 / ' + str(len(self.dataset_texts)))
        self.filename_text.setText(d[0] + '.wav')
        self.reading_text.setText(d[1])

    def reset_data(self):
        self.n = 0
        self.wave_recorder = WaveRecorder()
        self.wave_buffer = np.array([])
        self.wave_widget.setData(y=self.wave_buffer)

    def next_datafile(self):
        if self.cur_line_num + 1 < len(self.dataset_texts):
            self.cur_line_num += 1
            d = self.dataset_texts[self.cur_line_num].split()

            self.filenum_text.setText(str(self.cur_line_num + 1) + ' / ' + str(len(self.dataset_texts)))
            self.filename_text.setText(d[0] + '.wav')
            self.reading_text.setText(d[1])

            self.reset_data()

    def previous_datafile(self):
        if self.cur_line_num - 1 >= 0:
            self.cur_line_num -= 1
            d = self.dataset_texts[self.cur_line_num].split()

            self.filenum_text.setText(str(self.cur_line_num + 1) + ' / ' + str(len(self.dataset_texts)))
            self.filename_text.setText(d[0] + '.wav')
            self.reading_text.setText(d[1])

            self.reset_data()

class WavePlayer():
    def __init__(self):
        self.block_size = 1024

    def start(self, filename):
        self.wavefile = wave.open(DIRNAME + '/' + filename, 'rb')
        self.stream = pa.open(#stream_callback = self.cb_recording,
            format = pa.get_format_from_width(self.wavefile.getsampwidth()),
            channels = self.wavefile.getnchannels(), rate = self.wavefile.getframerate(),
            output = True)

        data = self.wavefile.readframes(self.block_size)

        while len(data) > 0:
            self.stream.write(data)
            data = self.wavefile.readframes(self.block_size)

        self.stream.stop_stream()
        self.stream.close()

class WaveRecorder():
    def __init__(self):
        self.qt_bar = None
        self.wave_widget = None
        self.n = 0
        self.is_stop_requested = False

        self.lock = threading.Lock()
        self.signal_data = []

    def get_data(self):
        with self.lock:
            signal_data = self.signal_data
            self.signal_data = []
            return signal_data

    def start_record(self, filename):
        self.is_stop_requested = False
        self.wavefile = wave.open(DIRNAME + '/' + filename, 'w')
        self.wavefile.setnchannels(CHANNEL_NUM)
        self.wavefile.setsampwidth(int(BIT_PER_SAMPLE / 8))
        self.wavefile.setframerate(SAMPLING_RATE)
        self.stream = pa.open(stream_callback = self.cb_recording,
            format = pa.get_format_from_width(int(BIT_PER_SAMPLE / 8)),
            channels = CHANNEL_NUM, rate = SAMPLING_RATE,
            frames_per_buffer = int(BUFSIZE_SEC * CHANNEL_NUM * SAMPLING_RATE * BIT_PER_SAMPLE / 8),
            input = True, output = False)
        self.stream.start_stream()

    def cb_recording(self, in_data, frame_count, time_info, status):
        self.wavefile.writeframes(in_data)

        np_data = np.fromstring(in_data, dtype=np.int16).astype(np.float32)
        max_amp = np.amax(np.absolute(np_data))

        with self.lock:
            self.signal_data.append(np_data)
            if self.is_stop_requested:
                return (None, pyaudio.paComplete)

        return (None, pyaudio.paContinue)

    def stop_record(self):
        with self.lock:
            self.is_stop_requested = True

        self.stream.stop_stream()
        self.stream.close()

        self.wavefile.close()

def main():
    # Create directory for recorded wavefiles
    if not os.path.exists(DIRNAME):
        os.mkdir(DIRNAME)
    
    app = QtGui.QApplication(sys.argv)
    widget = QtGui.QWidget()

    wavplayer = WavePlayer();

    my_widget = MyWidget(parent=widget)
    panel_layout = QtGui.QVBoxLayout()
    panel_layout.addWidget(my_widget)
    widget.setLayout(panel_layout)

    """ Main Window """
    main_window = QtGui.QMainWindow()
    main_window.setWindowTitle("ARAYURU.PY")
    main_window.setCentralWidget(widget)
    main_window.show()

    """ event listner """
    def click_start_record():
        my_widget.rec_button.setText("REC STOP")
        my_widget.rec_button.clicked.connect(click_stop_record)
        my_widget.wave_recorder.start_record(my_widget.filename_text.text())

    def click_stop_record():
        my_widget.rec_button.setText("REC START")
        my_widget.rec_button.clicked.connect(click_start_record)
        my_widget.wave_recorder.stop_record()

    def click_start_play():
        #my_widget.play_button.setText("STOP")
        #my_widget.play_button.clicked.connect(click_stop_play)

        wavplayer.start(my_widget.filename_text.text())

#    def click_stop_play():
#        my_widget.play_button.setText("PLAY")
#        my_widget.play_button.clicked.connect(click_start_play)

    my_widget.rec_button.clicked.connect(click_start_record)
    my_widget.play_button.clicked.connect(click_start_play)

    try:
        my_widget.load_datafile(sys.argv[1])
    except IndexError:
        my_widget.load_datafile_default()
    my_widget.next_button.clicked.connect(my_widget.next_datafile)
    my_widget.previous_button.clicked.connect(my_widget.previous_datafile)

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
    pa.terminate()
    print("Finish.")
