from PyQt6 import QtCore, QtGui
import Tools

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
        elif role == QtCore.Qt.ItemDataRole.ForegroundRole:
            return self.foreground(data, track)
        elif role == QtCore.Qt.ItemDataRole.BackgroundRole:
            return self.background(data, track)
        elif role == QtCore.Qt.ItemDataRole.DecorationRole:
            return self.decoration(data, track)


    def display(self, data, track):
        return str(data)
    def foreground(self, data, track):
        return QtGui.QColor('white')
    def background(self, data, track):
        return QtGui.QColor('black')
    def decoration(self, data, track):
        return None
        

class FilenameStyler(Styler):
    def decoration(self, data, track):
        res = QtGui.QColor('green')
        if track['bitrate'] < 800:
            res = QtGui.QColor('orange')
        if track['bitrate'] < 320:
            res = QtGui.QColor('red')
        return res
class GenreStyler(Styler):
    def display(self, data, track):
        if len(data) == 0:
            return ''
        return str(data)

    def background(self, data, track):
        if len(data) == 0:
            return QtGui.QColor('red')
        return super().background(data, track)

class RatingStyler(Styler):
    def display(self, data, track):
        return '*'*data

    def background(self, data, track):
        if data == 0:
            return QtGui.QColor('red')
        return super().background(data, track)

class DurationStyler(Styler):
    def display(self, data, track):
        return Tools.milliseconds_to_string(data)
