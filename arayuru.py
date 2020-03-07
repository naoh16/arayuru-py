# -*- coding: utf-8 -*-
# vim: ft=python ts=4 sw=4 et
# Recording application
#
# Requirement
#   PyQt5
#   pyqtgraph
#   pyaudio
#
# You can install them as below command:
#   $ conda install pyqt=5 pyqtgraph
#   $ python -m pip install pyaudio
#
# Copyright (c) 2015-2020 Sunao Hara, Okayama University.

import os
import sys
import codecs
import re

from PyQt5 import QtGui, QtCore
import pyqtgraph as pg

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

        self.setLimits(xMin=0, minYRange=20001, minXRange=2)

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
        self.update_plot_waveform()
        self.set_current_time(0)

    def add_waveform(self, waveform_frames):
        self.wave_buffer = np.append(self.wave_buffer, waveform_frames)
        self.update_plot_waveform()

    def update_plot_waveform(self):
        x = np.linspace(start=0, stop=len(self.wave_buffer)/SAMPLING_RATE, num=len(self.wave_buffer))
        self.plot_waveform.setData(x=x, y=self.wave_buffer)

    def load_wavefile(self, wavefile):
        self.reset_waveform()
        with wave.open(wavefile, 'rb') as wf:
            raw_data = wf.readframes( wf.getnframes() )
            self.add_waveform(np.frombuffer(raw_data, dtype=np.int16))

class MyWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent=parent)

        self.wave_recorder = WaveRecorder()
        self.wave_player = WavePlayer()

        self.reading_script = ReadingScript()

        self.init_ui()
        self.init_default_listner()

    def keyPressEvent(self, e):

        # KEY_LEFT:
        if e.key() == QtCore.Qt.Key_Left:
            self.previous_datafile()
            return

        # KEY_RIGHT:
        if e.key() == QtCore.Qt.Key_Right:
            self.next_datafile()
            return

        # KEY_SPACE:
        if e.key() == QtCore.Qt.Key_Space:
            if self.rec_button.isEnabled():
                self.rec_button.click()
            return

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
        if self.wave_player.stream is None:
            return

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

        self.open_readfile_button.clicked.connect(self.open_readfile)

    def init_ui(self):
        self.rec_button = QtGui.QPushButton("REC START", parent=self)
        self.rec_button.setFixedHeight(50)
        self.play_button  = QtGui.QPushButton("PLAY", parent=self)
        self.play_button.setFixedHeight(50)

        self.previous_button = QtGui.QPushButton("<-", parent=self)
        self.previous_button.setFixedHeight(50)
        self.next_button     = QtGui.QPushButton("->", parent=self)
        self.next_button.setFixedHeight(50)
        #self.zoomup_button   = QtGui.QPushButton("+", parent=self)
        #self.zoomdown_button = QtGui.QPushButton("-", parent=self)

        self.open_readfile_button = QtGui.QPushButton("LOAD", parent=self)

        self.reading_text = QtGui.QTextEdit(self)
        self.reading_text.setFontPointSize(20)
        self.reading_text.setReadOnly(True)
        self.reading_text.setText(u"あらゆる現実をすべて自分の方へねじ曲げたのだ。")

        self.datafile_text = QtGui.QLineEdit("(null)", self)
        self.datafile_text.setReadOnly(True)
        self.filenum_text = QtGui.QLineEdit("0 / 0", self)
        self.filenum_text.setReadOnly(True)
        self.filename_text = QtGui.QLineEdit("(null).wav", self)

        self.wave_widget = WavePlotWidget()

        layout = QtGui.QGridLayout()

        layout.addWidget(self.datafile_text, 0, 0, 1, 2)
        layout.addWidget(self.open_readfile_button, 0, 2, 1, 1)

        layout.addWidget(self.filenum_text,  1, 0)
        layout.addWidget(self.filename_text, 1, 1)

        layout.addWidget(self.reading_text, 2, 0, 2, 2)

        layout.addWidget(self.previous_button, 4, 0, 1, 1)
        layout.addWidget(self.next_button,     4, 1, 1, 1)

        layout.addWidget(self.rec_button,   5, 0, 1, 2)
        layout.addWidget(self.play_button,  5, 2, 1, 1)

        layout.addWidget(self.wave_widget,  6, 0, 4, 4)

        self.setLayout(layout)

    def load_datafile(self, filename=None):
        if filename:
            self.reading_script.load_file(filename)
        
        self.update_datafile_view()
        self.update_wavedata()

    def update_datafile_view(self):
        scr = self.reading_script.current_script()

        # Update Script information
        self.datafile_text.setText(self.reading_script.filename())
        self.filenum_text.setText("{:d}/{:d}".format(scr['number'], self.reading_script.count()))
        self.filename_text.setText(scr['id'] + '.wav')

        if 'pron' in scr:
            self.reading_text.setText(scr['text'] + '\n--\n' + scr['pron'])
        else:
            self.reading_text.setText(scr['text'])

        # Update UI related to the script information
        self.previous_button.setEnabled(self.reading_script.has_prev())
        self.next_button.setEnabled(self.reading_script.has_next())

    def update_wavedata(self):
        self.wave_recorder = WaveRecorder()

        if os.path.isfile(DIRNAME + '/' + self.filename_text.text()):
            self.wave_widget.load_wavefile(DIRNAME + '/' + self.filename_text.text())
            self.play_button.setEnabled(True)
            sys.stderr.write('INFO: Load {:s}/{:s}\n'.format(DIRNAME, self.filename_text.text()))
        else:
            self.wave_widget.reset_waveform()
            self.play_button.setEnabled(False)

    def next_datafile(self):
        self.reading_script.next_script()
        self.update_datafile_view()
        self.update_wavedata()

    def open_readfile(self):
        filename = QtGui.QFileDialog.getOpenFileName(self, u'読み上げリストファイルを開く', filter=r'Text Files(*.txt +.tsv *.list);;All Files(*.*)')
        if os.path.isfile(filename):
            self.reading_script.load_file(filename)
            self.update_wavedata()

    def previous_datafile(self):
        self.reading_script.prev_script()
        self.update_datafile_view()
        self.update_wavedata()

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

        sys.stderr.write('INFO: SAVE: {:s}\n'.format(self.filename_text.text()))

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
        self.wave_widget.set_current_time(0)

