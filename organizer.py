import sys

from PyQt6 import QtWidgets, QtGui
from Player import Player
from Logger import init_logger
from pathlib import Path
from Conf import Conf

def main():
    init_logger()
    app = QtWidgets.QApplication(sys.argv)
    icon = QtGui.QIcon("./tracksorganizer.png")
    app.setWindowIcon(icon)
    conffile = './conf.yml'
    if len(sys.argv) == 2:
        conffile = sys.argv[1]
    player = Player(conffile, app)
    if 'tracks' in Conf.conf_data['paths']:
        player.load_dir(Path(Conf.conf_data['paths']['tracks']))
    player.show()
    # player.resize(800, 600)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
