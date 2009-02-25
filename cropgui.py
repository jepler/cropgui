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
import Tkinter
import tkFileDialog
import Image
import ImageTk
import ImageFilter
import ImageDraw
import sys
import os
import signal
import math
import subprocess
import threading
import Queue
import log

def _(s): return s  # TODO: i18n

app = Tkinter.Tk()
app.wm_title(_("CropGUI -- lossless cropping and rotation of jpeg files"))
app.wm_iconname(_("CropGUI"))

preview = Tkinter.Label(app)
do_crop = Tkinter.Button(app, text="Crop")
info = Tkinter.Label(app)
preview.pack(side="bottom")
do_crop.pack(side="left")
info.pack(side="left")

(   
    DRAG_NONE,
    DRAG_TL, DRAG_T, DRAG_TR,
    DRAG_L,  DRAG_C, DRAG_R,
    DRAG_BL, DRAG_B, DRAG_BR
) = range(10)

def describe_ratio(a, b):
    if a == 0 or b == 0: return "degenerate"
    if a > b: return "%.2f:1" % (a*1./b)
    return "1:%.2f" % (b*1./a)

def clamp(value, low, high):
    if value < low: return low
    if high < value: return high
    return value

def ncpus():
    if os.path.exists("/proc/cpuinfo"):
        return open("/proc/cpuinfo").read().count("bogomips") or 1
    return 1
ncpus = ncpus()

class CropTask(object):
    def __init__(self):
        self.tasks = Queue.Queue()
        self.threads = set(self.create_task() for i in range(ncpus))
        for t in self.threads: t.start()

    def done(self):
        for t in self.threads:
            self.tasks.put(None)
        for t in self.threads:
            t.join()

    def create_task(self):
        return threading.Thread(target=self.runner)

    def count(self):
        return len(self.tasks) + len(self.threads)

    def add(self, args, target):
        self.tasks.put((args, target))

    def runner(self):
        while 1:
            task = self.tasks.get()
            if task is None:
                break
            args, target_name = task
            shortname = os.path.basename(target_name)
            target = open(target_name, "w")
            log.progress(_("Cropping %s") % shortname)
            subprocess.call(args, stdout=target)
            log.log(_("Cropped %s") % shortname)
            target.close()

task = CropTask()

