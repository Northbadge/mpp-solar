import abc
import importlib
import logging

log = logging.getLogger("MPP-Solar")

PORT_TYPE_TEST = 1
PORT_TYPE_USB = 2
PORT_TYPE_ESP32 = 4
PORT_TYPE_SERIAL = 8
PORT_TYPE_JKBLE = 16


class AbstractDevice(metaclass=abc.ABCMeta):
    """
    Abstract device class
    """

    def __init__(self, *args, **kwargs):
        self._protocol = None
        self._protocol_class = None
        self._port = None

    @abc.abstractmethod
    def __str__(self):
        raise NotImplementedError

    def is_test_device(self, serial_device):
        return "test" in serial_device.lower()

    def is_directusb_device(self, serial_device):
        """
        Determine if this instance is using direct USB connection
        (instead of a serial connection)
        """
        if not serial_device:
            return False
        if "hidraw" in serial_device:
            log.debug("Device matches hidraw")
            return True
        if "mppsolar" in serial_device:
            log.debug("Device matches mppsolar")
            return True
        return False

    def is_ESP32_device(self, serial_device):
        return "esp" in serial_device.lower()

    def is_JKBle_device(self, serial_device):
        """
        Current all MAC addresses will be JK BLE devices
        """
        # '3c:a5:09:0a:85:79'
        return ":" in serial_device.lower()

    def get_port_type(self, port):
        if self.is_test_device(port):
            return PORT_TYPE_TEST
        elif self.is_directusb_device(port):
            return PORT_TYPE_USB
        elif self.is_ESP32_device(port):
            return PORT_TYPE_ESP32
        elif self.is_JKBle_device(port):
            return PORT_TYPE_JKBLE
        else:
            return PORT_TYPE_SERIAL

    def set_protocol(self, protocol=None):
        """
        Set the protocol for this device
        """
        log.debug(f"device.set_protocol with protocol {protocol}")
        if protocol is None:
            self._protocol = None
            self._protocol_class = None
            return
        protocol_id = protocol.lower()
        # Try to import the protocol module with the supplied name (may not exist)
        try:
            proto_module = importlib.import_module("mppsolar.protocols." + protocol_id, ".")
        except ModuleNotFoundError:
            log.error(f"No module found for protocol {protocol_id}")
            self._protocol = None
            self._protocol_class = None
            return
        # Find the protocol class - classname must be the same as the protocol_id
        try:
            self._protocol_class = getattr(proto_module, protocol_id)
        except AttributeError:
            log.error(f"Module {proto_module} has no attribute {protocol_id}")
            self._protocol = None
            self._protocol_class = None
            return
        # Instantiate the class
        # TODO: fix protocol instantiate
        self._protocol = self._protocol_class("init_var", proto_keyword="value", second_keyword=123)

    def set_port(self, port=None, baud=2400):
        port_type = self.get_port_type(port)
        if port_type == PORT_TYPE_TEST:
            log.info("Using testio for communications")
            from mppsolar.io.testio import TestIO

            self._port = TestIO()
        elif port_type == PORT_TYPE_USB:
            log.info("Using hidrawio for communications")
            from mppsolar.io.hidrawio import HIDRawIO

            self._port = HIDRawIO(device_path=port)
        elif port_type == PORT_TYPE_ESP32:
            log.info("Using esp32io for communications")
            from mppsolar.io.esp32io import ESP32IO

            self._port = ESP32IO(device_path=port)
        elif port_type == PORT_TYPE_JKBLE:
            log.info("Using jkbleio for communications")
            from mppsolar.io.jkbleio import JkBleIO

            self._port = JkBleIO(device_path=port)
        elif port_type == PORT_TYPE_SERIAL:
            log.info("Using serialio for communications")
            from mppsolar.io.serialio import SerialIO

            self._port = SerialIO(device_path=port, serial_baud=baud)
        else:
            self._port = None

    def list_commands(self):
        # print(f"{'Parameter':<30}\t{'Value':<15} Unit")
        if self._protocol is None:
            log.error("Attempted to list commands with no protocol defined")
            return {"ERROR": ["Attempted to list commands with no protocol defined", ""]}
        result = {}
        for command in self._protocol.COMMANDS:
            result[command] = [self._protocol.COMMANDS[command]["description"], ""]
        return result

    def run_commands(self, commands) -> dict:
        """
        Run multiple commands sequentially
        :param commands: List of commands to run, either with or without an alias.
        If an alias is provided, it will be substituted in place of cmd name in the returned dict
        Additional elements in the tuple will be passed to run_command as ordered
        Example: ['QPIWS', ...] or [('QPIWS', 'ALIAS'), ...] or [('QPIWS', 'ALIAS', True), ...] or mix and match
        :return: Dictionary of responses
        """
        responses = {}
        for i, command in enumerate(commands):
            if isinstance(command, str):
                responses[command] = self.run_command(command)
            elif isinstance(command, tuple) and len(command) > 0:
                if len(command) == 1:  # Treat as string
                    responses[command[0]] = self.run_command(command[0])
                elif len(command) == 2:
                    responses[command[1]] = self.run_command(command[0])
                else:
                    responses[command[1]] = self.run_command(command[0], *command[2:])
            else:
                responses["Command {:d}".format(i)] = {"ERROR": ["Unknown command format", "(Indexed from 0)"]}
        return responses

    @abc.abstractmethod
    def run_command(self, command, show_raw=False):
        raise NotImplementedError

    @abc.abstractmethod
    def get_status(self, show_raw):
        raise NotImplementedError

    @abc.abstractmethod
    def get_settings(self, show_raw):
        raise NotImplementedError

    def run_default_command(self, show_raw):
        return self.run_command(command=self._protocol.DEFAULT_COMMAND, show_raw=show_raw)
