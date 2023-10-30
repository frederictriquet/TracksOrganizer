#! /usr/bin/env python3

import platform
import os
import sys
import json
import glob, shutil
import subprocess
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from PyQt6 import QtWidgets, QtGui, QtCore
from PyQt6.QtCore import Qt

import vlc
import re

TAGS=["Catas", "Phiphi", "Deep", "Hard", "Retro", "Trance", "Best", "Ambiant", "Fun", "Zarb", "A Cappella"]

def glob_re(pattern, strings):
    return filter(re.compile(pattern).match, strings)

def meta_description_to_filtered_array(meta_description):
    # print(meta_description)
    if meta_description:
        # print(list(filter(lambda x: x in TAGS, meta_description.split(','))))
        description = list(filter(lambda x: x in TAGS, meta_description.split(',')))
    else:
        # print('RIEN')
        description = []
    return description



class TracksModel(QtCore.QAbstractListModel):
    def __init__(self, *args, tracks=None, parent=None, **kwargs):
        super(TracksModel, self).__init__(*args, **kwargs)
        self.tracks = tracks or []
        self.parent = parent

    def retrieve_colors_for_file(self, fullpath):
        ext = os.path.splitext(fullpath)[-1][1:].lower()
        if ext == 'flac':
            color = '#00ffff'
        else:
            color = '#ffff00'

        self.instance = vlc.get_default_instance()
        self.mediaplayer = self.instance.media_player_new()
        self.media = self.instance.media_new(fullpath)
        self.mediaplayer.set_media(self.media)
        self.media.parse()
        # self.parent.instance = vlc.get_default_instance()
        # self.parent.mediaplayer = self.parent.instance.media_player_new()
        # self.parent.media = self.parent.instance.media_new(fullpath)
        # self.parent.mediaplayer.set_media(self.parent.media)
        # self.parent.media.parse()

        # print('retrieve_colors_for_file', fullpath)
        # print('Artist', self.parent.media.get_meta(vlc.Meta.Artist))
        # print('Title', self.parent.media.get_meta(vlc.Meta.Title))
        # print('Description', self.parent.media.get_meta(vlc.Meta.Description))


        description = meta_description_to_filtered_array(self.media.get_meta(vlc.Meta.Description))
        if description:
            bg_color = '#000000'
        else:
            bg_color = '#800000'
        return color, bg_color

    def data(self, index, role):
        if role == Qt.ItemDataRole.DisplayRole:
            filename, _, _, _ = self.tracks[index.row()]
            return filename
        if role == Qt.ItemDataRole.ForegroundRole:
            filename, fullpath, color, bgcolor = self.tracks[index.row()]
            if not color:
                color, bgcolor = self.retrieve_colors_for_file(fullpath)
                # # print(f'color for {filename}')
                # ext = os.path.splitext(filename)[-1][1:].lower()
                # if ext == 'flac':
                #     color = '#00ffff'
                # else:
                #     color = '#ffff00'
                self.tracks[index.row()] = (filename, fullpath, color, bgcolor)
            # else:
            #     print(f'already done {filename}')
            return QtGui.QColor(color)
        if role == Qt.ItemDataRole.BackgroundRole:
            filename, fullpath, color, bgcolor = self.tracks[index.row()]
            if not bgcolor:
                color, bgcolor = self.retrieve_colors_for_file(fullpath)
                self.tracks[index.row()] = (filename, fullpath, color, bgcolor)
            return QtGui.QColor(bgcolor)

    def rowCount(self, index):
        return len(self.tracks)



