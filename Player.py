import os
from pathlib import Path
from random import random
import shutil
from PyQt6 import QtWidgets, QtCore, QtGui
from Logger import logger, set_log_level
from TracksModel import TracksModel
import vlc, json
import Tools
from Conf import Conf
import Discogs
import subprocess
import threading
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

PATTERN = r"^.*\.(mp3|flac|aif|aiff)$"

class PlayerHTTPRequestHandler(SimpleHTTPRequestHandler):
    _player_instance = None

    def do_GET(self):
        self._player_instance.clear_filelist()
        self.send_response(404)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'404 - Not Found')

    def do_POST(self):
        # self.send_header('Content-type', 'text/html')
        try:
            data_string = self.rfile.read(int(self.headers['Content-Length']))
            data = json.loads(data_string)
            print(data)
            self._player_instance.push_command(data['command'])
            self.send_response(200)
        except:
            self.send_response(400)
        # self.end_headers()

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
        self.new_width = 1
        self.action_to_run = None

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

        # waveform
        self.waveform = QtWidgets.QLabel()
        canvas = QtGui.QPixmap(800, 30)
        canvas.fill(QtCore.Qt.GlobalColor.white)
        self.waveform.setPixmap(canvas)
        # self.waveform.clear()

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
        self.playbutton.setStyleSheet(
            "background-color: red;"
            "font-family: times;"
            "font-size: 20px;"
            "width: 200px;"
            "height: 80px;"
            )
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

        self.hyearbox = QtWidgets.QHBoxLayout()
        self.yearLabel = QtWidgets.QLabel("Year")
        self.hyearbox.addWidget(self.yearLabel)
        self.editableYear = QtWidgets.QLineEdit()
        self.editableYear.setFocusPolicy(QtCore.Qt.FocusPolicy.ClickFocus)
        self.hyearbox.addWidget(self.editableYear)
        self.editableYear.setEnabled(False)

        self.hdescriptionbox = QtWidgets.QHBoxLayout()
        self.descriptionLabel = QtWidgets.QLabel("Description")
        self.hdescriptionbox.addWidget(self.descriptionLabel)
        self.editableDescription = QtWidgets.QLineEdit()
        self.editableDescription.setFocusPolicy(QtCore.Qt.FocusPolicy.ClickFocus)
        self.hdescriptionbox.addWidget(self.editableDescription)
        self.editableDescription.setEnabled(False)

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
        self.vlabelbox.addLayout(self.hyearbox)
        self.vlabelbox.addLayout(self.hdescriptionbox)
        self.vlabelbox.addLayout(self.infobox)
        # /LABELS

        self.lowzone = QtWidgets.QHBoxLayout()
        self.lowzone.addLayout(self.vbuttonbox)
        self.lowzone.addLayout(self.vlabelbox)

        self.vboxlayout = QtWidgets.QVBoxLayout()
        self.vboxlayout.addWidget(self.filelist)
        self.vboxlayout.addWidget(self.waveform)
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

        self.timer_ui = QtCore.QTimer(self)
        self.timer_ui.setInterval(100)
        self.timer_ui.timeout.connect(self.update_ui_timer)
        self.timer_ui.stop()

        self.timer_tick = QtCore.QTimer(self)
        self.timer_tick.setInterval(100)
        self.timer_tick.timeout.connect(self.update_tick_timer)
        self.timer_tick.start()
        self.nb_ticks = 10
        self.jump_step_factor = 1
        try:
            self.launch_http_server()
        except:
            pass

    def launch_http_server(self):
        PlayerHTTPRequestHandler._player_instance = self
        self.http_server = ThreadingHTTPServer(("127.0.0.1", 8000), PlayerHTTPRequestHandler)
        self.http_server_thread = threading.Thread(target=self.http_server.serve_forever)
        self.http_server_thread.daemon = True
        self.http_server_thread.start()
    
    # def http_request_handler(self)

    def update_title_and_artist(self):
        self.track_model.update_title_and_artist(
            self.current_index,
            artist=self.editableArtist.text(),
            title=self.editableTitle.text(),
            year=self.editableYear.text(),
            description=self.editableDescription.text()
        )

    # HANDLERS

    def draw_something(self):
        canvas = self.waveform.pixmap()
        canvas.fill(QtCore.Qt.GlobalColor.white)
        painter = QtGui.QPainter(canvas)
        n = random()
        for x in range(800):
            painter.drawLine(x, 30, x, (n*x)%30)
        painter.end()
        self.waveform.setPixmap(canvas)

    def draw_waveform(self):
        return
        canvas = self.waveform.pixmap()
        canvas.fill(QtCore.Qt.GlobalColor.white)
        if self.current_index != None:
            painter = QtGui.QPainter(canvas)
            track = self.track_model.get_track(self.current_index)
            sound_data = track['sound_data']
            if sound_data is None:
                self.track_model.populate_soud_data(self.current_index)
                track = self.track_model.get_track(self.current_index)
                sound_data = track['sound_data']
            data_len = len(sound_data)
            img_width = self.new_width
            samples_per_pixel = data_len / img_width
            samples_per_pixel = 100
            print(f'{samples_per_pixel=}')
            for x in range(0,img_width,5):
                M = 0
                Z = int((x-0.5)*samples_per_pixel)
                ZZ = int((x+0.5)*samples_per_pixel)
                for j in range(max(0,Z), min(data_len,ZZ)):            
                    s = sound_data[j]
                    # sum += (s-128)/128.0
                    M = max(M, (s-128)/128.0, -(s-128)/128.0)
                # sum /= nb_sample_for_1tick
                y = M
                # painter.drawLine(x, 30, x, 30-y*30)
                painter.drawLine(x, 15+y*15, x, 15-y*15)
            painter.end()
        self.waveform.setPixmap(canvas)

    def clear_filelist(self):
        self.track_model.clear()
        self.current_index = None
        self.editableArtist.setText('')
        self.editableTitle.setText('')
        self.editableYear.setText('')
        self.editableDescription.setText('')

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
                self.timer_ui.stop()
                self.playbutton.setText("Play")

                # After the video finished, the play button stills shows "Pause",
                # which is not the desired behavior of a media player.
                # This fixes that "bug".
                if not self.is_paused:
                    self.stop()

    def update_tick_timer(self):
        self.run_action()
        self.nb_ticks -= 1
        if self.nb_ticks < 0:
            self.nb_ticks = 0
            self.jump_step_factor = 1

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.new_width = event.size().width() - 24 - 4
        size = self.descriptionLabel.size()
        self.artistLabel.setFixedSize(size)  # force alignment
        self.titleLabel.setFixedSize(size)  # force alignment
        self.yearLabel.setFixedSize(size)  # force alignment
        # self.descriptionLabel.setFixedSize(size)  # force alignment

        # waveform
        self.waveform.clear()
        # self.waveform = QtWidgets.QLabel()
        canvas = QtGui.QPixmap(self.new_width, 30)
        canvas.fill(QtCore.Qt.GlobalColor.white)
        self.waveform.setPixmap(canvas)
        self.draw_waveform()

    def dropEvent(self, e):
        import urllib.parse
        from pathlib import Path

        # drag and drop with filenames containing spaces replaces them with '%20'
        # and other character encondings
        print(e.mimeData().text())
        dropped_data = urllib.parse.unquote(e.mimeData().text())
        # logger.debug(f'---{dropped_data}---')
        dropped_data = dropped_data.replace("\r", "")
        dropped_paths = list(
            map(
                lambda f: Path(f.replace("file://", "").split('?')[0]),
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
        if not self.editableArtist.hasFocus() and not self.editableTitle.hasFocus() and not self.editableYear.hasFocus() and not self.editableDescription.hasFocus():
            action = self.key_to_action(key)
            if action:
                action()

    def reserved_tab_handler(self):
        """switch focus on editable inputs"""
        editables = [ self.editableArtist, self.editableTitle, self.editableYear, self.editableDescription ]
        focused_item = [ (idx, item) for idx, item in enumerate(editables) if item.hasFocus() ]
        if len(focused_item) > 1:
            raise IndexError('multiple focus, how is it possible?')
        if len(focused_item) == 0:
            editables[0].setFocus()
            editables[0].selectAll()
            return
        idx, item = focused_item[0]
        item.clearFocus()
        if idx < len(editables) - 1:
            editables[idx+1].setFocus()
            editables[idx+1].selectAll()
        else:
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
        self.timer_ui.stop()
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

    def command_to_action(self, command: str):
        actions = Conf.conf_data["actions"]
        return f"self.{actions[command]}"

    def run_action(self):
        if self.action_to_run:
            logger.critical(self.action_to_run)
            eval(self.action_to_run)
            self.action_to_run = None

    def push_command(self, command: str):
        self.action_to_run = self.command_to_action(command)

    def update_ui_items(self):
        if self.current_index == None:
            self.editableArtist.setText("")
            self.editableArtist.setEnabled(False)
            self.editableTitle.setText("")
            self.editableTitle.setEnabled(False)
            self.editableYear.setText("")
            self.editableYear.setEnabled(False)
            self.editableDescription.setText("")
            self.editableDescription.setEnabled(False)
            self.currenttimesLabel.setText("")
            self.currentbitrateLabel.setText("")
        else:
            track = self.track_model.get_track(self.current_index)
            self.editableArtist.setText(track["artist"])
            self.editableArtist.setEnabled(True)
            self.editableTitle.setText(track["title"])
            self.editableTitle.setEnabled(True)
            self.editableYear.setText(track["year"])
            self.editableYear.setEnabled(True)
            self.editableDescription.setText(track["description"])
            self.editableDescription.setEnabled(True)
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
        self.editableYear.clearFocus()
        self.editableDescription.clearFocus()
        self.draw_waveform()

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
        self.timer_ui.stop()

    def play(self):
        self.current_replay_speed = 1.0
        self.mediaplayer.play()
        self.playbutton.setText("Pause")
        self.timer_ui.start()
        self.is_paused = False

    # KEYBOARD ACTIONS
    def quit(self):
        self.close()

    def play_next_track(self):
        logger.debug('here')
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
        self.timer_ui.stop()
        self.mediaplayer.set_position(pos)
        self.timer_ui.start()

    def step_backward(self, seconds: int):
        self.step_forward(-seconds)

    def step_forward(self, seconds: int):
        seconds *= self.jump_step_factor
        self.jump_step_factor += 1
        self.nb_ticks = 10
        self.set_position(
            (self.mediaplayer.get_time() + seconds * 1000) / self.media.get_duration()
        )

    def rename_to(self, conf_path: str):
        self.move_to(conf_path, rename=True)

    def move_to(self, conf_path: str, rename: bool = False):
        if conf_path in Conf.conf_data["paths"]:
            self.move_file(Path(Conf.conf_data["paths"][conf_path]), rename)

    def copy_to(self, conf_path: str):
        if conf_path in Conf.conf_data["paths"]:
            self.copy_file(Path(Conf.conf_data["paths"][conf_path]))

    def link_to(self, conf_path: str):
        if conf_path in Conf.conf_data["paths"]:
            self.link_file(Path(Conf.conf_data["paths"][conf_path]))

    def clear_metas(self):
        if self.current_index != None:
            self.track_model.clear_metas(self.current_index)

    def incr_rating(self, amount=1):
        if self.current_index != None:
            self.track_model.incr_rating(self.current_index, amount)

    def set_rating(self, value):
        if self.current_index != None:
            self.track_model.set_rating(self.current_index, value)

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

    def import_old_tags(self):
        if self.current_index is None:
            return
        track = self.track_model.get_track(self.current_index)
        description = track["description"]
        TAGS={"Catas": "H", "Deep": "D", "Hard": "P", "Trance": "T", "Fun": "F", "A Cappella": "A"}
        d = list(filter(lambda x: x in TAGS, description.split(',')))
        if len(d) == 0:
            return
        try:
            rating = int(description.split(',')[0])
            if rating > 5:
                rating = 0
        except ValueError:
            rating = 0
        if rating == 0:
            return
        self.clear_metas()
        for g in d:
            self.set_style(TAGS[g])

        self.set_rating(rating)

    # / KEYBOARD ACTIONS

    def move_file(self, dest_dir: Path, rename: bool):
        if self.current_index == None:
            return
        track = self.track_model.get_track(self.current_index)
        fullname = track["fullname"]
        dest_filename = (
            f"{track['artist']} - {track['title']}.{track['ext']}" if rename else track['filename']
        ).replace('/','⁄') # replace with "not a real slash"
        if os.path.exists(dest_dir / dest_filename):
            return
        self.stop()
        shutil.move(fullname, dest_dir / dest_filename)
        self.track_model.remove_track(self.current_index)
        self.select(increment=0)
        if self.load_current():
            self.play()

    def copy_file(self, dest_dir: Path):
        if self.current_index == None:
            return
        track = self.track_model.get_track(self.current_index)
        fullname = track["fullname"]
        dest_filename = track['filename']

        if os.path.exists(dest_dir / dest_filename):
            logger.debug('Link not created: destination exists')
            return

        shutil.copy(fullname, dest_dir / dest_filename)
        logger.debug('File copied')

    def link_file(self, dest_dir: Path):
        if self.current_index == None:
            return
        track = self.track_model.get_track(self.current_index)
        fullname = track["fullname"]
        dest_filename = track['filename']

        if os.path.exists(dest_dir / dest_filename):
            logger.debug('Link not created: destination exists')
            return

        os.symlink(fullname, dest_dir / dest_filename, target_is_directory=False)
        logger.debug('Link created')

    def make_insta(self):
        if self.current_index == None:
            return
        print(int(self.mediaplayer.get_time()/1000))
        track = self.track_model.get_track(self.current_index)
        fullname = track["fullname"]
        artist_title = f"{track['artist']} - {track['title']}".replace('/','⁄') # replace with "not a real slash"
        print(['./video.sh', str(fullname), artist_title, int(self.mediaplayer.get_time()/1000)])
        suffix = ''
        if 'R' in track["genre"]:
            suffix = '-retro'
        elif 'P' in track["genre"]:
            suffix = '-power'

        if 'G' in track["genre"]:
            style = 'garden'
        elif 'D' in track["genre"]:
            style = 'deep'
        elif 'H' in track["genre"]:
            style = 'house'
        elif 'T' in track["genre"]:
            style = 'trance'
        else:
            style = 'deep'
        subprocess.run(['./video.sh', str(fullname), artist_title, str(int(self.mediaplayer.get_time()/1000)), style+suffix])
