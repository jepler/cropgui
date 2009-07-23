import Image
import ImageFilter
import ImageDraw
import subprocess
import threading
import Queue
import os
import math

def _(s): return s  # TODO: i18n

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
    def __init__(self, log):
        self.log = log
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
            self.log.progress(_("Cropping to %s") % shortname)
            subprocess.call(args, stdout=target)
            self.log.log(_("Cropped to %s") % shortname)
            target.close()

class DragManagerBase(object):
    def __init__(self):
        self.render_flag = 0
        self.show_handles = True
        self.state = DRAG_NONE
        self.round = 1
        self.image = None

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
            self._image = None
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
        self.image_set()
        self.render()

    def fix(self, a, b, lim):
        a, b = sorted((b,a))
        a = clamp(a, 0, lim)
        b = clamp(b, 0, lim)
        a = int(math.floor(a * 1. / self.round)*self.round)
        return a, b

    def get_corners(self):
        t, l, r, b = self.top, self.left, self.right, self.bottom
        sc = self.scale
        ll, tt, rr, bb = l*sc, t*sc, r*sc, b*sc

        return ll, tt, rr, bb

    def describe_ratio(self):
        w = self.right - self.left
        h = self.bottom - self.top
        return describe_ratio(w, h)

    def set_crop(self, top, left, right, bottom):
        self.top, self.bottom = self.fix(top, bottom, self.h)
        self.left, self.right = self.fix(left, right, self.w)
        self.render()

    def get_image(self):
        return self._image
    image = property(get_image, set_image, None,
                "change the target of this DragManager")

    def rendered(self):
        if self.image is None: return None

        t, l, r, b = self.top, self.left, self.right, self.bottom

        mask = Image.new('1', self.image.size, 0)
        mask.paste(1, (l, t, r, b))
        image = Image.composite(self.image, self.blurred, mask)

        if self.show_handles:
            dx = (r - l) / 4
            dy = (b - t) / 4

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
        return image

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

    def drag_start(self, x, y, fixed=False):
        self.x0 = x
        self.y0 = y
        self.t0 = self.top
        self.l0 = self.left
        self.r0 = self.right
        self.b0 = self.bottom
        self.state = self.classify(x, y)
        if self.state in (DRAG_TL, DRAG_TR, DRAG_BL, DRAG_BR):
            self.fixed_ratio = fixed
        else:
            # can't drag an edge and preserve ratio (what does that mean?)
            # dragging center always preserves ratio
            self.fixed_ratio = False

    def drag_continue(self, x, y):
        dx = x - self.x0
        dy = y - self.y0
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
        if self.state != DRAG_C:
            new_top = min(self.bottom-1, new_top)
            new_left = min(self.right-1, new_left)
            new_right = max(self.left+1, new_right)
            new_bottom = max(self.top+1, new_bottom)

        self.set_crop(new_top, new_left, new_right, new_bottom)

    def drag_end(self, x, y):
        self.set_crop(self.top, self.left, self.right, self.bottom)
        self.state = DRAG_NONE
