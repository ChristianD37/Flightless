import pygame

TITLE = "FLIGHTLESS"
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 600
FPS = 60
FONT = "assets/PressStart2P-vaV7.ttf"
HS_FILE = "highscore.txt"
SPRITESHEET = "articSpritesv.png"

#define colors

white = (255,255,255)
black = (0,0,0)
red = (255,0,0)
green = (0,255,0)
blue = (0,0,255)

# Starting platforms
platform_list = [(0, SCREEN_HEIGHT-40), (200, SCREEN_HEIGHT * 3 /4 ), (SCREEN_WIDTH/2 - 30, SCREEN_HEIGHT * .5 ), (250, SCREEN_HEIGHT * .2 ),(SCREEN_WIDTH/2, -20)]

# player properties
player_acc = .7
friction = -.12
gravity = .8
player_jump = -18

# OPTIONS

# Define player keys
#

# SET VOLUME ADJUSTMENT



