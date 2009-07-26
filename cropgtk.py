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

import gobject
import gtk
import gtk.glade

import filechooser

import sys
import traceback

# otherwise, on hardy the user is shown spurious "[application] closed
# unexpectedly" messages but denied the ability to actually "report [the]
# problem"
def excepthook(exc_type, exc_obj, exc_tb):
    try:
        w = app['window1']
    except NameError:
        w = None
    lines = traceback.format_exception(exc_type, exc_obj, exc_tb)
    print "".join(lines)
    m = gtk.MessageDialog(w,
                gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                gtk.MESSAGE_ERROR, gtk.BUTTONS_OK,
                _("Stepconf encountered an error.  The following "
                "information may be useful in troubleshooting:\n\n")
                + "".join(lines))
    m.show()
    m.run()
    m.destroy()
sys.excepthook = excepthook

import cropgui_common
gladefile = os.path.join(os.path.dirname(cropgui_common.__file__),
                "cropgui.glade")

class DragManager(DragManagerBase):
    def __init__(self, g):
        self.g = g
        self.idle = None
        self.busy = False

        DragManagerBase.__init__(self)

        w = g['window1']
        i = g['eventbox1']

        i.connect('button-press-event', self.press)
        i.connect('motion-notify-event', self.motion)
        i.connect('button-release-event', self.release)
        w.connect('delete-event', self.close)
        w.connect('key-press-event', self.key)
        g['toolbutton1'].connect('clicked', self.done)
        g['toolbutton2'].connect('clicked', self.escape)
        g['toolbutton3'].connect('clicked', self.ccw)
        g['toolbutton4'].connect('clicked', self.cw)

    def ccw(self, event):
        self.rotate_ccw()
    def cw(self, event):
        self.rotate_cw()

    def coords(self, event):
        return event.x, event.y

    def press(self, w, event):
        if event.type == gtk.gdk._2BUTTON_PRESS:
            return self.done()
        x, y = self.coords(event)
        self.drag_start(x, y, event.state & gtk.gdk.SHIFT_MASK)

    def motion(self, w, event):
        x, y = self.coords(event)
        if event.state & gtk.gdk.BUTTON1_MASK:
            self.drag_continue(x, y)
        else:
            self.idle_motion(x, y)

    idle_cursor = gtk.gdk.Cursor(gtk.gdk.WATCH)
    cursor_map = {
        DRAG_TL: gtk.gdk.Cursor(gtk.gdk.TOP_LEFT_CORNER),
        DRAG_L: gtk.gdk.Cursor(gtk.gdk.LEFT_SIDE),
        DRAG_BL: gtk.gdk.Cursor(gtk.gdk.BOTTOM_LEFT_CORNER),
        DRAG_TR: gtk.gdk.Cursor(gtk.gdk.TOP_RIGHT_CORNER),
        DRAG_R: gtk.gdk.Cursor(gtk.gdk.RIGHT_SIDE),
        DRAG_BR: gtk.gdk.Cursor(gtk.gdk.BOTTOM_RIGHT_CORNER),
        DRAG_T: gtk.gdk.Cursor(gtk.gdk.TOP_SIDE),
        DRAG_B: gtk.gdk.Cursor(gtk.gdk.BOTTOM_SIDE),
        DRAG_C: gtk.gdk.Cursor(gtk.gdk.FLEUR)}

    def idle_motion(self, x, y):
        i = self.g['image1']
        if not i: return
        if self.busy: cursor = self.idle_cursor
        else:
            what = self.classify(x, y)
            cursor = self.cursor_map.get(what, None)
        i.window.set_cursor(cursor)

    def release(self, w, event):
        x, y = self.coords(event)
        self.drag_end(x, y)

    def done(self, *args):
        self.result = 1
        self.loop.quit()

    def escape(self, *args):
        self.result = 0
        self.loop.quit()

    def close(self, *args):
        self.result = -1
        self.loop.quit()

    def key(self, w, e):
        if e.keyval == gtk.keysyms.Escape: self.escape()
        elif e.keyval == gtk.keysyms.Return: self.done()
        elif e.string in ',<': self.rotate_ccw()
        elif e.string in '.>': self.rotate_cw()

    def image_set(self):
        self.render()
            
    def render(self):
        if self.idle is None:
            self.idle = gobject.idle_add(self.do_render)

    def do_render(self):
        if not self.idle:
            return
        self.idle = None

        g = self.g
        i = g['image1']
        if not i:  # app shutting down
            return

        if self.image is None:
            pixbuf = gtk.gdk.pixbuf_new_from_data('\0\0\0',
                gtk.gdk.COLORSPACE_RGB, 0, 8, 1, 1, 3)
            i.set_from_pixbuf(pixbuf)
            g['pos_left'].set_text('---')
            g['pos_right'].set_text('---')
            g['pos_top'].set_text('---')
            g['pos_bottom'].set_text('---')
            g['pos_width'].set_text('---')
            g['pos_height'].set_text('---')
            g['pos_ratio'].set_text('---')

        else:
            rendered = self.rendered()
            rendered = rendered.convert('RGB')
            i.set_size_request(*rendered.size)
            pixbuf = gtk.gdk.pixbuf_new_from_data(rendered.tostring(),
                gtk.gdk.COLORSPACE_RGB, 0, 8,
                rendered.size[0], rendered.size[1], 3*rendered.size[0])

            ll, tt, rr, bb = self.get_corners()
            ratio = self.describe_ratio()

            g['pos_left'].set_text('%d' % ll)
            g['pos_right'].set_text('%d' % rr)
            g['pos_top'].set_text('%d' % tt)
            g['pos_bottom'].set_text('%d' % bb)
            g['pos_width'].set_text('%d' % (rr-ll))
            g['pos_height'].set_text('%d' % (bb-tt))
            g['pos_ratio'].set_text(self.describe_ratio())

        i.set_from_pixbuf(pixbuf)

        return False


    def wait(self):
        self.loop = gobject.MainLoop()
        self.result = -1
        self.loop.run()
        return self.result

