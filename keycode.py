#! /usr/bin/env python3
from PyQt6.QtCore import Qt

print( eval('Qt.Key.Key_Escape'))
print( Qt.Key.Key_Escape.value)
# print( dir(Qt.Key) )

k = filter(lambda key_name: key_name[0:4] == 'Key_', dir(Qt.Key))

print(list(k))