import unittest
from src.taskmaster.utils.log_reader import LogReader

file_content: list[str] = [
    "Hello, World!\n",
    "Something else\n",
    "aaa\n",
    "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\n",
    "\n",
    "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\n",
    "blabla\n",
    "blabla\n",
    "blabla\n",
    "blabla\n",
    "blabla\n",
]


class TestLogReader(unittest.TestCase):
    def setUp(self) -> None:
        with open("/tmp/test.log", "w") as f:
            f.writelines(file_content)
        return super().setUp()

    def tearDown(self) -> None:
        return super().tearDown()

    def test_read(self):
        with open("/tmp/test.log", "r") as f:
            reader = LogReader(f.name, size=200)
            self.assertEqual(reader._read(), file_content[:200])

    def test_half_read(self):
        with open("/tmp/test.log", "r") as f:
            reader = LogReader(f.name, size=5)
            self.assertEqual(reader._read(), file_content[6:11])

    def test_read_size_zero(self):
        with open("/tmp/test.log", "r") as f:
            self.assertRaises(ValueError, LogReader, f.name, size=0)

    def test_read_size_negative(self):
        with open("/tmp/test.log", "r") as f:
            self.assertRaises(ValueError, LogReader, f.name, size=-1)

    def test_up(self):
        with open("/tmp/test.log", "r") as f:
            reader = LogReader(f.name, size=5)
            reader._read()
            reader.up()
            self.assertEqual(reader._start, 6)
            self.assertEqual(reader._read(), file_content[6:11])

    def test_up_past_end(self):
        with open("/tmp/test.log", "r") as f:
            reader = LogReader(f.name, size=5)
            reader._read()
            for _ in range(10):
                reader.up()
            self.assertEqual(reader._start, 6)
            self.assertEqual(reader._read(), file_content[6:11])

    def test_down(self):
        with open("/tmp/test.log", "r") as f:
            reader = LogReader(f.name, size=5)
            reader._start = 5
            reader.down()
            self.assertEqual(reader._start, 4)
            self.assertEqual(reader._read(), file_content[4:9])

    def test_down_past_start(self):
        with open("/tmp/test.log", "r") as f:
            reader = LogReader(f.name, size=5)
            reader._start = 0
            reader.down()
            self.assertEqual(reader._start, 0)
            self.assertEqual(reader._read(), file_content[:5])

    def test_end(self):
        with open("/tmp/test.log", "r") as f:
            reader = LogReader(f.name, size=20)
            self.assertTrue(reader.end)

    def test_latest(self):
        with open("/tmp/test.log", "r") as f:
            reader = LogReader(f.name, size=5)
            reader.latest()
            self.assertEqual(reader.lines, file_content[6:11])

    def test_latest_past_end(self):
        with open("/tmp/test.log", "r") as f:
            reader = LogReader(f.name, size=30)
            reader.latest()
            self.assertEqual(reader.lines, file_content)

    def test_invalid_file(self):
        self.assertRaises(
            FileNotFoundError, LogReader, "/reohiushgoiuhgo/wefwugfeuag", size=5
        )

    def test_size_change(self):
        with open("/tmp/test.log", "r") as f:
            reader = LogReader(f.name, size=5)
            reader.size = 10
            self.assertEqual(reader.size, 10)
            self.assertEqual(reader._read(), file_content[1:11])

    def test_size_change_invalid(self):
        with open("/tmp/test.log", "r") as f:
            reader = LogReader(f.name, size=5)
            self.assertRaises(ValueError, setattr, reader, "size", 0)
            self.assertRaises(ValueError, setattr, reader, "size", -1)
