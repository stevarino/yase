from stl import mesh, Mesh
from dataclasses import dataclass
import numpy as np

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
  def __init__(self, mesh: Mesh):
     self.mesh = mesh

  @classmethod
  def load(cls, filename: str):
     return Shape(mesh.Mesh.from_file(filename))
  
  def save(self, filename: str, fh=None):
     self.mesh.save(filename, fh=fh)
  
  @property
  def volume(self):
     return Volume(
        self.mesh.x.min(), self.mesh.x.max(),
        self.mesh.y.min(), self.mesh.y.max(),
        self.mesh.z.min(), self.mesh.z.max(),
     )

  def copy(self):
     return Shape(mesh.Mesh(self.mesh.data.copy()))

  def zero(self):
     """Moves the min x/y/z points to zero."""
     self.translate(
        -1 * self.mesh.x.min(),
        -1 * self.mesh.y.min(),
        -1 * self.mesh.z.min(),
     )

  def center(self, x, y, z):
     v = self.volume
     self.translate(
        x - v.left - v.width / 2,
        y - v.bottom - v.height / 2,
        z - v.front - v.depth / 2,
     )

  def translate(self, dx: float, dy: float, dz: float):
     """Applies a constant offset the x/y/z points."""
     self.mesh.points[:] += 3 * [dx, dy, dz]

  def scale(self, x, y, z):
     self.mesh.points[:] *= 3 * [x, y, z]

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
    self.mesh = mesh.Mesh(np.concatenate([
       self.mesh.data, other.mesh.data
    ]))
