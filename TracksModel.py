from PyQt6 import QtCore, QtGui
import os, vlc, re
from CellRenderer import CellRenderer
from Logger import logger

COLUMNS = ['filename','genre','rating', 'duration']
GENRE_PATTERN = r'^([A-Z\*][1-5])(-[A-Z\*][1-5])*$'
class TracksModel(QtCore.QAbstractTableModel):
    def __init__(self, *args, tracks=None, **kwargs):
        super(TracksModel, self).__init__(*args, **kwargs)
        self.instance = vlc.get_default_instance()
        self.tracks = tracks or []
        self.cell_renderer = CellRenderer(COLUMNS)
        # self.tracks = list(map(lambda f: (f,), tracks)) or []

    def get_track(self, index: int):
        if index < 0 or len(self.tracks) <= index:
            return None
        if type(self.tracks[index]) is not dict:
            self.tracks[index] = self.get_populated(self.tracks[index])
        return self.tracks[index]

    def remove_track(self, index: int):
        del self.tracks[index]
        self.layoutChanged.emit()

    def data(self, index, role):
        track = self.get_track(index.row()) # ensures track is populated
        return self.cell_renderer.get_style(track, index.column(), role)

    def rowCount(self, index=0):
        # The length of the outer list.
        return len(self.tracks)

    def columnCount(self, index=0):
        # The following takes the first sub-list, and returns
        # the length (only works if all rows are an equal length)
        return len(COLUMNS)

    def headerData(self, section, orientation, role):
        # section is the index of the column/row.
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            if orientation == QtCore.Qt.Orientation.Horizontal:
                return str(COLUMNS[section])

            # if orientation == QtCore.Qt.Orientation.Vertical:
            #     return str(COLUMNS[section])

    def get_populated(self, fullname: str):
        import mutagen
        filename = fullname.split('/')[-1]
        f = mutagen.File(fullname, easy=True)
        bitrate = int(f.info.bitrate/1000)
        sample_rate = f.info.sample_rate
        ext = os.path.splitext(fullname)[-1][1:].lower()

        media = self.instance.media_new(fullname)
        media.parse()
        stored_genre = media.get_meta(vlc.Meta.Genre)
        logger.debug(stored_genre)
        duration = media.get_duration()
        del media
        genre = {}
        stored_rating = 0
        if isinstance(stored_genre, str) and re.match(GENRE_PATTERN, stored_genre):
            l = re.split('-', stored_genre)
            genre = {x[0]:int(x[1]) for x in l}
            if '*' in genre:
                stored_rating = genre['*']
                del genre['*']
        logger.debug(stored_genre)
        logger.debug(genre)
        return { 'filename': filename, 'genre': genre, 'rating': stored_rating, 'fullname': fullname,
                'ext': ext, 'bitrate': bitrate, 'sample_rate': sample_rate,
                'duration': duration }

    def emit_datachanged(self, row, column):
        table_index = self.index(row, column)
        self.dataChanged.emit(table_index,table_index)

    def set_style(self, index: int, style: str):
        track = self.get_track(index)
        if track == None:
            logger.critical(f'try to access track number {index} returns None')
            return
        genre = track['genre']
        # logger.debug(genre)
        count = 0
        if style in genre:
            count = genre[style]
        count = (count + 1) % 6
        if count == 0:
            del genre[style]
        else:
            genre[style] = count
        self.emit_datachanged(index,1) ## 1 = colonne 1 = genre
        self.save_track(index)

    def incr_rating(self, index: int):
        track = self.get_track(index)
        if track == None:
            logger.critical(f'try to access track number {index} returns None')
            return
        rating = track['rating']
        try:
            rating = int(rating)
        except:
            rating = 0
        rating = (rating + 1) % 6
        track['rating'] = rating
        self.emit_datachanged(index,2) ## 2 = colonne 2 = rating
        self.save_track(index)


    def save_track(self, index: int):
        track = self.get_track(index)
        if track == None:
            logger.critical(f'try to access track number {index} returns None')
            return
        genre = track['genre'].copy()
        genre['*'] = track['rating']
        genre_str = ("-".join(map(lambda x: f'{x}{genre[x]}', dict(sorted(genre.items())))))
        media = self.instance.media_new(track['fullname'])
        media.set_meta(vlc.Meta.Genre, genre_str)
        logger.debug(genre_str)
        media.save_meta()
        del media

        # media = self.instance.media_new(track['fullname'])
        # media.parse()
        # stored_genre = media.get_meta(vlc.Meta.Genre)
        # del media
        # if stored_genre == None:
        #     stored_genre = ""
        # if stored_genre != genre_str:
        #     logger.error(f'incorrect stored genre: "{genre_str}" expected, "{stored_genre}" stored')

