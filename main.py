import logging
import os
import threading
import time

from arduino_controller import serialreader
from arduino_controller.parseboards import parse_path_for_boards, BOARDS
from arduinocontrollserver.arduinocontrollserver import ArduinoControllServer
from json_dict.json_dict import JsonDict
from websocket_communication_server.socketserver import connect_to_first_free_port

from column_automation import ColumnAutomate

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    serialportconfig = JsonDict("portdata.json")
    serialportconfig.autosave = True

    socketserver = connect_to_first_free_port()
    threading.Thread(
        target=socketserver.run_forever
    ).start()  # runs server forever in background


    server = ArduinoControllServer(port=80,socketport=socketserver.port,www_data=os.path.join(os.path.dirname(__file__),"www-data"))
    threading.Thread(
        target=server.start
    ).start()  # runs server forever in background

    server.deploy(socketserver.get_www_data_path(),"websocketserver")
    server.deploy(server.get_www_data_path(),"arduinocontroller")

    ca = ColumnAutomate(sockethost=socketserver.ws_adress)
    parse_path_for_boards(os.path.join(os.path.abspath(os.path.dirname(__file__)),"boards"))
    print(BOARDS)
    time.sleep(1)
    serialreader.run(config=serialportconfig,host=socketserver.ws_adress)