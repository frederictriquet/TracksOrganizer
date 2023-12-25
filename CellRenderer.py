from PyQt6 import QtCore, QtGui
import Tools
from Conf import Conf

COLORS = {
    'mp3': 'yellow',
    'flac': '#00ffff',
    'aif': '#00ff00',
    'aiff': '#00ff00',
    'default': '#888888'
}

class CellRenderer:
    def __init__(self, columns: list[str]) -> None:
        self.columns = columns
        self.get_styler_for_title = {
            'filename': FilenameStyler(),
            'genre': GenreStyler(),
            'rating': RatingStyler(),
            'duration': DurationStyler()
        }
    
    def get_style(self, track, column, role):
        column_title = self.columns[column]
        data = track[column_title]
        return self.get_styler_for_title[column_title].get_style(data, role, track)

class Styler:
    def get_style(self, data, role, track):
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            return self.display(data, track)
        if role == QtCore.Qt.ItemDataRole.ToolTipRole:
            return self.tooltip(data, track)
        elif role == QtCore.Qt.ItemDataRole.ForegroundRole:
            return self.foreground(data, track)
        elif role == QtCore.Qt.ItemDataRole.BackgroundRole:
            return self.background(data, track)
        elif role == QtCore.Qt.ItemDataRole.DecorationRole:
            return self.decoration(data, track)
        elif role == QtCore.Qt.ItemDataRole.TextAlignmentRole:
            return self.alignment(data, track)

    def display(self, data, track):
        return str(data)
    def tooltip(self, data, track):
        return None
    def foreground(self, data, track):
        return QtGui.QColor(QtCore.Qt.GlobalColor.white)
    def background(self, data, track):
        return QtGui.QColor(QtCore.Qt.GlobalColor.black)
    def decoration(self, data, track):
        return None
    def alignment(self, data, track):
        return None
        

class FilenameStyler(Styler):
    def tooltip(self, data, track):
        return str(track['fullname'])
    def decoration(self, data, track):
        res = QtGui.QColor(QtCore.Qt.GlobalColor.green)
        if track['bitrate'] < 800:
            res = QtGui.QColor('yellow')
        if track['bitrate'] < 320:
            res = QtGui.QColor('orange')
        if track['bitrate'] < 256:
            res = QtGui.QColor(QtCore.Qt.GlobalColor.red)
        return res

class GenreStyler(Styler):
    def tooltip(self, data, track):
        return ' - '.join(sorted(map(lambda genre: Conf.get_genre(genre), track['genre'])))
    def display(self, data, track):
        if len(data) == 0:
            return ''
        return '/'.join(sorted(data))
    def decoration(self, data, track):
        if len(data) == 0:
            return QtGui.QColor(QtCore.Qt.GlobalColor.red)
        return super().decoration(data, track)

class RatingStyler(Styler):
    def display(self, data, track):
        return '*'*data
    def decoration(self, data, track):
        if data == 0:
            return QtGui.QColor(QtCore.Qt.GlobalColor.red)
        return super().decoration(data, track)

class DurationStyler(Styler):
    def display(self, data, track):
        return Tools.milliseconds_to_string(data)
    def alignment(self, data,track):
        return QtCore.Qt.AlignmentFlag.AlignVCenter + QtCore.Qt.AlignmentFlag.AlignRight

