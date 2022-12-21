from collections import Counter, defaultdict

class bidict(dict):
	def __init__(self, *args, **kwargs):
		super(bidict, self).__init__(*args, **kwargs)
		self.inverse = {}
		for key, value in self.items():
			self.inverse.setdefault(value, {})
			self.inverse[value][key] = True

	def __setitem__(self, key, value):
		if key in self:
			del self.inverse[self[key]][key]
		super(bidict, self).__setitem__(key, value)
		self.inverse.setdefault(value, {})
		self.inverse[value][key] = True


class Node:

	def __init__(self, w, h):
		self.w = w
		self.h = h
		self.groups = bidict()
		self.map = [[0 for x in range(w)] for y in range(h)]

	def get(self, x, y):
		return self.map[y][x]

	def set(self, x, y, v):
		old = self.map[y][x]
		self.groups[(x,y)] = v

		check = False
		for delta in [(-1,0), (1,0), (0,-1), (0,1)]:
			nx = x + delta[0]
			ny = y + delta[1]

			if nx < 0 or ny < 0 or nx >= self.w or ny >= self.h:
				continue

			if self.map[ny][nx] not in [0, v]:
				check = True
				break


		self.groups.inverse[v][(x,y)] = check
		self.map[y][x] = v

	@property
	def counter(self):
		return self.getFullCount()

	def getBorderTo(self, a, condition, count):
		result = []
		for (x, y), check in self.groups.inverse[a].items():
			if not check:
				continue
			for delta in [(-1,0), (1,0), (0,-1), (0,1)]:
				nx = x + delta[0]
				ny = y + delta[1]

				if nx < 0 or ny < 0 or nx >= self.w or ny >= self.h:
					continue

				if condition(self.groups[(nx, ny)]):
					result.append((nx, ny))
					if count is not None and len(result) == count:
						break
			else:
				continue
			break
		return set(result)

	def getAllRoot(self):
		return self.map

	def getFullCount(self):
		return {key:len(value) for key, value in self.groups.inverse.items()}

	def getHighestCountCoords(self, v):
		inv = list(self.groups.inverse[v].keys())
		if inv:
			return inv[0], len(inv)
		else:
			return (None, None), None
