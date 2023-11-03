from PyQt6 import QtCore

class TracksModel(QtCore.QAbstractTableModel):
    def __init__(self, *args, tracks=None, **kwargs):
        super(TracksModel, self).__init__(*args, **kwargs)
        self.tracks = tracks or []
        # self.tracks = list(map(lambda f: (f,), tracks)) or []

    def data(self, index, role):
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            # print(index.row(),index.column())
            # print(self.tracks[index.row()]) #[index.column()])
            # if (len(self.tracks[index.row()]) == 1):
            if type(self.tracks[index.row()]) is not tuple:
                self.tracks[index.row()] = self.populate(self.tracks[index.row()])
            return self.tracks[index.row()][index.column()]

    def rowCount(self, index):
        # The length of the outer list.
        return len(self.tracks)

    def columnCount(self, index):
        # The following takes the first sub-list, and returns
        # the length (only works if all rows are an equal length)
        return 2
        return len(self.tracks[0])

    def populate(self, track: str):
        filename = track.split('/')[-1]
        return (filename, track)