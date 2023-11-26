import os, shutil
from PyQt6 import QtWidgets, QtGui, QtCore
import re
from Logger import logger
from TracksModel import TracksModel
import vlc
import Tools

PATTERN = r'.*\.(mp3|flac|aif|aiff)'
class Player(QtWidgets.QMainWindow):

    def __init__(self, conf):
        QtWidgets.QMainWindow.__init__(self, None)
        self.conf = conf
        self.setWindowTitle("Media Player")
        self.init_create_ui()
        self.keys = list(filter(lambda key_name: key_name[0:4] == 'Key_', dir(QtCore.Qt.Key)))
        # Create a basic vlc instance
        self.instance = vlc.get_default_instance()
        self.media = None
        # Create an empty vlc media player
        self.mediaplayer = self.instance.media_player_new()
        self.current_index = None

    def init_create_ui(self):
        self.widget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.widget)
        self.setAcceptDrops(True)

        self.filelist = QtWidgets.QTableView()
        self.filelist.clicked.connect(self.item_clicked)
        self.filelist.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.filelist.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)

        self.positionslider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal, self)
        self.positionslider.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.positionslider.setToolTip("Position")
        self.positionslider.setMaximum(1000)
        self.positionslider.sliderMoved.connect(self.set_position_from_slider)
        self.positionslider.sliderPressed.connect(self.set_position_from_slider)


        # BUTTONS
        self.vbuttonbox = QtWidgets.QVBoxLayout()
        self.playbutton = QtWidgets.QPushButton("Play")
        self.vbuttonbox.addWidget(self.playbutton)
        self.playbutton.clicked.connect(self.play_pause)
        self.playbutton.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)

        self.stopbutton = QtWidgets.QPushButton("Stop")
        self.vbuttonbox.addWidget(self.stopbutton)
        self.stopbutton.clicked.connect(self.stop)
        self.stopbutton.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        # /BUTTONS

        # LABELS

        self.hartistbox = QtWidgets.QHBoxLayout()
        self.artistLabel = QtWidgets.QLabel('Artist')
        self.hartistbox.addWidget(self.artistLabel)
        self.editableArtist = QtWidgets.QLineEdit()
        self.editableArtist.setFocusPolicy(QtCore.Qt.FocusPolicy.ClickFocus)
        self.hartistbox.addWidget(self.editableArtist)
        self.editableArtist.setEnabled(False)

        self.htitlebox = QtWidgets.QHBoxLayout()
        self.titleLabel = QtWidgets.QLabel('Title')
        self.htitlebox.addWidget(self.titleLabel)
        self.editableTitle = QtWidgets.QLineEdit()
        self.editableTitle.setFocusPolicy(QtCore.Qt.FocusPolicy.ClickFocus)
        self.htitlebox.addWidget(self.editableTitle)
        self.editableTitle.setEnabled(False)

        self.infobox = QtWidgets.QHBoxLayout()
        self.currenttimesLabel = QtWidgets.QLabel()
        self.infobox.addWidget(self.currenttimesLabel)
        self.currentbitrateLabel = QtWidgets.QLabel()
        self.infobox.addWidget(self.currentbitrateLabel)
        self.currentfilesizeLabel = QtWidgets.QLabel()
        self.infobox.addWidget(self.currentfilesizeLabel)

        self.vlabelbox = QtWidgets.QVBoxLayout()
        self.vlabelbox.addLayout(self.hartistbox)
        self.vlabelbox.addLayout(self.htitlebox)
        self.vlabelbox.addLayout(self.infobox)
        # /LABELS

        # self.timelabel = QtWidgets.QLabel()
        # self.timelabel.setText("self.get_time_info()")
        # self.hbuttonbox.addWidget(self.timelabel)

        # self.vbuttonbox.addStretch(1)
        # self.volumeslider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal, self)
        # self.volumeslider.setMaximum(100)
        # # self.volumeslider.setValue(self.mediaplayer.audio_get_volume())
        # self.volumeslider.setToolTip("Volume")
        # self.hbuttonbox.addWidget(self.volumeslider)
        # # self.volumeslider.valueChanged.connect(self.set_volume)

        self.lowzone = QtWidgets.QHBoxLayout()
        self.lowzone.addLayout(self.vbuttonbox)
        self.lowzone.addLayout(self.vlabelbox)

        self.vboxlayout = QtWidgets.QVBoxLayout()
        self.vboxlayout.addWidget(self.filelist)
        self.vboxlayout.addWidget(self.positionslider)
        self.vboxlayout.addLayout(self.lowzone)

        self.widget.setLayout(self.vboxlayout)

        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.update_ui_timer)

    def update_title_and_artist(self):
        self.track_model.update_title_and_artist(self.current_index, artist=self.editableArtist.text(), title=self.editableTitle.text())

    # HANDLERS
    def update_ui_timer(self):
        # Set the slider's position to its corresponding media position
        # Note that the setValue function only takes values of type int,
        # so we must first convert the corresponding media position.
        media_pos = int(self.mediaplayer.get_position() * 1000)
        self.positionslider.setValue(media_pos)

        time = f'{Tools.milliseconds_to_string(self.mediaplayer.get_time())} / {Tools.milliseconds_to_string(self.media.get_duration())}'
        self.currenttimesLabel.setText(f'{time}')

        # No need to call this function if nothing is played
        if not self.mediaplayer.is_playing():
            self.timer.stop()

            # After the video finished, the play button stills shows "Pause",
            # which is not the desired behavior of a media player.
            # This fixes that "bug".
            if not self.is_paused:
                self.stop()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.titleLabel.setFixedSize(self.artistLabel.size()) # force alignment

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
        if key == QtCore.Qt.Key.Key_Tab.value:
            self.reserved_tab_handler()
        logger.debug(self.key_to_enum(key))
        action = self.key_to_action(key)
        if (action):
            action()

    def reserved_tab_handler(self):
        """switch focus on editable inputs"""
        if not self.editableArtist.hasFocus() and not self.editableTitle.hasFocus():
            self.editableArtist.setFocus()
        elif self.editableArtist.hasFocus():
            self.editableArtist.clearFocus()
            self.editableTitle.setFocus()
        else:
            self.editableTitle.clearFocus()
            self.update_title_and_artist()

    def item_clicked(self):
        self.select(self.filelist.currentIndex().row())
        if self.load_current():
            self.play()

    def play_pause(self):
        if self.mediaplayer.is_playing():
            self.pause()
        else:
            self.play()


    def stop(self):
        self.mediaplayer.stop()
        # self.playbutton.setText("Play")

    def set_position_from_slider(self):
        '''
        this position comes from the slider which has a [0, 1000] range
        '''
        # TODO retrieve pos value from event
        # The vlc MediaPlayer needs a float value between 0 and 1, Qt uses
        # integer variables, so you need a factor; the higher the factor, the
        # more precise are the results (1000 should suffice).

        # Set the media position to where the slider was dragged
        pos = self.positionslider.value()
        self.set_position(pos/1000.0)

    # / HANDLERS

    # "Key_Escape": "quit"
    def key_to_action(self, key):
        actions = self.conf['actions']
        action_key = list(filter(lambda k: key == eval('QtCore.Qt.Key.'+k), actions.keys()))
        if (len(action_key) == 0):
            return None
        return eval(f'self.{actions[action_key[0]]}')

    def key_to_enum(self, key):
        keyname = list(filter(lambda k: key == eval('QtCore.Qt.Key.'+k), self.keys))
        if (len(keyname) == 0):
            return None
        return keyname[0]

    def update_ui_items(self):
        if self.current_index == None:
            self.editableArtist.setText()
            self.editableArtist.setEnabled(False)
            self.editableTitle.setText()
            self.editableTitle.setEnabled(False)
            self.currenttimesLabel.setText('')
            self.currentbitrateLabel.setText('')
        else:
            track = self.track_model.get_track(self.current_index)
            self.editableArtist.setText(track['artist'])
            self.editableArtist.setEnabled(True)
            self.editableTitle.setText(track['title'])
            self.editableTitle.setEnabled(True)
            self.currenttimesLabel.setText('')
            self.currentbitrateLabel.setText(f"{track['bitrate']} kbits")
            self.currentfilesizeLabel.setText(f"{track['filesize']}")

    def load_dir(self, path):
        self.load_files(map(lambda f: path+f, sorted(os.listdir(path.replace('file://','')))))

    def load_files(self, filenames):
        self.update_tracklist(list(map(lambda f: f.replace('file://',''), filter(re.compile(PATTERN, re.IGNORECASE).match, filenames))))

    def update_tracklist(self, filepaths):
        self.track_model = TracksModel(tracks=filepaths)
        self.filelist.setModel(self.track_model)
        header = self.filelist.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
        # header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        # header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        # header.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        # self.filelist.resizeColumnsToContents()

    def load_track(self, track):
        self.media = self.instance.media_new(track['fullname'])
        self.mediaplayer.set_media(self.media)
        self.editableArtist.clearFocus()
        self.editableTitle.clearFocus()

    def select(self, index: int = None, increment: int = None):
        if index != None and increment != None:
            logger.critical('Bad Coder')
            return
        elif increment != None:
            index = self.current_index
            if increment > 0:
                if index == None:
                    index = -1
                index += increment
            elif increment < 0:
                if index == None:
                    index = self.track_model.rowCount()
                index += increment

        if self.track_model.rowCount() == 0:
            index = None

        if index != None:
            if index < 0 or self.track_model.rowCount() <= index:
                index = (index + self.track_model.rowCount()) % self.track_model.rowCount()

        self.current_index = index
        # logger.debug(self.current_index)
        if self.current_index != None:
            self.filelist.selectRow(self.current_index)

        self.update_ui_items()

    def load_current(self) -> bool:
        if self.current_index == None:
            return False
        track = self.track_model.get_track(self.current_index)
        self.load_track(track)
        return True

    def pause(self):
        self.mediaplayer.pause()
        self.playbutton.setText("Play")
        self.is_paused = True
        self.timer.stop()

    def play(self):
        self.mediaplayer.play()
        self.playbutton.setText("Pause")
        self.timer.start()
        self.is_paused = False

    # KEYBOARD ACTIONS
    def quit(self):
        print('QUIT') 
        self.close()
    
    def play_next_track(self):
        self.select(increment=1)
        if self.load_current():
            self.play()
    
    def play_previous_track(self):
        self.select(increment=-1)
        if self.load_current():
            self.play()
    
    def set_position(self, pos: float):
        self.timer.stop()
        self.mediaplayer.set_position(pos)
        self.timer.start()

    def step_backward(self, seconds: int):
        self.step_forward(-seconds)

    def step_forward(self, seconds: int):
        self.set_position((self.mediaplayer.get_time() + seconds * 1000) / self.media.get_duration())

    def move_to_dustbin(self):
        self.move_file(self.conf['paths']['dustbin'])
    
    def keep_file(self):
        print("MOVE TO ")

    def clear_metas(self):
        if self.current_index != None:
            self.track_model.clear_metas(self.current_index)

    def incr_rating(self):
        if self.current_index != None:
            self.track_model.incr_rating(self.current_index)

    def set_style(self, style):
        # print(f'style: {style}')
        if self.current_index != None:
            self.track_model.set_style(self.current_index, style)
    # / KEYBOARD ACTIONS

    def move_file(self, dest_dir):
        if self.current_index == None:
            return
        self.stop()
        track = self.track_model.get_track(self.current_index)
        fullname = track['fullname']
        shutil.move(fullname, dest_dir)
        self.track_model.remove_track(self.current_index)
        self.select(increment=0)
        if self.load_current():
            self.play()
 