#!/usr/bin/python3
"""
Speech Note Mic Toggle Daemon
Polls Speech Note state via D-Bus and toggles mic accordingly.
Mic is only hot when actively listening.
"""

import subprocess
import time
import dbus

# Speech Note states
IDLE_STATE = 3

def mute_mic():
    """Mute the mic"""
    subprocess.run(["amixer", "set", "Capture", "nocap"], check=False,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("[MIC] Muted (nocap)", flush=True)

def unmute_mic():
    """Unmute the mic"""
    subprocess.run(["amixer", "set", "Capture", "cap"], check=False,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("[MIC] Unmuted (cap)", flush=True)

def get_state(props):
    """Get current Speech Note state"""
    try:
        return int(props.Get("net.mkiol.SpeechNote", "State"))
    except:
        return IDLE_STATE

def set_analog_profile():
    """Force webcam to analog mic profile"""
    subprocess.run([
        "pactl", "set-card-profile",
        "alsa_card.usb-046d_Logi_Webcam_C920e_B7567EDF-02",
        "input:analog-stereo"
    ], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("[PROFILE] Webcam set to analog-stereo", flush=True)

def main():
    print("[INIT] Speech Note Mic Toggle Daemon (polling mode)", flush=True)

    # Force analog profile on startup
    set_analog_profile()

    # Start with mic muted
    mute_mic()

    bus = dbus.SessionBus()
    listening = False
    last_state = IDLE_STATE

    while True:
        try:
            proxy = bus.get_object("net.mkiol.SpeechNote", "/net/mkiol/SpeechNote")
            props = dbus.Interface(proxy, "org.freedesktop.DBus.Properties")
            state = get_state(props)

            if state != last_state:
                print(f"[STATE] Changed: {last_state} -> {state}", flush=True)
                last_state = state

            # Not idle = listening
            if state != IDLE_STATE:
                if not listening:
                    listening = True
                    unmute_mic()
            else:
                if listening:
                    listening = False
                    mute_mic()

        except dbus.exceptions.DBusException as e:
            # Speech Note not running, ensure muted
            if listening:
                listening = False
                mute_mic()

        time.sleep(0.2)  # Poll 5 times per second

if __name__ == "__main__":
    main()
