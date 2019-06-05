#!/usr/bin/python3
# G-Code streamer for Prusa i3 3D printers over serial port by haarp
# License: GNU General Public License v3 or newer

import sys
import serial
import time

green = "\033[32m"
yellow = "\033[33m"
reset = "\033[39m"

if( len(sys.argv) < 3 ):
	print( "Usage: " + sys.argv[0] + " <serial port> <G-Code file> [start line]" )
	sys.exit()

print( "Using file " + sys.argv[2] )
file = open( sys.argv[2], 'r' )
if( len(sys.argv) >= 4 ):
	startline = int(sys.argv[3])
else:
	startline = 1
print( "Starting at line " + str(startline) )


print( "Waking printer..." )
port = serial.Serial( sys.argv[1], 115200 )
start_time = time.time()
# wait until printer ready
while True:
	out = port.readline().decode("utf-8").strip()	# blocking
	print( yellow + "< " + out + reset )
	if out.startswith("echo:SD "):			# printer ready
		break

# start sending
i = 0
for line in file:
	try:
		i = i+1
		if i < startline:
			continue

		line = line.strip()		# strip EOL
		line = line.split(';')[0]	# strip comments
		if not line.strip():		# skip empty lines
			continue

		port.write( bytes(line + '\n', "utf-8") )
		print( "\033[K" + green + "> [" + str(i) + "] " + line + reset + "\r", end='', flush=True )	# stay in line
		needs_newline="\n"

		while True:
			out = port.readline().decode("utf-8").strip()	# blocking

			if out.startswith("ok"):
				break
			else:
				print( needs_newline + yellow + "< " + out + reset )
				needs_newline=""

	except KeyboardInterrupt:
		print("Aborting...")
		port.write( bytes("M104 S0\nM140 S0\nM107\nM84\n", "utf-8") )	# turn off heat, fan, motors
##		port.write( bytes("G91\nG1 Z45\nG90\n", "utf-8") )		# move print head up
		sys.exit()

file.close()
port.close()

hours, rest = divmod( time.time()-start_time, 3600 )
minutes, seconds = divmod( rest, 60 )
print( "--- done after {:0>2}h {:0>2}m ---".format( int(hours),int(minutes) ) )
