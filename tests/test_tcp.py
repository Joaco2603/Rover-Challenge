import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tcp import BufferNDJSON


def _msg(seq, v=1):
    return {"v": v, "seq": seq, "phase": "RUNNING"}


def _nd(obj):
    return (json.dumps(obj) + "\n").encode("utf-8")


class TestBufferNDJSON(unittest.TestCase):
    def test_dos_lineas_en_un_trozo_queda_la_ultima(self):
        buf = BufferNDJSON()
        got = buf.alimentar(_nd(_msg(1)) + _nd(_msg(2)))
        self.assertEqual(got["seq"], 2)
        self.assertEqual(buf.ultimo()["seq"], 2)

    def test_linea_partida(self):
        buf = BufferNDJSON()
        raw = _nd(_msg(7))
        self.assertIsNone(buf.alimentar(raw[:12]))
        self.assertEqual(buf.alimentar(raw[12:])["seq"], 7)

    def test_drena_no_encola(self):
        buf = BufferNDJSON()
        got = buf.alimentar(_nd(_msg(1)) + _nd(_msg(2)) + _nd(_msg(3)))
        self.assertEqual(got["seq"], 3)
        self.assertEqual(buf.alimentar(b"")["seq"], 3)

    def test_ignora_json_malo_y_v_distinta(self):
        buf = BufferNDJSON()
        buf.alimentar(_nd(_msg(1)))
        buf.alimentar(b"{no json\n")
        buf.alimentar(_nd(_msg(9, v=2)))
        self.assertEqual(buf.ultimo()["seq"], 1)

    def test_cap_sin_newline_no_envenena_la_siguiente(self):
        buf = BufferNDJSON()
        buf.alimentar(b"x" * 9000)
        self.assertEqual(buf.alimentar(_nd(_msg(5)))["seq"], 5)


if __name__ == "__main__":
    unittest.main()
