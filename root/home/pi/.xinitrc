#!/bin/sh
while true; do

    # Clean up previously running apps, gracefully at first then harshly
    sleep 2
    pkill -SIGKILL -f "python /home/pi/pikake/app.py"
    pkill -SIGKILL -f uzbl
    sleep 2
    rm -rf /tmp/uzbl*

    # Disable DPMS / Screen blanking
    xset -dpms
    xset s off

    # Reset the framebuffer's colour-depth
    fbset -depth $( cat /sys/module/*fb*/parameters/fbdepth );

    # Hide the cursor (move it to the bottom-right, comment out if you want mouse interaction)
    xwit -root -warp $( cat /sys/module/*fb*/parameters/fbwidth ) $( cat /sys/module/*fb*/parameters/fbheight )

    # Start the window manager (remove "-use_cursor no" if you actually want mouse interaction)
    matchbox-window-manager  -use_titlebar no -use_cursor no &

    # Start pykake
    python /home/pi/pikake/app.py

done;
