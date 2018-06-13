#    a part of cropgui, a graphical front-end for lossless jpeg cropping
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
import atexit
import fcntl
import os
import struct
import sys
import termios
import threading

lock = threading.RLock()

screen_width = screen_height = None
def screen_size():
    if not os.isatty(2): return 0, 0
    res = fcntl.ioctl(2, termios.TIOCGWINSZ, "\0" * 4)
    return struct.unpack("hh", res)
screen_width, screen_height = screen_size()

last_width = 0

def locked(f):
    def fu(*args, **kw):
        lock.acquire()
        try:
            return f(*args, **kw)
        finally:
            lock.release()
    return fu

@locked
def progress(message, *args):
    if args: message = message % args
    global last_width
    if screen_width == 0: return
    message = message[:screen_width - 1]
    width = len(message)
    if width < last_width:
        message += " " * (last_width - width)
    sys.stderr.write(message + "\r")
    sys.stderr.flush()
    last_width = width

@locked
def log(message, *args):
    if args: message = message % args
    progress_clear()
    sys.stderr.write(message + "\n");
    sys.stderr.flush()

def progress_clear():
    if last_width: progress("")

atexit.register(progress_clear)
