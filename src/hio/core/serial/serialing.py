"""
Asynchronous (nonblocking) serial io

"""
from __future__ import absolute_import, division, print_function

import sys
import os
import errno
import platform
from collections import deque


from ... import hioing, help
from ...base import doing

logger = help.ogler.getLogger()


class LineError(hioing.HioError):
    """
    Serial line error. Too big for buffer.

    Usage:
        raise LineError("error message")
    """

class Console():
    """
    Class to manage non blocking interactive I/O on serial console

    Opens non blocking read file descriptor on console
    Use instance method .close to close file descriptor
    Use instance methods .getline to read & .put to write to console
    Needs os module

    Attributes:
        bs (int): max buffer size for each read, defaults to 256
        fd (int):  file descriptor for console
        opened (bool): True means .fd opened, False means .fd closed
        rxbs (bytearray): of received characters (bytes)

    Methods:
        reopen ():  closes and reopens .fd, sets .opened
        close ():   closes .fd unsets .opened
        get (): returns chars including newline but no more than bs characters
        put ():  puts characters

    Hidden:
        ._line is bytearray of line buffer

    """
    MaxBufSize = 256

    def __init__(self, bs=None):
        """
        Initialization method for instance.
        Creates attributes.
        """
        self.bs = bs if bs is not None else self.MaxBufSize
        self.fd = None  # console file descriptor needs to be opened
        self.opened =  False
        self.rxbs = bytearray()


    def open(self, port=''):
        """
        Opens fd on terminal console in non blocking mode.

        port is the serial port device path name
        or if '' then use os.ctermid() which
        returns path name of console usually '/dev/tty'

        os.O_NONBLOCK makes non blocking io
        os.O_RDWR allows both read and write.
        os.O_NOCTTY don't make this the controlling terminal of the process
        O_NOCTTY is only for cross platform portability BSD never makes it the
        controlling terminal

        Don't use print at same time since it will mess up non blocking reads.

        Works in both canonical and non-canonical input mode.
        In canonical mode, no chars are available to read until eol newline
        is entered and eol is included in the read characters.

        It appears that canonical mode is the default for fd console os.ctermid().
        For other serial port fds  the characters may be  available immediately.

        To debug use os.isatty(fd) which returns True if the file descriptor
        fd is open and connected to a tty-like device, else False.

        On UNIX/macOS systems uses os.ctermid() to get console
        On Windows systems uses console directly via msvcrt
        """
        if not port:
            system = platform.system()
            if system == 'Windows':
                # Windows doesn't need a specific port for console access via msvcrt
                port = None
            else:
                # Unix/macOS use ctermid
                port = os.ctermid()  # default to console

        try:
            if platform.system() == 'Windows':
                # Windows handling through msvcrt
                import msvcrt
                # For Windows, we'll use stdin/stdout file descriptors
                # and rely on msvcrt for non-blocking operations
                self.fd = 0  # Use 0 as a placeholder value for Windows console
                # Check if stdin is a terminal on Windows
                if not os.isatty(sys.stdin.fileno()):
                    logger.error("Error: stdin is not a terminal on Windows\n")
                    return False
                # No specific open operation needed for Windows console via msvcrt
            else:
                # Unix/macOS handling
                self.fd = os.open(port, os.O_NONBLOCK | os.O_RDWR | os.O_NOCTTY)
        except OSError as ex:
            logger.error("Error opening console serial port, %s\n", ex)
            return False

        self.opened = True
        return self.opened


    def reopen(self, **kwa):
        """
        Idempotently opens console
        """
        self.close()
        return self.open()


    def close(self):
        """
        Closes fd.
        """
        if self.fd:
            os.close(self.fd)
        self.fd = None
        del self.rxbs[:]
        self.opened = False


    def put(self, data = b'\n'):
        """
        Writes data bytes to console and return number of bytes from data written.
        """
        if platform.system() == 'Windows':
            # Windows-specific console output
            import msvcrt
            # Write bytes to stdout
            for b in data:
                msvcrt.putch(bytes([b]))
            return len(data)
        else:
            # Unix/macOS
            return os.write(self.fd, data)  # returns number of bytes written


    def get(self, bs=None):
        """
        Gets nonblocking line of bytes from console of up to bs characters
        including eol newline if in bs characters otherwise
        must repeat get until a newline appears.

        Returns empty string if no characters available else returns line.
        Works in both canonical and non-canonical mode
        In canonical mode, no chars are available to read until eol newline
        is entered and eol is included in the read characters.

        Strips eol newline before returning line.
        """
        bs = bs if bs is not None else self.bs
        line = bytearray()

        try:
            if platform.system() == 'Windows':
                # Windows-specific non-blocking read using msvcrt
                import msvcrt
                # Check if any keys are available
                while msvcrt.kbhit():
                    # Read a character and add it to our buffer
                    char = msvcrt.getch()
                    self.rxbs.extend(char)
            else:
                # Unix/macOS non-blocking read
                self.rxbs.extend(os.read(self.fd, bs))
        except OSError as ex1:  # if no chars available generates exception
            # ex.args[0] == ex.errno for better os compatibility
            # the value of a given errno.XXXXX may be different on each os
            # EAGAIN: BSD 35, Linux 11, Windows 11
            # EWOULDBLOCK: BSD 35 Linux 11 Windows 140
            if ex1.args[0] in (errno.EAGAIN, errno.EWOULDBLOCK):
                pass  # No characters available
            else:
                logger.error("Error: Get on Console '%s'."
                              " '%s'\n", self.fd, ex1)
                raise  # re-raise exception ex1

        # Process any complete lines in the buffer
        if (idx := self.rxbs.find(ord(b'\n'))) != -1:
            line.extend(self.rxbs[:idx])  # copy all but newline
            del self.rxbs[:idx+1]  # delete including newline
        elif platform.system() == 'Windows' and (idx := self.rxbs.find(ord(b'\r'))) != -1:
            # On Windows, handle CR as line terminator too
            line.extend(self.rxbs[:idx])  # copy all but CR
            del self.rxbs[:idx+1]  # delete including CR

        return line


    def service(self):
        """
        Service puts and gets
        """


