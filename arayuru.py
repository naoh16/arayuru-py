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
REFRESH_INTERVAL_MS = 160

# create pyAudio Object
pa = pyaudio.PyAudio()

class WavePlotWidget(pg.PlotWidget):
    def __init__(self, parent=None):
        pg.PlotWidget.__init__(self, parent=parent)

        self.setLimits(xMin=0, minYRange=20001, minXRange=3)

        item = self.getPlotItem()
        item.setMouseEnabled(y = False) # y軸固定
        item.enableAutoRange()
        ax = item.getAxis("bottom")
        ax.setLabel("Time [s]")

        self.wave_buffer = np.array([])

        # Data Lines
        self.plot_waveform = self.plot(np.array([0]), np.array([0]), pen='g')
        self.plot_curtime  = self.addLine(x=0, pen='r')

    def set_current_time(self, time_by_point):
        self.plot_curtime.setValue(min(time_by_point, len(self.wave_buffer)/SAMPLING_RATE))

    def reset_waveform(self):
        self.wave_buffer = np.array([])

    def add_waveform(self, waveform_frames):
        self.wave_buffer = np.append(self.wave_buffer, waveform_frames)
        self.update_plot_waveform()

    def update_plot_waveform(self):
        x = np.linspace(start=0, stop=len(self.wave_buffer)/SAMPLING_RATE, num=len(self.wave_buffer))
        self.plot_waveform.setData(x=x, y=self.wave_buffer)


class MyWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent=parent)

        self.wave_recorder = WaveRecorder()
        self.wave_player = WavePlayer()

        self.init_ui()
        self.init_default_listner()

    def set_record_timer(self):
        self.record_timer = QtCore.QTimer()
        self.record_timer.timeout.connect(self.onRecordData)
        self.record_timer.start(REFRESH_INTERVAL_MS)

    def onRecordData(self):
        frames = self.wave_recorder.get_data()

        self.wave_widget.add_waveform(frames)

    def set_play_timer(self):
        self.play_timer = QtCore.QTimer()
        self.play_timer.timeout.connect(self.onPlayData)
        self.play_timer.start(REFRESH_INTERVAL_MS)

    def onPlayData(self):
        if self.wave_player.stream.is_active():
            self.wave_widget.set_current_time(self.wave_player.get_current_time())
        else:
            self.wave_player.stop()
            self.click_stop_play()

    def init_default_listner(self):
        self.rec_button.clicked.connect(self.click_start_record)
        self.play_button.clicked.connect(self.click_start_play)

        self.next_button.clicked.connect(self.next_datafile)
        self.previous_button.clicked.connect(self.previous_datafile)

    def init_ui(self):
        self.rec_button = QtGui.QPushButton("REC START", parent=self)
        self.play_button  = QtGui.QPushButton("PLAY", parent=self)

        self.previous_button = QtGui.QPushButton("<-", parent=self)
        self.next_button     = QtGui.QPushButton("->", parent=self)
        #self.zoomup_button   = QtGui.QPushButton("+", parent=self)
        #self.zoomdown_button = QtGui.QPushButton("-", parent=self)

        self.reading_text = QtGui.QTextEdit(self)
        self.reading_text.setFontPointSize(20)
        self.reading_text.setText(u"あらゆる現実をすべて自分の方へねじ曲げたのだ。");

        self.datafile_text = QtGui.QLineEdit(self)
        self.datafile_text.setText("(null)");
        self.filenum_text = QtGui.QLineEdit(self)
        self.filenum_text.setText("0 / 0");
        self.filename_text = QtGui.QLineEdit(self)
        self.filename_text.setText("(null).wav");

        self.wave_widget = WavePlotWidget()

        layout = QtGui.QGridLayout()

        layout.addWidget(self.datafile_text, 0, 0, 1, 1)
        layout.addWidget(self.filenum_text,  0, 1, 1, 1)
        layout.addWidget(self.filename_text, 0, 2, 1, -1)

        layout.addWidget(self.reading_text, 1, 0, 2, 4)

        layout.addWidget(self.previous_button, 3, 0, 1, 1)
        #layout.addWidget(self.zoomup_button,   3, 1, 1, 1)
        #layout.addWidget(self.zoomdown_button, 3, 2, 1, 1)
        layout.addWidget(self.next_button,     3, 3, 1, 1)

        layout.addWidget(self.rec_button,   4, 0, 1, 2)
        layout.addWidget(self.play_button,  4, 3, 1, 1)

        layout.addWidget(self.wave_widget,  5, 0, 4, 4)

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
        self.wave_recorder = WaveRecorder()
        self.wave_widget.reset_waveform()

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

    def click_start_record(self):
        self.rec_button.setText("REC STOP")
        try:
            self.rec_button.clicked.disconnect()
        except Exception:
            pass
        finally:
            self.rec_button.clicked.connect(self.click_stop_record)

        self.play_button.setEnabled(False)
        self.set_record_timer()
        self.wave_widget.reset_waveform()

        self.wave_recorder.start_record(self.filename_text.text())

    def click_stop_record(self):
        self.rec_button.setText("REC START")
        try:
            self.rec_button.clicked.disconnect()
        except Exception:
            pass
        finally:
            self.rec_button.clicked.connect(self.click_start_record)

        self.play_button.setEnabled(True)

        self.wave_recorder.stop_record()
        self.record_timer.stop()

    def click_start_play(self):
        self.play_button.setText("STOP")
        try:
            self.play_button.clicked.disconnect()
        except Exception:
            pass
        finally:
            self.play_button.clicked.connect(self.click_stop_play)

        self.rec_button.setEnabled(False)
        self.set_play_timer()

        self.wave_player.start(self.filename_text.text())

    def click_stop_play(self):
        self.play_button.setText("PLAY")
        try:
            self.play_button.clicked.disconnect()
        except Exception:
            pass
        finally:
            self.play_button.clicked.connect(self.click_start_play)

        self.rec_button.setEnabled(True)
        self.wave_player.stop()
        self.play_timer.stop()


