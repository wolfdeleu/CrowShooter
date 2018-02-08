#!/usr/bin/python
# -*- encoding: utf-8 -*-

__author__ = 'danieldeichfuss und wolfdeleu'

# Import Module
import os.path
import time
import sqlite3
from random import randint
import pygame
import pygame.gfxdraw
from pygame.locals import *

# Fenster beim Öffnen zentrieren
os.environ['SDL_VIDEO_CENTERED'] = '1'

# Überprüfen, ob die optionalen Text- und Sound-Module geladen werden konnten.
if not pygame.font: print('Fehler pygame.font Modul konnte nicht geladen werden!')
if not pygame.mixer: print('Fehler pygame.mixer Modul konnte nicht geladen werden!')

# Klasse Sound
class Sound():
    # Krähen Atmo
    def getCrows(self):
        return self.loadSound('crows.wav')

    # Spatzen Atmo
    def getSparrows(self):
        return self.loadSound('sparrows.wav')

    def getGun(self):
        return self.loadSound('shot.wav')

    # Nachladen der Waffe
    def getReload(self):
        return self.loadSound('reload.wav')

    # Sound der leeren Waffe (ungeladen)
    def getEmpty(self):
        return self.loadSound('empty.wav')

    # Krähensound laden (beim Abschuss)
    def getCrow(self):
        return self.loadSound('deadcrow.wav')

    # Spatzensound laden (beim Abschuss)
    def getSparrow(self):
        return self.loadSound('deadsparrow.wav')

    # Spielmusik laden
    def getMusic(self):
        return self.loadSound('game.wav')

    # Allgemeine Funktion zum Musik laden
    def loadSound(self, name):
        class NoneSound:
            def play(self): pass

        if not pygame.mixer or not pygame.mixer.get_init():
            return NoneSound()
        sound_data = os.path.join('data/sound', name)
        try:
            sound = pygame.mixer.Sound(sound_data)
        except pygame.error as message:
            print('Cannot load sound:', sound_data)
            raise SystemExit(message)
        return sound

# Klasse Image
class Image():
    _width = 1300
    _height = 600

    # Vogelbilder laden (Loop abhängig)
    def getBird(self, bird, loop):
        if bird == 'crow':
            if 1 <= loop <= 5:
                return self.loadImage('crow_loop' + str(loop) + '.gif', -1)
            else:
                return self.loadImage('crow.gif', -1)
        else:
            if 1 <= loop <= 5:
                return self.loadImage('sparrow_loop' + str(loop) + '.gif', -1)
            else:
                return self.loadImage('sparrow.gif', -1)

    # Hintergundbild laden (Spielfläche)
    def getBackground(self):
        return self.loadImage('background.png', None, 'Background')

    # Hintergundbild laden (Spielstart Anweisung)
    def getInstruction(self):
        return self.loadImage('instruction.png', None, 'Background')

    # Hintergundbild laden (Spielende Highscore)
    def getHighscore(self):
        return self.loadImage('highscore.png', None, 'Background')

    # Fadenkreuz
    def getBacksight(self):
        return self.loadImage('backsight.gif', -1)

    # Fadenkreuz mit roter Markierung
    def getFocus(self):
        return self.loadImage('focus.gif', -1)

    # Schussanzeige (Anzahl der nicht/vorhandenen Patronen)
    def getBullet(self, bool = False):
        if bool:
            return self.loadImage('bullet.png', None, 'Bullet')
        else:
            return self.loadImage('bulletfill.png', None, 'Bullet')

    # Spielfeldbreite übergeben
    def getWidth(self):
        return self._width

    # Spielfeldhöhe übergeben
    def getHeight(self):
        return self._height

    # Allgemeine Funktion zum Bilder laden
    def loadImage(self, name, color_key = None, image_type = 'Asset'):
        image_data = os.path.join('data/image', name)
        try:
            image = pygame.image.load(image_data)
        except pygame.error as message:
            print('Cannot load image:', image_data)
            raise SystemExit(message)
            image = image.convert()
        if color_key is not None:
            if color_key is -1:
                color_key = image.get_at((0, 0))
                image.set_colorkey(color_key, RLEACCEL)
        if image_type is 'Asset':
            return image, image.get_rect()
        return image

