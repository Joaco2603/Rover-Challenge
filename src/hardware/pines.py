# Pines del robot que anda (README.md). No importar board.
# IdeaBoard uses board.IO36 etc. pin_io maps with getattr(board, "IO36").
# sen1 IR FL, sen2 IR FR (no es color AO), sen3 IR BL, sen4 IR BR.
IR_FL, IR_FR, IR_BL, IR_BR = 36, 39, 34, 35
# US TRIG no es 25. US OUT no se conecta.
US_TRIG, US_ECHO = 23, 26
# Color LED DI / AO. AO no va en 39. VCC 3.3V. BOOT sin cable.
COLOR_LED, COLOR_AO = 4, 33
BOOT = 0
IR_FL_IO, IR_FR_IO, IR_BL_IO, IR_BR_IO = "IO36", "IO39", "IO34", "IO35"
US_TRIG_IO, US_ECHO_IO = "IO23", "IO26"
COLOR_LED_IO, COLOR_AO_IO, BOOT_IO = "IO4", "IO33", "IO0"
# MOTOR 1 (IO12/IO14), MOTOR 2 (IO13/IO15), IMU Qwiic, jumper SELECT–Vin.


def nombre_io(gpio):
    return "IO{}".format(int(gpio))
