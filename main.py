#Wanna find out what the best growth strategy is in a usual case
from collections import defaultdict, Counter
from random import random, randint
from math import log, ceil
from copy import deepcopy

from PIL import Image
import numpy as np

import contextlib
with contextlib.redirect_stdout(None):
    import pygame

from datastructures import Node

PIXEL_UNUSED, PIXEL_EMPTY = range(2)

fontcache = {}

def loadfont(fontname, size):
	key = (fontname,size)
	if key not in fontcache:
		fontcache[key] = pygame.font.Font(fontname, size)
	return fontcache[key]

def text(xy, text, color=(255,255,255), fontname=pygame.font.get_default_font(), size=12):
	font = loadfont(fontname, size)
	text = font.render(text, True, color)
	screen.blit(text, xy)

class Army:
	def __init__(self, target, strength):
		self.target = target
		self.strength = strength

class Player:
	def __init__(self, pno):
		self.pno = pno
		self.balance = 100
		self.color = [randint(100,255) for i in range(3)]	
		self.interest = 0.08
		self.armies = []
		
	def payInterest(self):
		self.balance += int(self.balance * self.interest)
		
	def play(self):
		pass

def nextPowerOfTwo(v):
	power = 1
	while power < v:
		power *= 2
	return power

QW = QH = 32

class World:
	def __init__(self):
		self.backgroundimage = Image.open("map.png")
		self.background = np.asarray(self.backgroundimage)

		self.w, self.h = self.backgroundimage.size
		print("loaded map with size", self.w, self.h)
		
		pot = ceil(log(max(nextPowerOfTwo(self.w/QW), nextPowerOfTwo(self.h/QH)), 2))
		print("pot", pot)
		
		self.ownership = Node(QW, QH, pot)
		
		for y in range(self.h):
			for x in range(self.w):
				if self.background[y][x][0] + self.background[y][x][1] - self.background[y][x][2] > 200:
					# impassable
					self.ownership.set(x,y,PIXEL_UNUSED)
				else:
					# occupyable
					self.ownership.set(x,y,PIXEL_EMPTY)
		
		print(self.ownership.counter)
		
		self.tick = 0
		
		NUMPLAYERS = 100

		self.players = {}
		
		for pno in range(PIXEL_EMPTY+1, NUMPLAYERS+PIXEL_EMPTY+1):
			self.players[pno] = Player(pno)
			
			while True:
				sx, sy = randint(0, self.w-1), randint(0, self.h-1)
				if self.empty_occupyable(self.ownership.get(sx, sy)):
					self.ownership.set(sx, sy, pno)
					break

	def occupyable(self, v):
		return v != PIXEL_UNUSED

	def empty_occupyable(self, v):
		return v == PIXEL_EMPTY

	def conquerable(self, pid, v):
		# TODO check adjacency?
		return self.occupyable(v) and v != pid and not self.friendly(pid, v)

	def friendly(self, pid1, pid2):
		if pid1 == 0 or pid2 == 0:
			return True
		
	
	def conquerableFor(self, pid):

		def inner(v):
			return self.conquerable(pid, v)

		return inner
	
	def isPlayer(self, pno):

		def inner(v):
			return v == pno

		return inner
	
	def getConquerableAdjacent(self, pno, count):
		return self.ownership.getBorderTo(pno, condition=self.conquerableFor(pno), count=count)

	def getAdjacentEnemy(self, pno, enemy, count):
		return self.ownership.getBorderTo(pno, condition=self.isPlayer(enemy), count=count, mustcontain=enemy)
	
	def getFreeAdjacent(self, pno, count):
		return self.ownership.getBorderTo(pno, condition=self.empty_occupyable, count=count, mustcontain=PIXEL_EMPTY)
	
	def update(self):

		
		for pno, player in self.players.items():
			for army in player.armies:
				if army.target != 1:
					attacking = int(army.strength*0.5)
					beforeBalance = self.players[army.target].balance
					self.players[army.target].balance -= attacking
					enemy_strength = self.ownership.counter[army.target]
					if enemy_strength > 0:
						lostTerritory = (attacking/beforeBalance)*enemy_strength
						actualLost = 0
						for x,y in self.getAdjacentEnemy(pno, army.target, lostTerritory):
							actualLost += 1
							self.ownership.set(x, y, pno)
						print(army.target, "lost", actualLost, "to", pno)
				else:
					attacking = int(army.strength*0.5)
					for x,y in self.getFreeAdjacent(pno, attacking):
						self.ownership.set(x, y, pno)
			
			# XXX
			player.armies = []
		
			player.balance += self.ownership.counter[pno]
		
		if self.tick > 0 and self.tick % 10 == 0:
			for pno, player in self.players.items():
				player.payInterest()
		
		
		defeated = []
		
		for pno, player in self.players.items():
			player.balance = min(150 * self.ownership.counter[pno], player.balance)
		
			if player.balance <= 0:
				defeated.append(pno)

			if player.balance > 0 and random() < 0.1:
				strength = randint(1, player.balance)
				player.balance -= strength
				player.armies.append(Army(PIXEL_EMPTY, strength))
				
			if player.balance > 0 and random() < 0.1:
				conquerable_adjacent = world.getConquerableAdjacent(pno, 1)
				if len(conquerable_adjacent) > 0:
					cx, cy = list(conquerable_adjacent)[0]
					strength = randint(1, player.balance)
					player.balance -= strength
					#print("attacking", self.ownership.get(cx, cy))
					player.armies.append(Army(self.ownership.get(cx, cy), strength))
				
					
		self.tick += 1
	
	def getMap(self):
		bg = np.array(self.background, copy=True)
		
		own = self.ownership.getAll()
		
		for y in range(self.h):
			for x in range(self.w):
				owner = own[y][x]
				if owner > PIXEL_EMPTY:
					bg[y][x] = self.players[owner].color
		
		return bg

world = World()

attacks = defaultdict(dict)

pygame.init()
pygame.display.set_caption("territorial.io")

clock = pygame.time.Clock()

screen = pygame.display.set_mode((world.w, world.h))

color = (0, 0, 0)

i = 0
running = True
while running:
	screen.fill(color)

	world.update()

	#pygame.draw.rect(screen, (255, 0, 0), pygame.Rect(i, i, 40, 30))
	i += 1

	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			running = False
		elif event.type == pygame.MOUSEBUTTONUP:
			pos = pygame.mouse.get_pos()
			print(pos)
	
	wmap = world.getMap()
	wmap = wmap.swapaxes(0,1)
	imgdata = pygame.surfarray.make_surface(wmap)
	
	screen.blit(imgdata, (0,0))

	text((world.w//2,world.h//2), "test")

	scores = Counter()
	
	for pno, player in world.players.items():
		scores[pno] = player.balance
	
	for scoreno, (pno, score) in enumerate(scores.most_common(10)):
		text((0, scoreno*12), f"{score: >16} {pno}")

	print(pygame.key.get_pressed()[pygame.K_UP])

	pygame.display.flip()
	clock.tick(60)





	
	
