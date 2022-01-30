"""
if any user try to resize window width will automatically resize window height too with aspect ratio. That's mean user can't be able to resize only one size. changing one side size will change another side too.
"""

import tkinter as tk
WIDTH, HEIGHT = 400, 300  # Defines aspect ratio of window.

def maintain_aspect_ratio(event, aspect_ratio):
    """ Event handler to override root window resize events to maintain the
        specified width to height aspect ratio.
    """
    if event.widget.master:  # Not root window?
        return  # Ignore.

    # <Configure> events contain the widget's new width and height in pixels.
    new_aspect_ratio = event.width / event.height

    # Decide which dimension controls.
    if new_aspect_ratio > aspect_ratio:
        # Use width as the controlling dimension.
        desired_width = event.width
        desired_height = int(event.width / aspect_ratio)
    else:
        # Use height as the controlling dimension.
        desired_height = event.height
        desired_width = int(event.height * aspect_ratio)

    # Override if necessary.
    if event.width != desired_width or event.height != desired_height:
        # Manually give it the proper dimensions.
        event.widget.geometry(f'{desired_width}x{desired_height}')
        return "break"  # Block further processing of this event.

root = tk.Tk()
root.geometry(f'{WIDTH}x{HEIGHT}')
root.bind('<Configure>', lambda event: maintain_aspect_ratio(event, WIDTH/HEIGHT))
root.mainloop()