class ConsoleDoer(doing.Doer):
    """
    Basic Console Doer. Wraps console in doer context so opens and closes console

    To test in WingIde must configure Debug I/O to use external console
    See Doer for inherited attributes, properties, and methods.

    Attributes:
       .console is serial Console instance

    """

    def __init__(self, console, **kwa):
        """
        Initialize instance.

        Parameters:
           console is serial Console instance

        """
        super(ConsoleDoer, self).__init__(**kwa)
        self.console = console


    def enter(self, *, temp=None):
        """Do 'enter' context actions. Override in subclass. Not a generator method.
        Set up resources. Comparable to context manager enter.

        Parameters:
            temp (bool | None): True means use temporary file resources if any
                                None means ignore parameter value. Use self.temp

        Inject temp or self.temp into file resources here if any

        Doist or DoDoer winds its doers on enter
        """
        # inject temp into file resources here if any
        result = self.console.reopen(temp=temp)


    def recur(self, tyme):
        """"""
        self.console.service()


    def exit(self):
        """"""
        self.console.close()


class EchoConsoleDoer(doing.Doer):
    """
    Basic Terminal Console IO to buffers. Echos input back to output

    To test in WingIde must configure Debug I/O to use external console

    See Doer for inherited attributes, properties, and methods.

    Attributes:
       .console is serial Console instance

    """

    def __init__(self, console, lines=None, txbs=None, **kwa):
        """
        Initialize instance.

        Parameters:
           console is serial Console instance
           lines is deque of input bytes bytearrays of each line from console
           txbs is ouput bytes bytearray to send to console

        """
        super(EchoConsoleDoer, self).__init__(**kwa)
        self.console = console
        self.lines = lines if lines is not None else deque()
        self.txbs = txbs if txbs is not None else bytearray()


    def enter(self, *, temp=None):
        """Do 'enter' context actions. Override in subclass. Not a generator method.
        Set up resources. Comparable to context manager enter.

        Parameters:
            temp (bool | None): True means use temporary file resources if any
                                None means ignore parameter value. Use self.temp

        Inject temp or self.temp into file resources here if any

        Doist or DoDoer winds its doers on enter
        """
        # inject temp into file resources here if any
        self.console.reopen(temp=temp)
        self.txbs.extend(b"Cmds: q=quit, h=help otherwise echoes.\n")
        self.txbs.extend(b"Type cmd & \n: ")


    def recur(self, tyme):
        """"""
        done = False
        prompt = False
        while self.lines:
            line = self.lines.popleft()
            #process line here
            if line == b'q':
                self.txbs.extend(b"Goodbye\n.")
                done = True  #  all done so indicate exit
                break

            elif line == b'h':
                self.txbs.extend(b"Help: type q to quit or h for help.\n")

            else:
                self.txbs.extend(b"Echo: %s\n" % line )

            prompt = True

        if prompt:
            self.txbs.extend(b"Type cmd & \n: ")


        if self.txbs:
            count =  self.console.put(self.txbs)  #  write
            del self.txbs[:count]

        line = self.console.get()  #  read
        if line:
            self.lines.append(line)


        return done  # keep going if done == False else ends

    def exit(self):
        """"""
        self.console.close()



