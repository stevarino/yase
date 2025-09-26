import types
import json


class ValidationError(Exception):
  def __init__(self, msg: str):
    self.msg = msg


class Validator:
  def __init__(self, func: types.FunctionType):
    self._test = func
    self._doc = func.__doc__

  @property
  def doc(self):
    return self._doc

  def test(self, input):
    try:
      self._test(input)
    except (AssertionError, ValidationError):
      raise ValidationError(self._test.__doc__)
    return True
  
  def check(self, input):
    try:
      self._test(input)
    except (AssertionError, ValidationError):
      return False
    return True

  @staticmethod
  def wrap(func: types.FunctionType):
    return Validator(func)


def enum(options):
  """Given a list, returns a validator of that list"""
  if type(options) != list:
    options = list(options)
  def inner(input):
    assert input in options
  inner.__doc__ = f'value in: {json.dumps(options)}'
  return Validator(inner)


def and_(*validators: Validator):
  def inner(input):
    assert all(v.test(input) for v in validators)
  inner.__doc__ = f'({") and (".join(v.doc for v in validators)})'
  return Validator(inner)


def or_(*validators: Validator):
  def inner(input):
    assert any(v.test(input) for v in validators)
  inner.__doc__ = f'({") or (".join(v.doc for v in validators)})'
  return Validator(inner)


@Validator.wrap
def any_(input):
  """Any input"""
  return


@Validator.wrap
def string(input):
  """String"""
  assert type(input) == str


@Validator.wrap
def map(input):
  """Key/Value mapping."""
  assert type(input) == dict and all(type(k) == str for k in input.keys())


@Validator.wrap
def numeric(input):
  """Numeric (int or float)"""
  assert type(input) == int or type(input) == float


@Validator.wrap
def vec(input):
  """Array"""
  assert type(input) == list


@Validator.wrap
def vec_numeric(input):
  """Array of all numeric"""
  vec.test(input)
  assert(numeric.test(n) for n in input)

@Validator.wrap
def vec3(input):
  """Array of length 3"""
  vec.test(input)
  assert len(input) == 3


@Validator.wrap
def vec3_numeric(input):
  """Numeric array of length 3"""
  vec3.test(input)
  vec_numeric.test(input)
  

@Validator.wrap
def vec3_numeric(input):
  """Numeric array of length 3"""
  vec_numeric.test(input)
  assert len(input) == 3
  

@Validator.wrap
def vec2_numeric(input):
  """Numeric array of length 3"""
  vec_numeric.test(input)
  assert len(input) == 2


@Validator.wrap
def vec1_numeric(input):
  """Numeric array of length 3"""
  vec_numeric.test(input)
  assert len(input) == 1


@Validator.wrap
def iterate_input(input):
  """1 to 3 numerics"""
  assert (
    numeric.check(input)
    or (
      vec_numeric.check(input)
      and 1<= len(input) <= 3
    )
    or (
      vec(input)
      and all(type(n) == dict for n in input)
    )
  )


@Validator.wrap
def commands(input):
  """A set of commands, either in list or dict format"""
  if type(input) == list:
    assert all(type(n) == dict for n in input)
  else:
    assert type(input) == dict