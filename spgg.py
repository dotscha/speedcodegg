import sys

param = ord('.')
separator = ord(' ')

pseudoByte = 'byt'

dataFile = sys.argv[1]
patternsFile = sys.argv[2]

data = list(bytearray(open(dataFile,'rb').read()))
dataAddr = data[0]+256*data[1]
data = data[2:]

# read and parse patterns
patterns = list(bytearray(open(patternsFile,'rb').read()))[2:]
patterns.append(separator)

pattern = []
for i in range(patterns.count(separator)):
	sep = patterns.index(separator)
	patt = patterns[:sep]
	if len(patt):
		pattern.append(patt)
	patterns = patterns[sep+1:]

print (data)
print (pattern)

# check if matching
def matching(data, pos, patt):
	posEnd = min(len(data),pos+len(patt))
	for i in range(posEnd-pos):
		if patt[i]!=param and data[pos+i]!=patt[i]:
			return False
	return True

#match parameters
def matchParams(data, pos, patt):
	posEnd = min(len(data),pos+len(patt))
	mp = []
	for i in range(len(patt)):
		if patt[i]==param:
			mp.append(data[pos+i] if i<posEnd-pos else param)
	return mp

# greedy search for optimal matches
pos = 0
matches = []
while pos<len(data):
	best = None
	bestCost = 100.0	#some big number
	for patt in pattern:
		if matching(data,pos,patt):
			params = matchParams(data,pos,patt)
			cost = (1.0+len(params))/(min(len(data),pos+len(patt))-pos)	#compr ratio
			if cost<bestCost:
				best = (patt, params)
				bestCost = cost
	if best!=None:
		matches.append(best)
		pos += len(best[0])
		print (best)
	else:
		print ("ERROR: No pattern found at {a}".format(a=hex(dataAddr+pos)),file=sys.stderr)
		exit(1)

if len(data)<pos:
	print ("WARNING: Partial match at the end overrun by {i} bytes.".format(i=pos-len(data)))


usedPatterns = []
for m in matches:
	if not m[0] in usedPatterns:
		usedPatterns.append(m[0])

if len(usedPatterns)>255:
	print ("ERROR: Too many patterns: {i}".format(i=len(usedPatterns)),file=sys.stderr)
	exit(1)

# printing the speedcode generator
def patternWriter(patt):
	for i in range(len(patt)):
		c = patt[i]
		if c!=param:
			print ("\tlda #{v}".format(v=c))
		else:
			print ("\tjsr get_param")
		print ("\tsta (dest),y")
		if i+1<len(patt):
			print ("\tiny")
	print ("\tjmp cont_next")

print ("speedcode_generator:")
print ("\tldx #0")
print ("writer_loop:")
print ("\tjsr get_param")
print ("\ttay")
print ("\tlda patt_write_lo,y")
print ("\tsta jump_to")
print ("\tlda patt_write_hi,y")
print ("\tsta jump_to+1")
print ("\tldy #0")
print ("jump_to = *+1")
print ("\tjmp $ffff")
print ("cont_next:")
print ("\tsec")
print ("\ttya")
print ("\tadc dest")
print ("\tsta dest")
print ("\tbcc writer_loop")
print ("\tinc dest+1")
print ("\tjmp writer_loop")

print ("")
print ("get_param:")
print ("\tlda speedcode_data,x")
print ("\tinx")
print ("\tbne patt_writer_0")
print ("\tinc get_param+2")

print ("")
print ("patt_writer_0:")
print ("\trts")


pattIdx = list(zip(usedPatterns,range(1,1+len(usedPatterns))))

for patt,idx in pattIdx:
	print ("patt_writer_{i}".format(i=idx))
	patternWriter(patt)

print ("")
print ("patt_writer_lo:")
for patt,idx in pattIdx:
	print ("\t{o} <patt_writer_{i}".format(o=pseudoByte,i=idx))
print ("patt_writer_hi:")
for patt,idx in pattIdx:
	print ("\t{o} >patt_writer_{i}".format(o=pseudoByte,i=idx))
