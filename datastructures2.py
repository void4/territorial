from collections import Counter, defaultdict

import numpy as np

class Node:

	def __init__(self, w, h):
		self.w = w
		self.h = h
		# v -> check -> coordinate
		self.v2k2c = defaultdict(lambda : defaultdict(dict))
		self.map = [[0 for x in range(w)] for y in range(h)]

	def get(self, x, y):
		return self.map[y][x]

	def set(self, x, y, v):
		old = self.map[y][x]
		# Have to do this first so neighbor checks later work
		if old != v:
			if (x,y) in self.v2k2c[old][True]:
				del self.v2k2c[old][True][(x,y)]
			if (x,y) in self.v2k2c[old][False]:
				del self.v2k2c[old][False][(x,y)]
		self.map[y][x] = v
		# Also have to check neighbors because their perspective might change

		for ndelta in [(0,0), (-1,0), (1,0), (0,-1), (0,1)]:
			check = False
			goodcoord = False
			nx = x + ndelta[0]
			ny = y + ndelta[1]

			if nx < 0 or ny < 0 or nx >= self.w or ny >= self.h:
				continue

			nv = self.map[ny][nx]

			# Have to check all again because otherwise can't set check back to true for neighbors
			for delta in [(-1,0), (1,0), (0,-1), (0,1)]:

				cx = nx + delta[0]
				cy = ny + delta[1]

				if cx < 0 or cy < 0 or cx >= self.w or cy >= self.h:
					continue

				if self.map[cy][cx] not in [0, nv]:
					check = True
					break

			if (not check) in self.v2k2c[nv]:
				if (nx,ny) in self.v2k2c[nv][not check]:
					del self.v2k2c[nv][not check][(nx,ny)]
			self.v2k2c[nv][check][(nx,ny)] = True

	@property
	def counter(self):
		return self.getFullCount()

	def getBorderTo3(self, a, b, count):
		ca = sorted(self.v2k2c[a][True].keys())
		cb = sorted(self.v2k2c[b][True].keys())

		print(ca)

	def getBorderTo2(self, a, b, count):
		result = []
		#print(len(self.v2k2c[a][True]))
		for (x, y) in self.v2k2c[a][True].keys():
			for delta in [(-1,0), (1,0), (0,-1), (0,1)]:
				nx = x + delta[0]
				ny = y + delta[1]

				#if nx < 0 or ny < 0 or nx >= self.w or ny >= self.h:
				#	continue

				if (nx, ny) in self.v2k2c[b][True]:
					result.append((nx, ny))
					if count is not None and len(result) == count:
						break
			else:
				continue
			break
		return set(result)

	def getBorderTo(self, a, condition, count):
		result = []
		#print(len(self.v2k2c[a][True]))
		for (x, y) in self.v2k2c[a][True].keys():
			for delta in [(-1,0), (1,0), (0,-1), (0,1)]:
				nx = x + delta[0]
				ny = y + delta[1]

				if nx < 0 or ny < 0 or nx >= self.w or ny >= self.h:
					continue

				# TODO just check if in b True list?
				if condition(self.map[ny][nx]):
					result.append((nx, ny))
					if count is not None and len(result) == count:
						break
			else:
				continue
			break
		return set(result)

	def getAllRoot(self):
		return self.map

	def getAllRootChecks(self):

		cmap = np.array(self.map, copy=True)

		nocheck = 0
		for v, dct in self.v2k2c.items():
			for coord in dct[True]:
				cmap[coord[1]][coord[0]] = 2
			for coord in dct[False]:
				if v in [0,1]:
					cmap[coord[1]][coord[0]] = v
				else:
					nocheck += 1
					cmap[coord[1]][coord[0]] = 3
		return cmap

	def getFullCount(self):
		return {key:len(value[False])+len(value[True]) for key, value in self.v2k2c.items()}

	def getHighestCountCoords(self, v):
		docheck = self.v2k2c[v][True]
		nocheck = self.v2k2c[v][False]

		if len(nocheck) > 0:
			return next(iter(nocheck)), len(nocheck) + len(docheck)
		if len(docheck) > 0:
			return next(iter(docheck)), len(docheck)
		else:
			return (None, None), None
