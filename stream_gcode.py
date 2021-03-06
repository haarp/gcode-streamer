#!/usr/bin/python3
# G-Code streamer for Prusa i3 3D printers over serial port by haarp
# License: GNU General Public License v3 or newer

import sys
import os
import serial
import time

col_send = "\033[32m"
col_recv = "\033[33m"
col_error = "\033[31m"
col_reset = "\033[39m"

def finish( exitcode ):
	try:
		file.close()
		ser.close()
	except:
		pass

	hours, rest = divmod( time.time()-start_time, 3600 )
	minutes, seconds = divmod( rest, 60 )
	print( "\n--- done after {}h {:0>2}m ---".format( int(hours),int(minutes) ) )

	sys.exit(exitcode)


start_time = time.time()

if( len(sys.argv) < 3 ):
	print( "Usage: " + sys.argv[0] + " <serial port> <G-Code file> [start line]" )
	sys.exit()

modified = os.path.getmtime( sys.argv[2] )
modified = time.strftime( '%x %X', time.localtime(modified) )
file = open( sys.argv[2], 'r' )

if( len(sys.argv) >= 4 ):
	startline = int(sys.argv[3])
else:
	startline = 1

print( "\033]0;" + os.path.basename( sys.argv[2] ) + " - G-code Streamer " + "\007" )	# set initial terminal title
print( "Using file " + sys.argv[2] + ", last modified " + modified )

ser = serial.Serial()
ser.port = sys.argv[1]
ser.baudrate = 115200
ser.dtr = False
ser.open()
time.sleep(0.1)
ser.flushInput()
time.sleep(0.1)

if startline == 1:
	print( "Waking printer..." )
	ser.dtr = True
	# wait until printer ready
	while True:
		out = ser.readline().decode("utf-8").strip()	# blocking
		print( col_recv + "< " + out + col_reset )
		if out.startswith("echo:SD "):			# printer init complete
			break
else:
	# skip waking/resetting the printer when resuming a print
	# won't work on unpatched Linux: https://unix.stackexchange.com/questions/446088/how-to-prevent-dtr-on-open-for-cdc-acm
	print( "Starting at line " + str(startline) )

print( "Printer ready, sending G-code..." )
i = 0
progress = -1; remaining = -1
out_newline=""; in_newline=""
for line in file:
	try:
		i = i+1
		if i < startline:
			continue

		line = line.strip()		# strip EOL
		line = line.split(';')[0]	# strip comments
		if not line.strip():		# skip empty lines
			continue

		if line.startswith( "M73 P" ):
			progress = int( line.split('P')[1].split('R')[0] )
			remaining = int( line.split('R')[1] )

		if( i % 25 == 0 and progress > -1 and remaining > -1 ):	# set terminal title with percentage and time remaining
			print( "\033]0;" + "[" + str(progress) + "% ⏱" + str(int(remaining/60)) + ":" + str(remaining%60).zfill(2) + "R] " +
				os.path.basename( sys.argv[2] ) + " - G-code Streamer" + "\007", end='', flush=True )	# no newline

		ser.write( bytes(line + '\n', "utf-8") )
		print( in_newline + "\033[K" + col_send + "> [" + str(i) + "] " + line + col_reset + "\r", end='', flush=True )	# stay in line
		in_newline=''; out_newline="\n"

		while True:
			out = ser.readline().decode("utf-8").strip()	# blocking
			if out.startswith("ok"):	# printer ready for more commands
				break
			elif out.startswith("echo:busy: processing"):
				pass
			elif ( out.startswith("NORMAL MODE: Percent") or out.startswith("SILENT MODE: Percent") ):
				pass
			elif out.startswith("T:"):
				print( out_newline + "\033[K" + col_recv + "< " + out + col_reset + "\r", end='', flush=True )	# stay in line
				out_newline=''; in_newline="\n"
			elif ( out == "start" or out.startswith("echo: Last Updated") ):
				if( out_newline or in_newline ):
					print("\n", end='')
				print( col_recv + "< " + out + col_reset )
				print( col_error + "Printer reset?! Bailing out!" + col_reset )
				finish(1)
			else:
				if( out_newline or in_newline ):
					print("\n", end='')
					out_newline=""
					in_newline=""
				print( col_recv + "< " + out + col_reset )

	except KeyboardInterrupt:
		print( "\n" + col_error + "Aborting... turning off heat, fan, motors" + col_reset )
		ser.write( bytes("M104 S0\nM140 S0\nM107\nM84\n", "utf-8") )
		finish(130)

finish(0)
