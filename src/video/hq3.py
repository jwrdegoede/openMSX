# $Id$

from hqcommon import blendWeights, isPow2, makeLite, permuteCase, printSubExpr

from itertools import izip
import sys

class Parser(object):

	def __init__(self):
		self.fileName = 'HQ3xScaler.in'
		self.pixelExpr = [ [ None ] * 8 for _ in range(1 << 12) ]
		self.__parse()
		sanityCheck(self.pixelExpr)

	@staticmethod
	def __filterSwitch(stream):
		log = False
		inIf = False
		for line in stream:
			line = line.strip()
			if line == 'switch (pattern) {':
				log = True
			elif line == '}':
				if inIf:
					inIf = False
				elif log:
					break
			elif line.startswith('//pixel'):
				line = line[2 : ]
			elif line.startswith('if'):
				inIf = True
			if log:
				yield line

	def __parse(self):
		cases = []
		subCases = range(1 << 4)
		for line in self.__filterSwitch(file(self.fileName)):
			if line.startswith('case'):
				cases.append(int(line[5 : line.index(':', 5)]))
			elif line.startswith('pixel'):
				subPixel = int(line[5]) - 1
				assert 0 <= subPixel < 9
				assert subPixel != (5 - 1)
				expr = line[line.index('=') + 1 : ].strip()
				self.__addCases(cases, subCases, subPixel, expr[ : -1])
			elif line.startswith('if'):
				index = line.find('edge')
				assert index != -1
				index1 = line.index('(', index)
				index2 = line.index(',', index1)
				index3 = line.index(')', index2)
				pix1s = line[index1 + 1 : index2].strip()
				pix2s = line[index2 + 1 : index3].strip()
				assert pix1s[0] == 'c', pix1s
				assert pix2s[0] == 'c', pix2s
				pix1 = int(pix1s[1:])
				pix2 = int(pix2s[1:])
				if pix1 == 2 and pix2 == 6:
					subCase = 0
				elif pix1 == 6 and pix2 == 8:
					subCase = 1
				elif pix1 == 8 and pix2 == 4:
					subCase = 2
				elif pix1 == 4 and pix2 == 2:
					subCase = 3
				else:
					assert False, (line, pix1, pix2)
				subCases = [ x for x in range(1 << 4) if x & (1 << subCase) ]
			elif line.startswith('} else'):
				subCases = [ x for x in range(1 << 4) if x not in subCases ]
			elif line.startswith('}'):
				subCases = range(1 << 4)
			elif line.startswith('break'):
				cases = []
				subCases = range(1 << 4)

	def __addCases(self, cases, subCases, subPixel, expr):
		pixelExpr = self.pixelExpr
		if subPixel > (5 - 1):
			subPixel -= 1
		for case in cases:
			for subCase in subCases:
				weights = [ 0 ] * 9
				if expr.startswith('interpolate'):
					factorsStr = expr[
						expr.index('<') + 1 : expr.index('>')
						].split(',')
					pixelsStr = expr[
						expr.index('(') + 1 : expr.index(')')
						].split(',')
					assert len(factorsStr) == len(pixelsStr)
					for factorStr, pixelStr in izip(factorsStr, pixelsStr):
						factor = int(factorStr)
						pixelStr = pixelStr.strip()
						assert pixelStr[0] == 'c'
						pixel = int(pixelStr[1 : ]) - 1
						weights[pixel] = factor
				else:
					assert expr[0] == 'c'
					weights[int(expr[1 : ]) - 1] = 1
				pixelExpr[(case << 4) | subCase][subPixel] = weights

def sanityCheck(pixelExpr):
	'''Check various observed properties.
	'''
	subsets = [ (5, 4, 2, 1), (5, 6, 2, 3), (5, 4, 8, 7), (5, 6, 8, 9) ]

	for case, expr in enumerate(pixelExpr):
		# Weight factor of center pixel is never zero.
		# TODO: This is not the case for 3x, is that expected or a problem?
		#for corner in expr:
			#assert corner[5 - 1] != 0, corner

		# Sum of weight factors is always a power of two.
		for corner in expr:
			total = sum(corner)
			assert total in (1, 2, 4, 8, 16), total
			#
			count = reduce(lambda x, y: x + (y != 0), corner, 0)
			# at most 3 non-zero coef
			assert count <= 3, (case, corner)
			# and if there are 3 one of those must be c5
			assert (count < 3) or (corner[4] != 0)

		# Subpixel depends only on the center and three neighbours in the
		# direction of the subpixel itself.
		# TODO: This is not the case for 3x, is that expected or a problem?
		#for corner, subset in zip(expr, subsets):
			#for pixel in range(9):
				#if (pixel + 1) not in subset:
					#assert corner[pixel] == 0, corner

