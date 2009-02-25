import atexit
import fcntl
import os
import struct
import sys
import threading

lock = threading.RLock()

TIOCGWINSZ = 0x5413

screen_width = screen_height = None
def screen_size():
    if not os.isatty(2): return 0, 0
    import fcntl
    res = fcntl.ioctl(2, TIOCGWINSZ, "\0" * 4)
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
