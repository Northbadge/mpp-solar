# shamelessly stolen from ccrisan https://github.com/qtoggle/qtoggleserver-mppsolar/blob/master/qtoggleserver/mppsolar/io.py
import abc
import logging

# from time import sleep
log = logging.getLogger("MPP-Solar")


class BaseIO(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def send_and_receive(self, full_command) -> dict:
        raise NotImplementedError
