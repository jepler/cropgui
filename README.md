# A GTK GUI for lossless JPEG cropping

Of the pictures I'd like to put online, I've found that in 75% of the cases
where I want to retouch the photo, it's to crop it and nothing else. Since I
shoot in jpeg, it's a lossy process to load the jpeg in gimp, crop it, and
write the result.

It turns out that debian's jpegtran has a "-crop" flag which performs lossless
cropping of jpeg images as long as the crop is to a multiple of what the
manpage calls the "iMCU boundary", a (usually?) 8x8 block of pixels. This
feature may have been pioneered by Guido of jpegclub.org some years ago.

There's apparently a nice Windows front-end to this program, but I didn't find
a Linux one. So I wrote one! It's pretty basic, but it gets the job done. You
can download it below.

To run cropgui, either list files on the commandline or select them from a file
browser (in the latter case, you're returned to the browser after cropping the
selected file(s); hit 'cancel' to exit completely). The output filename is
chosen automatically, and never overwrites the original (but it will silently
overwrite an earlier cropped version). For example, if the input is "moon.jpg"
then the output is "moon-cropped.jpg".

Images are automatically scaled by a power of 2 (e.g., 1/2, 1/4 or 1/8) in
order to fit onscreen. After releasing the mouse button, the cropped image
boundary may move a little bit; this represents the limitation that the
upper-left corner must be at a multiple of 8x8 original image pixels.

## PREREQUISITES

cropgui is written in Python and requires the following packages:
 * Debian: python, python-tkinter, python-imaging, python-imaging-tk,
   libjpeg-progs, and libimage-exiftool-perl.
 * Fedora: python2-pillow, libjpeg-turbo-utils, pygtk2,
   pygtk2-libglade, ImageMagick, and perl-Image-ExifTool.

The specific external programs required are:
 * `jpegtran` to crop jpeg images (debian package: libjpeg-turbo-progs or libjpeg-progs)
 * `exiftool` to clear the EXIF rotation flag from jpeg output images (debian package: libimage-exiftool-perl)
 * `convert` to rotate and crop other image types (debian package: imagemagick or graphicsmagick-imagemagick-compat)

## INSTALLATION

Although there are packages in the making, for a system-wide install, first make sure
prerequisites are met for your system and the "flavor" of cropgui you want to install.
For the GTK version, you may skip the TK dependencies. But make sure `jpegtran`, `exiftool`
and `convert` are installed.

Then do this on command line after cloning this repo:

    $ sudo bash ./install.sh -p /usr -P /usr/bin/python

Where the _-p_ flag tells install.sh to install to /usr instead of your home dir. And
flag _-P_ points to your python binary, which you can find via _$ type python_. You may
set the optional -f flag to switch between _tk_ and _gtk_ (the default) flavor of the app.

## Development status

The author (@jepler) is not actively developing this project.
Issues and pull requests are not likely to be acted on.
I would be interested in passing this project to a new maintainer.


## LICENSE
cropgui is available under the terms of the GNU GPL version 2 or later.
