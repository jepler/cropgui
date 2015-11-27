#!/usr/bin/env python
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
PREVIEW_SIZE = 300

import pygtk
pygtk.require('2.0')

import gtk
import gobject

import os
from PIL import Image
import cropgui_common

def apply_rotation(rotation, image):
    print "apply_rotation", rotation
    if rotation == 3: return image.transpose(Image.ROTATE_180)
    if rotation == 6: return image.transpose(Image.ROTATE_270)
    if rotation == 8: return image.transpose(Image.ROTATE_90)
    return image

HIGH_WATER, LOW_WATER = 25, 5
image_cache = {}
def update_preview_cb(file_chooser, preview):
    file_chooser.set_preview_widget_active(True)
    filename = file_chooser.get_preview_filename()
    if not filename or os.path.isdir(filename):
        preview.set_from_stock(gtk.STOCK_DIRECTORY, gtk.ICON_SIZE_LARGE_TOOLBAR)
    elif filename in image_cache:
        preview.set_from_pixbuf(image_cache[filename])
    else:
        try:
            i = Image.open(filename)
            r = cropgui_common.image_rotation(i)
            i.thumbnail((PREVIEW_SIZE, PREVIEW_SIZE), Image.ANTIALIAS)
            i = i.convert('RGB')
            i = apply_rotation(r, i)
            try:
                image_data = i.tostring()
            except:
                image_data = i.tobytes()
            pixbuf = gtk.gdk.pixbuf_new_from_data(image_data, 
                gtk.gdk.COLORSPACE_RGB, 0, 8, i.size[0], i.size[1],
                i.size[0]*3)
            preview.set_from_pixbuf(pixbuf)
            if len(image_cache) > HIGH_WATER:
                while len(image_cache) > LOW_WATER:
                    image_cache.popitem()
            image_cache[filename] = pixbuf
        except IOError, detail:
            print detail
            preview.set_from_stock(gtk.STOCK_MISSING_IMAGE,
                gtk.ICON_SIZE_LARGE_TOOLBAR)
        except:
            preview.set_from_stock(gtk.STOCK_MISSING_IMAGE,
                gtk.ICON_SIZE_LARGE_TOOLBAR)
            raise

class BaseChooser:
    def __init__(self, title, parent):
        self.dialog = dialog = \
            gtk.FileChooserDialog(title, parent, self.mode, self.buttons)

    def run(self):
        self.dialog.show()
        response = self.dialog.run()
        self.dialog.hide()
        if response == gtk.RESPONSE_OK:
            return self.dialog.get_filenames()
        else:
            return []

class Chooser(BaseChooser):
    mode = gtk.FILE_CHOOSER_ACTION_OPEN
    buttons = (gtk.STOCK_QUIT, gtk.RESPONSE_CANCEL,
               gtk.STOCK_OPEN, gtk.RESPONSE_OK)

    def __init__(self, title, parent):
        BaseChooser.__init__(self, parent, title)

        self.dialog.set_default_response(gtk.RESPONSE_OK)
        self.dialog.set_select_multiple(True)

        preview = gtk.Image()
        preview.set_size_request(PREVIEW_SIZE, PREVIEW_SIZE)

        self.dialog.set_preview_widget(preview)
        self.dialog.set_preview_widget_active(True)
        self.dialog.connect("update-preview", update_preview_cb, preview)

        filter = gtk.FileFilter()
        filter.set_name("Images")
        filter.add_mime_type("image/*")
        filter.add_pattern("*.jpg")
        filter.add_pattern("*.jpeg")
        filter.add_pattern("*.JPG")
        filter.add_pattern("*.JPEG")
        filter.add_pattern("*.png")
        filter.add_pattern("*.PNG")
        filter.add_pattern("*.tif")
        filter.add_pattern("*.TIF")
        filter.add_pattern("*.tiff")
        filter.add_pattern("*.TIFF")
        filter.add_pattern("*.gif")
        filter.add_pattern("*.GIF")
        self.dialog.add_filter(filter)

        filter = gtk.FileFilter()
        filter.set_name("All files")
        filter.add_pattern("*")
        self.dialog.add_filter(filter)

class DirChooser(BaseChooser):
    mode = gtk.FILE_CHOOSER_ACTION_SAVE
    buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
               gtk.STOCK_SAVE, gtk.RESPONSE_OK)

    def __init__(self, title, parent):
        BaseChooser.__init__(self, parent, title)
        self.dialog.set_default_response(gtk.RESPONSE_OK)

    def set_current_name(self, filename):
        self.dialog.set_current_name(filename)

    def set_title(self, title):
        self.dialog.set_title(title)

    def set_current_folder(self, directory):
        self.dialog.set_current_folder(directory)

if __name__ == '__main__':
    print prompt_open()
