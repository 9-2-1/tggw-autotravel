import unittest
from tggw_autotravel.run.winconsole import paramvine


class TestParamVine(unittest.TestCase):
    def test_no_args(self) -> None:
        """测试无参数的情况"""
        cmd = "notepad.exe"
        result = paramvine(cmd)
        self.assertEqual(result, "notepad.exe")

    def test_simple_args(self) -> None:
        """测试简单参数"""
        cmd = "notepad.exe"
        args = ("file.txt",)
        result = paramvine(cmd, *args)
        self.assertEqual(result, "notepad.exe file.txt")

    def test_space_in_cmd(self) -> None:
        """测试命令中有空格"""
        cmd = "C:\\Program Files\\notepad.exe"
        result = paramvine(cmd)
        self.assertEqual(result, '"C:\\Program Files\\notepad.exe"')

    def test_space_in_args(self) -> None:
        """测试参数中有空格"""
        cmd = "notepad.exe"
        args = ("my file.txt",)
        result = paramvine(cmd, *args)
        self.assertEqual(result, 'notepad.exe "my file.txt"')

    def test_quote_in_cmd(self) -> None:
        """测试命令中有引号"""
        cmd = 'not"epad.exe'
        result = paramvine(cmd)
        self.assertEqual(result, "notepad.exe")

    def test_quote_in_args(self) -> None:
        """测试参数中有引号"""
        cmd = "notepad.exe"
        args = ('file".txt',)
        result = paramvine(cmd, *args)
        self.assertEqual(result, 'notepad.exe "file\\".txt"')

    def test_backslash_before_quote(self) -> None:
        """测试参数中引号前的反斜杠"""
        cmd = "notepad.exe"
        args = ('path\\to\\"file.txt',)
        result = paramvine(cmd, *args)
        self.assertEqual(result, 'notepad.exe "path\\to\\\\\\"file.txt"')

    def test_multiple_args(self) -> None:
        """测试多个参数"""
        cmd = "git"
        args = ("commit", "-m", "initial commit")
        result = paramvine(cmd, *args)
        self.assertEqual(result, 'git commit -m "initial commit"')

    def test_complex_case(self) -> None:
        """测试复杂情况：空格+引号+反斜杠"""
        cmd = "C:\\My Programs\\app.exe"
        args = ('--path="C:\\Program Files\\data"', "--name=my file\\")
        result = paramvine(cmd, *args)
        self.assertEqual(
            result,
            '"C:\\My Programs\\app.exe" "--path=\\"C:\\Program Files\\data\\"" "--name=my file\\\\"',
        )


if __name__ == "__main__":
    unittest.main()
