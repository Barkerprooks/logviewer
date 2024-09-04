# credit: https://ballingt.com/nonblocking-stdin-in-python-3/

import termios
import fcntl
import tty
import os


class Raw(object):
    
    def __init__(self, io):
        self.io = io
        self.fd = self.io.fileno()
    
    def __enter__(self):
        self.old_tty = termios.tcgetattr(self.io)
        tty.setcbreak(self.io)

    def __exit__(self, *args):
        termios.tcsetattr(self.io, termios.TCSANOW, self.old_tty)


class NonBlocking(object):

    def __init__(self, io):
        self.io = io
        self.fd = self.io.fileno()

    def __enter__(self):
        self.old_fl = fcntl.fcntl(self.fd, fcntl.F_GETFL)
        fcntl.fcntl(self.fd, fcntl.F_SETFL, self.old_fl | os.O_NONBLOCK)
    
    def __exit__(self, *args):
        fcntl.fcntl(self.fd, fcntl.F_SETFL, self.old_fl)