class ReadingScript():
    def __init__(self):
        self._filename = ""
        self._script_data = list({'number': 1, 'id': 'A01', 'text': 'あらゆる現実をすべて自分の方へねじ曲げたのだ。'}) # this is dummy data
        self._current_text_number = 1  # This number should be start with 1 if this instance is activated

    def dump(self):
        for datum in self._script_data:
            print("{id:s}\t{text:s}".format(**datum))

    def load_file(self, filename):
        num = 0
        self._script_data = list()
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                # Skip comment line
                if line.startswith('#'):
                    continue
                
                # Read contents as 2-column CSV/TSV file
                # (1) Script ID
                # (2) Script text
                # (3) Pronounciation-hint text (optional)
                rows = re.split(r'[ \t,]+', line)
                num = num + 1
                datum = {'number': num, 'id': rows[0], 'text': rows[1]}
                if (len(rows) >= 3):
                    datum['pron'] = rows[2]
                self._script_data.append(datum)

        self._filename = filename
        self._current_text_number = 1

    def has_prev(self):
        return self._current_text_number > 1

    def has_next(self):
        return self._current_text_number < self.count()

    def count(self):
        return len(self._script_data)

    def filename(self):
        return self._filename

    def current_script(self):
        return self._script_data[self._current_text_number-1]

    def next_script(self):
        if self.has_next():
            self._current_text_number = self._current_text_number + 1

        return self._script_data[self._current_text_number-1]

    def prev_script(self):
        if self.has_prev():
            self._current_text_number = self._current_text_number - 1

        return self._script_data[self._current_text_number-1]


class WavePlayer():
    def __init__(self):
        self.is_stop_requested = False
        self.stream = None

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

        if not self.stream is None:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None

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
    
    def rotate_file(self, filename):
        fileparts = filename.rsplit('.', 2)
        suffix_number = 0
        
        # Find exist target file and its rotated files
        if os.path.exists("{:s}.{:s}".format(fileparts[0], fileparts[1])) :
            suffix_number = suffix_number + 1
        while os.path.exists("{:s},{:02d}.{:s}".format(fileparts[0], suffix_number, fileparts[1])) :
            suffix_number = suffix_number + 1
            if suffix_number >= 100:
                break
        
        # If we have rotated file, rotate each filenames
        while suffix_number > 1:
            src_filename = "{:s},{:02d}.{:s}".format(fileparts[0], suffix_number-1, fileparts[1])
            dst_filename = "{:s},{:02d}.{:s}".format(fileparts[0], suffix_number, fileparts[1])
            os.rename(src_filename, dst_filename)
            sys.stderr.write('INFO: ROTATE: {:s} --> {:s}\n'.format(src_filename, dst_filename))
            suffix_number = suffix_number - 1
        if suffix_number == 1:
            src_filename = "{:s}.{:s}".format(fileparts[0], fileparts[1])
            dst_filename = "{:s},{:02d}.{:s}".format(fileparts[0], suffix_number, fileparts[1])
            os.rename(src_filename, dst_filename)
            sys.stderr.write('INFO: ROTATE: {:s} --> {:s}\n'.format(src_filename, dst_filename))

        return filename

    def start_record(self, filename):
        self.is_stop_requested = False
        self.wavefile = wave.open(self.rotate_file(DIRNAME + '/' + filename), 'w')
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

        np_data = np.frombuffer(in_data, dtype=np.int16).astype(np.float32)

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
    my_widget = MyWidget(parent=None)

    ### Main Window
    main_window = QtGui.QMainWindow()
    main_window.setWindowTitle("ARAYURU.PY")
    main_window.setCentralWidget(my_widget)
    main_window.move(100, 100)
    main_window.show()

    try:
        my_widget.load_datafile(sys.argv[1])
    except IndexError:
        my_widget.load_datafile(None)

    return app.exec_()

if __name__ == '__main__':
    try:
        ret = main()
    finally:
        pa.terminate()
    sys.exit(ret)
