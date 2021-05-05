'''
DARK FORCES ANALYZER
* * *
Get a .lev file to analyze, optionally with its full path. Then find the corresponding .o and
.inf files if available, and provide some interesting statistics. If no .lev file given in the
command line, use 'secbase.lev' in the current dir as default.
Python 3.7 assumed - but should work with some version tolerance in either direction.
'''

import sys
import glob
import os

print('Dark Forces Analyzer\n--------------------')

# Determine the file to search for
if len(sys.argv) == 1:
    print('No .lev file provided in the command line; using secbase.lev as default')
    flev = 'secbase.lev'
else:
    flev = ' '.join(sys.argv[1:])

# Does it actually exist?
if not os.path.isfile(flev):
    print('ERROR: File missing, inaccessible or invalid.')
    sys.exit(1)

# Open and load to arrays
flevh = open(flev, 'r', encoding='ascii')
flevc = [e.strip(' \n') for e in flevh.readlines() if e.strip(' \n')]
flevh.close()
print('Opened {0} ({1} lines)'.format(flev, len(flevc)))

# Prepare collectors
ltextures = []
lsectors = []
lwalls = []

# Parse step-by-step
for line in flevc:
    # Texture definition
    if line.upper().startswith('TEXTURE:'):
        ltextures.append(line[8:].rpartition('#')[0].strip(' '))

    # Sector definition start
    if line.upper().startswith('SECTOR '):
        lsectors.append([None] * 13)
        lsectors[-1][9] = 0
        lsectors[-1][12] = 0
        # Name, ambient light, floor alt, ceiling alt, second alt,
        # Flags1, flags2, flags3, layer, vertex counter,
        # Floor texture, ceiling texture, wall counter

    # Sector name
    if line.upper().startswith('NAME '):
        lsectors[-1][0] = line[4:].strip(' ')

    # Ambient light
    if line.upper().startswith('AMBIENT '):
        lsectors[-1][1] = int(line[7:].strip(' '))

    # Floor texture
    if line.upper().startswith('FLOOR TEXTURE'):
        lsectors[-1][10] = int(line[13:].strip(' ').partition(' ')[0])

    # Floor alt
    if line.upper().startswith('FLOOR ALTITUDE'):
        lsectors[-1][2] = -float(line[14:].strip(' '))

    # Ceiling texture
    if line.upper().startswith('CEILING TEXTURE'):
        lsectors[-1][11] = int(line[15:].strip(' ').partition(' ')[0])

    # Ceiling alt
    if line.upper().startswith('CEILING ALTITUDE'):
        lsectors[-1][3] = -float(line[16:].strip(' '))

    # Second altitude
    if line.upper().startswith('SECOND ALTITUDE'):
        lsectors[-1][4] = -float(line[15:].strip(' '))

    # Flags
    if line.upper().startswith('FLAGS'):
        isolated = line[5:].strip().split(' ')
        lsectors[-1][5] = int(isolated[0])
        lsectors[-1][6] = int(isolated[1])
        lsectors[-1][7] = int(isolated[2])

    # Layer
    if line.upper().startswith('LAYER'):
        lsectors[-1][8] = int(line[5:].strip(' '))

    # Vertex
    if line.upper().startswith('X:'):
        lsectors[-1][9] += 1

    # Wall
    if line.upper().startswith('WALL '):
        lsectors[-1][12] += 1  # Increment sector counter
        # Now parse the wall as such
        walldata = [None, None, None, None]  # Local temporary collector
        while '  ' in line: line = line.replace('  ', ' ')
        ws = line.split(' ')
        ws = [e.upper() for e in ws]
        # Texture parsing
        # Mid
        if 'MID:' in ws:
            walldata[0] = int(ws[ws.index('MID:') + 1])
        # Top
        if 'TOP:' in ws:
            walldata[1] = int(ws[ws.index('TOP:') + 1])
        # Bot
        if 'BOT:' in ws:
            walldata[2] = int(ws[ws.index('BOT:') + 1])
        # Sign
        if 'SIGN:' in ws:
            walldata[3] = int(ws[ws.index('SIGN:') + 1])
        lwalls.append(walldata)  # Finally add all to master collector

print('LEV: {0} sectors, {1} textures, {2} walls loaded'.format(
    len(lsectors), len(ltextures), len(lwalls)))

# Look for INF and O files
fbase = flev.rpartition('.')[0]
fo = fbase + '.o'
finf = fbase + '.inf'

# Open INF and load
finfh = open(finf, 'r', encoding='ascii')
finfc = [e.strip(' \n') for e in finfh.readlines() if e.strip(' \n')]
finfh.close()

# Prepare counters
lclasses = 0
lelevators = 0
lstops = 0
ltriggers = 0

