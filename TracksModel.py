from PyQt6 import QtCore
import os, vlc, re
from CellRenderer import CellRenderer
from Logger import logger
import Tools
from pathlib import Path

COLUMNS = ['filename','genre','rating', 'duration']
GENRE_PATTERN = r'^([A-Z])(-[A-Z])*(-\*[0-5])$'
class TracksModel(QtCore.QAbstractTableModel):
    def __init__(self, *args, **kwargs):
        super(TracksModel, self).__init__(*args, **kwargs)
        self.instance = vlc.get_default_instance()
        self.tracks = []
        self.cell_renderer = CellRenderer(COLUMNS)
        # self.tracks = list(map(lambda f: (f,), tracks)) or []

    def append_tracks(self, tracks):
        self.tracks.extend(tracks)
        self.layoutChanged.emit()
        # logger.debug(self.tracks)

    def get_track(self, index: int):
        if index == None or index < 0 or len(self.tracks) <= index:
            return None
        if type(self.tracks[index]) is not dict:
            self.tracks[index] = self.get_populated(self.tracks[index])
        return self.tracks[index]

    def clear(self):
        self.tracks = []
        self.layoutChanged.emit()

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

    def get_populated(self, fullname: Path):
        import mutagen
        filename = fullname.name
        f = mutagen.File(fullname, easy=True)
        bitrate = int(f.info.bitrate/1000)
        sample_rate = f.info.sample_rate
        ext = fullname.suffix[1:].lower()

        media = self.instance.media_new(fullname)
        media.parse()
        artist = media.get_meta(vlc.Meta.Artist) or ''
        title = media.get_meta(vlc.Meta.Title) or ''
        filesize = Tools.bytes_to_mb(os.path.getsize(fullname))
        stored_genre = media.get_meta(vlc.Meta.Genre)
        duration = media.get_duration()
        del media
        genre = set()
        stored_rating = 0
        if isinstance(stored_genre, str) and re.match(GENRE_PATTERN, stored_genre):
            l = re.split('-', stored_genre)
            if l[-1][0] == '*':
                stored_rating = int(l[-1][1])
                l.pop()
            genre = set(l)
        # logger.debug(stored_genre)
        # logger.debug(genre)
        return { 'filename': filename, 'genre': genre, 'rating': stored_rating, 'fullname': fullname,
                'artist': artist, 'title': title, 'filesize': filesize,
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
        if style in genre:
            genre.discard(style)
        else:
            genre.add(style)

        self.emit_datachanged(index,1) ## 1 = colonne 1 = genre
        self.save_track(index)

    def clear_metas(self, index: int):
        track = self.get_track(index)
        if track == None:
            logger.critical(f'try to access track number {index} returns None')
            return
        track['rating'] = 0
        track['genre'] = set()
        self.emit_datachanged(index,1) ## 1 = colonne 2 = genre
        self.emit_datachanged(index,2) ## 2 = colonne 2 = rating
        self.save_track(index)

    def incr_rating(self, index: int, amount: int):
        track = self.get_track(index)
        if track == None:
            logger.critical(f'try to access track number {index} returns None')
            return
        rating = track['rating']
        try:
            rating = int(rating)
        except ValueError:
            rating = 0
        rating = (rating + amount + 6) % 6
        track['rating'] = rating
        self.emit_datachanged(index,2) ## 2 = colonne 2 = rating
        self.save_track(index)


    def save_track(self, index: int):
        track = self.get_track(index)
        if track == None:
            logger.critical(f'try to access track number {index} returns None')
            return
        artist_str = track['artist'].strip()
        title_str = track['title'].strip()
        genre_str = "-".join(sorted(track['genre']))
        genre_str = "-".join([ genre_str, f"*{track['rating']}" ])
        media = self.instance.media_new(track['fullname'])
        media.set_meta(vlc.Meta.Artist, artist_str)
        media.set_meta(vlc.Meta.Title, title_str)
        media.set_meta(vlc.Meta.Genre, genre_str)
        logger.debug(genre_str)
        media.save_meta()
        del media

    def update_title_and_artist(self, index: int, artist: str, title: str):
        track = self.get_track(index)
        if track == None:
            logger.critical(f'try to access track number {index} returns None')
            return
        track['artist'] = artist.strip()
        track['title'] = title.strip()
        self.save_track(index)
