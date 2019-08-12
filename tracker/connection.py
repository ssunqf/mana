import logging
import socket
from tracker.logger import MyLogger


class Connection:
    def __init__(self, hostname, port):
        self.hostname = hostname
        self.port = port
        self.sock = self.connect(self.hostname, self.port)

    def connect(self, hostname, port):
        # create socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # connect socket
            sock.connect((self.hostname, self.port))
        except Exception as e:
            # handle socket connection error
            MyLogger.log(
                "Tracker udp://{0}:{1} down falling back to udp://tracker.coppersurfer.tk".format(hostname, port),
                logging.WARNING)
            sock.close()
        return sock

    def close(self):
        """
        Closes a socket connection gracefully
        :return: None
        """
        self.sock.close()
