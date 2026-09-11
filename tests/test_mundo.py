import os
import random
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mundo import (
    AGE_PROPIO_MAX_MS,
    FASE_FINISHED,
    FASE_IDLE,
    FASE_READY,
    FASE_RUNNING,
    LATENCIA_MAX_MS,
    parsear,
)


def mensaje(**sobre):
    msg = {
        "v": 1,
        "seq": 7,
        "ts_ms": 1000000,
        "phase": FASE_RUNNING,
        "grid": {"cols": 20, "rows": 31, "cell_mm": 25.0},
        "rovers": [
            {"id": 11, "col": 1.5, "row": 2.5, "theta": 90.0, "age_ms": 0},
            {"id": 10, "col": 4.3, "row": 5.1, "theta": 46.2, "age_ms": 12},
        ],
        "cubes": [
            {"color": "red", "col": 8.0, "row": 9.0, "age_ms": 0},
            {"color": "blue", "col": 3.0, "row": 4.0, "age_ms": 900},
            {"color": "green", "col": 6.0, "row": 7.0, "age_ms": 0},
        ],
        "obstacles": [],
        "start": {"col": 2.5, "row": 2.5},
        "depots": [
            {"color": "blue", "col": 1.0, "row": 30.0},
            {"color": "red", "col": 19.0, "row": 30.0},
            {"color": "green", "col": 19.0, "row": 1.0},
        ],
    }
    msg.update(sobre)
    return msg


class TestParsear(unittest.TestCase):
    def test_busca_por_identidad_aunque_mezclen_listas(self):
        rng = random.Random(0)
        for _ in range(8):
            msg = mensaje()
            rng.shuffle(msg["rovers"])
            rng.shuffle(msg["cubes"])
            rng.shuffle(msg["depots"])
            m = parsear(msg)
            self.assertEqual(m.rover(10)["id"], 10)
            self.assertEqual(m.rover(11)["theta"], 90.0)
            self.assertEqual(m.cubo("green")["color"], "green")
            self.assertEqual(m.depot("red")["color"], "red")
            self.assertIsNone(m.rover(99))

    def test_grid_sale_del_mensaje(self):
        m = parsear(mensaje())
        self.assertEqual((m.grid_cols, m.grid_rows, m.cell_mm), (20, 31, 25.0))

    def test_obstaculos_vacios_se_iteran(self):
        n = 0
        for _o in parsear(mensaje()).obstacles:
            n += 1
        self.assertEqual(n, 0)

    def test_fases_se_juega(self):
        for fase in (FASE_IDLE, FASE_READY, FASE_FINISHED):
            self.assertFalse(parsear(mensaje(phase=fase)).se_juega())
        self.assertTrue(parsear(mensaje(phase=FASE_RUNNING)).se_juega())

    def test_datos_viejos_rover_faltante_age_y_latencia(self):
        fresco = parsear(mensaje())
        self.assertFalse(fresco.datos_viejos(10, 1000020))
        sin_10 = mensaje()
        sin_10["rovers"] = [r for r in sin_10["rovers"] if r["id"] != 10]
        self.assertTrue(parsear(sin_10).datos_viejos(10, 1000020))
        con_age = mensaje()
        for r in con_age["rovers"]:
            if r["id"] == 10:
                r["age_ms"] = AGE_PROPIO_MAX_MS + 1
        self.assertTrue(parsear(con_age).datos_viejos(10, 1000020))
        self.assertTrue(fresco.datos_viejos(10, 1000000 + LATENCIA_MAX_MS + 1))

    def test_v2_se_descarta(self):
        self.assertIsNone(parsear(mensaje(v=2)))
        self.assertIsNone(parsear({"seq": 1}))

    def test_cubo_ocluido_sigue_por_color(self):
        azul = parsear(mensaje()).cubo("blue")
        self.assertEqual(azul["color"], "blue")
        self.assertGreater(azul["age_ms"], 0)


if __name__ == "__main__":
    unittest.main()
