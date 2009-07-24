#!/usr/bin/env python
PREVIEW_SIZE = 300

import pygtk
pygtk.require('2.0')

import gtk
import gobject

import os
import Image

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
            w, h = i.size
            i.thumbnail((PREVIEW_SIZE, PREVIEW_SIZE), Image.ANTIALIAS)
            i = i.convert('RGB')
            pixbuf = gtk.gdk.pixbuf_new_from_data(i.tostring(), 
                gtk.gdk.COLORSPACE_RGB, 0, 8, i.size[0], i.size[1],
                i.size[0]*3)
            preview.set_from_pixbuf(pixbuf)
            if len(image_cache) > HIGH_WATER:
                while len(image_cache) > LOW_WATER:
                    image_cache.popitem()
            image_cache[filename] = pixbuf
        except:
            preview.set_from_stock(gtk.STOCK_MISSING_IMAGE,
                gtk.ICON_SIZE_LARGE_TOOLBAR)
            raise

class Chooser:
    def __init__(self, parent):
        self.dialog = dialog = \
            gtk.FileChooserDialog("Select images to crop",
                                  parent,
                                  gtk.FILE_CHOOSER_ACTION_OPEN,
                                  (gtk.STOCK_QUIT, gtk.RESPONSE_CANCEL,
                                   gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)
        dialog.set_select_multiple(True)

        preview = gtk.Image()
        preview.set_size_request(PREVIEW_SIZE, PREVIEW_SIZE)

        dialog.set_preview_widget(preview)
        dialog.set_preview_widget_active(True)
        dialog.connect("update-preview", update_preview_cb, preview)

        filter = gtk.FileFilter()
        filter.set_name("JPEG Images")
        filter.add_mime_type("image/jpeg")
        filter.add_pattern("*.jpg")
        filter.add_pattern("*.jpeg")
        filter.add_pattern("*.JPG")
        filter.add_pattern("*.JPEG")
        dialog.add_filter(filter)

        filter = gtk.FileFilter()
        filter.set_name("All files")
        filter.add_pattern("*")
        dialog.add_filter(filter)

    def run(self):
        self.dialog.show()
        response = self.dialog.run()
        self.dialog.hide()
        if response == gtk.RESPONSE_OK:
            return self.dialog.get_filenames()
        else:
            return []

if __name__ == '__main__':
    print prompt_open()
