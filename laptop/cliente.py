# Cliente laptop de telemetria oficial (TCP NDJSON :2026).
# Drena el socket y usa solo el ultimo JSON; quieto si phase != RUNNING.
#
# terminal 1: cd vision-system/contrato && python3 mock_publisher.py
# terminal 2: python3 laptop/cliente.py --id 10
# then type ready / start on the mock

import argparse
import os
import socket
import sys
import time

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _RAIZ not in sys.path:
    sys.path.insert(0, _RAIZ)

from mundo import parsear
from tcp import BufferNDJSON


def _drenar(sock, buf):
    """Lee todo lo disponible. False si se cayo la conexion."""
    while True:
        try:
            trozo = sock.recv(4096)
        except (BlockingIOError, InterruptedError, socket.timeout):
            return True
        except OSError:
            return False
        if not trozo:
            return False
        buf.alimentar(trozo)


def _linea(m, aruco_id, ahora_ms):
    r = m.rover(aruco_id)
    if r is None:
        pose = "rover=faltante age_ms=-"
    else:
        pose = "rover={} col={:.2f} row={:.2f} theta={:.1f} age_ms={}".format(
            r["id"], r["col"], r["row"], r["theta"], r["age_ms"])
    colores = []
    for c in m.cubes:
        colores.append(str(c["color"]))
    n_obst = 0
    for _o in m.obstacles:
        n_obst += 1
    mover = m.se_juega() and not m.datos_viejos(aruco_id, ahora_ms)
    cubos = ",".join(colores) if colores else "-"
    return "phase={} grid={}x{}@{}mm {} lat_ms={} cubos={} obst={} mover={}".format(
        m.phase, m.grid_cols, m.grid_rows, m.cell_mm, pose,
        m.latencia_ms(ahora_ms), cubos, n_obst, "si" if mover else "no")


def main():
    p = argparse.ArgumentParser(description="Cliente telemetria Vision Rover")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=2026)
    p.add_argument("--id", dest="aruco_id", type=int, default=10)
    p.add_argument("--duracion", type=float, default=0, help="segundos; 0 = infinito")
    args = p.parse_args()
    t0 = time.time()
    sock = None
    buf = BufferNDJSON()
    seq_vista = None
    try:
        while True:
            if args.duracion > 0 and (time.time() - t0) >= args.duracion:
                break
            if sock is None:
                try:
                    sock = socket.create_connection((args.host, args.port), timeout=3)
                    sock.setblocking(False)
                    buf = BufferNDJSON()
                    seq_vista = None
                    print("conectado {}:{}".format(args.host, args.port), flush=True)
                except OSError as e:
                    print("reconectando: {}".format(e), flush=True)
                    time.sleep(1.0)
                    continue
            if not _drenar(sock, buf):
                print("conexion perdida, reintento", flush=True)
                try:
                    sock.close()
                except OSError:
                    pass
                sock = None
                time.sleep(1.0)
                continue
            msg = buf.ultimo()
            if msg is not None:
                m = parsear(msg)
                if m is not None and m.seq != seq_vista:
                    seq_vista = m.seq
                    print(_linea(m, args.aruco_id, int(time.time() * 1000)), flush=True)
            time.sleep(0.05)
    except KeyboardInterrupt:
        print("")
    if sock is not None:
        try:
            sock.close()
        except OSError:
            pass


if __name__ == "__main__":
    main()