# Klasse Sniper
class Sniper(pygame.sprite.Sprite):
    # Bewegt den Mauszeiger übers Display
    def __init__(self):
        image = Image()
        pygame.sprite.Sprite.__init__(self)
        self.backsight, self.backsightbox = image.getBacksight()
        self.focus, self.focusbox = image.getFocus()
        self.setBacksight()
        self.connect = 0
        self.size = 100
        self.isfocus = False

    # Position vom Fadenkreuz mit Mauszeiger verbinden
    def update(self):
        position = pygame.mouse.get_pos()
        self.rect.left = position[0]
        self.rect.top = position[1]
        if self.connect:
            self.rect.move_ip(1, 1)

    # Fadenkreuz Bild laden
    def setBacksight(self):
        self.image = self.backsight
        self.rect = self.backsightbox

    # Fadenkreuz mit roter Markierung laden
    def setFocus(self):
        self.image = self.focus
        self.rect = self.focusbox
        self.image = pygame.transform.scale(self.image, (self.size, self.size))
        self.rect.inflate((self.size, self.size))
        self.isfocus = True

    # Zurücksetzen und Fadenkreuz anzeigen
    def setSniper(self):
        self.setBacksight()
        self.isfocus = False

    # Schuss
    def shot(self, target):
        if not self.connect:
            self.connect = 1
            shot_point = self.rect.left, self.rect.top
            return target.rect.collidepoint(shot_point)

    # Definition, wo der Hover Effekt ist (mittig vom Fadenkreuz Bild)
    def hover(self, target):
        hover_point = self.rect.left + round(self.size / 2), self.rect.top + round(self.size / 2)
        return target.rect.collidepoint(hover_point)

    # Focus entfernen und Fadenkreuz setzen (Verbindung zum Vogelobjekt nicht vorhanden)
    def reset(self):
        self.connect = 0
        self.setBacksight()
        self.isfocus = False

    # Fadenkreuz mit roten Punkt anzeigen
    def showFocus(self):
        if not self.isfocus:
            self.setFocus()

    # Fadenkreuz anzeigen
    def showSniper(self):
        if self.isfocus:
            self.setSniper()

# Klasse Bird
class Bird(pygame.sprite.Sprite) :
    _width = 0
    _height = 0
    _image = Image()
    _direction = 'l'
    _speed = 0
    _bird = ''

    # Definition der Vogelarten mit Größe, Name und Sound
    def __init__(self, bird):
        sound = Sound()
        self.crows_sound = sound.getCrows()
        self.sparrows_sound = sound.getSparrows()
        pygame.sprite.Sprite.__init__(self)
        screen = pygame.display.get_surface()
        self.area = screen.get_rect()
        if bird == 'crow':
            self._bird = 'crow'
            self._width = 100
            self._height = 128
        else:
            self._bird = 'sparrow'
            self._width = 64
            self._height = 47
        self.image, self.rect = self._image.getBird(bird, 0)
        self.setPosition()

    # Beim Durchlauf der Logik Objekte updaten
    def update(self):
        self._birds()
        self._fly()

    # Position, Geschwindigkeit, Richtung usw. per Zufall generieren
    def setPosition(self):
        self.image, self.rect = self._image.getBird(self._bird, 0)
        lor = randint(1, 2) # Links oder Rechts
        speedx = randint(2, 8)
        self._speed = speedx
        if lor == 1:
            self.image = pygame.transform.flip(self.image, 1, 0)  # Bilddrehen
            x = -(self._width)
            self._direction = 'r'
        else:
            x = 1300
            speedx = -speedx
            self._direction = 'l'
        y = randint(0, 600 - self._height)
        self.rect.topleft = x, y  # startposition
        speedy = randint(-1, 1)
        self.speed = [speedx, speedy]

    # Wenn Vogel erschossen, neue Position außerhalb der Spielfläche positionieren
    def isShot(self):
        self.setPosition()

    # Bewegung der Vögel mit unterschiedlichen Geschwindigkeiten usw.
    def _fly(self):
        new_pos = self.rect.move(self.speed)
        if self.rect.left < self.area.left - (self._width + 10) or self.rect.right > self.area.right + (self._width + 10):
            self.setPosition()
            new_pos = self.rect.move(self.speed)
        if self.rect.top < self.area.top - (self._height + 10) or self.rect.bottom > self.area.bottom + (self._height + 10):
            self.setPosition()
            new_pos = self.rect.move(self.speed)
        self._animate()
        self.rect = new_pos

    # Zuordnung der Vogelsounds
    def _birds(self):
        random = randint(1, 600)
        if random == 1 and self._bird == 'crow':
            self.crows_sound.play()
        elif random == 1:
            self.sparrows_sound.play()

    # Bewegung der Vögel animieren mit Hilfe der Zeit, Richtung usw.
    def _animate(self):
        move = round(time.time() * (6 + round(self._speed / 2)))
        self.image, self.rect = self._image.getBird(self._bird, (move % 6) + 1)
        if self._direction == 'r':
            self.image = pygame.transform.flip(self.image, 1, 0)  # Bilddrehen

