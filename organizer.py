import sys, json

from PyQt6 import QtWidgets
from Player import Player
from TracksModel import TracksModel
from Logger import init_logger

def load_conf(conffile = './conf.json'):
    with open(conffile) as jsonfile:
        stringdata = jsonfile.read()
        return json.loads(stringdata)

def main():
    init_logger()
    app = QtWidgets.QApplication(sys.argv)
    conf = load_conf('./conf.json')
    player = Player(conf)
    if 'default' in conf:
        player.load_dir(conf['default'])
    player.show()
    player.resize(800, 600)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
