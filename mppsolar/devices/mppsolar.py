import logging

from .device import AbstractDevice

log = logging.getLogger("MPP-Solar")


class mppsolar(AbstractDevice):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__()
        self._name = kwargs["name"]
        self.set_port(**kwargs)
        self.set_protocol(**kwargs)
        log.debug(
            f"mppsolar __init__ name {self._name}, port {self._port}, protocol {self._protocol}"
        )
        log.debug(f"mppsolar __init__ args {args}")
        log.debug(f"mppsolar __init__ kwargs {kwargs}")

    def __str__(self):
        """
        Build a printable representation of this class
        """
        return (
            f"mppsolar device - name: {self._name}, port: {self._port}, protocol: {self._protocol}"
        )

    def run_command(self, command, show_raw=False) -> dict:
        """
        mpp-solar specific method of running a 'raw' command, e.g. QPI or PI
        """
        log.info(f"Running command {command}")
        # TODO: implement protocol self determiniation??
        if self._protocol is None:
            log.error("Attempted to run command with no protocol defined")
            return {"ERROR": ["Attempted to run command with no protocol defined", ""]}
        if self._port is None:
            log.error(f"No communications port defined - unable to run command {command}")
            return {
                "ERROR": [
                    f"No communications port defined - unable to run command {command}",
                    "",
                ]
            }

        response = self._port.send_and_receive(command, show_raw, self._protocol)
        log.debug(f"Send and Receive Response {response}")
        return response

    def get_status(self, show_raw) -> dict:
        # Run all the commands that are defined as status from the protocol definition
        data = {}
        for command in self._protocol.STATUS_COMMANDS:
            data.update(self.run_command(command))
        return data

    def get_settings(self, show_raw) -> dict:
        # Run all the commands that are defined as settings from the protocol definition
        data = {}
        for command in self._protocol.SETTINGS_COMMANDS:
            data.update(self.run_command(command))
        return data
