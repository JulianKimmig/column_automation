def definitions(self):
    return {
    "X_STEP_PIN": 54,
    "X_DIR_PIN": 55,
    "X_ENABLE_PIN": 38,
    "X_MIN_PIN": 3,
    "X_MAX_PIN": 2,

    "Y_STEP_PIN": 60,
    "Y_DIR_PIN": 61,
    "Y_ENABLE_PIN": 56,
    "Y_MIN_PIN": 14,
    "Y_MAX_PIN": 15,
    "Z_STEP_PIN": 46,
    "Z_DIR_PIN": 48,
    "Z_ENABLE_PIN": 62,
    "Z_MIN_PIN": 18,
    "Z_MAX_PIN": 19,
    }

def global_vars(self):
    return {
        'motor_x(AccelStepper::DRIVER, X_STEP_PIN, X_DIR_PIN)': ['AccelStepper', None],
        'motor_y(AccelStepper::DRIVER, Y_STEP_PIN, Y_DIR_PIN)': ['AccelStepper', None],
        'motor_z(AccelStepper::DRIVER, Z_STEP_PIN, Z_DIR_PIN)': ['AccelStepper', None],
    }

def includes(self):
   return ["<AccelStepper.h>"]

def functions(self):
    return {}

def setup(self):
    return "motor_x.setMaxSpeed(1000);\n" \
           "motor_x.setAcceleration(200);\n"\
           "motor_y.setMaxSpeed(1000);\n"\
           "motor_y.setAcceleration(200);\n"\
           "motor_z.setMaxSpeed(1000);\n"\
           "motor_z.setAcceleration(200);\n"


def loop(self):
    return "motor_x.run();\n"\
           "motor_y.run();\n"\
           "motor_z.run();\n"


def dataloop(self):
    return (
            "write_data(motor_x.currentPosition(),"
            + str(self.get_portcommand_by_name("x_set_position").byteid)
            + ");\n"
            +"write_data(motor_y.currentPosition(),"
            + str(self.get_portcommand_by_name("y_set_position").byteid)
            + ");\n"
            +"write_data(motor_z.currentPosition(),"
            + str(self.get_portcommand_by_name("z_set_position").byteid)
            + ");\n"
    )


def create(self):
    return {
        'definitions': definitions(self),
        'global_vars': global_vars(self),
        'includes': includes(self),
        'functions': functions(self),
        'setup': setup(self),
        'loop': loop(self),
        'dataloop': dataloop(self)
    }
