import struct
from math import *
from mathFunctions import *
from structFunctions import *

class Envmap(object):
    def __init__(self, path):
        self.path = path
        self.read()

    def read(self):
        image = open(self.path, 'rb')
        image.seek(10)
        headerSize = struct.unpack('=l', image.read(4))[0]

        image.seek(14 + 4)
        self.width = struct.unpack('=l', image.read(4))[0]
        self.height = struct.unpack('=l', image.read(4))[0]
        image.seek(headerSize)

        self.pixels = []

        for y in range(self.height):
            self.pixels.append([])
            for x in range(self.width):
                b = ord(image.read(1))
                g = ord(image.read(1))
                r = ord(image.read(1))
                self.pixels[y].append(color(r, g, b))

        image.close()

    def get_color(self, direction):
        direction = norm(direction)

        x = int((atan2(direction[2], direction[0]) / (2 * pi) + 0.5) * self.width)
        y = int(acos(-direction[1]) / pi * self.height)

        if x < self.width and y < self.height:
            return self.pixels[y][x]
        else:
            return color(0, 0, 0)