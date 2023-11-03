import os
from PyQt6 import QtWidgets, QtGui, QtCore
import re
from Logger import logger
from TracksModel import TracksModel

PATTERN = r'.*\.(mp3|Mp3|MP3|flac)'
TAGS=["Catas", "Phiphi", "Deep", "Hard", "Retro", "Trance", "Best", "Ambiant", "Fun", "Zarb", "A Cappella"]

class Player(QtWidgets.QMainWindow):

    def __init__(self, conf):
        QtWidgets.QMainWindow.__init__(self, None)
        self.conf = conf
        self.setWindowTitle("Media Player")
        self.init_create_ui()
        self.keys = list(filter(lambda key_name: key_name[0:4] == 'Key_', dir(QtCore.Qt.Key)))
        self.filepaths = []

    def init_create_ui(self):
        self.widget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.widget)
        self.setAcceptDrops(True)

        self.tagsbuttonbox = QtWidgets.QHBoxLayout()

        self.tagbutton = {}
        for tag in TAGS:
            self.tagbutton[tag] = QtWidgets.QPushButton(tag)
            self.tagbutton[tag].setCheckable(True)
            # self.tagbutton[tag].clicked[bool].connect(self.set_tags)
            self.tagbutton[tag].setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
            self.tagsbuttonbox.addWidget(self.tagbutton[tag])

        self.topzone = QtWidgets.QHBoxLayout()
        self.topzone.addLayout(self.tagsbuttonbox)

        # self.filelist = QtWidgets.QListView()
        self.filelist = QtWidgets.QTableView()
        # self.filelist.clicked.connect(self.item_clicked)
        self.filelist.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)

        self.waveform = QtWidgets.QFrame()

        self.positionslider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal, self)
        self.positionslider.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.positionslider.setToolTip("Position")
        self.positionslider.setMaximum(1000)
        # self.positionslider.sliderMoved.connect(self.set_position)
        # self.positionslider.sliderPressed.connect(self.set_position)

        self.hbuttonbox = QtWidgets.QHBoxLayout()
        self.playbutton = QtWidgets.QPushButton("Play")
        self.hbuttonbox.addWidget(self.playbutton)
        # self.playbutton.clicked.connect(self.play_pause)

        self.stopbutton = QtWidgets.QPushButton("Stop")
        self.hbuttonbox.addWidget(self.stopbutton)
        # self.stopbutton.clicked.connect(self.stop)

        self.timelabel = QtWidgets.QLabel()
        # self.timelabel.setText(self.get_time_info())
        self.hbuttonbox.addWidget(self.timelabel)

        self.hbuttonbox.addStretch(1)
        self.volumeslider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal, self)
        self.volumeslider.setMaximum(100)
        # self.volumeslider.setValue(self.mediaplayer.audio_get_volume())
        self.volumeslider.setToolTip("Volume")
        self.hbuttonbox.addWidget(self.volumeslider)
        # self.volumeslider.valueChanged.connect(self.set_volume)

        self.lowzone = QtWidgets.QVBoxLayout()
        self.lowzone.addWidget(self.positionslider)
        self.lowzone.addLayout(self.hbuttonbox)

        self.vboxlayout = QtWidgets.QVBoxLayout()
        self.vboxlayout.addWidget(self.filelist)
        self.vboxlayout.addLayout(self.topzone)
        self.vboxlayout.addLayout(self.lowzone)

        self.widget.setLayout(self.vboxlayout)


    def dropEvent(self, e):
        dropped_data = e.mimeData().text()
        entries = dropped_data.split('\n')
        #.replace('file://','')
        # print(entries)
        if len(entries) == 0:
            print('0 entries dropped on app, ignoring')
            self.load_files([])
        elif len(entries) > 1:
            print('multiple entries dropped, keeping files only')
            self.load_files(entries)
        elif entries[0][-1] == '/':
            print('dropped a directory')
            self.load_dir(entries[0])
        else:
            print('dropped a file')
            self.load_files(entries)
        e.setDropAction(QtCore.Qt.DropAction.MoveAction)
        e.accept()

    def dragEnterEvent(self, e):
        e.accept()

    def keyPressEvent(self, event):
        key = event.key()
        # print('pressed from myDialog: ', key)
        if key == QtCore.Qt.Key.Key_Escape.value:
            self.close()
        logger.debug(self.key_to_enum(key))
        action = self.key_to_action(key)
        if (action):
            action()

    def key_to_action(self, key):
        actions = self.conf['actions']
        action_item = list(filter(lambda k: key == eval('QtCore.Qt.Key.'+actions[k]), actions.keys()))
        if (len(action_item) == 0):
            return None
        return eval(f'self.{action_item[0]}')

    def key_to_enum(self, key):
        keyname = list(filter(lambda k: key == eval('QtCore.Qt.Key.'+k), self.keys))
        if (len(keyname) == 0):
            return None
        return keyname[0]

    def load_dir(self, path):
        self.load_files(map(lambda f: path+f, sorted(os.listdir(path.replace('file://','')))))

    def load_files(self, filenames):
        self.filepaths = list(map(lambda f: f.replace('file://',''), filter(re.compile(PATTERN).match, filenames)))
        self.update_tracklist()

    def update_tracklist(self):
        self.track_model = TracksModel(tracks=self.filepaths)
        self.filelist.setModel(self.track_model)

    def quit(self):
        print('QUIT') 
        self.close()
    
    def move_to_dustbin(self):
        print("MOVE TO DUSTBIN")