class WavePlayer():
    def __init__(self):
        self.is_stop_requested = False

        self.lock = threading.Lock()

    def get_current_time(self):
        try:
            return self.stream.get_time() - self._play_start_time
        except Exception:
            if self.wavefile:
                return self.wavefile.getnframes()
            else:
                return -1

    def start(self, filename):
        self.wavefile = wave.open(DIRNAME + '/' + filename, 'rb')
        self.stream = pa.open(stream_callback = self.cb_playing,
            format = pa.get_format_from_width(self.wavefile.getsampwidth()),
            channels = self.wavefile.getnchannels(), rate = self.wavefile.getframerate(),
            output = True)

        self.is_stop_requested = False
        self._play_start_time = self.stream.get_time()

        self.stream.start_stream()

    def cb_playing(self, in_data, frame_count, time_info, status):
        data = self.wavefile.readframes(frame_count)

        if frame_count > len(data)*self.wavefile.getsampwidth():
            return (data, pyaudio.paComplete)

        with self.lock:
            if self.is_stop_requested:
                return (data, pyaudio.paComplete)

        return (data, pyaudio.paContinue)

    def stop(self):
        with self.lock:
            self.is_stop_requested = True

        self.stream.stop_stream()
        self.stream.close()

        self.wavefile.close()

class WaveRecorder():
    def __init__(self):
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
#    widget = QtGui.QWidget()

#    my_widget = MyWidget(parent=widget)
    #panel_layout = QtGui.QVBoxLayout()
    #panel_layout.addWidget(my_widget)
    #widget.setLayout(panel_layout)
    my_widget = MyWidget(parent=None)

    ### Main Window
    main_window = QtGui.QMainWindow()
    main_window.setWindowTitle("ARAYURU.PY")
    # main_window.setCentralWidget(widget)
    main_window.setCentralWidget(my_widget)
    main_window.move(100, 100)
    main_window.show()

    try:
        my_widget.load_datafile(sys.argv[1])
    except IndexError:
        my_widget.load_datafile_default()

    return app.exec_()

if __name__ == '__main__':
    try:
        ret = main()
    finally:
        pa.terminate()
    sys.exit(ret)
