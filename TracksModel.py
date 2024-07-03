from random import random
import subprocess
from PyQt6 import QtCore
import os, vlc, re
from CellRenderer import CellRenderer
from Logger import logger
import Tools
from pathlib import Path

COLUMNS = ["filename", "genre", "rating", "duration", "description"]
GENRE_PATTERN = r"^([A-Z])(-[A-Z])*(-\*[0-5])$"


class TracksModel(QtCore.QAbstractTableModel):
    def __init__(self, *args, **kwargs):
        super(TracksModel, self).__init__(*args, **kwargs)
        self.instance = vlc.get_default_instance()
        self.tracks = []
        self.cell_renderer = CellRenderer(COLUMNS)

    def append_tracks(self, tracks):
        self.tracks.extend(tracks)
        self.layoutChanged.emit()

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
        track = self.get_track(index.row())  # ensures track is populated
        return self.cell_renderer.get_style(track, index.column(), role)

    def rowCount(self, index=0):
        # The length of the outer list.
        return len(self.tracks)

    def columnCount(self, index=0):
        return len(COLUMNS)

    def headerData(self, section, orientation, role):
        # section is the index of the column/row.
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            if orientation == QtCore.Qt.Orientation.Horizontal:
                return str(COLUMNS[section])

            if orientation == QtCore.Qt.Orientation.Vertical:
                return f"{section+1}/{len(self.tracks)}"

    def get_populated(self, fullname: Path):
        import mutagen

        filename = fullname.name
        f = mutagen.File(fullname, easy=True)
        try:
            bitrate = int(f.info.bitrate / 1000)
        except AttributeError as e:
            logger.critical(fullname)
            logger.critical(e)
        sample_rate = f.info.sample_rate
        ext = fullname.suffix[1:].lower()

        media = self.instance.media_new(fullname)
        media.parse()
        artist = media.get_meta(vlc.Meta.Artist) or ""
        title = media.get_meta(vlc.Meta.Title) or ""
        filesize = Tools.bytes_to_mb(os.path.getsize(fullname))
        stored_genre = media.get_meta(vlc.Meta.Genre)
        stored_date = media.get_meta(vlc.Meta.Date) or ""
        stored_description = media.get_meta(vlc.Meta.Description) or ""
        duration = media.get_duration()
        del media
        genre = set()
        stored_rating = 0
        if isinstance(stored_genre, str) and re.match(GENRE_PATTERN, stored_genre):
            l = re.split("-", stored_genre)
            if l[-1][0] == "*":
                stored_rating = int(l[-1][1])
                l.pop()
            genre = set(l)
        return {
            "filename": filename,
            "genre": genre,
            "rating": stored_rating,
            "fullname": fullname,
            "artist": artist,
            "title": title,
            "filesize": filesize,
            "ext": ext,
            "bitrate": bitrate,
            "sample_rate": sample_rate,
            "duration": duration,
            "description": stored_description,
            "previous_description": stored_description,
            "year": stored_date,
            "sound_data": None
        }

    def populate_soud_data(self, index: int):
        track = self.get_track(index)
        if track == None:
            logger.critical(f"try to access track number {index} returns None")
            return
        if track['sound_data']:
            return
        # sound_data = [ random() for _ in range(800) ]
        result = subprocess.run(["ffmpeg", "-i", str(track['fullname']), "-ac", "1", "-filter:a", "aresample=250", "-map", "0:a", "-c:a", "pcm_u8", "-f", "data", "-"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # print(result.stdout)
        # print(len(result.stdout), duration)
        l = len(result.stdout)
        nb_sample_for_1tick = int(l / 800)
        sound_data = []
        for i in range(800):
            M = 0
            for j in range(nb_sample_for_1tick):            
                s = result.stdout[int(i*nb_sample_for_1tick + j)]
                # sum += (s-128)/128.0
                M = max(M, (s-128)/128.0, -(s-128)/128.0)
            # sum /= nb_sample_for_1tick
            # sound_data.append(sum)
            sound_data.append(M)
        # print(sound_data)
        track['sound_data'] = sound_data

    def emit_datachanged(self, row, column):
        table_index = self.index(row, column)
        self.dataChanged.emit(table_index, table_index)

    def set_style(self, index: int, style: str):
        track = self.get_track(index)
        if track == None:
            logger.critical(f"try to access track number {index} returns None")
            return
        genre = track["genre"]
        if style in genre:
            genre.discard(style)
        else:
            genre.add(style)

        self.emit_datachanged(index, 1)  ## 1 = column 1 = genre
        self.save_track(index)

    def clear_metas(self, index: int):
        track = self.get_track(index)
        if track == None:
            logger.critical(f"try to access track number {index} returns None")
            return
        track["rating"] = 0
        track["genre"] = set()
        track["description"] = ''
        self.emit_datachanged(index, 1)  ## 1 = column 1 = genre
        self.emit_datachanged(index, 2)  ## 2 = column 2 = rating
        self.emit_datachanged(index, 4)  ## 4 = column 4 = description
        self.save_track(index)

    def incr_rating(self, index: int, amount: int):
        track = self.get_track(index)
        if track == None:
            logger.critical(f"try to access track number {index} returns None")
            return
        rating = track["rating"]
        try:
            rating = int(rating)
        except ValueError:
            rating = 0
        rating = (rating + amount + 6) % 6
        track["rating"] = rating
        self.emit_datachanged(index, 2)  ## 2 = column 2 = rating
        self.save_track(index)

    def set_rating(self, index: int, value: int):
        track = self.get_track(index)
        if track == None:
            logger.critical(f"try to access track number {index} returns None")
            return
        rating = value % 6
        track["rating"] = rating
        self.emit_datachanged(index, 2)  ## 2 = column 2 = rating
        self.save_track(index)

    def save_track(self, index: int):
        track = self.get_track(index)
        if track == None:
            logger.critical(f"try to access track number {index} returns None")
            return
        artist_str = track["artist"].strip()
        title_str = track["title"].strip()
        genre_str = "-".join(sorted(track["genre"]))
        genre_str = "-".join([genre_str, f"*{track['rating']}"])
        year_str = track["year"].strip()
        description_str = track["description"].strip()

        if description_str != track['previous_description'] and track['ext'] == 'flac':
            from mutagen.flac import FLAC  
            file = FLAC(track["fullname"])
            file.delete()
            logger.debug('deleted tags from FLAC file')
            track['previous_description'] = description_str

        media = self.instance.media_new(track["fullname"])
        media.set_meta(vlc.Meta.Artist, artist_str)
        media.set_meta(vlc.Meta.Title, title_str)
        media.set_meta(vlc.Meta.Genre, genre_str)
        media.set_meta(vlc.Meta.Description, description_str)
        media.set_meta(vlc.Meta.Date, year_str)
        logger.debug(genre_str)
        res = media.save_meta()
        logger.debug(f'Save meta = {res}')
        del media

    def update_title_and_artist(self, index: int, artist: str, title: str, year: str, description: str):
        track = self.get_track(index)
        if track == None:
            logger.critical(f"try to access track number {index} returns None")
            return
        track["artist"] = artist.strip()
        track["title"] = title.strip()
        track["year"] = year.strip()
        track["description"] = description.strip()
        self.emit_datachanged(index, 4)  ## 4 = column 4 = description
        logger.debug(f'new description = {description}')
        self.save_track(index)
