#Wanna find out what the best growth strategy is in a usual case
from collections import defaultdict, Counter
from time import sleep
from random import random, randint
from copy import deepcopy

from PIL import Image
import numpy as np

import contextlib
with contextlib.redirect_stdout(None):
    import pygame

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

QW = QH = 32

class Node:
	def __init__(self, level, parent=None, path=None, root=None):
		if path is None:
			self.path = []
		else:
			self.path = path
		self.parent = parent
		self.offset = 0
		self.level = level
		if root is None:
			self.root = self
		else:
			self.root = root
		self.counter = Counter({0:4**level*QW*QH})
		if level == 0:
			self.map = [[0 for x in range(QW)] for y in range(QH)]
			self.sx = 0
			self.sy = 0
			for i, v in enumerate(self.path):
				xx = v%2
				yy = v//2
				self.sx += 2**(len(self.path)-i)*QW//2*xx
				self.sy += 2**(len(self.path)-i)*QW//2*yy
			print(self.path, self.sx, self.sy)
		else:
			self.children = []
			for i in range(4):
				self.children.append(Node(level-1, self, self.path+[i], self.root))
	
	def index(self, x, y):
		scale = 2**self.level
		xres = scale*QW // 2
		yres = scale*QH // 2
		cx = x//xres
		cy = y//yres
		index = 2*cy+cx
		nx = x-xres*cx
		ny = y-yres*cy
		return index, nx, ny
	
	def get(self, x, y):
		if self.level == 0:
			return self.map[y][x]
		else:
			index, nx, ny = self.index(x,y)
			return self.children[index].get(nx, ny)

	def set(self, x, y, v):
		if self.level == 0:
			old = self.map[y][x]
			self.counter[old] -= 1
			self.counter[v] += 1
			self.map[y][x] = v
			return old
		else:
			index, nx, ny = self.index(x,y)
			old = self.children[index].set(nx, ny, v)
			self.counter[old] -= 1
			self.counter[v] += 1			
			return old
	
	def getQuad(self, path):
		if path is None:
			return None
		elif len(path) == 0:
			return self
		else:
			return self.children[path[0]].getQuad(path[1:])
	
	def pathmath(self, path, delta):
		print(path, delta)
		if path == []:
			# failure, out of bounds
			return None
		# only support single 0/1-deltas for now
		dx = delta[0]
		dy = delta[1]
		last = path[-1]
		lx = last%2
		ly = last//2
		nx = lx+dx
		ny = ly+dy
		if nx == -1:
			subpath = self.pathmath(path[:-1], (-1,0))
			return subpath + [1+2*ny] if subpath else None
		elif nx == 2:
			subpath = self.pathmath(path[:-1], (1,0))
			return subpath + [0+2*ny] if subpath else None
		elif ny == -1:
			subpath = self.pathmath(path[:-1], (0,-1))
			return subpath + [nx+2*1] if subpath else None
		elif ny == 2:
			subpath = self.pathmath(path[:-1], (0,1))
			return subpath + [nx+2*0] if subpath else None
		else:
			return path[:-1] + [nx+ny*2]
			
	
	def getRelativeQuad(self, path, delta):
		newpath = self.pathmath(path, delta)
		return self.root.getQuad(newpath)
	
	def allCoordDeltas(self, target):
		for y in range(QH):
			for x in range(QW):
				if self.map[y][x] == target:
					for delta in [(0,1), (0,-1), (1,0), (-1,0)]:
						yield x, y, delta
	
	def borderDeltas(self):
		#for caching efficiency
		for x in range(QW):
			yield x, 0, (0, -1)
		for x in range(QW):
			yield x, QH-1, (0, 1)
		for y in range(QH):
			yield 0, y, (-1, 0)
		for y in range(QH):
			yield QW-1, y, (1, 0)
	
	def getBorderTo(self, a, b):
		# could improve efficiency with intermediate stages
		if self.level == 0:
			if a not in self.counter:
				return set()
			
			# TODO if only a and 0 in count, only check siblings, outer border
			border = set()
			
			codeltagen = self.allCoordDeltas(a) if b in self.counter else self.borderDeltas()
			
			for x, y, delta in codeltagen:
				nx = x + delta[0]
				ny = y + delta[1]
				
				# TODO
				within = False
				if nx < 0:
					print(self.path)
					#	# check sibling, difficult in quadtree, may have to go several parents up, then down again
					#	self.parent.children[
					nx = QW-1
					ny = y
				elif ny < 0:
					nx = x
					ny = QH-1
				elif nx >= QW:
					nx = 0
					ny = y
				elif ny >= QH:
					nx = x
					ny = 0
				else:
					within = True
					# within this quad
					if self.map[ny][nx] == b:
						border.add((self.sx+nx, self.sy+ny))
				
				if not within:
					# TODO: cache this!
					sibling = self.root.getRelativeQuad(self.path, delta)
					if sibling is not None:
						if sibling.map[ny][nx] == b:
							border.add((self.sx+nx, self.sy+ny))
			return border
		else:
			if a in self.counter:
				total = set()
				for child in self.children:
					total = total.union(child.getBorderTo(a,b))
				return total
			else:
				return set()

	def getFullCount(self):
		return self.counter

	def getFullBaseCount(self):
		if self.level == 0:
			return self.counter
		else:
			return sum([child.getFullCount() for child in self.children], Counter())

root = Node(4)
print(root.get(0,0))
root.set(0,0,1)
print(root.get(0,0))
print(root.getFullCount())
print(root.getBorderTo(0,1))
exit(0)

