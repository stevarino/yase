import unittest
import backend.stl_lib as stl_lib
from stl import Mesh


def make_cube(n: float = 2.0, x: float = 0.0, y: float = 0.0, z: float = 0.0):
  verts = [
    [0, 0, 0, n, 0, 0, 0, n, 0], # front
    [n, n, 0, n, 0, 0, 0, n, 0],
    [0, 0, n, n, n, 0, 0, n, n], # back
    [n, n, n, n, n, 0, 0, n, n],
    [0, 0, 0, n, 0, 0, 0, 0, n], # bottom
    [n, 0, n, n, 0, 0, 0, 0, n],
    [0, n, 0, n, n, 0, 0, n, n], # top
    [n, n, n, n, n, 0, 0, n, n],
    [0, 0, 0, 0, 0, n, 0, n, 0], # left
    [0, n, n, 0, 0, n, 0, n, 0],
    [0, 0, 0, 0, 0, n, 0, n, 0], # right
    [n, n, n, n, 0, n, n, n, 0],
  ]
  verts = [[
    v[0] + x, v[1] + y, v[2] + z,
    v[3] + x, v[4] + y, v[5] + z,
    v[6] + x, v[7] + y, v[8] + z,
  ] for v in verts]
  m = Mesh()
  m.data = verts
  return m

class StlLibTests(unittest.TestCase):
  def setUp(self):
    pass

  def test_binary_search(self):
    for (arr, target, expected) in [
      ([1,2,3,4,5,6], 3, 2),
      ([1,2,3,3,4,5,6], 3, 3),
      ([1,2,3,3,3,4,5,6], 3, 4),
      ([1,2,3,4,4,5,6], 3, 2),
      ([1,2,3,4,4,4,5,6], 3, 2),
      ([1,2,3,4,5,6], 3.5, 2),
    ]:
      with self.subTest(arr=arr, target=target, expected=expected):
        arr = [(0, (x,)) for x in arr]
        value = stl_lib._binary_search(arr, 0, target)
        self.assertEqual(value, expected)
 