# Klasse Higscore (mit Datenbankanbindung)
class Highscore():
    # Spielername aus einer ini-Datei laden (für den Highscore)
    def loadData(self):
        with open(os.path.join('data', 'crow.ini'), 'r') as file:
            try:
                self._name = str(file.read())
            except:
                self._name = "Spieler"

    # Spielername in ini-Datei speichern (für den Highscore)
    def saveData(self, name):
        with open(os.path.join('data', 'crow.ini'), 'w') as file:
            file.write(str(name))

    # Datenbankverbindung herstellen
    def connect_to_db(self):
        self.conn = sqlite3.connect(os.path.join('data', 'highscore.db'))
        self.cursor = self.conn.cursor()
        sql_command = """CREATE TABLE IF NOT EXISTS highscore (score INTEGER, name VARCHAR (32));"""
        self.cursor.execute(sql_command)

    # Neuen Highscore in Datenbank speichern
    def write_to_db(self, high_score, name):
        sql_command = """INSERT INTO highscore VALUES(?, ?)"""
        self.cursor.execute(sql_command, (high_score, self._name))
        self.conn.commit()

    # Daten aus der Datenbank laden und als Array zurückgeben
    def get_db_data(self):
        self.cursor.execute("SELECT * FROM highscore")
        rows = self.cursor.fetchall()
        highscoreArray = []
        for row in rows:
            highscoreArray.append((row[0], row[1]))
        return highscoreArray

    # Wenn noch keine Daten vorhanden Datenbank mit Samples initialisieren
    def fill_db_with_fake_data(self):
        fakeDataHighscore = [(5, "Marcell"), (10, "Daniel"), (15, "Ben"), (20, "Alex"), (25, "Max"), (30, "Kim"),
                             (35, "Tom"),
                             (40, "Bella")]
        for item in fakeDataHighscore:
            self.write_to_db(item[0], item[1])