class Device():
    """
    Class to manage non blocking IO on serial device port.

    Opens non blocking read file descriptor on serial port
    Use instance method close to close file descriptor
    Use instance methods get & put to read & write to serial device
    Needs os module
    """
    def __init__(self, port=None, speed=9600, bs=1024):
        """
        Initialization method for instance.

        port = serial device port path string
        speed = serial port speed in bps
        bs = buffer size for reads
        """
        self.fd = None  # serial device port file descriptor, must be opened first
        self.port = port

        if not self.port:
            system = platform.system()
            if system == 'Windows':
                self.port = 'COM1'  # Default Windows serial port
            else:
                self.port = os.ctermid()  # Default to console on Unix/macOS

        self.speed = speed or 9600
        self.bs = bs or 1024
        self.opened = False


    def reopen(self, port=None, speed=None, bs=None):
        """
        Idempotently open serial device port
        Opens fd on serial port in non blocking mode.

        port is the serial port device path name or
        if '' then use os.ctermid() which
        returns path name of console usually '/dev/tty'

        os.O_NONBLOCK makes non blocking io
        os.O_RDWR allows both read and write.
        os.O_NOCTTY don't make this the controlling terminal of the process
        O_NOCTTY is only for cross platform portability BSD never makes it the
        controlling terminal

        Don't use print and console at same time since it will mess up non blocking reads.

        The input mode, canonical or noncanonical, is controlled by the
        ICANON flag see termios module.

        Raw mode

        def setraw(fd, when=TCSAFLUSH):
            Put terminal into a raw mode.
            mode = tcgetattr(fd)
            mode[IFLAG] = mode[IFLAG] & ~(BRKINT | ICRNL | INPCK | ISTRIP | IXON)
            mode[OFLAG] = mode[OFLAG] & ~(OPOST)
            mode[CFLAG] = mode[CFLAG] & ~(CSIZE | PARENB)
            mode[CFLAG] = mode[CFLAG] | CS8
            mode[LFLAG] = mode[LFLAG] & ~(ECHO | ICANON | IEXTEN | ISIG)
            mode[CC][VMIN] = 1
            mode[CC][VTIME] = 0
            tcsetattr(fd, when, mode)


        # set up raw mode / no echo / binary
        cflag |=  (TERMIOS.CLOCAL|TERMIOS.CREAD)
        lflag &= ~(TERMIOS.ICANON|TERMIOS.ECHO|TERMIOS.ECHOE|TERMIOS.ECHOK|TERMIOS.ECHONL|
                     TERMIOS.ISIG|TERMIOS.IEXTEN) #|TERMIOS.ECHOPRT
        for flag in ('ECHOCTL', 'ECHOKE'): # netbsd workaround for Erk
            if hasattr(TERMIOS, flag):
                lflag &= ~getattr(TERMIOS, flag)

        oflag &= ~(TERMIOS.OPOST)
        iflag &= ~(TERMIOS.INLCR|TERMIOS.IGNCR|TERMIOS.ICRNL|TERMIOS.IGNBRK)
        if hasattr(TERMIOS, 'IUCLC'):
            iflag &= ~TERMIOS.IUCLC
        if hasattr(TERMIOS, 'PARMRK'):
            iflag &= ~TERMIOS.PARMRK

        """
        self.close()

        if port is not None:
            self.port = port
        if speed is not None:
            self.speed = speed
        if bs is not None:
            self.bs = bs

        system = platform.system()

        if system == 'Windows':
            try:
                # Try to use pyserial for COM ports on Windows for better handling
                import serial
                self._serial = serial.Serial(port=self.port,
                                        baudrate=self.speed,
                                        timeout=0)
                # Placeholder for fd
                self.fd = 0
            except ImportError:
                # Fall back to basic file operations if pyserial is not available
                self.fd = os.open(self.port, os.O_RDWR | os.O_BINARY)
                import msvcrt
                msvcrt.setmode(self.fd, os.O_BINARY)
                self._serial = None
        else:
            # Unix/macOS handling
            self.fd = os.open(self.port, os.O_NONBLOCK | os.O_RDWR | os.O_NOCTTY)
            self._serial = None

        if (system == 'Darwin') or (system == 'Linux'):  # use termios to set values
            import termios

            iflag, oflag, cflag, lflag, ispeed, ospeed, cc = range(7)

            settings = termios.tcgetattr(self.fd)
            #print(settings)

            settings[lflag] = (settings[lflag] & ~termios.ICANON)

            settings[lflag] = (settings[lflag] & ~termios.ECHO) # no echo

            #ignore carriage returns on input
            #settings[iflag] = (settings[iflag] | (termios.IGNCR)) #ignore cr

            # 8N1 8bit word no parity one stop bit nohardware handshake ctsrts
            # to set size have to mask out(clear) CSIZE bits and or in size
            settings[cflag] = ((settings[cflag] & ~termios.CSIZE) | termios.CS8)
            # no parity clear PARENB
            settings[cflag] = (settings[cflag] & ~termios.PARENB)
            #one stop bit clear CSTOPB
            settings[cflag] = (settings[cflag] & ~termios.CSTOPB)
            #no hardware handshake clear crtscts
            settings[cflag] = (settings[cflag] & ~termios.CRTSCTS)

            # in linux the speed flag does not equal value so always set it
            speedattr = "B{0}".format(self.speed)  # convert numeric speed to attribute name string
            speed = getattr(termios, speedattr)
            settings[ispeed] = speed
            settings[ospeed] = speed

            termios.tcsetattr(self.fd, termios.TCSANOW, settings)
            #print(settings)

        self.opened = True

        return self.opened



    def close(self):
        """
        Closes fd.
        """
        if self._serial:
            self._serial.close()
            self._serial = None

        if self.fd and platform.system() != 'Windows' or not self._serial:
            # Close fd if not Windows or if we didn't use pyserial
            os.close(self.fd)

        self.fd = None
        self.opened = False


    def receive(self):
        """
        Reads nonblocking characters from serial device up to bs characters
        Returns empty bytes if no characters available else returns all available.
        In canonical mode no chars are available until newline is entered.
        """
        data = b''
        try:
            if platform.system() == 'Windows':
                if self._serial:
                    # Use pyserial if available
                    data = self._serial.read(self.bs)
                else:
                    # Fall back to msvcrt for console
                    import msvcrt
                    if msvcrt.kbhit():
                        char = msvcrt.getch()
                        data = char
                    else:
                        data = os.read(self.fd, self.bs)
            else:
                # Unix/macOS read
                data = os.read(self.fd, self.bs)  #if no chars available generates exception
        except OSError as ex1:  # ex1 is the target instance of the exception
            # ex.args[0] == ex.errno for better os compatibility
            # the value of a given errno.XXXXX may be different on each os
            # EAGAIN: BSD 35, Linux 11, Windows 11
            # EWOULDBLOCK: BSD 35 Linux 11 Windows 140
            if ex1.args[0] in (errno.EAGAIN, errno.EWOULDBLOCK):
                pass #No characters available
            else:
                logger.error("Error: Receive on Device '%s'."
                              " '%s'\n", self.port, ex1)
                raise #re raise exception ex1

        return data

    def send(self, data=b'\n'):
        """
        Writes data bytes to serial device port.
        Returns number of bytes sent
        """
        try:
            if platform.system() == 'Windows' and self._serial:
                # Use pyserial if available
                count = self._serial.write(data)
            else:
                count = os.write(self.fd, data)
        except OSError as ex1:  # ex1 is the target instance of the exception
            # ex.args[0] == ex.errno for better os compatibility
            # the value of a given errno.XXXXX may be different on each os
            # EAGAIN: BSD 35, Linux 11, Windows 11
            # EWOULDBLOCK: BSD 35 Linux 11 Windows 140
            if ex1.args[0] in (errno.EAGAIN, errno.EWOULDBLOCK):
                count = 0  # buffer full can't write
            else:
                logger.error("Error: Send on Device '%s'."
                              " '%s'\n", self.port, ex1)
                raise #re raise exception ex1

        return count


