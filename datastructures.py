from collections import Counter
import numpy as np

class Node:
	def __init__(self, qw, qh, level, parent=None, path=None, root=None):
		self.qw = qw
		self.qh = qh
		if path is None:
			self.path = []
		else:
			self.path = path
		self.parent = parent
		self.offset = 0
		self.level = level
		
		if self.parent is None:
			self.quadmap = [[None for x in range(2**level)] for y in range(2**level)]
		
		if root is None:
			self.root = self
		else:
			self.root = root
		self.counter = Counter({0:4**level*self.qw*self.qh})
		if level == 0:
			self.map = [[0 for x in range(self.qw)] for y in range(self.qh)]
			self.sx = 0
			self.sy = 0
			
			for i, v in enumerate(self.path):
				xx = v%2
				yy = v//2
				self.sx += 2**(len(self.path)-i)*self.qw//2*xx
				self.sy += 2**(len(self.path)-i)*self.qw//2*yy
			
			self.qx = self.sx//self.qw
			self.qy = self.sy//self.qh
			self.root.quadmap[self.qy][self.qx] = self#old self?
			#print(self.path, self.sx, self.sy)
		else:
			self.children = []
			for i in range(4):
				self.children.append(Node(qw, qh, level-1, self, self.path+[i], self.root))
		
		
		
	
	def getAll(self):
		if self.level > 0:
			a = np.concatenate([self.children[0].getAll(), self.children[1].getAll()], axis=1)
			b = np.concatenate([self.children[2].getAll(), self.children[3].getAll()], axis=1)
			return np.concatenate([a, b], axis=0)
		else:
			return self.map
	
	def getAllRoot(self):
		w = 2**self.level*self.qw
		h = 2**self.level*self.qh
		
		qww = qhh = 2**self.level
		
		total = np.zeros((h,w), dtype=np.int8)#XXX if more than 256 players, have to use int16!
		
		for y in range(qhh):
			for x in range(qww):
				quad = self.quadmap[y][x]
				total[quad.sy:quad.sy+self.qh, quad.sx:quad.sx+self.qw] = quad.map
		
		return total
	
	def index(self, x, y):
		scale = 2**self.level
		xres = scale*self.qw // 2
		yres = scale*self.qh // 2
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
	
	def getRelativeQuad(self, dxy):
		try:
			return self.root.quadmap[self.qy+dxy[1]][self.qx+dxy[0]]
		except IndexError:
			return None
	
	def allCoordDeltas(self, target):
		for y in range(self.qh):
			for x in range(self.qw):
				if self.map[y][x] == target:
					for delta in [(0,1), (0,-1), (1,0), (-1,0)]:
						yield x, y, delta
	
	def borderDeltas(self, target, morethan=None):
		#for caching efficiency
		
		UP, DOWN, LEFT, RIGHT = [(0, -1), (0, 1), (-1, 0), (1, 0)]
		
		sibling = self.getRelativeQuad(UP)
		if sibling is not None and sibling.containsMoreThan(morethan):
			for x in range(self.qw):
				if self.map[0][x] == target:
					yield x, 0, UP

		sibling = self.getRelativeQuad(DOWN)
		if sibling is not None and sibling.containsMoreThan(morethan):	
			for x in range(self.qw):
				if self.map[self.qh-1][x] == target:
					yield x, self.qh-1, DOWN
		
		sibling = self.getRelativeQuad(LEFT)
		if sibling is not None and sibling.containsMoreThan(morethan):
			for y in range(self.qh):
				if self.map[y][0] == target:
					yield 0, y, LEFT
					
		sibling = self.getRelativeQuad(RIGHT)
		if sibling is not None and sibling.containsMoreThan(morethan):
			for y in range(self.qh):
				if self.map[y][self.qw-1] == target:
					yield self.qw-1, y, RIGHT
	
	def containsMoreThan(self, morethan):
		return morethan is None or len(set(self.counter.keys()).difference([morethan, 0])) > 0
	
	def getBorderTo(self, a, condition, count=None, border=None, mustcontain=None, morethan=None):
		if border is None:
			border = {}
		# could improve efficiency with intermediate stages
		if self.level == 0:
			if a not in self.counter:
				return border
			
			# TODO if only a and 0 in count, only check siblings, outer border
			
			if (mustcontain is None or mustcontain in self.counter) and self.containsMoreThan(morethan):
				codeltagen = self.allCoordDeltas(a) 
			else:
				codeltagen = self.borderDeltas(a, morethan)
			
			for x, y, delta in codeltagen:
			
				if count is not None and len(border) >= count:
					return border
			
				nx = x + delta[0]
				ny = y + delta[1]
				
				# TODO
				within = False
				if nx < 0:
					#	# check sibling, difficult in quadtree, may have to go several parents up, then down again
					#	self.parent.children[
					nx = self.qw-1
					ny = y
				elif ny < 0:
					nx = x
					ny = self.qh-1
				elif nx >= self.qw:
					nx = 0
					ny = y
				elif ny >= self.qh:
					nx = x
					ny = 0
				else:
					within = True
					# within this quad
					if condition(self.map[ny][nx]):
						border[(self.sx+nx, self.sy+ny)] = True
				
				quadcache = {}
				if not within:
					# TODO: cache this!
					if delta not in quadcache:
						sibling = self.getRelativeQuad(delta)
						quadcache[delta] = sibling
					else:
						sibling = quadcache[delta]
					if sibling is not None:
						if condition(sibling.map[ny][nx]):
							border[(sibling.sx+nx, sibling.sy+ny)] = True
			return border
		else:
			if a in self.counter:
				for child in self.children:
					border = child.getBorderTo(a, condition, count, border, mustcontain)
				return border
			else:
				return border

	def getFullCount(self):
		return self.counter

	def getFullBaseCount(self):
		if self.level == 0:
			return self.counter
		else:
			return sum([child.getFullCount() for child in self.children], Counter())

	def getHighestCountCoords(self, v):
		if self.level > 1:
			cnt = Counter()
			for child in self.children:
				if v in child.counter:
					cnt.update(child.getHighestCountCoords(v))
			return cnt
		else:
			return {(child.sx+self.qw//2, child.sy+self.qh//2): child.counter[v] for child in self.children}

if __name__ == "__main__":
	QW = QH = 32
	root = Node(QW, QH, 4)
	print(root.get(0,0))
	root.set(0,0,1)
	print(root.get(0,0))
	print(root.getFullCount())
	print(root.getBorderTo(1,lambda v: v==0))