def printSwitch(pixelExpr, filename):
	permutation = (2, 9, 7, 4, 3, 10, 11, 1, 8, 0, 6, 5)
	file = open(filename, 'w')
	exprToCases = {}
	for case, expr in enumerate(pixelExpr):
		exprToCases.setdefault(
			tuple(tuple(subExpr) for subExpr in expr),
			[]
			).append(permuteCase(permutation, case))
	print >> file, 'switch (pattern) {'
	for cases, expr in sorted(
		( sorted(cases), expr )
		for expr, cases in exprToCases.iteritems()
		):
		for case in cases:
			print >> file, 'case %d:' % case
		for subPixel, subExpr in enumerate(expr):
			num = subPixel + 1
			if num > 4:
				num += 1
			print >> file, ('\tpixel%d = %s;' %
			       (num, printSubExpr(subExpr)))
		print >> file, '\tbreak;'
	print >> file, 'default:'
	print >> file, '\tUNREACHABLE;'
	print >> file, '\tpixel1 = pixel2 = pixel3 = pixel4 ='
	print >> file, '\tpixel6 = pixel7 = pixel8 = pixel9 = 0; // avoid warning'
	print >> file, '}'
	file.close()

tablePermutation = (5, 0, 4, 6, 3, 10, 11, 2, 1, 9, 8, 7)

def printHQLiteScalerTable(pixelExpr):
	pixelExpr2 = [ [ None ] * 16 for _ in range(1 << 12) ]
	for case in range(1 << 12):
		pixelExpr2[permuteCase(tablePermutation, case)] = pixelExpr[case]
	#
	for case in range(1 << 12):
		sys.stdout.write('// %d\n' % case)
		for subPixel in range(9):
			if subPixel == 4:
				sys.stdout.write('   0, 255,   0,')
			else:
				if subPixel > 4:
					subPixel -= 1
				factor = 256 / sum(pixelExpr2[case][subPixel])
				for c in (3, 4, 5):
					sys.stdout.write(' %3d,' % min(255, factor * pixelExpr2[case][subPixel][c]))
			sys.stdout.write('\n')

def printHQLiteScalerTable2Binary(pixelExpr, filename):
	file = open(filename, 'wb')
	pixelExpr2 = [ [ None ] * 16 for _ in range(1 << 12) ]
	for case in range(1 << 12):
		pixelExpr2[permuteCase(tablePermutation, case)] = pixelExpr[case]
	#
	offset_x = ( 43,   0, -43,  43, -43,  43,   0, -43)
	offset_y = ( 43,  43,  43,   0,   0, -43, -43, -43)
	for case in range(1 << 12):
		#sys.stdout.write('// %d\n' % case)
		for subPixel in range(9):
			if subPixel == 4:
				x = 128
				y = 128
			else:
				if subPixel > 4:
					subPixel -= 1
				for c in (0, 1, 2, 6, 7, 8):
					assert pixelExpr2[case][subPixel][c] == 0
				assert (pixelExpr2[case][subPixel][3] == 0) or (pixelExpr2[case][subPixel][5] == 0)
				factor = sum(pixelExpr2[case][subPixel])
				x = offset_x[subPixel] + 128
				y = offset_y[subPixel] + 128
				if pixelExpr2[case][subPixel][5] == 0:
					x -= 128 * pixelExpr2[case][subPixel][3] / factor
				else:
					x += 128 * pixelExpr2[case][subPixel][5] / factor
			#print x, y
			assert 0 <= x
			assert x <= 255
			file.write(chr(x) + chr(y))
	file.close()

def printHQLiteScalerTableBinary(pixelExpr, filename):
	file = open(filename, 'wb')
	pixelExpr2 = [ [ None ] * 16 for _ in range(1 << 12) ]
	for case in range(1 << 12):
		pixelExpr2[permuteCase(tablePermutation, case)] = pixelExpr[case]
	#
	for case in range(1 << 12):
		for subPixel in range(9):
			if subPixel == 4:
				file.write(chr(0) + chr(255) + chr(0))
			else:
				if subPixel > 4:
					subPixel -= 1
				factor = 256 / sum(pixelExpr2[case][subPixel])
				for c in (3, 4, 5):
					file.write(chr(min(255, factor * pixelExpr2[case][subPixel][c])))
	file.close()

