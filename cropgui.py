#!/usr/bin/python2
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
preview.pack(side="bottom")

do_crop = Tkinter.Button(app, text="Crop")
do_crop.pack(side="left")

crop169_button = Tkinter.Menubutton(app, text="16:9")
crop169_button.pack(side="left")
crop169 = Tkinter.Menu(crop169_button)
crop169_button.config(menu=crop169)

crop85_button = Tkinter.Menubutton(app, text="8:5")
crop85_button.pack(side="left")
crop85 = Tkinter.Menu(crop85_button)
crop85_button.config(menu=crop85)

crop32_button = Tkinter.Menubutton(app, text="3:2")
crop32_button.pack(side="left")
crop32 = Tkinter.Menu(crop32_button)
crop32_button.config(menu=crop32)

crop43_button = Tkinter.Menubutton(app, text="4:3")
crop43_button.pack(side="left")
crop43 = Tkinter.Menu(crop43_button)
crop43_button.config(menu=crop43)

crop11_button = Tkinter.Menubutton(app, text="1:1")
crop11_button.pack(side="left")
crop11 = Tkinter.Menu(crop11_button)
crop11_button.config(menu=crop11)

crop34_button = Tkinter.Menubutton(app, text="3:4")
crop34_button.pack(side="left")
crop34 = Tkinter.Menu(crop34_button)
crop34_button.config(menu=crop34)

crop23_button = Tkinter.Menubutton(app, text="2:3")
crop23_button.pack(side="left")
crop23 = Tkinter.Menu(crop23_button)
crop23_button.config(menu=crop23)

info = Tkinter.Label(app)
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

        tt, ll, rr, bb = self.get_corners()
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

crop169.add_command(label='1920 x 1080',command=lambda: drag.set_stdsize(1920,1080))
crop169.add_command(label='3840 x 2160',command=lambda: drag.set_stdsize(3840,2160))
crop169.add_command(label='4000 x 2248',command=lambda: drag.set_stdsize(4000,2248))

crop85.add_command (label='1920 x 1200',command=lambda: drag.set_stdsize(1920,1200))
crop85.add_command (label='3456 x 2160',command=lambda: drag.set_stdsize(3456,2160))
crop85.add_command (label='4000 x 2496',command=lambda: drag.set_stdsize(4000,2496))
crop85.add_command (label='4000 x 2496',command=lambda: drag.set_stdsize(4000,2496))
crop85.add_command (label='5184 x 3240',command=lambda: drag.set_stdsize(5184,3240))

crop32.add_command (label='1136 x  760',command=lambda: drag.set_stdsize(1136, 760))
crop32.add_command (label='1440 x  960',command=lambda: drag.set_stdsize(1440, 960))
crop32.add_command (label='1536 x 1024',command=lambda: drag.set_stdsize(1536,1024))
crop32.add_command (label='1752 x 1168',command=lambda: drag.set_stdsize(1752,1168))
crop32.add_command (label='2048 x 1360',command=lambda: drag.set_stdsize(2048,1360))
crop32.add_command (label='2592 x 1728',command=lambda: drag.set_stdsize(2592,1728))
crop32.add_command (label='3072 x 2048',command=lambda: drag.set_stdsize(3072,2048))
crop32.add_command (label='3240 x 2160',command=lambda: drag.set_stdsize(3240,2160))
crop32.add_command (label='4000 x 2664',command=lambda: drag.set_stdsize(4000,2664))

crop43.add_command (label='1280 x  960',command=lambda: drag.set_stdsize(1280, 960))
crop43.add_command (label='1600 x 1200',command=lambda: drag.set_stdsize(1600,1200))
crop43.add_command (label='1720 x 1280',command=lambda: drag.set_stdsize(1720,1280))
crop43.add_command (label='2048 x 1536',command=lambda: drag.set_stdsize(2048,1536))
crop43.add_command (label='2560 x 1920',command=lambda: drag.set_stdsize(2560,1920))
crop43.add_command (label='2880 x 2160',command=lambda: drag.set_stdsize(2880,2160))
crop43.add_command (label='4000 x 3000',command=lambda: drag.set_stdsize(4000,3000))
crop43.add_command (label='4320 x 3240',command=lambda: drag.set_stdsize(4320,3240))

crop11.add_command (label='3000 x 3000',command=lambda: drag.set_stdsize(3000,3000))

crop34.add_command (label=' 960 x 1280',command=lambda: drag.set_stdsize( 960,1280))
crop34.add_command (label='1200 x 1600',command=lambda: drag.set_stdsize(1200,1600))
crop34.add_command (label='1280 x 1720',command=lambda: drag.set_stdsize(1280,1720))
crop34.add_command (label='1536 x 2048',command=lambda: drag.set_stdsize(1536,2048))
crop34.add_command (label='1920 x 2560',command=lambda: drag.set_stdsize(1920,2560))
crop34.add_command (label='2160 x 2880',command=lambda: drag.set_stdsize(2160,2880))
crop34.add_command (label='3000 x 4000',command=lambda: drag.set_stdsize(3000,4000))
crop34.add_command (label='3240 x 4320',command=lambda: drag.set_stdsize(3240,4320))

crop23.add_command (label=' 760 x 1136',command=lambda: drag.set_stdsize( 760,1136))
crop23.add_command (label=' 960 x 1440',command=lambda: drag.set_stdsize( 960,1440))
crop23.add_command (label='1024 x 1536',command=lambda: drag.set_stdsize(1024,1536))
crop23.add_command (label='1168 x 1752',command=lambda: drag.set_stdsize(1168,1752))
crop23.add_command (label='1360 x 2048',command=lambda: drag.set_stdsize(1360,2048))
crop23.add_command (label='1728 x 2592',command=lambda: drag.set_stdsize(1728,2592))
crop23.add_command (label='2048 x 3072',command=lambda: drag.set_stdsize(2048,3072))
crop23.add_command (label='2664 x 4000',command=lambda: drag.set_stdsize(2664,4000))


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
        # load new image
        set_busy()
        i = Image.open(image_name)
        if i.format == "JPEG":
            drag.round = 8
        else:
            drag.round = 1

        # compute scale to fit image on display
        drag.w, drag.h = i.size
        drag.scale=1
        drag.scale = max (drag.scale, (drag.w-1)/max_w+1)
        drag.scale = max (drag.scale, (drag.h-1)/max_h+1)

        # put image into drag object
        i.thumbnail((drag.w/drag.scale, drag.h/drag.scale))
        drag.image = i

        # get user input
        set_busy(0)
        v = drag.wait()
        set_busy()
        if v == -1: break   # user closed app
        if v == 0: continue # user hit "next" / escape

        # compute parameters for command line of cropping tool
        base, ext = os.path.splitext(image_name)
        t, l, r, b = drag.get_corners()
        cropspec = "%dx%d+%d+%d" % (r-l, b-t, l, t)
        target = base + "-crop" + ext
        print cropspec

        if i.format == "JPEG":
            task.add(['nice', 'jpegtran', '-copy',    'all',     '-crop', cropspec, '-outfile', target, image_name], target)
        else:
            task.add(['nice', 'convert',  image_name, '+repage', '-crop', cropspec,             target],             target)
finally:
    task.done()

# 1. open image
# 2. choose 1/2, 1/4, 1/8 scaling so that resized image fits onscreen
# 3. load image at requested size
# 4. run GUI to get desired crop settings
# 5. write output file