# Klasse Game
class Game():

    # Spiel initialisieren (Sounds, Zeit, Bullets usw.)
    def __init__(self):
        sound = Sound()
        self.gun_sound = sound.getGun()
        self.empty_sound = sound.getEmpty()
        self.reload_sound = sound.getReload()
        self.dead_crow = sound.getCrow()
        self.dead_sparrow = sound.getSparrow()
        self._music_sound = sound.getMusic()
        self._music_sound.play()
        self._start = time.time()
        self._gametime = 60
        self._score_num = 0
        self._shot_num = 0
        self._bullet_num = 15
        self._play_game = True

    # Beenden der Game While Schleife
    def stopGame(self):
        self._play_game = False

    # Rückgabe der Spielzeit
    def getGametime(self):
        return self._gametime

    # Rückgabe der aktuellen Zeit (Minus Counter)
    def getTime(self):
        return self.getGametime() - round(time.time() - self._start)

    # Methode für diverse Abfragen (zeitliche Berechnung)
    def waitInstruction(self):
        return round(time.time() - self._start)

    # Anzahl der Schüsse zurückgeben
    def getBullets(self):
        return self._bullet_num

    # Nachladen und entsprechende Sounds nach Zustand zurückgeben
    def setBullets(self, load = False):
        if load:
            self._bullet_num = 15
            self.reload_sound.play()
        elif self._bullet_num > 0:
            self._bullet_num -= 1
            self.setShots()
            self.gun_sound.play()
        else:
            self._bullet_num = 0
            self.empty_sound.play()

    # Aktuelle Punkte zurückgeben
    def getScore(self):
        return self._score_num

    # Punkte setzen
    def setScore(self, points):
        if points >= 1:
            self.dead_crow.play()
        elif points == -5:
            self.dead_sparrow.play()
        if self._score_num + points < 1:
            self._score_num = 0
        else:
            self._score_num += points

    # Anzahl der Schüsse zurückgeben
    def getShots(self):
        return self._shot_num

    # Anzahl der Schüsse um 1 erhöhen
    def setShots(self):
        self._shot_num += 1


