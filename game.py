import pygame
from settings import *
from Sprites import *
import random
from os import path, environ


class Game:
    def __init__(self):
        # Initialize game window
        pygame.mixer.pre_init(44100, -16, 2, 2048) # Prevents delay in jumping sound
        pygame.init()
        pygame.mixer.init()
        self.monitor_size = [pygame.display.Info().current_w,pygame.display.Info().current_h]
        environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (self.monitor_size[0] / 2 - SCREEN_WIDTH/2, self.monitor_size[1] / 2 - SCREEN_HEIGHT/2)
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.fullScreen = False
        pygame.display.set_caption(TITLE)
        self.VOLUME_SETTING = 100
        self.volume_mult = 1
        self.clock = pygame.time.Clock()
        self.running = True
        self.font_name = FONT
        # Load saved data
        self.load_data()
        self.start_image = pygame.image.load("Sprites/start_screen.png")
        pygame.mixer.music.load(path.join(self.sound_dir, "little march.ogg"))
        self.water = pygame.image.load("Sprites/water2.png")
        self.mountains = pygame.image.load("Sprites/mountains.png")
        self.moon = pygame.transform.scale(pygame.image.load("Sprites/moon.png"), (45,45) )
        self.play_again = True
        self.jump_range = 50
        self.spawn_y = 0
        self.plat_chance = 10
        self.balloon_chance = 1000
        self.last_score = 0


    def reset(self):
        self.press_sound.play()
        # Display The Ready Screen
        self.ReadyScreen()
        if not self.running:
             return
        self.score = 0
        # Initialize non-player sprites
        self.all_Sprites = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.balloons = pygame.sprite.Group()
        self.platforms = pygame.sprite.Group()
        self.seagulls = pygame.sprite.Group()
        self.objects = pygame.sprite.Group()

        # Spawn the player
        self.player = Player(self) # Reference all the games variables to the player as well
        self.all_Sprites.add(self.player)

        for plat in platform_list:
            p = Platform(self,*plat, self.platforms, self.all_Sprites) # * explodes the list
            self.last_spawn = p

        pygame.mixer.music.load(path.join(self.sound_dir, "theme.ogg"))
        #self.orca = orca(self)
        self.game()

    def game(self):
        # main game loop
        pygame.mixer.music.play(loops = -1) # Start the music loop
        self.playing = True
        while self.playing:
            self.clock.tick(FPS)
            self.events()
            self.update()
            self.draw()
        pygame.mixer.music.fadeout(50) # Fade out over half a second

    def update(self):
        # Game loop update
        self.all_Sprites.update()
        self.collisionCheck()
        self.platformSpawn()
        self.scrollUp()
        self.scrollDown()
        self.seagullSpawn()
        self.increase_difficulty()
        # Check for game over
        self.check_death()
        # Check if player reaches the top of the screen


    def events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.playing = False
                self.running = False
            if event.type == pygame.VIDEORESIZE:
                if not self.fullScreen:
                    self.screen = pygame.display.set_mode((event.w, event.h))
            if event.type == pygame.KEYDOWN: # better method for keeping track of how many times space is pressed
                if event.key == pygame.K_SPACE:
                    self.player.jump()
                if event.key == pygame.K_ESCAPE:
                    self.playing = False
                    self.running = False
                if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                    self.pause()
                if event.key == pygame.K_F5:
                    self.fullScreen = not self.fullScreen
                    if self.fullScreen:
                        self.screen  = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
                    else:
                        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_SPACE and not self.player.bouncing and not self.player.plummeting and not self.player.stun and not self.player.got_balloon:
                    self.player.velocity.y = 0 # also gives the flap effect
                    self.player.space_pressed += 1
                    if self.player.space_pressed > 1:
                        self.flap_sound.play()

    def pause(self):
        paused = True
        pygame.mixer.pause()
        while paused:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.playing = False
                    self.running = False
                    paused = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.playing = False
                        self.running = False
                        return
                    if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                        pygame.mixer.unpause()
                        paused = False
                    if event.key == pygame.K_F5:
                        self.fullScreen = not self.fullScreen
                        if self.fullScreen:
                            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
                        else:
                            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
            self.draw_text("PAUSED", 24, white, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
            pygame.display.flip()


    def draw(self):
        self.screen.fill((47,55,150))
        self.screen.blit(self.water, (0,400))
        self.screen.blit(self.moon, (530, 50))
        self.screen.blit(self.mountains, (0,300))
        self.snoweffect()
        self.all_Sprites.draw(self.screen)
        self.screen.blit(self.player.image, self.player.rect) # always draw the player last so they aren't overshadowed
        self.draw_text(str(self.score), 22, white, SCREEN_WIDTH/2, 15)
        pygame.display.flip()

    def increase_difficulty(self):
        if self.score - self.last_score > 100:
            self.last_score = self.score
            self.plat_chance += 5
            self.balloon_chance +=10


    def check_death(self):
        if len(self.platforms) == 0 and not self.player.plummeting:
            self.player.plummeting = True
            self.falling_sound.play()

        if self.player.rect.top > SCREEN_HEIGHT: # If the top of the player hits the bottom screen, its game over
            self.falling_sound.stop()
            self.player.kill()
            for sprite in self.all_Sprites:
                #sprite.rect.y -= max(self.player.velocity.y,10) # Make platforms
                if sprite.rect.bottom < 0: # Kill any sprites that are no longer on screen
                    sprite.kill()
        if len(self.all_Sprites) == 0: # When all sprites are killed, reset the game
            self.lose_sound.play()
            self.playing = False

    def collisionCheck(self):
        # Check if the player hits a platform, but only when falling
        if self.player.velocity.y > 0 and not self.player.got_balloon:
            hits = pygame.sprite.spritecollide(self.player, self.platforms, False,)
            if hits:
                self.player.stun = False
                # Snap to the lowest platform that the player has collided with
                lowest = hits[0]
                for hit in hits:
                    if hit.rect.bottom > lowest.rect.bottom:
                        lowest = hit
                if self.player.pos.y < lowest.rect.bottom: # Only snap to the platform if the player is above it
                    self.player.pos.y = lowest.rect.top
                    self.player.velocity.y = 0
                    self.player.rect.midbottom = self.player.pos # Keeps the player from jiggling by updating the player rect before drawing
                    self.player.jumping = False
                    self.player.space_pressed = 0
                    hit.touched = True
        enems = pygame.sprite.spritecollide(self.player,self.enemies, False,)
        if enems and not self.player.stun and not self.player.got_balloon:
            if self.player.pos.y < enems[0].rect.bottom and self.player.velocity.y > 0:
                if type(enems[0]).__name__ == "seagull":
                    self.bounceSeagull(enems[0])
                else:
                    self.bounce()
            else:
                self.knockback(self.player)
        power_up = pygame.sprite.spritecollide(self.player,self.balloons, False,)
        if power_up and not self.player.stun:
            power_up[0].used = True
            self.player.got_balloon = True


    def knockback(self, player):
        if not self.player.bouncing:
            self.hurt_sound.play()
            player.stun = True
            player.velocity.y -= 12
            if player.velocity.x >= 0:
                player.velocity.x= -25
            else:
                player.velocity.x = 25

    def bounce(self):
        self.bounce_sound.play()
        self.player.bouncing = True
        self.player.velocity.y = -30
    def bounceSeagull(self, seagull):
        seagull.hit = True
        self.bounce_sound.play()
        self.player.bouncing = True
        self.player.velocity.y = -15





    # Checks if the camera needs to scroll up
    def scrollUp(self):
        if self.player.rect.top <= SCREEN_HEIGHT * .35:
            self.player.pos.y += max(abs(self.player.velocity.y),5) # Move the player's position
            self.spawn_y += max(abs(self.player.velocity.y), 5)
            self.addScore()
            for plat in self.platforms:
                plat.rect.y += max(abs(self.player.velocity.y),5) # Platforms should move at the same speed as the player
                if plat.rect.top >= SCREEN_HEIGHT: # If the platform goes offscreen, delete it
                     if (plat.hasSeal):
                         plat.seal.kill()
                     if plat.hasWalrus:
                         plat.walrus.kill()
                     if plat.hasSnowman:
                         plat.snowman.kill()
                     plat.kill()


            for enemy in self.enemies:
                enemy.rect.y += max(abs(self.player.velocity.y),5)  # Platforms should move at the same speed as the player
                if enemy.rect.top >= SCREEN_HEIGHT:# and not type(enemy).__name__ =='orca':  # If the platform goes offscreen, delete it
                    enemy.kill()
                    #self.score += 10
            for object in self.objects:
                object.rect.y += max(abs(self.player.velocity.y),5)  # Platforms should move at the same speed as the player
                if object.rect.top >= SCREEN_HEIGHT:  # If the platform goes offscreen, delete it
                    object.kill()



    # Checks if the camera needs to scroll down
    def scrollDown(self):
        if self.player.rect.bottom >= SCREEN_HEIGHT * 3/4:
            self.player.pos.y -= abs(self.player.velocity.y)
            for plat in self.platforms:
                plat.rect.y -= abs(self.player.velocity.y)
                if plat.rect.y < -SCREEN_HEIGHT/2:
                    plat.kill()
            for enemy in self.enemies:
                enemy.rect.y -= abs(self.player.velocity.y)
            for object in self.objects:
                object.rect.y -= abs(self.player.velocity.y)


    def addScore(self):
        if self.player.velocity.y < 0:
            self.score += abs(self.player.velocity.y / 12)
            self.score = self.truncate(self.score,3)
            if int(self.score) % 210 < 10:
                self.plat_chance += 1

    def platformSpawn(self):
        width = random.randrange(100, 150)  # get random with of the platform from the screen
        if self.last_spawn.rect.y > 0:
            if self.spawn_y > self.jump_range:
                self.spawn_y = 0
                self.last_spawn = Platform(self, random.randrange(0, SCREEN_WIDTH - width),
                                     random.randrange(-130,-100),self.platforms, self.all_Sprites ) # Spawn above the window)
            elif self.spawn_y > 20:
                if random.randint(1,self.plat_chance) ==  1:
                    self.spawn_y = 0
                    Platform(self, random.randrange(0, SCREEN_WIDTH - width),
                             random.randrange(-130,-100), self.platforms, self.all_Sprites)  # Spawn above the window)


    # def platformSpawn(self):
    #
    #     # Remove any overlapping platforms
    #     max_plat = 0
    #     for plat in self.platforms:
    #         overlaps = pygame.sprite.spritecollide(plat, self.platforms, False)
    #         if len(overlaps) > 1:
    #             if plat.hasSeal:
    #                 plat.seal.kill()
    #             if plat.hasWalrus:
    #                 plat.walrus.kill()
    #             if plat.hasSnowman:
    #                 plat.snowman.kill()
    #             plat.kill()
    #         if plat.rect.y < max_plat:
    #             max_plat = plat.rect.y
    #
    #
    #     while len(self.platforms) < 7:
    #         width = random.randrange(100,150) # get random with of the platform from the screen
    #         #print(max_plat)
    #         p = Platform(self,random.randrange(0, SCREEN_WIDTH-width),
    #                      random.randrange(max_plat - 60,max_plat  - 50),self.platforms, self.all_Sprites ) # Spawn above the window)
    #         #print(p.rect.y)
    #         max_plat = p.rect.y




    def seagullSpawn(self):
        if len(self.seagulls) < 1:
            if int(self.score) % 210 < 10:
                s = seagull(self)
        if len(self.balloons) < 1:
            if random.randint(1,self.balloon_chance) == 1:
                b = balloon(self)

    def draw_text(self, text, size, color, x, y):
        font = pygame.font.Font(self.font_name,size)
        text_surface = font.render(text,True,color)
        text_rect = text_surface.get_rect()
        text_rect.midtop = (x,y)
        self.screen.blit(text_surface, text_rect)

    def startScreen(self):
        waiting = True
        self.selectCursor = cursor(self)
        self.StartMenuStars()
        while waiting:
            self.screen.blit(self.start_image, (0,0))
            for star in self.stars:
                star.drawStar()
            self.selectCursor.drawCursor()
            self.draw_text(TITLE, 48, white, SCREEN_WIDTH/2, SCREEN_HEIGHT /4 + 20)
            #self.draw_text("A and D to move, Space to Jump", 18, white, SCREEN_WIDTH/2, SCREEN_HEIGHT/2 )
            self.draw_text("START", 15, white, SCREEN_WIDTH/2, SCREEN_HEIGHT *3/4 )
            self.draw_text("CREDITS", 15, white, SCREEN_WIDTH / 2, SCREEN_HEIGHT * 3 / 4 + 30)
            self.draw_text("OPTIONS", 15, white, SCREEN_WIDTH / 2, SCREEN_HEIGHT * 3 / 4 + 60)
            #self.draw_text("HOW TO PLAY", 15, white, SCREEN_WIDTH / 2, SCREEN_HEIGHT * 3 / 4 + 90)
            self.draw_text("High Score: " + str(self.highscore), 15, white, SCREEN_WIDTH / 2, SCREEN_HEIGHT /4 + 105)


            pygame.display.flip() # Print the contents to the screen
            waiting = self.wait_for_key("start")




    def wait_for_key(self, mode):
        waiting = True
        for event in pygame.event.get():
            if mode == "start":
                self.selectCursor.moveCursor(event)
            else:
                pass
            if event.type == pygame.QUIT:
                waiting = False
                self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                    return
                if event.key == pygame.K_F5:
                    self.fullScreen = not self.fullScreen
                    if self.fullScreen:
                        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
                    else:
                        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
                if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                    if mode == "options":
                        self.options_select()
                    else:
                        waiting = False
                elif (event.key == self.UP_KEY or event.key == self.DOWN_KEY) and mode == "options":
                    self.selectCursor.moveCursorOptions(event)
                elif event.key == pygame.K_BACKSPACE and mode == "options":
                    waiting = False
        return waiting

    def updateHighScore(self):
        if self.score > self.highscore:
            self.highscore = self.score
            self.draw_text("New High Score!", 15, white, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 40)
            with open(path.join(self.dir, HS_FILE), 'w') as file:
                file.write(str(self.highscore))
        else:
            self.draw_text("High Score: " + str(self.highscore), 15, white, SCREEN_WIDTH / 2, 15)

    def load_data(self):
        self.dir = path.dirname(path.abspath("game.py")) # Gets the directory name of the game.py file
        img_dir = path.join(self.dir, "Sprites")
        with open(path.join(self.dir,HS_FILE), 'r+' ) as file: # open highscore file, w allows us to write the file and creates it if doesnt exist
            # Read the highscore only if it exists
            try:
                self.highscore = float(file.read())
                file.close()
            except:
                self.highscore = 0 # If file isnt read, use 0

            # Load the spritesheet
            self.spritesheet = Spritesheet(path.join(img_dir, SPRITESHEET))

            # Load the snow
            self.initializeSnow()

            # Load controls
            self.LEFT_KEY = pygame.K_a
            self.RIGHT_KEY = pygame.K_d
            self.UP_KEY = pygame.K_w
            self.DOWN_KEY = pygame.K_s

            # load sounds
            self.sound_dir = path.join(self.dir, "sound")
            self.jump_sound = pygame.mixer.Sound(path.join(self.sound_dir, "Jump8.wav"))
            self.jump_sound.set_volume(.1)
            self.bounce_sound = pygame.mixer.Sound(path.join(self.sound_dir, "Bounce.wav"))
            self.bounce_sound.set_volume(.1)
            self.hurt_sound = pygame.mixer.Sound(path.join(self.sound_dir, "Hurt.wav"))
            self.hurt_sound.set_volume(.1)
            self.select_sound = pygame.mixer.Sound(path.join(self.sound_dir,"Cursor_Select.wav"))
            self.select_sound.set_volume(.1)
            self.press_sound = pygame.mixer.Sound(path.join(self.sound_dir, "Press_Sound.wav"))
            self.press_sound.set_volume(.1)
            self.flap_sound = pygame.mixer.Sound(path.join(self.sound_dir, "flap.wav"))
            self.flap_sound.set_volume(.1)
            self.falling_sound = pygame.mixer.Sound(path.join(self.sound_dir, "falling.wav"))
            self.falling_sound.set_volume(.5)
            self.lose_sound = pygame.mixer.Sound(path.join(self.sound_dir, "lose.wav"))
            self.lose_sound.set_volume(.5)
            self.up_sound = pygame.mixer.Sound(path.join(self.sound_dir, "fly_away.wav"))
            self.up_sound.set_volume(.5)


    def initializeSnow(self):
        # Initialize snow array
        self.snowflakes = []
        for i in range(200):
            self.snowflakes.append(snow(self))

    def snoweffect(self):
        for s in self.snowflakes:
            s.y += 1.5
            if (s.y > SCREEN_HEIGHT):
                s.x  = random.randrange(0,SCREEN_WIDTH)
                s.y = random.randrange(-50,-10)
            s.drawSnow()



    def truncate(self, n, decimals=0):
        multiplier = 10 ** decimals
        return int(n * multiplier) / multiplier

    def Credits(self):
        waiting = True
        self.press_sound.play()
        while waiting:

            self.screen.fill(black)
            self.snoweffect()
            self.draw_text("CREDITS", 48, white, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 4)
            self.draw_text("Game and Music by ", 22, white, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 45)
            self.draw_text("Christian Duenas", 22, white, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 )
            self.draw_text("Press Enter to return", 15, white, SCREEN_WIDTH / 2, SCREEN_HEIGHT * 3 / 4 + 100)
            self.draw_text("Font: \"Press Start 2P\" by codeman38 ", 15, white, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 50)
            self.draw_text("Thanks to Chris Bradfield for his pygame Tutorial ", 11, white, SCREEN_WIDTH / 2,SCREEN_HEIGHT / 2 + 160)
            self.draw_text("Music Created with BeepBox", 12, white, SCREEN_WIDTH / 2,SCREEN_HEIGHT / 2 + 100)
            self.draw_text("Sound Effects Created with Bfxr", 12, white, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 130)
            pygame.display.flip()  # Print the contents to the screen
            waiting = self.wait_for_key("credits")
        self.press_sound.play()

    def StartMenuStars(self):
        self.stars = []
        for i in range(100):
            self.stars.append(star(self, random.randrange(0, SCREEN_WIDTH), random.randrange(100, 390)))
        for i in range(30):
            self.stars.append(star(self, random.randrange(200, 400), random.randrange(10, 150)))

    def optionsMenu(self):
        waiting = True
        self.optionCursor = cursor(self)
        self.press_sound.play()
        self.selectCursor = cursor(self)
        self.selectCursor.selected = "VOLUME"
        self.selectCursor.offset = -125
        self.selectCursor.x = SCREEN_WIDTH / 2 + self.selectCursor.offset
        self.selectCursor.y = SCREEN_HEIGHT /2
        while waiting:
            if not self.running:
                return

            self.screen.fill(black)
            self.snoweffect()
            self.selectCursor.drawCursor()
            self.draw_text("OPTIONS", 48, white, SCREEN_WIDTH /2, SCREEN_HEIGHT / 4)
            self.draw_text("VOLUME", 18, white, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
            self.draw_text("CONTROLS", 18, white, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 30)
            self.draw_text("Press F5 to enter Fullscreen Mode", 12, white, SCREEN_WIDTH / 2, SCREEN_HEIGHT - 100)
            pygame.display.flip()  # Print the contents to the screen
            waiting = self.wait_for_key("options")

    def options_select(self):
        option = self.selectCursor.selected
        if option == "VOLUME":
            self.press_sound.play()
            self.volumeControl()
        elif option == "CONTROLS":
            self.press_sound.play()
            self.changeControls()

    def volumeControl(self):
        selected = False
        self.optionCursor.selected = "LOWER"
        self.optionCursor.x = SCREEN_WIDTH / 4 + self.optionCursor.offset
        self.optionCursor.y = SCREEN_HEIGHT / 2 + 80
        while not selected:
            self.screen.fill(black)
            self.snoweffect()
            self.draw_text("OPTIONS", 48, white, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 4)
            self.draw_text("VOLUME", 18, white, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
            self.draw_text("-", 18, white, SCREEN_WIDTH / 4, SCREEN_HEIGHT / 2 + 80)
            self.draw_text("+", 18, white, SCREEN_WIDTH * 3 / 4, SCREEN_HEIGHT / 2 + 80)
            self.draw_text(str(self.VOLUME_SETTING) +'%', 18, white, SCREEN_WIDTH /2, SCREEN_HEIGHT / 2 + 80)
            self.optionCursor.drawCursor()
            selected = self.optionCursor.controlOptionSound()
            self.adjustSounds()

            pygame.display.flip()  # Print the contents to the screen

    def adjustSounds(self):
        pygame.mixer.music.set_volume(self.volume_mult)
        self.jump_sound.set_volume(.1 * self.volume_mult)
        self.bounce_sound.set_volume(.1* self.volume_mult)
        self.hurt_sound.set_volume(.1 * self.volume_mult)
        self.select_sound.set_volume(.1 * self.volume_mult)
        self.press_sound.set_volume(.1* self.volume_mult)
        self.falling_sound.set_volume(.5 * self.volume_mult)
        self.flap_sound.set_volume(.1* self.volume_mult)
        self.lose_sound.set_volume(.5 * self.volume_mult)
        self.up_sound.set_volume(.5 * self.volume_mult)

    def changeControls(self):
        selected = False
        self.optionCursor.selected = "ASDW"
        self.optionCursor.x = SCREEN_WIDTH / 4 + self.optionCursor.offset
        self.optionCursor.y = SCREEN_HEIGHT / 2 + 80
        while not selected:

            self.screen.fill(black)
            self.snoweffect()
            self.draw_text("OPTIONS", 48, white, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 4)
            self.draw_text("CONTROLS", 18, white, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 30)
            self.draw_text("ASDW", 18, white, SCREEN_WIDTH / 4, SCREEN_HEIGHT / 2 + 80)
            self.draw_text("Arrow Keys", 18, white, SCREEN_WIDTH* 3 / 4, SCREEN_HEIGHT / 2 + 80)
            self.optionCursor.drawCursor()
            selected = self.optionCursor.controlOptionCursor()
            pygame.display.flip()  # Print the contents to the screen

    def Gameover(self):
        # Prevent the Game over screen when the user exits out

        pygame.mixer.music.load(path.join(self.sound_dir, "tired march.ogg"))
        pygame.mixer.music.set_volume(.7* self.volume_mult)
        pygame.mixer.music.play(-1)
        self.gameOver_cursors = cursor(self)
        selected = False
        self.gameOver_cursors.offset = -175
        self.gameOver_cursors.x = SCREEN_WIDTH / 2 + self.gameOver_cursors.offset
        self.gameOver_cursors.y = SCREEN_HEIGHT / 2

        while not selected:

            if not self.running:
                return
            self.screen.fill(black)
            self.snoweffect()
            self.draw_text("GAME OVER", 48, white, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 4)
            self.draw_text("Score:" + str(self.score), 22, white, SCREEN_WIDTH / 2, SCREEN_HEIGHT *3 / 4)
            self.draw_text("PLAY AGAIN", 18, white, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
            self.draw_text("RETURN TO MENU", 18, white, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 30)
            self.gameOver_cursors.drawCursor()
            pygame.display.flip()
            selected = self.gameOver_cursors.GameoverCursor()
            self.updateHighScore()

        if self.gameOver_cursors.selectedGO == "PLAY_AGAIN":
            self.play_again = True
        else:
            self.play_again = False

    def logoScreen(self):
        now = pygame.time.get_ticks()
        colors = 0
        #me = Christian(self)
        self.shootingStar = shooting_star(self, SCREEN_WIDTH, -60)
        self.shootingStar2 = shooting_star(self, SCREEN_WIDTH + 50, -60)
        while now < 6750:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    return
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.playing = False
                        self.running = False
                        return
                    if event.key == pygame.K_F5:
                        self.fullScreen = not self.fullScreen
                        if self.fullScreen:
                            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
                        else:
                            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

            self.screen.fill(black)
            if now > 1000:
                self.shootingStar.move()
                self.shootingStar.draw()
            if now > 1500:
                self.shootingStar2.move()
                self.shootingStar2.draw()
            #me.draw(now)
            self.draw_text("Game by Christian Duenas", 18, (colors,colors,colors), SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
            self.draw_text("2020 All Rights Reserved", 10, (colors,colors,colors), SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 30)
            #self.draw_text("This game is free", 10, (colors, colors, colors), SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 30)
            if (colors <= 255) and now < 4000:
                colors += .2
            elif now > 3000:
                if (colors >= 0):
                    colors -= .22
                else:
                    colors  = 0

            pygame.display.flip()
            now = pygame.time.get_ticks()


    def ReadyScreen(self):
        pygame.mixer.music.set_volume(self.volume_mult)
        pygame.mixer.music.load(path.join(self.sound_dir, "march_sound.ogg"))
        pygame.mixer.music.play(1)
        now = pygame.time.get_ticks()
        self.last_update = pygame.time.get_ticks()
        while now - self.last_update < 2700:
            self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    return
            now = pygame.time.get_ticks()
            self.screen.fill(black)
            self.snoweffect()
            self.draw_text("How High Can You Fly?", 24, white, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 50)
            self.draw_text("High Score: " + str(self.highscore), 15, white, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 30)
            pygame.display.flip()