class DragManager(object):
    def __init__(self, w, b=None, inf=None):
        self.render_flag = 0
        self.show_handles = True
        self.l = w
        if b: b.configure(command=self.done)
        self.inf = inf
        w.bind("<Button-1>", self.start)
        w.bind("<Shift-Button-1>", self.shift_start)
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
        self.state = DRAG_NONE
        self.round = 1
        self.image = None
        self.v = Tkinter.IntVar(app)

    def get_w(self): return self.image.size[0]
    w = property(get_w)
    def get_h(self): return self.image.size[1]
    h = property(get_h)

    def set_image(self, image):
        if image is None:
            if hasattr(self, 'left'): del self.left
            if hasattr(self, 'right'): del self.right
            if hasattr(self, 'bottom'): del self.bottom
            if hasattr(self, 'blurred'): del self.blurred
            if hasattr(self, 'xor'): del self.xor
            if hasattr(self, 'tkimage'): del self.tkimage
            self._image = None
            self.l.configure(image=self.dummy_tkimage)
        else:
            self._image = image.copy()
            self.top = 0
            self.left = 0
            self.right = self.w
            self.bottom = self.h
            mult = len(self.image.mode) # replicate filter for L, RGB, RGBA
            self.blurred = image.copy().filter(
                ImageFilter.SMOOTH_MORE).point([x/2 for x in range(256)] * mult)
            self.xor = image.copy().point([x ^ 128 for x in range(256)] * mult)
            self.tkimage = ImageTk.PhotoImage(self._image)
            self.l.configure(image=self.tkimage)
        self.render()

    def fix(self, a, b, lim):
        a, b = sorted((b,a))
        a = clamp(a, 0, lim)
        b = clamp(b, 0, lim)
        a = int(math.floor(a * 1. / self.round)*self.round)
        return a, b

    def set_crop(self, top, left, right, bottom):
        self.top, self.bottom = self.fix(top, bottom, self.h)
        self.left, self.right = self.fix(left, right, self.w)
        self.render()

    def get_image(self):
        return self._image
    image = property(get_image, set_image, None,
                "change the target of this DragManager")

    def render(self):
        if not self.render_flag:
            self.render_flag = True
            app.after_idle(self.do_render)

    def do_render(self):
        if not self.render_flag: return
        self.render_flag = False
        if self.image is None:
            return

        mask = Image.new('1', self.image.size, 0)
        mask.paste(1, (self.left, self.top, self.right, self.bottom))
        image = Image.composite(self.image, self.blurred, mask)

        t, l, r, b = self.top, self.left, self.right, self.bottom
        dx = (r - l) / 4
        dy = (b - t) / 4

        if self.inf:
            sc = self.scale
            ll, tt, rr, bb = l*sc, t*sc, r*sc, b*sc
            ratio = describe_ratio(rr-ll, bb-tt)
            self.inf.configure(text=
                "Left:  %4d  Top:    %4d    Right: %4d  Bottom: %4d\n"
                "Width: %4d  Height: %4d    Ratio: %8s\n"
                    % (ll, tt, rr, bb, rr-ll, bb-tt, ratio),
                font="fixed", justify="l", anchor="w")

        if self.show_handles:
            mask = Image.new('1', self.image.size, 1)
            draw = ImageDraw.Draw(mask)

            draw.line([l, t, r, t], fill=0)
            draw.line([l, b, r, b], fill=0)
            draw.line([l, t, l, b], fill=0)
            draw.line([r, t, r, b], fill=0)

            draw.line([l+dx, t, l+dx, t+dy, l, t+dy], fill=0)
            draw.line([r-dx, t, r-dx, t+dy, r, t+dy], fill=0)
            draw.line([l+dx, b, l+dx, b-dy, l, b-dy], fill=0)
            draw.line([r-dx, b, r-dx, b-dy, r, b-dy], fill=0)

            image = Image.composite(image, self.xor, mask)
        self.tkimage.paste(image)

    def enter(self, event):
        self.show_handles = True
        self.render()

    def leave(self, event):
        self.show_handles = False
        self.render()

    def classify(self, x, y):
        t, l, r, b = self.top, self.left, self.right, self.bottom
        dx = (r - l) / 4
        dy = (b - t) / 4

        if x < l: return DRAG_NONE
        if x > r: return DRAG_NONE
        if y < t: return DRAG_NONE
        if y > b: return DRAG_NONE

        if x < l+dx:
            if y < t+dy: return DRAG_TL
            if y < b-dy: return DRAG_L
            return DRAG_BL
        if x < r-dx:
            if y < t+dy: return DRAG_T
            if y < b-dy: return DRAG_C
            return DRAG_B
        else:
            if y < t+dy: return DRAG_TR
            if y < b-dy: return DRAG_R
            return DRAG_BR

    def start(self, event, fixed=False):
        self.x0 = event.x
        self.y0 = event.y
        self.t0 = self.top
        self.l0 = self.left
        self.r0 = self.right
        self.b0 = self.bottom
        self.state = self.classify(event.x, event.y)
        if self.state in (DRAG_TL, DRAG_TR, DRAG_BL, DRAG_BR):
            self.fixed_ratio = fixed
        else:
            # can't drag an edge and preserve ratio (what does that mean?0
            # dragging center always preserves ratio
            self.fixed_ratio = False
    def shift_start(self, event):
        self.start(event, True)

    cursor_map = {
        DRAG_TL: 'top_left_corner',
        DRAG_L: 'left_side',
        DRAG_BL: 'bottom_left_corner',
        DRAG_TR: 'top_right_corner',
        DRAG_R: 'right_side',
        DRAG_BR: 'bottom_right_corner',
        DRAG_T: 'top_side',
        DRAG_B: 'bottom_side',
        DRAG_C: 'fleur'}

    def idle_motion(self, event):
        what = self.classify(event.x, event.y)
        cursor = self.cursor_map.get(what, "")
        self.l.configure(cursor=cursor)

    def motion(self, event):
        dx = event.x - self.x0
        dy = event.y - self.y0
        if self.fixed_ratio:
            ratio = (self.r0-self.l0) * 1. / (self.b0 - self.t0)
            if self.state in (DRAG_TR, DRAG_BL): ratio = -ratio
            if abs(dx/ratio) > abs(dy):
                dy = int(round(dx / ratio))
            else:
                dx = int(round(dy * ratio))
        new_top, new_left, new_right, new_bottom = \
            self.top, self.left, self.right, self.bottom
        if self.state == DRAG_C:
            # A center drag bumps into the edges
            if dx > 0:
                dx = min(dx, self.w - self.r0 - 1)
            else:
                dx = max(dx, -self.l0)
            if dy > 0:
                dy = min(dy, self.h - self.b0 - 1)
            else:
                dy = max(dy, -self.t0)
        if self.state in (DRAG_TL, DRAG_T, DRAG_TR, DRAG_C):
            new_top = self.t0 + dy
        if self.state in (DRAG_TL, DRAG_L, DRAG_BL, DRAG_C):
            new_left = self.l0 + dx
        if self.state in (DRAG_TR, DRAG_R, DRAG_BR, DRAG_C):
            new_right = self.r0 + dx
        if self.state in (DRAG_BL, DRAG_B, DRAG_BR, DRAG_C):
            new_bottom = self.b0 + dy
        # A drag never moves left past right and so on
        new_top = min(self.bottom-1, new_top)
        new_left = min(self.right-1, new_left)
        new_right = max(self.left+1, new_right)
        new_bottom = max(self.top+1, new_bottom)

        self.set_crop(new_top, new_left, new_right, new_bottom)

    def end(self, event):
        self.set_crop(self.top, self.left, self.right, self.bottom)
        self.state = DRAG_NONE

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

for image_name in image_names():
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
    v = drag.wait()
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
    task.add(['nice', 'jpegtran', '-crop', cropspec, image_name], target)
task.done()

# 1. open image
# 2. choose 1/2, 1/4, 1/8 scaling so that resized image fits onscreen
# 3. load image at requested size
# 4. run GUI to get desired crop settings
# 5. write output file
