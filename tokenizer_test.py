import unittest
from CodeTokenizer.tokenizer import TokeNizer


class TestChangeDetector(unittest.TestCase):
    code = [
        "a = 0",
        "if a.isEmpty():",
        "print(\"hello\")",
        """
        a=b
        b=c
        """
    ]
    answer = [
        ["a", "=", "0"],
        ["if", "a", ".", "isEmpty", "(", ")", ":"],
        ["print", "(", "\"hello\"", ")"],
    ]

    def test_python(self):
        TN = TokeNizer("Python")
        tokens = TN.getPureTokens(self.code[0])
        self.assertEqual(tokens, self.answer[0])


if __name__ == '__main__':
    unittest.main()
