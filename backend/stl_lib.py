from stl import mesh, Mesh
import numpy as np
from collections import namedtuple


bbox = namedtuple('bbox', 'minx maxx miny maxy minz maxz')

def _triangle_to_bounding_box(tri: list[np.float32]):
  return bbox(
    min(tri[0], tri[3], tri[6]), max(tri[0], tri[3], tri[6]),
    min(tri[1], tri[4], tri[7]), max(tri[1], tri[4], tri[7]),
    min(tri[2], tri[5], tri[8]), max(tri[2], tri[5], tri[8]),
  )

def _mesh_to_bounding_boxes(shape: Mesh):
  return [(i, _triangle_to_bounding_box(tri))
          for i, tri in enumerate(shape.data)]

def _binary_search(boxes: list[tuple[int, bbox]], index: int, target: np.float32):
  """Find the right edge where left values are lte to target."""
  lower = 0
  upper = len(boxes) - 1
  last = upper
  while lower <= upper:
    mid = lower + (upper - lower) // 2
    value = boxes[mid][1][index]
    if mid == last:
      return last
    next_ = boxes[mid+1][1][index]
    if value <= target and  next_ > target:
      return mid
    if value > target:
      upper = mid - 1
    else:
      lower = mid + 1
  raise ValueError('Unable to find boundary')  


def _find_intersection(boxes: list[tuple[int, bbox]], bbox):
  """Given a bounding box and list of bounding boxes, return indexes of overlaps."""
  cnt = len(boxes)
  intersection: set[int] = None
  for i, j in [
    (0, 1),  # boxes.left <= bbox.right
    (1, 0),  # boxes.right >= bbox.left
    (2, 3),  # boxes.bottom >= bbox.top
    (3, 2),  # boxes.top >= bbox.bottom
    (4, 5),  # boxes.front >= bbox.back
    (5, 4),  # boxes.back >= bbox.front
  ]:
    boxes.sort(key=lambda box: box[1][i])
    edge = _binary_search(boxes, i, bbox[j])
    if i < j:
      range_ = range(0, edge+1)
    else:
      range_ = range(edge, cnt)
    indexes = set(boxes[i][i] for i in range_)
    if intersection is None:
      intersection = indexes
    else:
      intersection &= indexes
  return intersection


def get_intersections(lhv: Mesh, rhv: Mesh):
  """
  Find triangles whose bounding boxes overlap, yielding 
  
  Complexity is expected to be `m n log n` where m is length of rhv and n is
  length of lhv. An optimizatio could be to flip them bso rhv is always the
  smaller, but unsure if its worth the `log n` gain.
  """
  bboxes = _mesh_to_bounding_boxes(lhv)
  for i, pts in enumerate(rhv.data):
    bbox = _triangle_to_bounding_box(pts)
    yield (i, _find_intersection(bboxes, bbox))