class Player(QtWidgets.QMainWindow):
    """A simple Media Player using VLC and Qt
    """

    def __init__(self, master=None):
        self.load_conf(sys.argv[1])
        QtWidgets.QMainWindow.__init__(self, master)
        self.setWindowTitle("Media Player")

        # Create a basic vlc instance
        self.instance = vlc.get_default_instance()

        self.media = None

        # Create an empty vlc media player
        self.mediaplayer = self.instance.media_player_new()

        self.create_ui()
        self.is_paused = False

    def load_conf(self, conffile = './conf.json'):
        with open(conffile) as jsonfile:
            stringdata = jsonfile.read()
            self.conf = json.loads(stringdata)

    # def retrieve_colors_for_file(self, fullpath):
    #     ext = os.path.splitext(fullpath)[-1][1:].lower()
    #     if ext == 'flac':
    #         color = Qt.GlobalColor.yellow
    #     else:
    #         color = Qt.GlobalColor.cyan

    #     self.media = self.instance.media_new(fullpath)
    #     self.mediaplayer.set_media(self.media)
    #     self.media.parse()
    #     # print(fullpath)
    #     # print('Artist', self.media.get_meta(vlc.Meta.Artist))
    #     # print('Title', self.media.get_meta(vlc.Meta.Title))
    #     # print('Description', self.media.get_meta(vlc.Meta.Description))
    #     description = self.meta_description_to_filtered_array(self.media.get_meta(vlc.Meta.Description))
    #     if description:
    #         bg_color = Qt.GlobalColor.black
    #     else:
    #         bg_color = Qt.GlobalColor.darkRed
    #     return color, bg_color

    def dropEvent(self, e):
        dirname = e.mimeData().text().replace('file://','')
        print(dirname)
        e.setDropAction(Qt.DropAction.MoveAction)
        e.accept()
        self.conf['source_dir'] = dirname
        self.load_dir()

    def dragEnterEvent(self, e):
        e.accept()

    def load_dir(self):
        src_dir = self.conf["source_dir"]
        print(f"Loading from {src_dir}")
        # filez = sorted( filter( os.path.isfile, glob.glob(f'{sourcedir}*.[Mm][Pp]3')))
        filez = sorted(glob_re(r'.*\.(mp3|Mp3|MP3|flac)', os.listdir(src_dir)))

        filez = list(map(lambda x: (x.split('/')[-1], f'{src_dir}{x}', None, None), filez))
        # print(self.filez[0])
        self.track_model = TracksModel(tracks=filez, parent=self)
        self.filelist.setModel(self.track_model)

        # self.track_model.layoutChanged.emit()
        # print(self.filez)
        # n = 0
        # self.filelist.clear()
        # for filename in self.filez:
        #     print(filename)
        #     self.filelist.insertItem(n, filename)
        #     (color, bg_color) = self.retrieve_colors_for_file(f'{src_dir}{filename}')
        #     self.filelist.item(n).setForeground(color)
        #     self.filelist.item(n).setBackground(bg_color)
        #     n = n+1


    def create_ui(self):
        """Set up the user interface, signals & slots
        """
        self.widget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.widget)

        self.setAcceptDrops(True)


        self.tagsbuttonbox = QtWidgets.QHBoxLayout()

        self.tagbutton = {}
        for tag in TAGS:
            self.tagbutton[tag] = QtWidgets.QPushButton(tag)
            self.tagbutton[tag].setCheckable(True)
            # self.tagbutton[tag].clicked[bool].connect(self.set_tag)
            self.tagbutton[tag].clicked[bool].connect(self.set_tags)
            self.tagbutton[tag].setFocusPolicy(Qt.FocusPolicy.NoFocus)
            self.tagsbuttonbox.addWidget(self.tagbutton[tag])

        self.topzone = QtWidgets.QHBoxLayout()
        self.topzone.addLayout(self.tagsbuttonbox)

        # self.filelist = QtWidgets.QListWidget()
        self.filelist = QtWidgets.QListView()
        self.filelist.clicked.connect(self.item_clicked)
        self.filelist.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.load_dir()

        self.waveform = QtWidgets.QFrame()

        self.positionslider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal, self)
        self.positionslider.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.positionslider.setToolTip("Position")
        self.positionslider.setMaximum(1000)
        self.positionslider.sliderMoved.connect(self.set_position)
        self.positionslider.sliderPressed.connect(self.set_position)

        self.hbuttonbox = QtWidgets.QHBoxLayout()
        # self.playbutton = QtWidgets.QPushButton("Play")
        # self.hbuttonbox.addWidget(self.playbutton)
        # self.playbutton.clicked.connect(self.play_pause)

        self.stopbutton = QtWidgets.QPushButton("Stop")
        self.hbuttonbox.addWidget(self.stopbutton)
        self.stopbutton.clicked.connect(self.stop)

        self.timelabel = QtWidgets.QLabel()
        self.timelabel.setText(self.get_time_info())
        self.hbuttonbox.addWidget(self.timelabel)

        self.hbuttonbox.addStretch(1)
        self.volumeslider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal, self)
        self.volumeslider.setMaximum(100)
        self.volumeslider.setValue(self.mediaplayer.audio_get_volume())
        self.volumeslider.setToolTip("Volume")
        self.hbuttonbox.addWidget(self.volumeslider)
        self.volumeslider.valueChanged.connect(self.set_volume)

        self.lowzone = QtWidgets.QVBoxLayout()
        self.lowzone.addWidget(self.positionslider)
        self.lowzone.addLayout(self.hbuttonbox)

        self.vboxlayout = QtWidgets.QVBoxLayout()
        self.vboxlayout.addWidget(self.filelist)
        self.vboxlayout.addLayout(self.topzone)
        self.vboxlayout.addLayout(self.lowzone)

        self.widget.setLayout(self.vboxlayout)
        menu_bar = self.menuBar()

        # File menu
        file_menu = menu_bar.addMenu("File")

        # Add actions to file menu
        open_dir_action = QtGui.QAction("Load directory", self)
        # open_action = QtGui.QAction("Load Video", self)
        close_action = QtGui.QAction("Close App", self)
        file_menu.addAction(open_dir_action)
        # file_menu.addAction(open_action)
        file_menu.addAction(close_action)

        open_dir_action.triggered.connect(self.open_dir)
        # open_action.triggered.connect(self.open_file)
        close_action.triggered.connect(sys.exit)

        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.update_ui)


    def item_clicked(self):
        self.current_index = self.filelist.currentIndex().row()
        if self.current_index >= 0 and self.current_index < len(self.track_model.tracks):
            tuple = self.track_model.tracks[self.current_index]
            # self.current_filename = self.track_model.tracks[self.current_index]
            self.load_mp3(tuple[1])
            # self.label.setText("You have selected: " + str(item.text()))

    def jump_to_next_item(self, incr=1):
        next_row = self.filelist.currentIndex().row()+incr
        next_index = self.track_model.index(next_row)
        self.filelist.setCurrentIndex(next_index)
        self.item_clicked()

    def play_pause(self):
        if self.mediaplayer.is_playing():
            self.mediaplayer.pause()
            self.playbutton.setText("Play")
            self.is_paused = True
            self.timer.stop()
        else:
            if self.mediaplayer.play() == -1:
                self.open_file()
                return

            self.mediaplayer.play()
            # self.playbutton.setText("Pause")
            self.timer.start()
            self.is_paused = False

    def stop(self):
        self.mediaplayer.stop()
        # self.playbutton.setText("Play")


    def move_file(self, dest_dir):
        self.stop()
        # currentrow = self.filelist.currentRow()
        # item = self.filelist.takeItem(currentrow)
        # fullpath = f"{self.conf['source_dir']}{item.text()}"
        tuple = self.track_model.tracks[self.current_index]
        fullpath = tuple[1]
        shutil.move(fullpath, dest_dir)

        del self.track_model.tracks[self.current_index]
        self.track_model.layoutChanged.emit()
        self.filelist.setCurrentIndex(self.track_model.index(self.current_index))
        self.item_clicked()

    def copy_file(self, dest_dir):
        tuple = self.track_model.tracks[self.current_index]
        fullpath = tuple[1]
        shutil.copy2(fullpath, dest_dir)

    def incr_rating(self, incr):
        self.rating += incr
        if self.rating < 0:
            self.rating = 0
        if self.rating > 5:
            self.rating = 0
        self.media.set_meta(vlc.Meta.Rating, f'{self.rating}')
        self.media.save_meta()
        self.set_tags()

    def set_tags(self):
        tags = [str(self.rating)]
        for tag in TAGS:
            if self.tagbutton[tag].isChecked():
                tags.append(tag)
        self.media.set_meta(vlc.Meta.Rating, f'{self.rating}')
        print("SET META", self.media.set_meta(vlc.Meta.Description, None), tags)
        print("SAVE META", self.media.save_meta())
        print("SET META", self.media.set_meta(vlc.Meta.Description, ','.join(tags)), tags)
        self.media.set_meta(vlc.Meta.Rating, f'{self.rating}')
        print("SAVE META", self.media.save_meta())
        tuple_as_list = list(self.track_model.tracks[self.current_index])
        tuple_as_list[3] = None
        self.track_model.tracks[self.current_index] = tuple(tuple_as_list)
        index = self.track_model.index(self.current_index)
        self.track_model.dataChanged.emit(index, index)

    def update_tag_buttons(self):
        stored_description = self.media.get_meta(vlc.Meta.Description)
        try:
            self.rating = int(stored_description.split(',')[0])
            if self.rating > 5:
                self.rating = 0
        except:
            self.rating = 0
        description = meta_description_to_filtered_array(stored_description)
        for tag in TAGS:
            if tag in description:
                self.tagbutton[tag].setChecked(True)
            else:
                self.tagbutton[tag].setChecked(False)
            self.tagbutton[tag].clearFocus()
            self.tagbutton[tag].setFocusPolicy(Qt.FocusPolicy.NoFocus)

    def get_time_info(self):
        if self.mediaplayer.is_playing():
            stars = '* '*self.rating + '_ '*(5-self.rating)
            return f'{self.milliseconds_to_string(self.mediaplayer.get_time())} / {self.milliseconds_to_string(self.media.get_duration())} -- {self.filesize} -- {self.bitrate} -- {stars}'
        return 'Stopped'

    def milliseconds_to_string(self, ms):
        m = int(ms / 60000)
        s = int(ms / 1000) % 60
        return f'{m}:{s:02}'
    
    def bytes_to_Mb(self, b):
        m = int(100 * b / 1024 / 1024) / 100
        return f'{m} Mb'

    def load_mp3(self, fullpath):
        # fullpath = f"{self.conf['source_dir']}{filename}"
        self.media = self.instance.media_new(fullpath)
        self.mediaplayer.set_media(self.media)
        self.media.parse()
        print('Artist', self.media.get_meta(vlc.Meta.Artist))
        print('Title', self.media.get_meta(vlc.Meta.Title))
        print('Description', self.media.get_meta(vlc.Meta.Description))
        # print('Rating', self.media.get_meta(vlc.Meta.Rating))
        # print(self.milliseconds_to_string(self.media.get_duration()))
        self.filesize = self.bytes_to_Mb(os.path.getsize(fullpath))
        # self.rating = int(self.media.get_meta(vlc.Meta.Rating) or 0)
        # print('self.rating', self.rating)
        self.setWindowTitle(f'{self.media.get_meta(vlc.Meta.Artist)} --- {self.media.get_meta(vlc.Meta.Title)}')

        ext = os.path.splitext(fullpath)[-1].lower()
        if ext == '.flac':
            file = FLAC(fullpath)
        elif ext == '.mp3':
            file = MP3(fullpath)
        self.bitrate = int(file.info.bitrate/1000)

        self.update_tag_buttons()
        self.play_pause()

    def spot(self, strip = False):
        # print(self.media.get_meta(vlc.Meta.Artist))
        # print(self.media.get_meta(vlc.Meta.Title))
        tuple = self.track_model.tracks[self.current_index]
        # fullpath = tuple[1]
        # filename = fullpath.split('/')[-1]
        filename = tuple[0]
        flacdir = self.conf['bigflac']
        
        # title = self.media.get_meta(vlc.Meta.Title)
        # if strip:
        #     title = title.split('(', 1)[0]
        # request = f'{self.media.get_meta(vlc.Meta.Artist)} {title}'.replace("'", " ")
        request = filename.rsplit('.',1)[0]
        request = request.replace('-', ' ').replace("'", ' ')
        if strip:
            request = request.split('(', 1)[0]
        basecmd = 'spotdl --of flac --path-template "{artist} - {title}.{ext}"'
        cmd = f"{basecmd} -o '{flacdir}' '{request}' &"
        print(cmd)
        subprocess.call(cmd, shell=True)

    def open_file(self):
        dialog_txt = "Choose Media File"
        # filename = QtWidgets.QFileDialog.getOpenFileName(self, dialog_txt, os.path.expanduser('.'))
        filename = QtWidgets.QFileDialog.getExistingDirectory(self, dialog_txt, os.path.expanduser('.'))
        if not filename:
            return

        # getOpenFileName returns a tuple, so use only the actual file name
        self.media = self.instance.media_new(filename[0])

        # Put the media in the media player
        self.mediaplayer.set_media(self.media)

        # Parse the metadata of the file
        self.media.parse()

        # Set the title of the track as window title
        self.setWindowTitle(self.media.get_meta(0))

        # The media player has to be 'connected' to the QFrame (otherwise the
        # video would be displayed in it's own window). This is platform
        # specific, so we must give the ID of the QFrame (or similar object) to
        # vlc. Different platforms have different functions for this
        # if platform.system() == "Linux": # for Linux using the X Server
        #     self.mediaplayer.set_xwindow(int(self.videoframe.winId()))
        # elif platform.system() == "Windows": # for Windows
        #     self.mediaplayer.set_hwnd(int(self.videoframe.winId()))
        # elif platform.system() == "Darwin": # for MacOS
        #     self.mediaplayer.set_nsobject(int(self.videoframe.winId()))

        self.play_pause()

    def open_dir(self):
        dialog_txt = "Choose Directory"
        dirname = QtWidgets.QFileDialog.getExistingDirectory(self, dialog_txt, os.path.expanduser('/users/fred/Music/Soulseek'))
        if not dirname:
            return
        self.conf['source_dir'] = dirname+'/'
        self.load_dir()

    def set_volume(self, volume):
        """Set the volume
        """
        self.mediaplayer.audio_set_volume(volume)

    def keyPressEvent(self, event):
        # keyPressEvent defined in child
        key = event.key()
        # print('pressed from myDialog: ', key)
        if key == Qt.Key.Key_Escape.value:
            self.close()
        if Qt.Key.Key_0.value <= key <= Qt.Key.Key_9.value:
            pos = 100*(key - 48)
            self.set_position(pos)
        if key == Qt.Key.Key_Space.value:
            self.jump_to_next_item()
        if key == 16777250: # Qt.Key.Key_Control.value:
            self.jump_to_next_item(-1)
        if key == Qt.Key.Key_Backspace.value:
            self.set_description(None)
        for tag in TAGS:
            if key == ord(tag[0]):
                self.tagbutton[tag].toggle()
                self.set_tags()
        if key == Qt.Key.Key_Plus.value:
            self.incr_time(5)
        if key == Qt.Key.Key_Minus.value:
            self.incr_time(-5)
        if key == Qt.Key.Key_Asterisk.value:
            self.move_file(self.conf['dustbin'])
        if key == Qt.Key.Key_Greater.value or key == Qt.Key.Key_Less.value:
            self.copy_file(self.conf['selection'])
        if key == Qt.Key.Key_At.value:
            self.move_file(self.conf['rename'])
        if key == Qt.Key.Key_K.value:
            self.move_file(self.conf['keep'])
        # if key == Qt.Key.Key_Enter.value:
        #     self.incr_rating(1)
        if key == Qt.Key.Key_Comma.value:
            self.incr_rating(1)
        #     self.spot(strip=True)

    def incr_time(self, incr):
        self.set_position(1000*(self.mediaplayer.get_time() + incr * 1000) / self.media.get_duration())
        # media_pos = int(self.mediaplayer.get_position() * 1000)


    def set_position(self, pos=None):
        """Set the movie position according to the position slider.
        """

        # The vlc MediaPlayer needs a float value between 0 and 1, Qt uses
        # integer variables, so you need a factor; the higher the factor, the
        # more precise are the results (1000 should suffice).

        # Set the media position to where the slider was dragged
        self.timer.stop()
        if pos == None:
            pos = self.positionslider.value()
        self.mediaplayer.set_position(pos / 1000.0)
        self.timer.start()


    def update_ui(self):
        """Updates the user interface"""

        # Set the slider's position to its corresponding media position
        # Note that the setValue function only takes values of type int,
        # so we must first convert the corresponding media position.
        media_pos = int(self.mediaplayer.get_position() * 1000)
        self.positionslider.setValue(media_pos)
        self.timelabel.setText(self.get_time_info())

        # No need to call this function if nothing is played
        if not self.mediaplayer.is_playing():
            self.timer.stop()

            # After the video finished, the play button stills shows "Pause",
            # which is not the desired behavior of a media player.
            # This fixes that "bug".
            if not self.is_paused:
                self.stop()

def main():
    """Entry point for our simple vlc player
    """
    app = QtWidgets.QApplication(sys.argv)
    player = Player()
    player.show()
    player.resize(800, 600)
    sys.exit(app.exec())

if __name__ == "__main__":
    print(Qt.DropAction.MoveAction)
    main()
