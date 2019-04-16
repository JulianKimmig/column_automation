import logging
import os
import time

from json_dict import JsonDict
from websocket_communication_server.messagetemplates import (
    commandmessage,
    datapointmessage,
)
from websocket_communication_server.socketclient import WebSocketClient

class ArduinoControllerAPI():
    def __init__(self, name="arduinocontrollerapi", sockethost=8888,basedir=os.getcwd()):
        self.basedir = basedir
        self.name = name
        self.data = {}
        self.dataupdate = 1
        self.lastupdate = 0

        self.logger = logging.getLogger(self.name)
        self.ws = WebSocketClient(
            logger=self.logger, name=self.name, host=sockethost
        )
        print(basedir)
        self.config = JsonDict(
            file=os.path.join(basedir, "config.json"), createfile=True
        )
        self.config.autosave = True

        self.sensor_ports = set([])

        self.ws.add_cmd_function("set_ports", self.set_ports)
        self.ws.add_cmd_function("add_sensor_port", self.add_sensor_port)
        self.ws.add_cmd_function("get_data", self.get_data)
        self.ws.add_message_type("data", self.data_validator)
        self.ws.add_cmd_function("boardupdate", self.boardupdate)

    def set_ports(self, connected_ports=None):
        if connected_ports is None:
            connected_ports = []
        for port in connected_ports:
            if port not in self.sensor_ports:
                self.add_sensor_port(port)

    def add_sensor_port(self, port=None):
        if port is not None:
            self.sensor_ports.add(port)
            self.ws.write_to_socket(
                commandmessage(
                    cmd="add_data_target",
                    sender=self.name,
                    target=port,
                    data_target=self.name,
                )
            )
            self.ws.write_to_socket(
                commandmessage(
                    cmd="remove_data_target",
                    sender=self.name,
                    target=port,
                    data_target="gui",
                )
            )

    def data_validator(self, message):
        if not message["data"]["key"] in self.data:
            self.data[message["data"]["key"]] = []
        self.data[message["data"]["key"]].append([message["data"]["x"], message["data"]["y"], message["data"]["t"]])

        t = time.time()
        if t - self.lastupdate > self.dataupdate:
            self.lastupdate = t
            for key, dates in self.data.items():
                self.ws.write_to_socket(
                    datapointmessage(
                        sender=self.name,
                        x=dates[-1][0],
                        y=dates[-1][1],
                        key=key,
                        target="gui",
                        t=dates[-1][2],
                        as_string=True,
                    )
                )
            return True
        return False

    def get_data(self, data_target=None, timestep=None):
        if data_target is None: return
        self.ws.write_to_socket(
            commandmessage(
                sender=self.name,
                cmd="set_data",
                target=data_target,
                as_string=True,
                data=self.data,
            )
        )

    def boardupdate(self, boarddata=None):
        if boarddata is None:
            return

    def ask_for_ports(self):
        self.ws.write_to_socket(
            commandmessage(
                cmd="get_ports",
                sender=self.name,
                target="serialreader",
                data_target=self.name,
            )
        )

    def start(self):
        while 1:
            self.ask_for_ports()
            time.sleep(3)


POSSIBLE_MOTOR_FIRMWARES = [4]


