import sys

from PyQt6 import QtWidgets, QtGui
from Player import Player
from TracksModel import TracksModel
from Logger import init_logger, logger


def main():
    init_logger()
    app = QtWidgets.QApplication(sys.argv)
    icon = QtGui.QIcon("./tracksorganizer.png")
    app.setWindowIcon(icon)
    conffile = './conf.yml'
    if len(sys.argv) == 2:
        conffile = sys.argv[1]
    player = Player(conffile)
    # if 'tracks' in conf['paths']:
    #     player.load_dir(conf['paths']['tracks'])
    player.show()
    # player.resize(800, 600)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