class World:
	def __init__(self):
		self.backgroundimage = Image.open("map.png")
		self.background = np.asarray(self.backgroundimage)

		self.w, self.h = self.backgroundimage.size
		print("loaded map with size", self.w, self.h)
		self.ownership = [[0 for x in range(self.w)] for y in range(self.h)]
		
		
		self.tick = 0
		
		self.total_occupyable = 0
		
		for y in range(self.h):
			for x in range(self.w):
				if self.occupyable(x, y):
					self.total_occupyable += 1

		NUMPLAYERS = 100

		self.players = {}
		
		for p in range(1, NUMPLAYERS+1):
			pno = len(self.players)
			self.players[pno] = Player(pno)
			
			while True:
				sx, sy = randint(0, self.w-1), randint(0, self.h-1)
				if self.empty_occupyable(sx, sy):
					self.ownership[sy][sx] = pno
					break

	def occupyable(self, x, y):
		return not np.array_equal(self.background[y][x], [0,0,0]) and self.background[y][x][0] + self.background[y][x][1] - self.background[y][x][2] > 100 

	def empty_occupyable(self, x, y):
		return self.occupyable(x, y) and self.ownership[y][x] == 0

	def conquerable(self, pid, x, y):
		# TODO check adjacency?
		return self.occupyable(x, y) and self.ownership[y][x] != pid and not self.friendly(pid, self.ownership[y][x])

	def friendly(self, pid1, pid2):
		if pid1 == 0 or pid2 == 0:
			return True
		
	
	def conquerableFor(self, pid):

		def inner(x, y):
			return self.conquerable(pid, x, y)

		return inner
	
	def isPlayer(self, pno):

		def inner(x, y):
			return self.ownership[y][x] == pno

		return inner
	
	def getConquerableAdjacent(self, pno, count):
		return self.getAdjacent(pno, count, condition=self.conquerableFor(pno))

	def getAdjacentEnemy(self, pno, enemy, count):
		return self.getAdjacent(pno, count, condition=self.isPlayer(enemy), checkreverse=True)
	
	def getFreeAdjacent(self, pno, count):
		return self.getAdjacent(pno, count, condition=self.empty_occupyable, checkreverse=True)
	
	def getAdjacent(self, pno, count, condition, checkreverse=False):
		found = 0
		adjacent = []
		playerset = self.playersets[pno] if not checkreverse else reversed(self.playersets[pno])#should be a bit faster, because newer fields (less likely to be completely surrounded by own ones) are checked first, unless array is copied
		for x,y in playerset:
			for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
				nx, ny = x+dx, y+dy
				if nx < 0 or ny < 0 or nx >= self.w or ny >= self.h:
					continue
				
				if condition(nx, ny):
					adjacent.append([nx,ny])
				
			if found == count:
				return adjacent

		return adjacent
	
	def update(self):


		cnt = Counter()
		
		self.playersets = defaultdict(list)
		
		for y in range(self.h):
			for x in range(self.w):
				cnt[self.ownership[y][x]] += 1
				self.playersets[self.ownership[y][x]].append([x,y])
		"""
		
		unique, counts = np.unique(self.ownership, return_counts=True)
		for pno, count in zip(unique, counts):
			cnt[pno] = count
			
			self.playersets[pno] = np.argwhere(self.ownership==pno)#list(zip(*np.where(self.ownership==pno)))
		"""
		print(cnt)
		
		for pno, player in self.players.items():
		
			for army in player.armies:
				if army.target != 0:
					attacking = int(army.strength*0.5)
					beforeBalance = self.players[army.target].balance
					self.players[army.target].balance -= attacking
					lostTerritory = (attacking/beforeBalance)*len(self.playersets[army.target])
					actualLost = 0
					for x,y in self.getAdjacentEnemy(pno, army.target, lostTerritory):
						actualLost += 1
						self.ownership[y][x] = pno
					print(army.target, "lost", actualLost, "to", pno)
				else:
					attacking = int(army.strength*0.5)
					for x,y in self.getFreeAdjacent(pno, attacking):
						self.ownership[y][x] = pno
			
			# XXX
			player.armies = []
		
			player.balance += cnt[pno]
		
		if self.tick > 0 and self.tick % 10 == 0:
			for pno, player in self.players.items():
				player.payInterest()
		
		
			
		
		defeated = []
		
		for pno, player in self.players.items():
			player.balance = min(150 * cnt[pno], player.balance)
		
			if player.balance <= 0:
				defeated.append(pno)

			if player.balance > 0 and random() < 0.1:
				strength = randint(1, player.balance)
				player.balance -= strength
				player.armies.append(Army(0, strength))
				
			if player.balance > 0 and random() < 0.1:
				conquerable_adjacent = world.getConquerableAdjacent(pno, 1)
				if len(conquerable_adjacent) > 0:
					cx, cy = conquerable_adjacent[0]
					strength = randint(1, player.balance)
					player.balance -= strength
					player.armies.append(Army(self.ownership[cy][cx], strength))
				
					
		self.tick += 1
	
	def getMap(self):
		bg = deepcopy(self.background)
		for y in range(self.h):
			for x in range(self.w):
				owner = self.ownership[y][x]
				if owner != 0:
					bg[y][x] = deepcopy(self.players[owner].color)
		
		return bg

world = World()

attacks = defaultdict(dict)

pygame.init()
pygame.display.set_caption("territorial.io")


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
	sleep(0.04)





	
	
