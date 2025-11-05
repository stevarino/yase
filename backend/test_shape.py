import unittest
import backend.shape as shape

import trimesh as tm


class TestShape(unittest.TestCase):
  def setUp(self):
    pass

  def test_shape(self):
    s = shape.Shape(tm.creation.box())
    vol = s.volume.to_dict()
    for key, val in [('width', 1), ('height', 1), ('depth', 1),
                     ('bottom', -0.5), ('front', -0.5), ('left', -0.5),
                     ('top', 0.5), ('back', 0.5), ('right', 0.5),]:
      self.assertEqual(vol[key], val, f'Expected {key}={val}, got {vol[key]}')

  def test_zero(self):
    s = shape.Shape(tm.creation.box())
    s.zero()
    vol = s.volume.to_dict()
    for key, val in [('width', 1), ('height', 1), ('depth', 1),
                     ('bottom', 0), ('front', 0), ('left', 0),
                     ('top', 1), ('back', 1), ('right', 1),]:
      self.assertEqual(vol[key], val, f'Expected {key}={val}, got {vol[key]}')

  def test_translate(self):
    s = shape.Shape(tm.creation.box())
    s.zero()
    s.translate(2, 3, 4)
    vol = s.volume.to_dict()
    for key, val in [('width', 1), ('height', 1), ('depth', 1),
                     ('left', 2), ('bottom', 3), ('front', 4),
                     ('right', 3), ('top', 4), ('back', 5),]:
      self.assertEqual(vol[key], val, f'Expected {key}={val}, got {vol[key]}')

  def test_scale(self):
    s = shape.Shape(tm.creation.box())
    s.scale(2, 3, 4)
    vol = s.volume.to_dict()
    for key, val in [('width', 2), ('height', 3), ('depth', 4)]:
      self.assertEqual(vol[key], val, f'Expected {key}={val}, got {vol[key]}')

  def test_merge(self):
    s = shape.Shape(tm.creation.box())
    s.zero()
    other = shape.Shape(tm.creation.box())
    other.translate(1, 1, 1)
    s.merge(other)
    vol = s.volume.to_dict()
    pts = set()
    for triangle in s.mesh.triangles:
      [pts.add(tuple(map(float, pt))) for pt in triangle]
    [t for t in s.mesh.triangles]
    for key, val in [('width', 1.5), ('height', 1.5), ('depth', 1.5)]:
      self.assertEqual(vol[key], val, f'Expected {key}={val}, got {vol[key]}')

    for (pt, expected) in [
      ((0, 0, 0), True),
      ((1.0, 0, 1.0), True),
      ((1.5, 1.5, 1.5), True),
      ((0.5, 1.5, 0.5), True),
      ((0.5, 1, 0.5), True),
      ((0.5, 0.5, 0.5), False),
      ((1, 0.5, 1), True),
      ((1, 1, 1), False),
    ]:
      with self.subTest(pt=pt, expected=expected):
        if expected:
          self.assertIn(pt, pts)
        else:
          self.assertNotIn(pt, pts)

  def test_subtract(self):
    s = shape.Shape(tm.creation.box())
    s.zero()
    other = shape.Shape(tm.creation.box())
    other.translate(1, 1, 1)
    s.subtract(other)
    vol = s.volume.to_dict()
    pts = set()
    for triangle in s.mesh.triangles:
      [pts.add(tuple(map(float, pt))) for pt in triangle]
    for key, val in [('width', 1), ('height', 1), ('depth', 1)]:
      self.assertEqual(vol[key], val, f'Expected {key}={val}, got {vol[key]}')

    for (pt, expected) in [
      ((0, 0, 0), True),
      ((1.0, 0, 1.0), True),
      ((1.5, 1.5, 1.5), False),
      ((0.5, 1.5, 0.5), False),
      ((0.5, 1, 0.5), True),
      ((0.5, 0.5, 0.5), True),
      ((1, 0.5, 1), True),
      ((1, 1, 1), False),
    ]:
      with self.subTest(pt=pt, expected=expected):
        if expected:
          self.assertIn(pt, pts)
        else:
          self.assertNotIn(pt, pts)

if __name__ == '__main__':
  unittest.main()
