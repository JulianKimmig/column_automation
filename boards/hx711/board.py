from arduino_controller.portcommand import PortCommand
from basicboard.board import ArduinoBasicBoard

from boards.hx711 import arduino_data


class HX711(ArduinoBasicBoard):
    FIRMWARE = 6

    def __init__(self):
        super().__init__()
        self.add_pin("dout", 2)
        self.add_pin("sck", 3)
        self.gain = 32
        self.inocreator.add_creator(arduino_data.create)
        self.add_port_command(
            PortCommand(
                module=self,
                name="read_data",
                receivetype="l",
                sendtype="B",
                receivefunction=self.datapoint,
                byteid=self.firstfreebyteid,
                arduino_code="write_data(hx711.read_average(average),{BYTEID});",
            )
        )


if __name__ == "__main__":
    import inspect
    import os

    ins = HX711()

    ino = ins.inocreator.create()
    dir = os.path.dirname(inspect.getfile(ins.__class__))
    name = os.path.basename(dir)
    with open(os.path.join(dir, name + ".ino"), "w+") as f:
        f.write(ino)
