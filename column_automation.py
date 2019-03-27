import logging
import os
import time

from json_dict.json_dict import JsonDict
from websocket_communication_server.messagetemplates import commandmessage, datapointmessage
from websocket_communication_server.socketclient import WebSocketClient

POSSIBLE_MOTOR_FIRMWARES = [4]
BASEDIR = os.path.abspath(os.path.dirname(__file__))


class ColumnAutomate():
    def __init__(self, sockethost=8888):
        self.vials_x = 1
        self.vials_y = 1
        self.vials_dist = 30
        self.time = 0
        self.motor_port = None
        self.homeposition = (0, 0)
        self.sensor_ports = set([])
        self.x = 0
        self.y = 0

        self.dataupdate = 0.5
        self.lastupdate = 0

        self.logger = logging.getLogger("ColumnAutomate")
        self.ws = WebSocketClient(logger=self.logger, name='columnautomate',host=sockethost)
        #self.ws.add_on_message(self.ws.default_messagevalidator)
        #self.ws.connect_to_socket("ws://127.0.0.1:" + str(socketport))
        self.ws.add_cmd_function("move_to_vial", self.move_to_vial)
        self.ws.add_cmd_function("set_vials_x", self.set_vials_x)
        self.ws.add_cmd_function("set_vials_y", self.set_vials_y)
        self.ws.add_cmd_function("set_vials_dist", self.set_vials_dist)

        self.ws.add_cmd_function("set_motor_port", self.motor_port)
        self.ws.add_cmd_function("set_time", self.set_time)
        self.ws.add_cmd_function("add_sensor_port", self.add_sensor_port)
        self.ws.add_cmd_function("set_ports", self.set_ports)
        self.ws.add_cmd_function("boardupdate", self.boardupdate)
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
        #    self.ws.add_cmd_function("set_top_image", self.set_top_image)
        #    self.ws.add_cmd_function("set_corner_points", self.set_corner_points)
        #    self.ws.add_cmd_function("get_top_image", self.get_top_image)

        self.ws.add_message_type("data", self.data_validator)
        self.config = JsonDict(file=os.path.join(BASEDIR, "config.json"), createfile=True)
        self.config.autosave = True

    def get_vials(self, data_target="gui"):
        self.ws.write_to_socket(commandmessage(cmd="set_vials", sender="columnautomate", target=data_target,
                                               vials=self.config.get("vials",default=[])
                                               ))

    def add_vial(self,x=None,y=None,position=None):
        if x is None or y is None:
            return
        if position is None:
            position = len(self.config.get("vials",default=[]))
        self.config.get("vials",default=[]).insert(position,{'x':x,'y':y,})
        self.config.save()

    def remove_vial(self,position = None):
        if position is None: return
        try:
            del self.config.get("vials",default=[])[position]
            self.config.save()
        except:
            self.logger.exception(Exception)

    def set_max_mm_sec(self, max_mm_sec=None):
        if max_mm_sec is None or self.motor_port is None: return
        self.ws.write_to_socket(commandmessage(cmd="set_max_mm_sec", sender="columnautomate", target=self.motor_port,max_mm_sec=[max_mm_sec,max_mm_sec,10]))

    def set_acceleration(self, acceleration=None):
        if acceleration is None or self.motor_port is None: return
        self.ws.write_to_socket(commandmessage(cmd="set_acceleration", sender="columnautomate", target=self.motor_port,acceleration=[acceleration,acceleration,1]))

    def set_steps_per_mm(self, steps_per_mm=None):
        if steps_per_mm is None or self.motor_port is None: return
        self.ws.write_to_socket(commandmessage(cmd="set_steps_per_mm", sender="columnautomate", target=self.motor_port,steps_per_mm=[steps_per_mm,steps_per_mm,200]))


    def get_frame_size(self, data_target="gui"):
        self.ws.write_to_socket(commandmessage(cmd="set_frame_size", sender="columnautomate", target=data_target,
                                               width=self.config.get("frame", "size", "width", default=100),
                                               height=self.config.get("frame", "size", "height", default=100),
                                               savedist=self.config.get("frame", "savedist", default=0)
                                ))

    def set_frame_size(self, width=100, height=100,savedist=0):
        self.config.put("frame", "size", "width", value=width)
        self.config.put("frame", "size", "height", value=height)
        self.config.put("frame", "savedist", value=savedist)

    def boardupdate(self, boarddata=None):
        if boarddata is None:
            return
        if self.motor_port is None:
            if boarddata["fw"] in POSSIBLE_MOTOR_FIRMWARES:
                self.set_motor_port(boarddata["port"])

        if self.motor_port == boarddata["port"]:
            try:
                self.ws.write_to_socket(commandmessage(cmd="set_acceleration", sender="columnautomate", target="gui",
                                                       acceleration=list(boarddata["acceleration"])[0]))
                self.ws.write_to_socket(commandmessage(cmd="set_steps_per_mm", sender="columnautomate", target="gui",
                                                       steps_per_mm=list(boarddata["steps_per_mm"])[0]))
                self.ws.write_to_socket(commandmessage(cmd="set_max_mm_sec", sender="columnautomate", target="gui",
                                                       max_mm_sec=list(boarddata["max_mm_sec"])[0]))
            except:
                self.logger.exception(Exception)

    def set_ports(self, connected_ports=None):
        if connected_ports is None:
            connected_ports = []
        for port in connected_ports:
            if port not in self.sensor_ports:
                self.add_sensor_port(port)

    def data_validator(self, message):
        if message['data']['key'].endswith('position_x'):
            self.x = message['data']['y']
        elif message['data']['key'].endswith('position_y'):
            self.y = message['data']['y']
        t = time.time()
        if t - self.lastupdate > self.dataupdate:
            self.lastupdate = t
            self.ws.write_to_socket(
                datapointmessage(sender="columnautomate", x=0.5 * (self.x + self.y), y=0.5 * (self.x - self.y),
                                 key="motorposition", target="gui", t=t, as_string=True))

    def set_time(self, time):
        self.time = time

    def set_position(self, x, y):
        if self.motor_port is None:
            return
        print(x,y)
        self.ws.write_to_socket(commandmessage(cmd="set_position", sender="columnautomate", target=self.motor_port,
                                               **{'xyz': [x + y, x - y, 0]}))

    def move_to(self, x, y):
        if self.motor_port is None:
            return
        w = self.config.get("frame", "size", "width", default=400)
        h = self.config.get("frame", "size", "height", default=400)
        sd = self.config.get("frame", "savedist", default=0)
        x=min(max(sd,x),w-sd)
        y=min(max(sd,y),h-sd)
        self.ws.write_to_socket(commandmessage(cmd="move_to", sender="columnautomate", target=self.motor_port,
                                               **{'xyz': [x + y, x - y, 0]}))

    def move_to_vial(self, number=0):
        if self.motor_port is None:
            return
        pos_y = number // self.vials_x
        pos_x = number % self.vials_x
        if pos_y % 2 == 1:
            pos_x = self.vials_x - pos_x - 1
        pos_x = pos_x * self.vials_dist + self.homeposition[0]
        pos_y = pos_y * self.vials_dist + self.homeposition[1]
        self.ws.write_to_socket(commandmessage(cmd="move_to", sender="columnautomate", target=self.motor_port,
                                               **{'xyz': [pos_x + pos_y, pos_x - pos_y, 0]}))
        return number, pos_x, pos_y

    def set_vials_x(self, count=1):
        self.vials_x = count

    def set_vials_y(self, count=1):
        self.vials_y = count

    def set_vials_dist(self, mm=30):
        self.vials_dist = mm

    def add_sensor_port(self, port=None):
        if port is not None:
            self.sensor_ports.add(port)
            self.ws.write_to_socket(commandmessage(cmd="add_data_target", sender="columnautomate", target=port,
                                                   data_target="columnautomate"))
            self.ws.write_to_socket(
                commandmessage(cmd="remove_data_target", sender="columnautomate", target=port, data_target="gui"))

    def set_motor_port(self, motor_port=None):
        if motor_port is not None:
            self.motor_port = motor_port
            self.add_sensor_port(motor_port)

    def ask_for_ports(self):
        self.ws.write_to_socket(commandmessage(cmd="get_ports", sender="columnautomate", target="serialreader"))

    def start(self):
        while 1:
            self.ask_for_ports()
            time.sleep(3)

if __name__ == "__main__":
    ca = ColumnAutomate()
    ca.set_vials_x(4)
    ca.set_vials_y(3)
    for i in range(ca.vials_x * ca.vials_y):
        print(ca.move_to_vial(i))