class ColumnAutomate(ArduinoControllerAPI):
    def __init__(self, sockethost=8888):
        super().__init__(name="columnautomate", sockethost=sockethost,basedir=os.path.abspath(os.path.dirname(__file__)))
        self.switchxy = True
        self.iverty = True
        self.ivertx = False
        self.vials_x = 1
        self.vials_y = 1
        self.vials_dist = 30
        self.motor_port = None
        self.homeposition = (0, 0)
        self.x = 0
        self.y = 0

        self.ws.add_cmd_function("set_motor_port", self.set_motor_port)
        self.ws.add_cmd_function("get_frame_size", self.get_frame_size)
        self.ws.add_cmd_function("set_frame_size", self.set_frame_size)
        self.ws.add_cmd_function("move_to", self.move_to)
        self.ws.add_cmd_function("set_position", self.set_position)
        self.ws.add_cmd_function("set_steps_per_mm", self.set_steps_per_mm)
        self.ws.add_cmd_function("set_acceleration", self.set_acceleration)
        self.ws.add_cmd_function("set_max_mm_sec", self.set_max_mm_sec)
        self.ws.add_cmd_function("add_vial", self.add_vial)
        self.ws.add_cmd_function("remove_vial", self.remove_vial)
        self.ws.add_cmd_function("get_vials", self.get_vials)

    def get_vials(self, data_target="gui"):
        self.ws.write_to_socket(
            commandmessage(
                cmd="set_vials",
                sender=self.name,
                target=data_target,
                vials=self.config.get("vials", default=[]),
            )
        )

    def add_vial(self, x=None, y=None, position=None):
        if x is None or y is None:
            return
        if position is None:
            position = len(self.config.get("vials", default=[]))
        self.config.get("vials", default=[]).insert(position, {"x": x, "y": y})
        self.config.save()

    def remove_vial(self, position=None):
        if position is None:
            return
        try:
            del self.config.get("vials", default=[])[position]
            self.config.save()
        except:
            self.logger.exception(Exception)

    def set_max_mm_sec(self, max_mm_sec=None):
        if max_mm_sec is None or self.motor_port is None:
            return
        self.ws.write_to_socket(
            commandmessage(
                cmd="boardfunction",
                board_cmd="set_max_mm_sec",
                sender=self.name,
                target=self.motor_port,
                max_mm_sec=[max_mm_sec, max_mm_sec, 10],
            )
        )

    def set_acceleration(self, acceleration=None):
        if acceleration is None or self.motor_port is None:
            return
        self.ws.write_to_socket(
            commandmessage(
                cmd="boardfunction",
                board_cmd="set_acceleration",
                sender=self.name,
                target=self.motor_port,
                acceleration=[acceleration, acceleration, 1],
            )
        )

    def set_steps_per_mm(self, steps_per_mm=None):
        if steps_per_mm is None or self.motor_port is None:
            return
        self.ws.write_to_socket(
            commandmessage(
                cmd="boardfunction",
                board_cmd="set_steps_per_mm",
                sender=self.name,
                target=self.motor_port,
                steps_per_mm=[steps_per_mm, steps_per_mm, 200],
            )
        )

    def get_frame_size(self, data_target="gui"):
        self.ws.write_to_socket(
            commandmessage(
                cmd="set_frame_size",
                sender=self.name,
                target=data_target,
                width=self.config.get("frame", "size", "width", default=100),
                height=self.config.get("frame", "size", "height", default=100),
                savedist=self.config.get("frame", "savedist", default=0),
            )
        )

    def set_frame_size(self, width=100, height=100, savedist=0):
        self.config.put("frame", "size", "width", value=width)
        self.config.put("frame", "size", "height", value=height)
        self.config.put("frame", "savedist", value=savedist)

    def boardupdate(self, boarddata=None):
        super().boardupdate()
        if boarddata is None:
            return

        if self.motor_port is None:
            if boarddata["fw"] in POSSIBLE_MOTOR_FIRMWARES:
                self.set_motor_port(boarddata["port"])

        if self.motor_port == boarddata["port"]:
            try:
                self.ws.write_to_socket(
                    commandmessage(
                        cmd="set_acceleration",
                        sender=self.name,
                        target="gui",
                        acceleration=list(boarddata["acceleration"])[0],
                    )
                )
                self.ws.write_to_socket(
                    commandmessage(
                        cmd="set_steps_per_mm",
                        sender=self.name,
                        target="gui",
                        steps_per_mm=list(boarddata["steps_per_mm"])[0],
                    )
                )
                self.ws.write_to_socket(
                    commandmessage(
                        cmd="set_max_mm_sec",
                        sender=self.name,
                        target="gui",
                        max_mm_sec=list(boarddata["max_mm_sec"])[0],
                    )
                )
            except:
                self.logger.exception(Exception)

    def data_validator(self, message):
        if message["from"] == self.motor_port:
            if message["data"]["key"].endswith("position_x"):
                if self.switchxy:
                    self.y = message["data"]["y"] * (-1 if self.ivertx else 1)
                else:
                    self.x = message["data"]["y"] * (-1 if self.ivertx else 1)
            elif message["data"]["key"].endswith("position_y"):
                if self.switchxy:
                    self.x = message["data"]["y"] * (-1 if self.iverty else 1)
                else:
                    self.y = message["data"]["y"] * (-1 if self.iverty else 1)

        if super().data_validator(message):
            self.ws.write_to_socket(
                datapointmessage(
                    sender=self.name,
                    x=0.5 * (self.x + self.y),
                    y=0.5 * (self.x - self.y),
                    key="motorposition",
                    target="gui",
                    t=t,
                    as_string=True,
                )
            )
            return True
        return False

    def set_position(self, x, y):
        if self.motor_port is None:
            return
        if self.switchxy:
            x, y = y * (-1 if self.iverty else 1), x * (-1 if self.ivertx else 1)
        self.ws.write_to_socket(
            commandmessage(
                cmd="boardfunction",
                sender=self.name,
                target=self.motor_port,
                **dict(board_cmd="set_position", xyz=[x + y, x - y, 0])
            )
        )

    def move_to(self, x, y):
        if self.motor_port is None:
            return

        w = self.config.get("frame", "size", "width", default=400)
        h = self.config.get("frame", "size", "height", default=400)
        sd = self.config.get("frame", "savedist", default=0)
        x = min(max(sd, x), w - sd)
        y = min(max(sd, y), h - sd)

        if self.switchxy:
            x, y = y * (-1 if self.iverty else 1), x * (-1 if self.ivertx else 1)
        self.ws.write_to_socket(
            commandmessage(
                cmd="boardfunction",
                sender=self.name,
                target=self.motor_port,
                **dict(board_cmd="move_to", xyz=[x + y, x - y, 0])
            )
        )

    def set_motor_port(self, motor_port=None):
        if motor_port is not None:
            self.motor_port = motor_port
            self.add_sensor_port(motor_port)


if __name__ == "__main__":
    ca = ColumnAutomate()
    ca.set_vials_x(4)
    ca.set_vials_y(3)
    for i in range(ca.vials_x * ca.vials_y):
        print(ca.move_to_vial(i))
