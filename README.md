Requirements
===
Python 3 and pyserial

Usage
===
Run the without arguments to see usage info

Startline
===
Set startline to resume a print, if you know the last line in the .gcode that was sent to the printer. The script will then try to avoid resetting the printer on launch.
Note that this will not work on unpatched Linux, due to its drivers always dutifully setting the DTR line high when the port is opened.

See https://unix.stackexchange.com/questions/446088/how-to-prevent-dtr-on-open-for-cdc-acm

I don't know how other OS will react.

To use this feature regardless, you will probably have to "tune" temperature/settings at the printer after launching the script.
