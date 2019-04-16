def functions(self):
    return {"start_hx711": ["void", [], "hx711.begin(dout, sck,gain);\n"]}


def create(self):
    return {
        "global_vars": {
            "hx711": ["HX711", None],
            "average": ["uint8_t", 1],
            "gain": ["uint8_t", self.gain],
        },
        "includes": ["<HX711.h>"],
        "functions": functions(self),
        "setup": "start_hx711();\n",
        #'loop': loop(self),
        "dataloop": self.get_portcommand_by_name("read_data").arduino_code,
    }
