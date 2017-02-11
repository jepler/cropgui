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

cropgui is written in Python and requires python, python-tkinter,
python-imaging, python-imaging-tk, and libjpeg-progs. It is available under the
terms of the GNU GPL version 2 or later. 

The specific external programs required are:
 * `jpegtran` to crop jpeg images (debian package: libjpeg-turbo-progs or libjpeg-progs)
 * `jpegexiforient` to clear the EXIF rotation flag from jpeg output images (debian package: libjpeg-turbo-progs or libjpeg-progs)
 * `convert` to rotate and crop other image types (debian package: imagemagick or graphicsmagick-imagemagick-compat)
