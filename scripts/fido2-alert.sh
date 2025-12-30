#!/bin/bash
# FIDO2 Touch Alert - Plays audio when FIDO2 tap is required
# Called by pam_exec before pam_u2f

# Use paplay for PulseAudio, run as the actual user (not root)
SOUND="/usr/share/sounds/freedesktop/stereo/window-attention.oga"

# Get the real user's PulseAudio socket
if [ -n "$SUDO_USER" ]; then
    PULSE_USER="$SUDO_USER"
else
    PULSE_USER="$PAM_USER"
fi

# Run paplay as the actual user to access their PulseAudio session
if [ -n "$PULSE_USER" ]; then
    sudo -u "$PULSE_USER" PULSE_RUNTIME_PATH="/run/user/$(id -u "$PULSE_USER")/pulse" paplay "$SOUND" 2>/dev/null &
fi

exit 0