class Serial():
    """
    Class to manage non blocking IO on serial device port using pyserial

    Opens non blocking read file descriptor on serial port
    Use instance method close to close file descriptor
    Use instance methods get & put to read & write to serial device
    Needs os module
    """
    def __init__(self, port=None, speed=9600, bs=1024):
        """
        Initialization method for instance.

        port = serial device port path string
        speed = serial port speed in bps
        bs = buffer size for reads


        """
        self.serial = None  # Serial instance
        self.port = port

        if not self.port:
            system = platform.system()
            if system == 'Windows':
                self.port = 'COM1'  # Default Windows serial port
            else:
                self.port = os.ctermid()  # Default to console on Unix/macOS

        self.speed = speed or 9600
        self.bs = bs or 1024
        self.opened = False


    def reopen(self, port=None, speed=None, bs=None):
        """
        Opens fd on serial port in non blocking mode.

        port is the serial port device path name or
        if None then use os.ctermid() which returns path name of console
        usually '/dev/tty'
        """
        self.close()

        if port is not None:
            self.port = port
        if speed is not None:
            self.speed = speed
        if bs is not None:
            self.bs = bs

        import serial  # import pyserial
        self.serial = serial.Serial(port=self.port,
                                    baudrate=self.speed,
                                    timeout=0,
                                    writeTimeout=0)
        #self.serial.nonblocking()
        self.serial.reset_input_buffer()
        self.opened = True

        return self.opened


    def close(self):
        """
        Closes .serial
        """
        if self.serial:
            self.serial.reset_output_buffer()
            self.serial.close()
            self.serial = None
            self.opened = False

    def receive(self):
        """
        Reads nonblocking characters from serial device up to bs characters
        Returns empty bytes if no characters available else returns all available.
        In canonical mode no chars are available until newline is entered.
        """
        data = b''
        try:
            data = self.serial.read(self.bs)  #if no chars available generates exception
        except OSError as ex1:  # ex1 is the target instance of the exception
            # ex.args[0] == ex.errno for better os compatibility
            # the value of a given errno.XXXXX may be different on each os
            # EAGAIN: BSD 35, Linux 11, Windows 11
            # EWOULDBLOCK: BSD 35 Linux 11 Windows 140
            if ex1.args[0] in (errno.EAGAIN, errno.EWOULDBLOCK):
                pass #No characters available
            else:
                logger.error("Error: Receive on Serial '%s'."
                              " '%s'\n", self.port, ex1)
                raise #re raise exception ex1

        return data

    def send(self, data=b'\n'):
        """
        Writes data bytes to serial device port.
        Returns number of bytes sent
        """
        try:
            count = self.serial.write(data)
        except OSError as ex1:  # ex1 is the target instance of the exception
            # ex.args[0] == ex.errno for better os compatibility
            # the value of a given errno.XXXXX may be different on each os
            # EAGAIN: BSD 35, Linux 11, Windows 11
            # EWOULDBLOCK: BSD 35 Linux 11 Windows 140
            if ex1.args[0] in (errno.EAGAIN, errno.EWOULDBLOCK):
                count = 0  # buffer full can't write
            else:
                logger.error("Error: Send on Serial '%s'."
                              " '%s'\n", self.port, ex1)
                raise #re raise exception ex1

        return count



