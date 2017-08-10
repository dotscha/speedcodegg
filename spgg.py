import sys

#param = ord('.')		# will be $ff
#separator = ord(' ')	# will be $ea

param = 0xff
separator = 0xea

pseudoByte = '!byte'

dataFile = sys.argv[1]
patternsFile = sys.argv[2]
streamsFile = None if len(sys.argv)<4 else sys.argv[3]

outPrefix = "output"

data = list(bytearray(open(dataFile,'rb').read()))
dataAddr = data[0]+256*data[1]
data = data[2:]

# read and parse patterns and streams
patterns = list(bytearray(open(patternsFile,'rb').read()))[2:]
patterns.append(separator)

streams = None
if streamsFile!=None:
	streams = list(bytearray(open(streamsFile,'rb').read()))[2:]
	streams.append(separator)
	if len(patterns)!=len(streams) or not all([(p==param or p==s) for (p,s) in zip(patterns,streams)]):
		print ("Patterns and streams are not aligned.",file=sys.stderr)
		exit(1)
else:
	streams = [(c if c!=param else 0) for c in patterns]
	
pattern = {}
for i in range(patterns.count(separator)):
	sep = patterns.index(separator)
	patt = patterns[:sep]
	stre = streams[:sep]
	if len(patt):
		pattern[tuple(patt)] = stre
	patterns = patterns[sep+1:]
	streams = streams[sep+1:]

#print ("data")
#print (data)
#print ("pattern")
#print (pattern)

# check if matching
def matching(data, pos, patt):
	posEnd = min(len(data),pos+len(patt))
	for i in range(posEnd-pos):
		if patt[i]!=param and data[pos+i]!=patt[i]:
			return False
	return True

# match parameters
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
		#print ("match: {m}".format(m=best))
	else:
		print ("ERROR: No pattern found at {a}".format(a=hex(dataAddr+pos)),file=sys.stderr)
		exit(1)

if len(data)<pos:
	print ("WARNING: Partial match at the end overrun by {i} bytes.".format(i=pos-len(data)))

usedPatterns = {tuple(m[0]) for m in matches}

if len(usedPatterns)>255:
	print ("ERROR: Too many patterns: {i}".format(i=len(usedPatterns)),file=sys.stderr)
	exit(1)

# printing the speedcode generator
def patternWriter(patt,stre):
	for i in range(len(patt)):
		c = patt[i]
		if c!=param:
			print ("\tlda #{v}".format(v=c),file=outGen)
		else:
			print ("\tjsr get_param{s}".format(s="" if stre[i]==0 else "_{i}".format(i=stre[i])),file=outGen)
		print ("\tsta (dest),y",file=outGen)
		if i+1<len(patt):
			print ("\tiny",file=outGen)
	print ("\tjmp cont_next",file=outGen)

outGen = open(outPrefix+"_spgen.asm",'w')

print ("speedcode_generator:",file=outGen)
print ("\tldx #0",file=outGen)
print ("writer_loop:",file=outGen)
print ("\tjsr get_param",file=outGen)
print ("\ttay",file=outGen)
print ("\tlda patt_write_lo,y",file=outGen)
print ("\tsta jump_to",file=outGen)
print ("\tlda patt_write_hi,y",file=outGen)
print ("\tsta jump_to+1",file=outGen)
print ("\tldy #0",file=outGen)
print ("jump_to = *+1",file=outGen)
print ("\tjmp $ffff",file=outGen)
print ("cont_next:",file=outGen)
print ("\tsec",file=outGen)
print ("\ttya",file=outGen)
print ("\tadc dest",file=outGen)
print ("\tsta dest",file=outGen)
print ("\tbcc writer_loop",file=outGen)
print ("\tinc dest+1",file=outGen)
print ("\tjmp writer_loop",file=outGen)

print ("",file=outGen)
print ("get_param:",file=outGen)
print ("\tlda speedcode_data,x",file=outGen)
print ("\tinx",file=outGen)
print ("\tbne patt_writer_0",file=outGen)
print ("\tinc get_param+2",file=outGen)

print ("",file=outGen)
print ("patt_writer_0:",file=outGen)
print ("\trts",file=outGen)


pattIdx = list(zip(usedPatterns,range(1,1+len(usedPatterns))))

for patt,idx in pattIdx:
	print ("patt_writer_{i}".format(i=idx),file=outGen)
	patternWriter(patt, pattern[patt])

print ("",file=outGen)
print ("patt_writer_lo:",file=outGen)
for patt,idx in pattIdx:
	print ("\t{o} <patt_writer_{i}".format(o=pseudoByte,i=idx),file=outGen)
print ("patt_writer_hi:",file=outGen)
for patt,idx in pattIdx:
	print ("\t{o} >patt_writer_{i}".format(o=pseudoByte,i=idx),file=outGen)

outGen.close()

# saving data into streams

def extractStreams(patt,stre):
	return [s for p,s in zip(patt,stre) if p==param]
	
def splitDataIntoStreams(data, stre, m):
	for d,s in zip(data,stre):
		if s in m:
			m[s].append(d)
		else:
			m[s] = [d]
	return m

def writeStream(s,data,comment=None):
	if not s in outData:
		outData[s] = open(outPrefix+"_spdata_{s}.asm".format(s=s),'w')
		print ("speedcode_data_{s}:".format(s=s),file=outData[s])
	print (
		"\t{o} {l}{c}".format(
			o = pseudoByte,
			l = ",".join([hex(d).replace("0x","$") for d in data]),
			c = "" if comment==None else "\t;"+comment
		),
		file = outData[s]
	)
	
outData = { 0 : open(outPrefix+"_spdata.asm",'w')}
print ("speedcode_data:",file=outData[0])

pattIdx = { patt:(i,extractStreams(patt,pattern[patt])) for patt,i in pattIdx }

#print ("pattIdx")
#print (pattIdx)

for patt,params in matches:
	ds = splitDataIntoStreams(params,pattIdx[patt][1],{0:[pattIdx[patt][0]]})
	for s,data in ds.items():
		writeStream(s,data)
		
writeStream(0,[0],"the end")

for s,f in outData.items():
	if s!=0:
		print ("",file=f)
		print ("get_param_{s}:".format(s=s),file=f)
		print ("\tlda speedcode_data_{s}".format(s=s),file=f)
		print ("\tinc get_param_{s}+1".format(s=s),file=f)
		print ("\tbne *+5",file=f)
		print ("\tinc get_param_{s}+2".format(s=s),file=f)
		print ("\trts",file=f)
	f.close()
