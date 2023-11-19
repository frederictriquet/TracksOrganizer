from PyQt6 import QtCore, QtGui
import os, vlc, re
from Logger import logger

COLUMNS = ['filename','description','foreground']
COLORS = { 'mp3': '#ffff00', 'flac': '#00ffff', 'aif': '#00ff00', 'aiff': '#00ff00', 'default': '#888888' }
class TracksModel(QtCore.QAbstractTableModel):
    def __init__(self, *args, tracks=None, **kwargs):
        super(TracksModel, self).__init__(*args, **kwargs)
        self.instance = vlc.get_default_instance()
        self.tracks = tracks or []
        # self.tracks = list(map(lambda f: (f,), tracks)) or []

    def get_track(self, index: int):
        if index < 0 or len(self.tracks) <= index:
            return None
        if type(self.tracks[index]) is not dict:
            self.tracks[index] = self.get_populated(self.tracks[index])
        return self.tracks[index]

    def data(self, index, role):
        # if type(self.tracks[index.row()]) is not dict:
        #     self.tracks[index.row()] = self.populate(self.tracks[index.row()])
        self.get_track(index.row())

        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            # print(index.row(),index.column())
            # print(self.tracks[index.row()]) #[index.column()])
            # if (len(self.tracks[index.row()]) == 1):
            return str(self.tracks[index.row()][COLUMNS[index.column()]])
        if role == QtCore.Qt.ItemDataRole.ForegroundRole:
            return QtGui.QColor(self.tracks[index.row()]['foreground'])
        # if role == QtCore.Qt.ItemDataRole.BackgroundRole:
        #     return self.tracks[index.row()]['foreground']

    def rowCount(self, index=0):
        # The length of the outer list.
        return len(self.tracks)

    def columnCount(self, index=0):
        # The following takes the first sub-list, and returns
        # the length (only works if all rows are an equal length)
        return 3

    def get_populated(self, fullname: str):
        filename = fullname.split('/')[-1]
        ext = os.path.splitext(fullname)[-1][1:].lower()
        foreground = COLORS['default']
        if ext in COLORS:
            foreground = COLORS[ext]

        media = self.instance.media_new(fullname)
        media.parse()
        stored_description = media.get_meta(vlc.Meta.Description)
        del media
        description = {}
        PATTERN = r'^([A-Z\*][1-5])(-[A-Z\*][1-5])*$'
        if isinstance(stored_description, str) and re.match(PATTERN, stored_description):
            l = re.split('-', stored_description)
            description = {x[0]:int(x[1]) for x in l}
        logger.debug(stored_description)
        logger.debug(description)
        return { 'filename': filename, 'description': description, 'fullname': fullname, 'foreground': foreground }

    def set_style(self, index: int, style: str):
        track = self.get_track(index)
        if track == None:
            logger.critical(f'try to access track number {index} returns None')
            return
        description = track['description']
        # logger.debug(description)
        count = 0
        if style in description:
            count = description[style]
        count = (count + 1) % 6
        if count == 0:
            del description[style]
        else:
            description[style] = count
        table_index = self.index(index,1) ## 1 = colonne 1 = description
        self.dataChanged.emit(table_index,table_index)
        self.save_track(index)

    def save_track(self, index: int):
        track = self.get_track(index)
        if track == None:
            logger.critical(f'try to access track number {index} returns None')
            return
        description = track['description']
        description_str = ("-".join(map(lambda x: f'{x}{description[x]}', dict(sorted(description.items())))))
        logger.debug(description_str)
        media = self.instance.media_new(track['fullname'])
        media.set_meta(vlc.Meta.Description, description_str)
        media.save_meta()
        del media

        media = self.instance.media_new(track['fullname'])
        media.parse()
        stored_description = media.get_meta(vlc.Meta.Description)
        del media
        if stored_description == None:
            stored_description = ""
        if stored_description != description_str:
            logger.error(f'incorrect stored description: "{description_str}" expected, "{stored_description}" stored')

