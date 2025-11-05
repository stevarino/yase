from dataclasses import dataclass
from itertools import chain

import trimesh as tm

@dataclass
class Volume:
  left: float
  right: float
  bottom: float
  top: float
  front: float
  back: float

  @property
  def width(self):
    return self.right - self.left

  @property
  def height(self):
    return self.top - self.bottom
  
  @property
  def depth(self):
    return self.back - self.front
  
  @property
  def mid_x(self):
    return self.width / 2 + self.left
  
  @property
  def mid_y(self):
    return self.height / 2 + self.bottom
  
  @property
  def mid_z(self):
    return self.depth / 2 + self.front
  
  def __str__(self):
    return f'{self.width}x{self.height}x{self.depth} @ ({self.left}, {self.bottom}, {self.front})'

  def to_dict(self):
    return dict(
      left=float(self.left),
      right=float(self.right),
      bottom=float(self.bottom),
      top=float(self.top),
      front=float(self.front),
      back=float(self.back),
      width=float(self.width),
      height=float(self.height),
      depth=float(self.depth),
      mid_x=float(self.mid_x),
      mid_y=float(self.mid_y),
      mid_z=float(self.mid_z),
    )


class Shape:
  def __init__(self, mesh: tm.Trimesh):
     self.mesh = mesh

  @classmethod
  def load(cls, filename: str):
    return Shape(tm.load_mesh(filename))
  
  def save(self, filename: str, fh=None):
    # trimesh does not support filenames in STL headers
    self.mesh.export(fh or filename, file_type='stl')

  @property
  def volume(self):
    bbox: tm.primitives.Box = self.mesh.bounding_box
    # bbox.bounds of np.float64: 
    #   [[x_min, y_min, z_min], [x_max, y_max, z_max]]
    return Volume(
      *(float(n) for n in chain(*zip(*bbox.bounds)))
    )

  def copy(self):
     return Shape(self.mesh.copy())

  def zero(self):
     """Moves the min x/y/z points to zero."""
     bbox: tm.primitives.Box = self.mesh.bounding_box
     self.mesh.apply_translation(-1 * bbox.bounds[0])

  def center(self, x, y, z):
     v = self.volume
     self.translate(
        x - v.left - v.width / 2,
        y - v.bottom - v.height / 2,
        z - v.front - v.depth / 2,
     )

  def translate(self, dx: float, dy: float, dz: float):
     """Applies a constant offset the x/y/z points."""
     self.mesh.apply_translation([dx, dy, dz])

  def scale(self, x, y, z):
     self.mesh.apply_scale([x, y, z])

  def set_width(self, width: float):
     x = float(width) / self.volume.width
     self.scale(x, 1, 1)

  def set_height(self, height: float):
     y = float(height) / self.volume.height
     self.scale(1, y, 1)

  def set_depth(self, depth: float):
     z = float(depth) / self.volume.depth
     self.scale(1, 1, z)

  def set_size(self, width, height, depth):
    vol = self.volume
    x = float(width) / vol.width
    y = float(height) / vol.height
    z = float(depth) / vol.depth
    self.scale(x, y, z)

  def merge(self, other: 'Shape'):
    self.mesh = tm.boolean.union([self.mesh, other.mesh], engine='manifold')

  def subtract(self, other: 'Shape'):
    self.mesh = tm.boolean.difference([self.mesh, other.mesh], engine='manifold')
