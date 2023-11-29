import sys

from PyQt6 import QtWidgets, QtGui
from Player import Player
from TracksModel import TracksModel
from Logger import init_logger, logger

def load_conf(conffile = './conf.yml'):
    import yaml
    with open(conffile) as file:
        stringdata = yaml.safe_load(file)
        return stringdata

def main():
    init_logger()
    app = QtWidgets.QApplication(sys.argv)
    icon = QtGui.QIcon("./tracksorganizer.png")
    app.setWindowIcon(icon)
    conffile = './conf.yml'
    if len(sys.argv) == 2:
        conffile = sys.argv[1]
    logger.debug(conffile)
    conf = load_conf(conffile)
    player = Player(conf)
    if 'tracks' in conf['paths']:
        player.load_dir(conf['paths']['tracks'])
    player.show()
    # player.resize(800, 600)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
