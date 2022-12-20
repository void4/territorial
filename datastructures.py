from collections import Counter

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
			#print(self.path, self.sx, self.sy)
		else:
			self.children = []
			for i in range(4):
				self.children.append(Node(qw, qh, level-1, self, self.path+[i], self.root))
	
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
	
	def getQuad(self, path):
		if path is None:
			return None
		elif len(path) == 0:
			return self
		else:
			return self.children[path[0]].getQuad(path[1:])
	
	def pathmath(self, path, delta):
		#print(path, delta)
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
		for y in range(self.qh):
			for x in range(self.qw):
				if self.map[y][x] == target:
					for delta in [(0,1), (0,-1), (1,0), (-1,0)]:
						yield x, y, delta
	
	def borderDeltas(self, target):
		#for caching efficiency
		for x in range(self.qw):
			if self.map[0][x] == target:
				yield x, 0, (0, -1)
		for x in range(self.qw):
			if self.map[self.qh-1][x] == target:
				yield x, self.qh-1, (0, 1)
		for y in range(self.qh):
			if self.map[y][0] == target:
				yield 0, y, (-1, 0)
		for y in range(self.qh):
			if self.map[y][self.qw-1] == target:
				yield self.qw-1, y, (1, 0)
	
	def getBorderTo(self, a, condition, count=None, border=None, mustcontain=None):
		if border is None:
			border = set()
		# could improve efficiency with intermediate stages
		if self.level == 0:
			if a not in self.counter:
				return border
			
			# TODO if only a and 0 in count, only check siblings, outer border
			
			codeltagen = self.allCoordDeltas(a) if mustcontain is None or mustcontain in self.counter else self.borderDeltas(a)
			
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
						border.add((self.sx+nx, self.sy+ny))
				
				if not within:
					# TODO: cache this!
					sibling = self.root.getRelativeQuad(self.path, delta)
					if sibling is not None:
						if condition(sibling.map[ny][nx]):
							border.add((sibling.sx+nx, sibling.sy+ny))
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

if __name__ == "__main__":
	QW = QH = 32
	root = Node(QW, QH, 4)
	print(root.get(0,0))
	root.set(0,0,1)
	print(root.get(0,0))
	print(root.getFullCount())
	print(root.getBorderTo(1,lambda v: v==0))