# Parse
for line in finfc:
    line = line.lower()
    if 'class:' in line:
        lclasses += 1
        if 'trigger ' in line:
            ltriggers += 1
        elif 'elevator ' in line:
            lelevators += 1
    if 'stop:' in line:
        lstops += 1

print('INF: {0} entries'.format(lclasses))

# Open O and load
foh = open(fo, 'r', encoding='ascii')
foc = [e.strip(' \n') for e in foh.readlines() if e.strip(' \n')]
foh.close()

# Prepare counters
lobjects = 0
lframes = 0
lsprites = 0
lsecob = dict()

# Parse
for line in foc:
    line = line.upper()
    if line.startswith('CLASS:'):
        lobjects += 1
        lclass = line[6:].strip(' ').partition(' ')[0].strip(' ')
        if lclass == 'FRAME': lframes += 1
        elif lclass == 'SPRITE': lsprites += 1
        # Get sector
        if 'SEC:' in line:
            sector = line[line.index('SEC:') + 4:].strip(' ').partition(' ')[0]
            sector = int(sector)
            if sector in lsecob:
                lsecob[sector] += 1
            else:
                lsecob[sector] = 1

print('O: {0} objects'.format(lobjects))

# Collected all data. Now show some stats
print('\nSTATISTICS\n==========\n')
stats = []  # Collector of strings

# Sector-based
stats.append('Number of sectors: {0}'.format(len(lsectors)))
stats.append('Total number of walls: {0}'.format(len(lwalls)))
stats.append('Total number of textures: {0}'.format(len(ltextures)))

# Most complex sector and stats
maxw = max([e[12] for e in lsectors])
stats.append('Max. number of walls in a sector: {0}'.format(maxw))
avgw = sum([e[12] for e in lsectors]) / len(lsectors)
stats.append('Avg. number of walls per sector: {0:.6}'.format(avgw))

# Lighting and altitudes
lts = [e[1] for e in lsectors]
stats.append('Avg. lighting across level: {0:.6}'.format(sum(lts) / len(lts)))
floors = [e[2] for e in lsectors]
ceils = [e[3] for e in lsectors]
wheights = [e[3] - e[2] for e in lsectors]
stats.append('Highest ceiling: {0}'.format(max(ceils)))
stats.append('Lowest floor: {0}'.format(min(floors)))
stats.append('Avg. floor alt: {0:.6}'.format(sum(floors) / len(floors)))
stats.append('Avg. ceiling alt: {0:.6}'.format(sum(ceils) / len(ceils)))
stats.append('Tallest room height: {0}'.format(max(wheights)))
stats.append('Shortest room height: {0}'.format(min(wheights)))
stats.append('Avg. room height: {0}'.format(sum(wheights) / len(wheights)))

# Textures
fltex = [e[10] for e in lsectors]
flcnt = [(fltex.count(k), k) for k in set(fltex)]
flcnt.sort(reverse=True)
stats.append('Most common floor texture: {0} (in {1} sectors)'.
             format(ltextures[flcnt[0][1]], flcnt[0][0]))
cltex = [e[11] for e in lsectors]
clcnt = [(cltex.count(k), k) for k in set(cltex)]
clcnt.sort(reverse=True)
stats.append('Most common ceiling texture: {0} (in {1} sectors)'.
             format(ltextures[clcnt[0][1]], clcnt[0][0]))

# Walls
wws = [e for e in lwalls if e[3] != -1]
stats.append('Share of walls having a sign: {0:.8}'.format(len(wws) / len(lwalls)))

# INF
stats.append('Number of INF entries: {0}'.format(lclasses))
stats.append('Number of INF elevators: {0}'.format(lelevators))
stats.append('Number of INF elevator stops: {0}'.format(lstops))
stats.append('Avg. stops per elevator: {0:.6}'.format(lstops / lelevators))
stats.append('Number of INF triggers: {0}'.format(ltriggers))
stats.append('INF entries per sector: {0:.6}'.format(lclasses / len(lsectors)))

# Objects
stats.append('Number of objects: {0}'.format(lobjects))
stats.append('Number of sprites: {0}'.format(lsprites))
stats.append('Number of frames: {0}'.format(lframes))
stats.append('Avg. objects per sector: {0:.6}'.format(lobjects / len(lsectors)))
objroom = [(lsecob[e], e) for e in lsecob.keys()]
objroom.sort(reverse=True)
if objroom: stats.append('Most objects in a single sector: {0}'.format(objroom[0][0]))

# Show it all
print('\n'.join(stats))

# Save to file
print('\nExporting to file dfa.txt...')
outf = open('dfa.txt', 'w', encoding='ascii')
outf.write('\n'.join(stats))
outf.close()