def printHQScalerTable(pixelExpr):
	pixelExpr2 = [ [ None ] * 9 for _ in range(1 << 12) ]
	for case in range(1 << 12):
		pcase = permuteCase(tablePermutation, case)
		for subPixel in range(9):
			if subPixel < 4:
				pixelExpr2[pcase][subPixel] = pixelExpr[case][subPixel]
			elif subPixel == 4:
				pixelExpr2[pcase][subPixel] = [0, 0, 0, 0, 1, 0, 0, 0, 0]
			else:
				pixelExpr2[pcase][subPixel] = pixelExpr[case][subPixel - 1]
	#
	xy = [[[-1] * 2 for _ in range(9)] for _ in range(1 << 12)]
	for case in range(1 << 12):
		for subPixel in range(9):
			j = 0
			for i in (0, 1, 2, 3, 5, 6, 7, 8):
				if pixelExpr2[case][subPixel][i] != 0:
					assert j < 2
					xy[case][subPixel][j] = i
					j = j + 1
	for case in range(1 << 12):
		sys.stdout.write('// %d\n' % case)
		for subPixel in range(9):
			for i in range(2):
				t = xy[case][subPixel][i]
				if t == -1:
					t = 4
				x = min(255, (t % 3) * 128)
				y = min(255, (t / 3) * 128)
				sys.stdout.write(' %3d, %3d,' % (x, y))
			sys.stdout.write('\n')
	sys.stdout.write('//-------------\n')
	for case in range(1 << 12):
		sys.stdout.write('// %d\n' % case)
		for subPixel in range(9):
			factor = 256 / sum(pixelExpr2[case][subPixel])
			for c in (xy[case][subPixel][0], xy[case][subPixel][1], 4):
				t = 0
				if c != -1:
					t = pixelExpr2[case][subPixel][c]
				sys.stdout.write(' %3d,' % min(255, factor * t))
			sys.stdout.write('\n')

def printHQScalerTableBinary(pixelExpr, offsetsFilename, weightsFilename):
	pixelExpr2 = [ [ None ] * 9 for _ in range(1 << 12) ]
	for case in range(1 << 12):
		pcase = permuteCase(tablePermutation, case)
		for subPixel in range(9):
			if subPixel < 4:
				pixelExpr2[pcase][subPixel] = pixelExpr[case][subPixel]
			elif subPixel == 4:
				pixelExpr2[pcase][subPixel] = [0, 0, 0, 0, 1, 0, 0, 0, 0]
			else:
				pixelExpr2[pcase][subPixel] = pixelExpr[case][subPixel - 1]

	offsetsFile = open(offsetsFilename, 'wb')
	xy = [[[-1] * 2 for _ in range(9)] for _ in range(1 << 12)]
	for case in range(1 << 12):
		for subPixel in range(9):
			j = 0
			for i in (0, 1, 2, 3, 5, 6, 7, 8):
				if pixelExpr2[case][subPixel][i] != 0:
					assert j < 2
					xy[case][subPixel][j] = i
					j = j + 1
	for case in range(1 << 12):
		for subPixel in range(9):
			for i in range(2):
				t = xy[case][subPixel][i]
				if t == -1:
					t = 4
				x = min(255, (t % 3) * 128)
				y = min(255, (t / 3) * 128)
				offsetsFile.write(chr(x) + chr(y))
	offsetsFile.close()
	weightsFile = open(weightsFilename, 'wb')
	for case in range(1 << 12):
		for subPixel in range(9):
			factor = 256 / sum(pixelExpr2[case][subPixel])
			for c in (xy[case][subPixel][0], xy[case][subPixel][1], 4):
				t = 0
				if c != -1:
					t = pixelExpr2[case][subPixel][c]
				weightsFile.write(chr(min(255, factor * t)))
	weightsFile.close()

def makeNarrow(pixelExpr):
	centerOnly = [0, 0, 0, 0, 1, 0, 0, 0, 0]
	return [
		[	blendWeights(expr[0], expr[1], 2, 1),
			blendWeights(expr[2], expr[1], 2, 1),
			blendWeights(expr[3], centerOnly, 2, 1),
			blendWeights(expr[4], centerOnly, 2, 1),
			blendWeights(expr[5], expr[6], 2, 1),
			blendWeights(expr[7], expr[6], 2, 1),
			]
		for expr in pixelExpr
		]

if __name__ == '__main__':
	#for case in range(1 << 12):
	#	for pixel in range(8):
	#		print case, pixel, pixelExpr[case][pixel]

	#pixelExpr = makeNarrow(pixelExpr)

	pixelExpr = Parser().pixelExpr
	#printHQScalerTable(pixelExpr)
	printHQScalerTableBinary(pixelExpr, 'HQ3xOffsets.dat', 'HQ3xWeights.dat')

	pixelExpr = Parser().pixelExpr
	makeLite(pixelExpr)
	#printHQLiteScalerTable(pixelExpr)
	#printHQLiteScalerTableBinary(pixelExpr, 'HQ3xLiteWeights.dat')

	pixelExpr = Parser().pixelExpr
	makeLite(pixelExpr, (2, 4, 7))
	printHQLiteScalerTable2Binary(pixelExpr, 'HQ3xLiteOffset.dat')

	pixelExpr = Parser().pixelExpr
	printSwitch(pixelExpr, 'HQ3xScaler-1x1to3x3.nn')
	makeLite(pixelExpr)
	printSwitch(pixelExpr, 'HQ3xLiteScaler-1x1to3x3.nn')