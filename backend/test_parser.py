import unittest
from backend.parser import parse

class TestParser(unittest.TestCase):
  def setUp(self):
    pass

  def test_parser(self):
    for (input, kwargs, expected) in [
      ('3', {}, 3),
      ('-5', {}, -5),
      ('3.145', {}, 3.145),
      ('+', {}, None),
      ('foo', {'foo': 99}, 99),
      ('foo', {'bar': 99}, None),
      ('1 + 2', {}, 3),
      ('1 -2', {}, -1),
      ('1 --2', {}, 3),
      ('2 * 3', {}, 6),
      ('2 * 3 + 4', {}, 10),
      ('2 + 3 * 4', {}, 14),
      ('(2 + 3) * 4', {}, 20),
      ('((((((((foo))))))))', {'foo': 3}, 3),
      ('((((((((foo)))))))', {'foo': 3}, None),
      ('(((((((foo))))))))', {'foo': 3}, None),
      ('foo + bar', {'foo': 3, 'bar': 4}, 7),
      ('[foo, bar, 5]', {'foo': 3, 'bar': 4}, [3,4,5]),
      ('[foo, bar] * 5', {'foo': 3, 'bar': 4}, [15, 20]),
      ('foo * [bar, 5]', {'foo': 3, 'bar': 4}, [12, 15]),
      ('avg(foo, bar + 5)', {'foo': 3, 'bar': 4}, 6),

    ]:
      with self.subTest(input=input, kwargs=kwargs, expected=expected):
        if expected is None:
          with self.assertRaises(AssertionError):
            self.assertEqual(parse(input, kwargs), expected)
        else:
          self.assertEqual(parse(input, kwargs), expected)

if __name__ == '__main__':
  unittest.main()