max_h = gtk.gdk.screen_height() - 64*3
max_w = gtk.gdk.screen_width() - 64
max_sz = min(max_w, max_h)

class App:
    def __init__(self):
        self.glade = gtk.glade.XML(gladefile)
        self.drag = DragManager(self)
        self.task = CropTask(self)
        self.dirchooser = None
        self['window1'].set_title(_("CropGTK"))

    def __getitem__(self, name):
        return self.glade.get_widget(name)

    def log(self, msg):
        s = self['statusbar1']
        if s:
            s.pop(0)
            s.push(0, msg)
    progress = log

    def set_busy(self, is_busy=True):
        self.drag.busy = is_busy
        i = self['image1']
        if i:
            self.drag.idle_motion(*i.get_pointer())

    def run(self):
        drag = self.drag
        task = self.task

        for image_name in self.image_names():
            self['window1'].set_title(
                _("%s - CropGTK") % os.path.basename(image_name))
            self.set_busy()
            try:
                i = Image.open(image_name)
                iw, ih = i.size
                scale = 1
                while iw > max_sz or ih > max_sz:
                    iw /= 2
                    ih /= 2
                    scale *= 2
                i.thumbnail((iw, ih))
            except (IOError,), detail:
                m = gtk.MessageDialog(self['window1'],
                    gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                    gtk.MESSAGE_ERROR, gtk.BUTTONS_OK,
                    "Could not open %s: %s" % (image_name, detail))
                m.show()
                m.run()
                m.destroy()
                continue
            drag.image = i
            drag.rotation = image_rotation(i)
            drag.round = max(1, 8/scale)
            drag.scale = scale
            self.set_busy(0)
            v = self.drag.wait()
            self.set_busy()
            if v == -1: break   # user closed app
            if v == 0:
                self.log("Skipped %s" % os.path.basename(image_name))
                continue # user hit "next" / escape
            
            t, l, r, b = drag.top, drag.left, drag.right, drag.bottom
            t *= scale
            l *= scale
            r *= scale
            b *= scale
            cropspec = "%dx%d+%d+%d" % (r-l, b-t, l, t)
            command = ['nice', 'jpegtran']
            if   drag.rotation == 3: command.extend(['-rotate', '180'])
            elif drag.rotation == 6: command.extend(['-rotate', '90'])
            elif drag.rotation == 8: command.extend(['-rotate', '270'])
            command.extend(['-crop', cropspec, image_name])
            target = self.output_name(image_name)
            if not target:
                self.log("Skipped %s" % os.path.basename(image_name))
                continue # user hit "cancel" on save dialog
            print " ".join(command), ">", target
            task.add(command, target)

    def image_names(self):
        if len(sys.argv) > 1:
            for i in sys.argv[1:]: yield i
        else:
            c = filechooser.Chooser(self['window1'], _("Select images to crop"))
            while 1:
                files = c.run()
                if not files: break
                for i in files: yield i

    def output_name(self, image_name):
        d = os.path.dirname(image_name)
        i = os.path.basename(image_name)
        j = os.path.splitext(i)[0].lower() + "-crop.jpg"
        if os.access(d, os.W_OK): return os.path.join(d, j)
        title = _('Save cropped version of %s') % i
        if self.dirchooser is None:
            self.dirchooser = filechooser.DirChooser(self['window1'], title)
            self.dirchooser.set_current_folder(desktop_name())
        else:
            self.dirchooser.set_title(title)
        self.dirchooser.set_current_name(j)
        r = self.dirchooser.run()
        if not r: return ''
        r = r[0]
        e = os.path.splitext(r)[1]
        if e.lower() in ['.jpg', '.jpeg']: return r
        return e + ".jpg"

app = App()
try:
    app.run()
finally:
    app.task.done()
    del app.task
    del app.drag
