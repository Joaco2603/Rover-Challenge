from .pines import nombre_io

try:
    import board
    from ideaboard import IdeaBoard
except ImportError:
    board = None
    IdeaBoard = None

ROJO, VERDE, AMARILLO = (255, 0, 0), (0, 255, 0), (255, 180, 0)


def pin_io(gpio):
    return getattr(board, nombre_io(gpio))


def frenar(ib):
    if ib is not None:
        ib.motor_1.throttle = 0
        ib.motor_2.throttle = 0


def pintar(ib, rgb):
    if ib is not None:
        ib.pixel = rgb


def throttle(x):
    if x > 1:
        return 1
    if x < -1:
        return -1
    return x


def escribir_motores(ib, izq, der):
    if ib is None:
        return
    ib.motor_1.throttle = throttle(izq)
    ib.motor_2.throttle = throttle(der)
