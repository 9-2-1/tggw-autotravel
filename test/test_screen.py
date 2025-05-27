import unittest
from tggw_autotravel.screen import Screen, Char, Color, Cursor


class TestScreenConversion(unittest.TestCase):
    def test_screen_conversion(self) -> None:
        # 创建一个复杂的 Screen 对象
        lines = 10
        columns = 20
        screen = Screen(lines, columns)

        # 填充复杂的字符数据
        for y in range(lines):
            for x in range(columns):
                char = chr(ord("A") + (x + y) % 26)
                fg = Color((x * y) % 16)
                bg = Color((x + y) % 16)
                screen.buffer[y][x] = Char(char, fg, bg)

        # 设置复杂的光标位置和可见性
        screen.cursor = Cursor(9, 9, 2)

        # 转换为 JSON 字符串
        json_str = screen.to_json()

        # 从 JSON 字符串恢复 Screen 对象
        restored_screen = Screen.from_json(json_str)

        # 验证恢复后的 Screen 对象与原始对象相同
        self.assertEqual(screen.lines, restored_screen.lines)
        self.assertEqual(screen.columns, restored_screen.columns)
        self.assertEqual(screen.cursor.x, restored_screen.cursor.x)
        self.assertEqual(screen.cursor.y, restored_screen.cursor.y)
        self.assertEqual(screen.cursor.visibility, restored_screen.cursor.visibility)
        for y in range(lines):
            for x in range(columns):
                self.assertEqual(
                    screen.buffer[y][x].char, restored_screen.buffer[y][x].char
                )
                self.assertEqual(
                    screen.buffer[y][x].fg, restored_screen.buffer[y][x].fg
                )
                self.assertEqual(
                    screen.buffer[y][x].bg, restored_screen.buffer[y][x].bg
                )


if __name__ == "__main__":
    unittest.main()
