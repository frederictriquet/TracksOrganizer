from PyQt6 import QtCore
import os

COLUMNS = ['filename','track','foreground']
COLORS = { 'mp3': '#ffff00', 'flac': '#00ffff', 'aif': '#00ff00', 'aiff': '#00ff00', 'default': '#888888' }
class TracksModel(QtCore.QAbstractTableModel):
    def __init__(self, *args, tracks=None, **kwargs):
        super(TracksModel, self).__init__(*args, **kwargs)
        self.tracks = tracks or []
        # self.tracks = list(map(lambda f: (f,), tracks)) or []

    def data(self, index, role):
        if type(self.tracks[index.row()]) is not dict:
            self.tracks[index.row()] = self.populate(self.tracks[index.row()])

        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            # print(index.row(),index.column())
            # print(self.tracks[index.row()]) #[index.column()])
            # if (len(self.tracks[index.row()]) == 1):
            return self.tracks[index.row()][COLUMNS[index.column()]]
        if role == QtCore.Qt.ItemDataRole.ForegroundRole:
            return self.tracks[index.row()]['foreground']

    def rowCount(self, index=0):
        # The length of the outer list.
        return len(self.tracks)

    def columnCount(self, index=0):
        # The following takes the first sub-list, and returns
        # the length (only works if all rows are an equal length)
        return 3

    def populate(self, track: str):
        filename = track.split('/')[-1]
        ext = os.path.splitext(track)[-1][1:].lower()
        foreground = COLORS['default']
        if ext in COLORS:
            foreground = COLORS[ext]
        return { 'filename': filename, 'track': track, 'foreground': foreground }