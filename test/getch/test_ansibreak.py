import unittest
from tggw_autotravel.getch.ansibreak import AnsiBreak


class TestAnsiBreakDecode(unittest.TestCase):
    def setUp(self):
        self.parser = AnsiBreak()

    def test_ground_state_text(self):
        """测试GROUND状态下普通文本"""
        text = "hello"
        result = self.parser.decode(text)
        self.assertEqual(result, ["h", "e", "l", "l", "o"])

    def test_escape_sequence_start(self):
        """测试ESC字符开始转义序列"""
        text = "\x1b[31m"
        result = self.parser.decode(text)
        self.assertEqual(result, ["\x1b[31m"])

    def test_mixed_text_and_escape(self):
        """测试混合文本和转义序列"""
        text = "hello\x1b[31mworld\x1b[0m"
        result = self.parser.decode(text)
        self.assertEqual(
            result,
            ["h", "e", "l", "l", "o", "\x1b[31m", "w", "o", "r", "l", "d", "\x1b[0m"],
        )

    def test_partial_escape_sequence(self):
        """测试部分转义序列"""
        text1 = "\x1b"
        result1 = self.parser.decode(text1)
        self.assertEqual(result1, [])

        text2 = "[31m"
        result2 = self.parser.decode(text2)
        self.assertEqual(result2, ["\x1b[31m"])

    def test_multiple_escape_sequences(self):
        """测试多个转义序列"""
        text = "\x1b[31mred\x1b[32mgreen\x1b[0m"
        result = self.parser.decode(text)
        self.assertEqual(
            result,
            ["\x1b[31m", "r", "e", "d", "\x1b[32m", "g", "r", "e", "e", "n", "\x1b[0m"],
        )

    def test_empty_input(self):
        """测试空输入"""
        text = ""
        result = self.parser.decode(text)
        self.assertEqual(result, [])

    def test_invalid_escape_sequence(self):
        """测试无效转义序列"""
        text = "\x1b[invalid"
        result = self.parser.decode(text)
        self.assertEqual(result, ["\x1b[i", "n", "v", "a", "l", "i", "d"])

    def test_csi_sequence(self):
        """测试CSI序列"""
        text = "\x1b[5;10H"
        result = self.parser.decode(text)
        self.assertEqual(result, ["\x1b[5;10H"])

    def test_osc_sequence(self):
        """测试OSC序列"""
        text = "\x1b]0;title\x07"
        result = self.parser.decode(text)
        self.assertEqual(result, ["\x1b]0;title\x07"])

    def test_long_text_between_escapes(self):
        """测试转义序列之间的长文本"""
        text = "\x1b[31m" + "a" * 100 + "\x1b[0m"
        result = self.parser.decode(text)
        expected = ["\x1b[31m"] + list("a" * 100) + ["\x1b[0m"]
        self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
