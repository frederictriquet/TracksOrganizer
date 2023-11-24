import sys, json

from PyQt6 import QtWidgets
from Player import Player
from TracksModel import TracksModel
from Logger import init_logger

def load_conf(conffile = './conf.yml'):
    import yaml
    with open(conffile) as file:
        stringdata = yaml.safe_load(file)
        return stringdata

def main():
    init_logger()
    app = QtWidgets.QApplication(sys.argv)
    conf = load_conf('./conf.yml')
    player = Player(conf)
    if 'tracks' in conf['paths']:
        player.load_dir(conf['paths']['tracks'])
    player.show()
    # player.resize(800, 600)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