class Driver():
    """
    Nonblocking Serial Device Port Driver
    """

    def __init__(self,
                 name=u'',
                 uid=0,
                 port=None,
                 speed=9600,
                 bs=1024,
                 server=None):
        """
        Initialization method for instance.

        Parameters:
            name = user friendly name for driver
            uid = unique identifier for driver
            port = serial device port path string
            speed = serial port speed in bps
            canonical = canonical mode True or False
            bs = buffer size for reads
            server = serial port device server if any

        Attributes:
           name = user friendly name for driver
           uid = unique identifier for driver
           server = serial device server nonblocking
           txbs = bytearray of data bytes to send
           rxbs = bytearray of data bytes received

        """
        self.name = name
        self.uid = uid

        if not server:
            try:
                import serial
                self.server = Serial(port=port,
                                       speed=speed,
                                       bs=bs)

            except ImportError as  ex:
                logger.error("Error: importing pyserial\n%s\n", ex)
                self.server = Device(port=port,
                                       speed=speed,
                                       bs=bs)
        else:
            self.server = server

        self.txbs = bytearray()  # bytearray of data to send
        self.rxbs = bytearray()  # bytearray of data received


    def serviceReceives(self):
        """
        Service receives until no more
        """
        while self.server.opened:
            data = self.server.receive()  # bytes
            if not data:
                break
            self.rxbs.extend(data)


    def clearRxbs(self):
        """
        Clear .rxbs
        """
        del self.rxbs[:]


    def scan(self, start):
        """
        Returns offset of given start byte in self.rxbs
        Returns None if start is not given or not found
        If strip then remove any bytes before offset
        """
        offset = self.rxbs.find(start)
        if offset < 0:
            return None
        return offset


    def send(self, data):
        """
        Handle one tx data
        """
        count = self.server.send(data)
        return count


    def tx(self, data):
        """
        Queue data onto .txbs
        """
        self.txbs.extend(data)


    def serviceSends(self):
        """
        Service .txbs
        """
        while self.txbs and self.server.opened:
            count = self.send(self.txbs)
            del self.txbs[:count]
            break  # try again later


    def service(self):
        """
        Sevice receives and sends
        """
        self.serviceReceives()
        self.serviceSends()


