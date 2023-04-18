'''
import tkinter as tk

from mission import mode_switch
# TODO: other imports, integration


def press(event):
    k = event.keysym
    if k == "BackSpace":
        mode_switch(vehicle, "AUTO")
    elif k == "Escape":
        mode_switch(vehicle, "RTL")
    elif k == "w":  # Pitch down
        pass
        vehicle.channels.overrides["2"] = 0  # TODO: figure out values
    elif k == "s":  # Pitch up
        pass
    elif k == "a":  # Roll left
        pass
    elif k == "d":  # Roll right
        pass
    elif k == "r":  # Throttle up
        pass
    elif k == "f":  # Throttle down
        pass
    elif k == "i":
        print(vehicle.attitude)


def release(event):
    k = event.keysym
    if k == "w":
        pass
    elif k == "s":
        pass
    elif k == "a":
        pass
    elif k == "d":
        pass
    elif k == "r":
        pass
    elif k == "f":
        pass


tk_root = tk.Tk()
tk_root.bind("<Key>", press)
tk_root.bind("<KeyRelease>", release)
tk_root.mainloop()
'''
