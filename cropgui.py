#!/usr/bin/python
#    cropgui, a graphical front-end for lossless jpeg cropping
#    Copyright (C) 2009 Jeff Epler <jepler@unpythonic.net>
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

from cropgui_common import *
from cropgui_common import _

import Tkinter
import ImageTk
import tkFileDialog
import sys
import os
import signal
import log

app = Tkinter.Tk()
app.wm_title(_("CropGUI -- lossless cropping and rotation of jpeg files"))
app.wm_iconname(_("CropGUI"))

preview = Tkinter.Label(app)
do_crop = Tkinter.Button(app, text="Crop")
info = Tkinter.Label(app)
preview.pack(side="bottom")
do_crop.pack(side="left")
info.pack(side="left")

task = CropTask(log)

class DragManager(DragManagerBase):
    def __init__(self, w, b, inf):
        self.l = w
        b.configure(command=self.done)
        self.inf = inf
        w.bind("<Button-1>", self.press)
        w.bind("<Shift-Button-1>", self.shift_press)
        w.bind("<Double-Button-1>", self.double)
        w.bind("<Button1-Motion>", self.motion)
        w.bind("<Motion>", self.idle_motion)
        w.bind("<ButtonRelease-1>", self.end)
        w.bind("<Enter>", self.enter)
        w.bind("<Leave>", self.leave)
        app.bind("<Return>", self.double)
        app.bind("<Escape>", self.escape)
        w.bind("<Button1-Enter>", "#nothing")
        w.bind("<Button1-Leave>", "#nothing")
        dummy_image = Image.new('L', (max_w/2,max_h/2), 0xff)
        self.dummy_tkimage = ImageTk.PhotoImage(dummy_image)
        self.v = Tkinter.IntVar(app)
        DragManagerBase.__init__(self)

    def image_set(self):
        if self.image is None:
            self.l.configure(image=self.dummy_tkimage)
            self.inf.configure(text="\n\n")
        else:
            self.tkimage = ImageTk.PhotoImage(self.image)
            self.l.configure(image=self.tkimage)
            self.render()

    def render(self):
        if not self.render_flag:
            self.render_flag = True
            app.after_idle(self.do_render)

    def do_render(self):
        if not self.render_flag:
            return
        self.render_flag = False
        if self.image is None:
            self.l.configure(image=self.dummy_tkimage)
            self.inf.configure(text="\n\n")
            return

        ll, tt, rr, bb = self.get_corners()
        ratio = self.describe_ratio()
        self.inf.configure(text=
            "Left:  %4d  Top:    %4d    Right: %4d  Bottom: %4d\n"
            "Width: %4d  Height: %4d    Ratio: %8s\n"
                % (ll, tt, rr, bb, rr-ll, bb-tt, ratio),
            font="fixed", justify="l", anchor="w")

        self.tkimage.paste(self.rendered())

    def enter(self, event):
        self.show_handles = True
        self.render()

    def leave(self, event):
        self.show_handles = False
        self.render()

    def press(self, event): self.drag_start(event.x, event.y, False)
    def shift_press(self, event): self.drag_start(event.x, event.y, True)

    def idle_motion(self, event):
        what = self.classify(event.x, event.y)
        if busy:
            cursor = "watch"
        else:
            cursor = self.cursor_map.get(what, "")
        self.l.configure(cursor=cursor)

    def motion(self, event):
        self.drag_continue(event.x, event.y)

    def end(self, event):
        self.drag_end(event.x, event.y)

    def close(self):
        self.v.set(-1)

    def cancel(self):
        self.v.set(0)

    def escape(self, event):
        self.cancel()

    def done(self):
        self.v.set(1)

    def double(self, event):
        self.done()

    def wait(self):
        app.wait_variable(self.v)
        value = self.v.get()
        return value


max_h = app.winfo_screenheight() - 64 - 32
max_w = app.winfo_screenwidth() - 64

drag = DragManager(preview, do_crop, info)
app.wm_protocol('WM_DELETE_WINDOW', drag.close)

def image_names():
    if len(sys.argv) > 1:
        for i in sys.argv[1:]: yield i
    else:
        while 1:
            names = tkFileDialog.askopenfilenames(master=app,
                defaultextension=".jpg", multiple=1, parent=app,
                filetypes=(
                    (_("JPEG Image Files"), ".jpg .JPG .jpeg .JPEG"),
                    (_("All files"), "*"),
                ),
                title=_("Select images to crop"))
            if not names: break
            for name in names: yield name

pids = set()
def reap():
    global pids
    pids = set(p for p in pids if p.poll() is None)

def set_busy(new_busy=True):
    global busy
    busy = new_busy
    if busy:
        drag.l.configure(cursor="watch")
        app.configure(cursor="watch")
        do_crop.configure(state="disabled")
    else:
        drag.l.configure(cursor="")
        app.configure(cursor="")
        do_crop.configure(state="normal")
    app.update_idletasks()

try:
    for image_name in image_names():
        set_busy()
        i = Image.open(image_name)
        iw, ih = i.size
        scale=1
        while iw > max_w or ih > max_h:
            iw /= 2
            ih /= 2
            scale *= 2
        i.thumbnail((iw, ih))
        drag.image = i
        drag.round = max(1, 8/scale)
        drag.scale = scale
        set_busy(0)
        v = drag.wait()
        set_busy()
        if v == -1: break   # user closed app
        if v == 0: continue # user hit "next" / escape
        
        base, ext = os.path.splitext(image_name)
        t, l, r, b = drag.top, drag.left, drag.right, drag.bottom
        t *= scale
        l *= scale
        r *= scale
        b *= scale
        cropspec = "%dx%d+%d+%d" % (r-l, b-t, l, t)
        target = base + "-crop" + ext
        task.add(['nice', 'jpegtran', '-copy', 'all', '-crop', cropspec, image_name], target)
finally:
    task.done()

# 1. open image
# 2. choose 1/2, 1/4, 1/8 scaling so that resized image fits onscreen
# 3. load image at requested size
# 4. run GUI to get desired crop settings
# 5. write output file