def main():
    image = Image()
    playgame = pygame
    playgame.init()
    playgame.mouse.set_visible(0)
    display = playgame.display
    displaysize = (image.getWidth(), image.getHeight())
    screen = display.set_mode(displaysize)
    display.set_caption('Märkisches Viertel - Krähenschießen')
    pygame.display.update()
    pygame.display.flip()
    bg = image.getBackground()
    instruction = image.getInstruction()
    highscore = image.getHighscore()

    bullet = image.getBullet(True)
    bulletfill = image.getBullet()
    clock = pygame.time.Clock()

    # Instanzen
    game = Game()
    sniper = Sniper()
    crow1 = Bird('crow')
    crow2 = Bird('crow')
    crow3 = Bird('crow')
    crow4 = Bird('crow')
    sparrow1 = Bird('sparrow')
    sparrow2 = Bird('sparrow')
    sparrow3 = Bird('sparrow')
    sparrow4 = Bird('sparrow')
    level = pygame.sprite.LayeredUpdates()
    level.add(crow1)
    level.add(crow2)
    level.add(crow3)
    level.add(crow4)
    level.add(sparrow1)
    level.add(sparrow2)
    level.add(sparrow3)
    level.add(sparrow4)
    level.add(sniper)

    gotScore = False

    # Instructionsanzeige
    while game.waitInstruction() < 10:
        wait = pygame.font.Font(None, 70)
        wait = wait.render(" Start in {0} s  ".format(-game.waitInstruction() + 10), 1, (133, 124, 100), (212, 212, 210))
        instruction.blit(wait, (145, 490))
        screen.blit(instruction, (0, 0))
        pygame.display.flip()

    # Spiellogik
    while game._play_game:
        clock.tick(60)

        # Nach Spielende Highscore einblenden
        if round(game.getTime()) < 1:
            if not gotScore:
                db_Highscore = Highscore()
                db_Highscore.loadData()
                db_Highscore.connect_to_db()
                if len(db_Highscore.get_db_data())<1:
                    db_Highscore.fill_db_with_fake_data()
                db_Highscore.write_to_db(game.getScore(), db_Highscore._name)
                highscoreArray = db_Highscore.get_db_data()
                print(highscoreArray)
                highscoreArray.sort(reverse=True)
                gotScore = True

            # Highscore anzeigen
            while round(game.getTime()) >= -10:
                wait = pygame.font.Font(None, 70)
                wait = wait.render(" Close in {0} s  ".format(-game.waitInstruction() + 70), 1, (133, 124, 100), (212, 212, 210))
                highscore.blit(wait, (145, 490))
                x_score = 150
                y_score = 150
                x_name = 230

                # Highscore auslesen
                for x in range(0, 8):
                    color = (133, 124, 100)
                    if highscoreArray[x][0] == game.getScore():
                        color = (229, 72, 37)

                    score_item = pygame.font.Font(None, 50)
                    score_name = pygame.font.Font(None, 50)
                    score_item = score_item.render(str(highscoreArray[x][0]), True, color, (212, 212, 210))
                    score_name = score_name.render(str(highscoreArray[x][1]), True, color, (212, 212, 210))
                    highscore.blit(score_item, (x_score, y_score))
                    highscore.blit(score_name, (x_name, y_score))
                    y_score = y_score + 40

                # Bildschirm aktualiseren
                screen.blit(highscore, (0, 0))
                pygame.display.flip()

            # Spiel beenden
            game.stopGame()

        # Fadenkreuz entsprechend anpassen (mit und ohne roter Markierung)
        if sniper.hover(crow1) or sniper.hover(crow2) or sniper.hover(crow3) or sniper.hover(crow4) \
                or sniper.hover(sparrow1) or sniper.hover(sparrow2) or sniper.hover(sparrow3) or sniper.hover(sparrow4):
            sniper.showFocus()
        else:
            sniper.showSniper()

        # Event Handler (Reaktion/Interaktion)
        for event in pygame.event.get():
            if event.type == QUIT:          # Fenster schließen (X)
                game.stopGame()
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:   # Fenster schließen (Escape)
                    game.stopGame()

            # Event Behandlung bei Mausklick (vorher und nachher)
            elif event.type == MOUSEBUTTONDOWN:
                if event.button == 2 or event.button == 3:
                    game.setBullets(True)
                else:
                    game.setBullets()
                    if game.getBullets() > 0:
                        if sniper.hover(crow1):
                            game.setScore(10)
                            crow1.isShot()
                        elif sniper.hover(crow2):
                            game.setScore(10)
                            crow2.isShot()
                        elif sniper.hover(crow3):
                            game.setScore(10)
                            crow3.isShot()
                        elif sniper.hover(crow4):
                            game.setScore(10)
                            crow4.isShot()
                        elif sniper.hover(sparrow1):
                            game.setScore(-5)
                            sparrow1.isShot()
                        elif sniper.hover(sparrow2):
                            game.setScore(-5)
                            sparrow2.isShot()
                        elif sniper.hover(sparrow3):
                            game.setScore(-5)
                            sparrow3.isShot()
                        elif sniper.hover(sparrow4):
                            game.setScore(-5)
                            sparrow4.isShot()
                        else:
                            game.setScore(-1)
            elif event.type == MOUSEBUTTONUP:
                sniper.reset()

        # Update aller Vögel, Fadenkreuz
        crow1.update()
        crow2.update()
        crow3.update()
        crow4.update()
        sparrow1.update()
        sparrow2.update()
        sparrow3.update()
        sparrow4.update()
        sparrow4.update()
        sniper.update()

        # Zeit anzeigen
        time = pygame.font.Font(None, 85)
        time = time.render(" {0}   ".format(game.getTime()), 1, (255, 255, 255), (121, 184, 224))
        bg.blit(time, (600, 15))
        screen.blit(bg, (0, 0))

        # Score anzeigen
        score = pygame.font.Font(None, 40)
        score = score.render("Score: {0}   ".format(game.getScore()), 1, (255, 255, 255), (121, 184, 224))
        bg.blit(score, (15, 15))
        screen.blit(bg, (0, 0))

        # Schüsse anzeigen
        shots = pygame.font.Font(None, 25)
        shots = shots.render("Shots: {0} ".format(game.getShots()), 1, (255, 255, 255), (121, 184, 224))
        bg.blit(shots, (15, 45))
        screen.blit(bg, (0, 0))

        # Bulletanzeige
        for x in range(0, game.getBullets()):
            bg.blit(bullet, ((x * 10) + 1140, 15))
        for x in range(game.getBullets(), 15):
            bg.blit(bulletfill, ((x * 10) + 1140, 15))

        # Bildschirm aktualiseren
        level.draw(screen)
        pygame.display.flip()

if __name__ == '__main__':
    main()
