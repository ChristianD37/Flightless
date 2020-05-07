from game import Game
from settings import *
from os import path

# Font: "Press Start 2P" by codeman38


# Initialize and create window


g = Game()
# Load music
pygame.mixer.music.load(path.join(g.sound_dir, "little march.ogg"))
pygame.mixer.music.play(-1)

g.logoScreen()
while g.running:

    g.startScreen()  # Show the start screen
    g.play_again = True
    if not g.running:
        break
    if g.selectCursor.selected == "CREDITS":
        g.Credits()
    elif g.selectCursor.selected == "OPTIONS":
        g.optionsMenu()
    else:
        while g.play_again and g.running:
            g.reset()
            g.Gameover()
            # Reset title music
            pygame.mixer.music.set_volume(g.volume_mult)
            pygame.mixer.music.load(path.join(g.sound_dir, "little march.ogg"))
            pygame.mixer.music.play(-1)


pygame.quit()