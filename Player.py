import os
from pathlib import Path
import shutil
from PyQt6 import QtWidgets, QtCore, QtGui
from Logger import logger, set_log_level
from TracksModel import TracksModel
import vlc
import Tools
from Conf import Conf
import Discogs

PATTERN = r"^.*\.(mp3|flac|aif|aiff)$"


class Player(QtWidgets.QMainWindow):
    def __init__(self, conffilename: str, app: QtWidgets.QApplication):
        self.app = app
        self.conffilename = conffilename
        self.track_model = TracksModel()
        QtWidgets.QMainWindow.__init__(self, None)
        self.setWindowTitle("Media Player")
        self.init_create_ui()
        self.keys = list(
            filter(lambda key_name: key_name[0:4] == "Key_", dir(QtCore.Qt.Key))
        )
        # Create a basic vlc instance
        self.instance = vlc.get_default_instance()
        self.media = None
        # Create an empty vlc media player
        self.mediaplayer = self.instance.media_player_new()
        self.current_index = None
        self.current_replay_speed = 1.0
        self.setWindowTitle("Tracks Organizer")
        self.load_current_conffile()

    def init_create_ui(self):
        self.widget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.widget)
        self.setAcceptDrops(True)

        self.filelist = QtWidgets.QTableView()
        self.filelist.setModel(self.track_model)
        self.filelist.clicked.connect(self.item_clicked)
        self.filelist.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.filelist.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        header = self.filelist.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)

        self.positionslider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal, self)
        self.positionslider.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.positionslider.setToolTip("Position")
        self.positionslider.setMaximum(1000)
        self.positionslider.setTickInterval(100)
        self.positionslider.setTickPosition(QtWidgets.QSlider.TickPosition.TicksBelow)
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

        self.autoplaycheckbox = QtWidgets.QCheckBox("auto play")
        self.vbuttonbox.addWidget(self.autoplaycheckbox)
        self.autoplaycheckbox.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)

        self.speedLabel = QtWidgets.QLabel("speed: 1.0")
        self.vbuttonbox.addWidget(self.speedLabel)
        # /BUTTONS

        # LABELS

        self.hartistbox = QtWidgets.QHBoxLayout()
        self.artistLabel = QtWidgets.QLabel("Artist")
        self.hartistbox.addWidget(self.artistLabel)
        self.editableArtist = QtWidgets.QLineEdit()
        self.editableArtist.setFocusPolicy(QtCore.Qt.FocusPolicy.ClickFocus)
        self.hartistbox.addWidget(self.editableArtist)
        self.editableArtist.setEnabled(False)

        self.htitlebox = QtWidgets.QHBoxLayout()
        self.titleLabel = QtWidgets.QLabel("Title")
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

        self.lowzone = QtWidgets.QHBoxLayout()
        self.lowzone.addLayout(self.vbuttonbox)
        self.lowzone.addLayout(self.vlabelbox)

        self.vboxlayout = QtWidgets.QVBoxLayout()
        self.vboxlayout.addWidget(self.filelist)
        self.vboxlayout.addWidget(self.positionslider)
        self.vboxlayout.addLayout(self.lowzone)

        self.widget.setLayout(self.vboxlayout)

        # MENU
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("File")

        clearfilelist_action = QtGui.QAction("Clear tracks", self)
        file_menu.addAction(clearfilelist_action)
        clearfilelist_action.triggered.connect(self.clear_filelist)

        file_menu.addSeparator()

        confopen_action = QtGui.QAction("Open configuration file", self)
        file_menu.addAction(confopen_action)
        confopen_action.triggered.connect(self.open_conffile)
        self.confreload_action = QtGui.QAction(
            f"Reload configuration file ({self.conffilename})", self
        )
        file_menu.addAction(self.confreload_action)
        self.confreload_action.triggered.connect(self.load_current_conffile)
        copytoclipboard_action = QtGui.QAction("Copy to clipboard", self)
        file_menu.addAction(copytoclipboard_action)
        copytoclipboard_action.triggered.connect(self.copy_to_clipboard)

        file_menu.addSeparator()

        quit_action = QtGui.QAction("Quit", self)
        file_menu.addAction(quit_action)
        quit_action.triggered.connect(self.quit)

        # /MENU

        # TOOLBAR
        toolbar = QtWidgets.QToolBar("My main toolbar")
        self.addToolBar(toolbar)

        toolbar.addAction(clearfilelist_action)
        toolbar.addSeparator()
        toolbar.addAction(confopen_action)
        toolbar.addAction(self.confreload_action)
        toolbar.addSeparator()
        toolbar.addAction(copytoclipboard_action)

        # /TOOLBAR

        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.update_ui_timer)
        self.timer.stop()

    def update_title_and_artist(self):
        self.track_model.update_title_and_artist(
            self.current_index,
            artist=self.editableArtist.text(),
            title=self.editableTitle.text(),
        )

    # HANDLERS

    def clear_filelist(self):
        self.track_model.clear()
        self.current_index = None
        self.editableArtist.setText('')
        self.editableTitle.setText('')

    def copy_to_clipboard(self):
        if self.current_index != None:
            text = f"{self.editableArtist.text()} {self.editableTitle.text()}"
            self.app.clipboard().setText(text)

    def open_conffile(self):
        # returns a tuple
        conffilename = QtWidgets.QFileDialog.getOpenFileName(
            self, "Choose YAML configuration file", filter=" Yaml Files (*.yml *.yaml)"
        )
        conffilename = conffilename[0]
        if len(conffilename) > 4:
            self.conffilename = conffilename
            self.load_current_conffile()

    def load_current_conffile(self):
        logger.debug(f"Load conffile: {self.conffilename}")
        Conf.load(self.conffilename)
        self.confreload_action.setText(
            f"Reload configuration file ({self.conffilename})"
        )
        self.autoplaycheckbox.setChecked(Conf.conf_data["conf"]["auto_play_next_track"])
        set_log_level(Conf.conf_data["conf"]["log_level"])

    def update_ui_timer(self):
        # Set the slider's position to its corresponding media position
        # Note that the setValue function only takes values of type int,
        # so we must first convert the corresponding media position.
        media_pos = int(self.mediaplayer.get_position() * 1000)
        self.positionslider.setValue(media_pos)
        self.speedLabel.setText(f"speed: {self.current_replay_speed:.1f}")

        if self.current_index is not None:
            time = f"{Tools.milliseconds_to_string(self.mediaplayer.get_time())} / {Tools.milliseconds_to_string(self.media.get_duration())}"
            self.currenttimesLabel.setText(f"{time}")

        # No need to call this function if nothing is played
        if not self.mediaplayer.is_playing():
            if self.autoplaycheckbox.isChecked():
                self.play_next_track()
            else:
                self.timer.stop()
                self.playbutton.setText("Play")

                # After the video finished, the play button stills shows "Pause",
                # which is not the desired behavior of a media player.
                # This fixes that "bug".
                if not self.is_paused:
                    self.stop()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.titleLabel.setFixedSize(self.artistLabel.size())  # force alignment

    def dropEvent(self, e):
        import urllib.parse
        from pathlib import Path

        # drag and drop with filenames containing spaces replaces them with '%20'
        # and other character encondings
        dropped_data = urllib.parse.unquote(e.mimeData().text())
        # logger.debug(f'---{dropped_data}---')
        dropped_data = dropped_data.replace("\r", "")
        dropped_paths = list(
            map(
                lambda f: Path(f.replace("file://", "")),
                filter(lambda f: len(f) > 0, dropped_data.split("\n")),
            )
        )
        # logger.debug(dropped_paths)
        filepaths = Tools.scan_paths(dropped_paths, PATTERN)
        # logger.debug(filepaths)
        self.load_files(filepaths)
        e.setDropAction(QtCore.Qt.DropAction.MoveAction)
        e.accept()

    def dragEnterEvent(self, e):
        logger.debug(e.mimeData())
        e.accept()

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        key = event.key()
        # print('pressed from myDialog: ', key)
        if key == QtCore.Qt.Key.Key_Tab.value:
            self.reserved_tab_handler()
        logger.debug(self.key_to_enum(key))
        if not self.editableArtist.hasFocus() and not self.editableTitle.hasFocus():
            action = self.key_to_action(key)
            if action:
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
            if self.current_index == None:
                self.play_next_track()
            else:
                self.play()

    def stop(self):
        self.mediaplayer.stop()
        self.timer.stop()
        self.playbutton.setText("Play")

    def set_position_from_slider(self):
        """
        this position comes from the slider which has a [0, 1000] range
        """
        # The vlc MediaPlayer needs a float value between 0 and 1, Qt uses
        # integer variables, so you need a factor; the higher the factor, the
        # more precise are the results (1000 should suffice).

        # Set the media position to where the slider was dragged
        pos = self.positionslider.value()
        self.set_position(pos / 1000.0)

    # / HANDLERS

    # "Key_Escape": "quit"
    def key_to_action(self, key):
        actions = Conf.conf_data["actions"]
        action_key = list(
            filter(lambda k: key == eval("QtCore.Qt.Key." + k), actions.keys())
        )
        if len(action_key) == 0:
            return None
        return eval(f"self.{actions[action_key[0]]}")

    def key_to_enum(self, key):
        keyname = list(filter(lambda k: key == eval("QtCore.Qt.Key." + k), self.keys))
        if len(keyname) == 0:
            return None
        return keyname[0]

    def update_ui_items(self):
        if self.current_index == None:
            self.editableArtist.setText("")
            self.editableArtist.setEnabled(False)
            self.editableTitle.setText("")
            self.editableTitle.setEnabled(False)
            self.currenttimesLabel.setText("")
            self.currentbitrateLabel.setText("")
        else:
            track = self.track_model.get_track(self.current_index)
            self.editableArtist.setText(track["artist"])
            self.editableArtist.setEnabled(True)
            self.editableTitle.setText(track["title"])
            self.editableTitle.setEnabled(True)
            self.currenttimesLabel.setText("")
            self.currentbitrateLabel.setText(f"{track['bitrate']} kbits")
            self.currentfilesizeLabel.setText(f"{track['filesize']}")

    def load_dir(self, path: Path):
        try:
            logger.debug(path)
            logger.debug(sorted(os.listdir(path), key=str.casefold))
            filepaths = Tools.scan_paths(
                list(map(lambda f: path / f, sorted(os.listdir(path), key=str.casefold))), PATTERN
            )
            self.load_files(filepaths)

        except FileNotFoundError as e:
            logger.error(e)

    def load_files(self, filenames):
        logger.debug(filenames)
        self.append_tracks(filenames)

    def append_tracks(self, filepaths):
        self.track_model.append_tracks(tracks=filepaths)

    def load_track(self, track):
        self.media = self.instance.media_new(track["fullname"])
        self.mediaplayer.set_media(self.media)
        self.editableArtist.clearFocus()
        self.editableTitle.clearFocus()

    def select(self, index: int = None, increment: int = None):
        if index != None and increment != None:
            logger.critical("Bad Coder")
            return
        if increment != None:
            index = self.current_index
            if index == None:
                if increment > 0:
                    index = -1
                elif increment < 0:
                    index = self.track_model.rowCount()
            index += increment or 0

        if self.track_model.rowCount() == 0:
            index = None

        if index != None and (index < 0 or self.track_model.rowCount() <= index):
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
        self.current_replay_speed = 1.0
        self.mediaplayer.play()
        self.playbutton.setText("Pause")
        self.timer.start()
        self.is_paused = False

    # KEYBOARD ACTIONS
    def quit(self):
        self.close()

    def play_next_track(self):
        self.select(increment=1)
        if self.load_current():
            self.play()
        else:
            self.stop()

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
        self.set_position(
            (self.mediaplayer.get_time() + seconds * 1000) / self.media.get_duration()
        )

    def rename_to(self, conf_path: str):
        self.move_to(conf_path, rename=True)

    def move_to(self, conf_path: str, rename: bool = False):
        if conf_path in Conf.conf_data["paths"]:
            self.move_file(Path(Conf.conf_data["paths"][conf_path]), rename)

    def clear_metas(self):
        if self.current_index != None:
            self.track_model.clear_metas(self.current_index)

    def incr_rating(self, amount=1):
        if self.current_index != None:
            self.track_model.incr_rating(self.current_index, amount)

    def set_style(self, style):
        # print(f'style: {style}')
        if self.current_index != None:
            self.track_model.set_style(self.current_index, style)

    def incr_replay_speed(self, incr):
        self.current_replay_speed += incr
        self.mediaplayer.set_rate(self.current_replay_speed)

    def ask_discogs(self):
        if self.current_index != None:
            track = self.track_model.get_track(self.current_index)
            Discogs.ask(track['artist'],track['title'])

    # / KEYBOARD ACTIONS

    def move_file(self, dest_dir: Path, rename: bool):
        if self.current_index == None:
            return
        self.stop()
        track = self.track_model.get_track(self.current_index)
        fullname = track["fullname"]
        dest_filename = (
            f"{track['artist']} - {track['title']}.{track['ext']}" if rename else ""
        ).replace('/','_')
        shutil.move(fullname, dest_dir / dest_filename)
        self.track_model.remove_track(self.current_index)
        self.select(increment=0)
        if self.load_current():
            self.play()
