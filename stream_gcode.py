#!/usr/bin/python3
# G-Code streamer for Prusa i3 3D printers over serial port by haarp
# License: GNU General Public License v3 or newer

import sys
import serial
import time

color_send = "\033[32m"
color_recv = "\033[33m"
color_reset = "\033[39m"

start_time = time.time()

if( len(sys.argv) < 3 ):
	print( "Usage: " + sys.argv[0] + " <serial port> <G-Code file> [start line]" )
	sys.exit()

print( "Using file " + sys.argv[2] )
file = open( sys.argv[2], 'r' )

if( len(sys.argv) >= 4 ):
	startline = int(sys.argv[3])
else:
	startline = 1

ser = serial.Serial()
ser.port = sys.argv[1]
ser.baudrate = 115200
ser.dtr = False
ser.open()

if startline == 1:
	print( "Waking printer..." )
	ser.dtr = True
	# wait until printer ready
	while True:
		out = ser.readline().decode("utf-8").strip()	# blocking
		print( color_recv + "< " + out + color_reset )
		if out.startswith("echo:SD "):			# printer init complete
			break
else:
	# skip waking/resetting the printer when resuming a print
	# won't work on unpatched Linux: https://unix.stackexchange.com/questions/446088/how-to-prevent-dtr-on-open-for-cdc-acm
	# -> the printer will reset anyway and you'll have to manually "tune" temperature/settings before continuing
	print( "Starting at line " + str(startline) )

print( "Starting to send G-code..." )
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

		ser.write( bytes(line + '\n', "utf-8") )
		print( "\033[K" + color_send + "> [" + str(i) + "] " + line + color_reset + "\r", end='', flush=True )	# stay in line
		needs_newline="\n"

		while True:
			out = ser.readline().decode("utf-8").strip()	# blocking
			if out.startswith("ok"):	# printer ready for more commands
				break
			else:
				print( needs_newline + color_recv + "< " + out + color_reset )
				needs_newline=""

	except KeyboardInterrupt:
		print("Aborting... turning off heat, fan, motors")
		ser.write( bytes("M104 S0\nM140 S0\nM107\nM84\n", "utf-8") )
		break

file.close()
ser.close()

hours, rest = divmod( time.time()-start_time, 3600 )
minutes, seconds = divmod( rest, 60 )
print( "--- done after {}h {:0>2}m ---".format( int(hours),int(minutes) ) )
