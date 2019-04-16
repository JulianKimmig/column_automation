from arduino_controller.portcommand import PortCommand
from basicboard.board import ArduinoBasicBoard

from boards.RAMPS_14_AccelStepper import arduino_data


class RAMPS_14_AccelStepper(ArduinoBasicBoard):
    FIRMWARE = 4

    def __init__(self):
        super().__init__()
        self.save_attributes.update(
            {
                "position": "double",
                "steps_per_mm": "double",
                "max_mm_sec": "double",
                "acceleration": "double",
            }
        )
        self._position = [0, 0, 0]
        self._steps_per_mm = [1600, 1600, 1600]
        self._max_mm_sec = [5, 5, 1]
        self._acceleration = [1, 1, 1]
        self.addPortCommands()

        self.inocreator.add_creator(arduino_data.create)

    def addPortCommands(self):
        self.add_port_command(
            PortCommand(
                module=self,
                name="x_move_to",
                receivetype="q",
                sendtype="q",
                receivefunction=lambda data: 0,
                arduino_code="int32_t temp;memcpy(&temp,data,4);motor_x.moveTo(temp);",
            )
        )
        self.add_port_command(
            PortCommand(
                module=self,
                name="y_move_to",
                receivetype="q",
                sendtype="q",
                receivefunction=lambda data: 0,
                arduino_code="int32_t temp;memcpy(&temp,data,4);motor_y.moveTo(temp);",
            )
        )
        self.add_port_command(
            PortCommand(
                module=self,
                name="z_move_to",
                receivetype="l",
                sendtype="l",
                receivefunction=lambda data: 0,
                arduino_code="int32_t temp;memcpy(&temp,data,4);motor_z.moveTo(temp);",
            )
        )
        self.add_port_command(
            PortCommand(
                module=self,
                name="x_set_max_speed",
                receivetype="f",
                sendtype="f",
                receivefunction=lambda data: 0,
                arduino_code="float temp;memcpy(&temp,data,4);motor_x.setMaxSpeed(temp);",
            )
        )
        self.add_port_command(
            PortCommand(
                module=self,
                name="y_set_max_speed",
                receivetype="f",
                sendtype="f",
                receivefunction=lambda data: 0,
                arduino_code="float temp;memcpy(&temp,data,4);motor_y.setMaxSpeed(temp);",
            )
        )
        self.add_port_command(
            PortCommand(
                module=self,
                name="z_set_max_speed",
                receivetype="f",
                sendtype="f",
                receivefunction=lambda data: 0,
                arduino_code="float temp;memcpy(&temp,data,4);motor_z.setMaxSpeed(temp);",
            )
        )

        self.add_port_command(
            PortCommand(
                module=self,
                name="x_set_acceleration",
                receivetype="f",
                sendtype="f",
                receivefunction=lambda data: 0,
                arduino_code="float temp;memcpy(&temp,data,4);motor_x.setAcceleration(temp);",
            )
        )
        self.add_port_command(
            PortCommand(
                module=self,
                name="y_set_acceleration",
                receivetype="f",
                sendtype="f",
                receivefunction=lambda data: 0,
                arduino_code="float temp;memcpy(&temp,data,4);motor_y.setAcceleration(temp);",
            )
        )
        self.add_port_command(
            PortCommand(
                module=self,
                name="z_set_acceleration",
                receivetype="f",
                sendtype="f",
                receivefunction=lambda data: 0,
                arduino_code="float temp;memcpy(&temp,data,4);motor_z.setAcceleration(temp);",
            )
        )

        def receive_position_x(data):
            self.set_position(
                [data / self._steps_per_mm[0], self._position[1], self._position[2]],
                to_board=False,
            )
            if self.identified:
                self.serialport.data_to_socket(
                    key=str(self.id) + "_position_x",
                    y=data / self._steps_per_mm[0],
                    x=None,
                )

        self.add_port_command(
            PortCommand(
                module=self,
                name="x_set_position",
                receivetype="l",
                sendtype="l",
                receivefunction=receive_position_x,
                arduino_code="int32_t temp;memcpy(&temp,data,4);motor_x.setCurrentPosition(temp);",
            )
        )

        def receive_position_y(data):
            self.set_position(
                [self._position[0], data / self._steps_per_mm[1], self._position[2]],
                to_board=False,
            )
            if self.identified:
                self.serialport.data_to_socket(
                    key=str(self.id) + "_position_y",
                    y=data / self._steps_per_mm[1],
                    x=None,
                )

        self.add_port_command(
            PortCommand(
                module=self,
                name="y_set_position",
                receivetype="l",
                sendtype="l",
                receivefunction=receive_position_y,
                arduino_code="int32_t temp;memcpy(&temp,data,4);motor_y.setCurrentPosition(temp);",
            )
        )

        def receive_position_z(data):
            self.set_position(
                [self._position[0], self._position[1], data / self._steps_per_mm[2]],
                to_board=False,
            )
            if self.identified:
                self.serialport.data_to_socket(
                    key=str(self.id) + "_position_z",
                    y=data / self._steps_per_mm[2],
                    x=None,
                )

        self.add_port_command(
            PortCommand(
                module=self,
                name="z_set_position",
                receivetype="l",
                sendtype="l",
                receivefunction=receive_position_z,
                arduino_code="float temp;memcpy(&temp,data,4);motor_z.setCurrentPosition(temp);",
            )
        )

    def set_position(self, xyz, to_board=True):
        try:
            if len(xyz) > 3:
                xyz = xyz[:3]
            elif len(xyz) < 3:
                xyz = (list(xyz) + [0, 0, 0])[:3]
        except:
            xyz = [0, 0, 0]
        steps = [
            int(self.steps_per_mm[0] * xyz[0]),
            int(self.steps_per_mm[1] * xyz[1]),
            int(self.steps_per_mm[2] * xyz[2]),
        ]

        if self._position[0] != xyz[0]:
            self.serialport.logger.info("set x: " + str(xyz[0]))
            if to_board:
                self.get_portcommand_by_name("x_set_position").sendfunction(steps[0])
        if self._position[1] != xyz[1]:
            self.serialport.logger.info("set y: " + str(xyz[1]))
            if to_board:
                self.get_portcommand_by_name("y_set_position").sendfunction(steps[1])
        if self._position[2] != xyz[2]:
            self.serialport.logger.info("set z: " + str(xyz[2]))
            if to_board:
                self.get_portcommand_by_name("z_set_position").sendfunction(
                    int(steps[2])
                )
        self._position = xyz

    def move_to(self, xyz, to_board=True):
        steps = [
            int(self.steps_per_mm[0] * xyz[0]),
            int(self.steps_per_mm[1] * xyz[1]),
            int(self.steps_per_mm[2] * xyz[2]),
        ]
        if self._position[0] != xyz[0]:
            self.serialport.logger.info("move to x: " + str(xyz[0]))
            if to_board:
                self.get_portcommand_by_name("x_move_to").sendfunction(int(steps[0]))
        if self._position[1] != xyz[1]:
            self.serialport.logger.info("move to y: " + str(xyz[1]))
            if to_board:
                self.get_portcommand_by_name("y_move_to").sendfunction(int(steps[1]))
        if self._position[2] != xyz[2]:
            self.serialport.logger.info("move to z: " + str(xyz[2]))
            if to_board:
                self.get_portcommand_by_name("z_move_to").sendfunction(int(steps[2]))

    def get_position(self):
        return self._position

    def get_steps_per_mm(self):
        return self._steps_per_mm

    def set_steps_per_mm(self, steps_per_mm):
        self._steps_per_mm = steps_per_mm

    def get_max_mm_sec(self):
        return self._max_mm_sec

    def get_acceleration(self):
        return self._acceleration

    def set_max_mm_sec(self, max_mm_sec, to_board=True):
        max_steps_sec = [
            self.steps_per_mm[0] * max_mm_sec[0],
            self.steps_per_mm[1] * max_mm_sec[1],
            self.steps_per_mm[2] * max_mm_sec[2],
        ]
        if self._max_mm_sec[0] != max_mm_sec[0]:
            self.serialport.logger.info("set x speed: " + str(max_mm_sec[0]))
            if to_board:
                self.get_portcommand_by_name("x_set_max_speed").sendfunction(
                    max_steps_sec[0]
                )
        if self._max_mm_sec[1] != max_mm_sec[1]:
            self.serialport.logger.info("set y speed: " + str(max_mm_sec[1]))
            if to_board:
                self.get_portcommand_by_name("y_set_max_speed").sendfunction(
                    max_steps_sec[1]
                )
        if self._max_mm_sec[2] != max_mm_sec[2]:
            self.serialport.logger.info("set z speed: " + str(max_mm_sec[2]))
            if to_board:
                self.get_portcommand_by_name("z_set_max_speed").sendfunction(
                    max_steps_sec[2]
                )
        self._max_mm_sec = max_mm_sec

    def set_acceleration(self, acceleration, to_board=True):
        steps_acceleration = [
            self.steps_per_mm[0] * acceleration[0],
            self.steps_per_mm[1] * acceleration[1],
            self.steps_per_mm[2] * acceleration[2],
        ]
        if self._acceleration[0] != acceleration[0]:
            self.serialport.logger.info("set x acceleration: " + str(acceleration[0]))
            if to_board:
                self.get_portcommand_by_name("x_set_acceleration").sendfunction(
                    steps_acceleration[0]
                )
        if self._acceleration[1] != acceleration[1]:
            self.serialport.logger.info("set y acceleration: " + str(acceleration[1]))
            if to_board:
                self.get_portcommand_by_name("y_set_acceleration").sendfunction(
                    steps_acceleration[1]
                )
        if self._acceleration[2] != acceleration[2]:
            self.serialport.logger.info("set z acceleration: " + str(acceleration[2]))
            if to_board:
                self.get_portcommand_by_name("z_set_acceleration").sendfunction(
                    steps_acceleration[2]
                )
        self._acceleration = acceleration

    position = property(get_position, set_position)
    steps_per_mm = property(get_steps_per_mm, set_steps_per_mm)
    max_mm_sec = property(get_max_mm_sec, set_max_mm_sec)
    acceleration = property(get_acceleration, set_acceleration)


if __name__ == "__main__":
    import inspect
    import os

    ins = RAMPS_14_AccelStepper()
    ino = ins.inocreator.create()
    dir = os.path.dirname(inspect.getfile(ins.__class__))
    name = os.path.basename(dir)
    with open(os.path.join(dir, name + ".ino"), "w+") as f:
        f.write(ino)
