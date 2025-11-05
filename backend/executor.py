"""
Executes logic according to a given data structure.
"""

from dataclasses import dataclass
import numpy as np
import typing
import json
import asyncio

import backend.parser as parser
from backend.shape import Shape, Volume
import backend.validators as val


class AbortError(Exception):
  pass


@dataclass
class ExecutorFunction:
  """A wrapper for executor functions."""
  name: str
  func: typing.Callable[[list|str|int|float], None]
  expects: val.Validator


class ExecutorEnvironment:
  """How the executor interacts with the system (cli, filesystem, http)"""
  def print(self, *args):
    print(*args)

  def error(self, error: str):
    print('Error: ', error)

  def get_file(self, filename: str, _: dict):
    return open(f'output/{filename}', 'wb')


executior_env = ExecutorEnvironment()


class Context:
  """
  State object for the application.
  """
  def __init__(self, executor: 'Executor', env: ExecutorEnvironment = None):
    self.path = []
    self.args = []
    self.kwargs = {}
    self.executor = executor
    self.env = env or ExecutorEnvironment()
    self.shape: Shape | None = None
    self.other: Shape | None = None
    self.volume: Volume | None = None

  @property
  def kwargs_with_args(self):
    dic = dict(self.kwargs)
    dic.update({f'arg{i}': v for i, v in enumerate(self.args)})
    return dic

  def copy(self):
    ctx = Context(self.executor.copy())
    ctx.path = self.path[:]
    ctx.args = self.args[:]
    ctx.kwargs = dict(self.kwargs)
    ctx.shape = None if self.shape is None else self.shape.copy()
    ctx.other = None if self.other is None else self.other.copy()
    ctx.volume = self.volume
    ctx.env = self.env
    return ctx
  
  async def process(self, config: dict|None=None):
    await self.executor.process(self, config)
  
  def merge(self):
    self.shape.merge(self.other)
    self.other = None

  async def save(self, filename):
    props = {'volume': self.volume.to_dict()}
    async with await self.env.get_file(filename, props) as fh:
      self.shape.save(filename, fh=fh)

  async def print(self, *args):
    if len(args) == 1 and isinstance(args[0], str):
      args = args[0]
    else:
      args = json.dumps(args)
    await self.env.print(f'[{".".join(self.path)}] {args}')

  async def error(self, *args):
    if len(args) == 1 and isinstance(args[0], str):
      args = args[0]
    else:
      args = json.dumps(args)
    await self.env.error(f'[{".".join(self.path)}] {args}')

class Executor():
  def __init__(self):
    self.index: list[ExecutorFunction] = []
    self.map: dict[str, ExecutorFunction] = dict()
    self.config = {}

  def wrap(self, name: str|None = None, expected: val.Validator|None=None):
    """
    Functino wrapper that registers an action and its name, while 
    maintaing order
    """
    def inner(func: typing.Callable):
      name_ = name or func.__name__
      async def wrapped(input, ctx: Context):
        if expected is not None:
          try:
            expected.test(input)
          except val.ValidationError as e:
            await ctx.error(f'Expected {e.msg}, got {type(input).__name__}')
            raise AbortError()
        return await func(input, ctx)
      wrapped.__doc__ = func.__doc__
      self.index.append(name_)
      self.map[name_] = ExecutorFunction(name_, wrapped, expected)
      return wrapped
    return inner

  async def process(self, ctx: Context, config: dict|None):
    """
    Run the executor functions over the context's config in the order declared
    by the wrap method.
    """
    try:
      config = dict(config)
    except Exception as e:
      print(config)
      raise e
    self.config = config

    missing = [k for k in config.keys() if k not in self.map]
    if missing:
      await ctx.error(f'Unrecognized key(s): [{" ".join(missing)}]')
      raise AbortError()

    for name in self.index:
       if name not in config:
         continue
       ctx.path.append(name)
       value = config[name]
       try:
        if self.map[name].expects != val.commands:
          if isinstance(value, (dict, list)):
            cp = json.loads(json.dumps(value))
            value = self.evaluate(cp, ctx.kwargs_with_args)
        del config[name]
        await (self.map[name].func)(value, ctx)
       except val.ValidationError as e:
         await ctx.print(e.msg)
         raise AbortError()
       ctx.path.pop()
    return True
  
  def evaluate(self, value, kwargs):
    """
    Searches a given value for eval blocks, and if found, searches for any
    nested strings and evaluates those.
    """
    def _find(value, test, mutator):
      if test(value):
        return mutator(value)
      if isinstance(value, dict):
        for k, v in value.items():
          value[k] = _find(v, test, mutator)
      if isinstance(value, list):
        for i, v in enumerate(value):
          value[i] = _find(v, test, mutator)
      return value
    
    def _is_evaluable(val):
      return isinstance(val, dict) and 'eval' in val
    
    def _is_string(val):
      return isinstance(val, str)
    
    def _process_string(val):
      return parser.parse(val, kwargs)

    def _eval(value):
      try:
        return _find(value['eval'], _is_string, _process_string)
      except AssertionError as e:
        if 'else' in value:
          try:
            return _find(value['else'], _is_string, _process_string)
          except AssertionError as e:
            raise val.ValidationError(e.args[0])
        raise val.ValidationError(e.args[0])
    
    return _find(value, _is_evaluable, _eval)

  def copy(self):
    executor = Executor()
    executor.map = self.map
    executor.index = self.index
    executor.config = dict(self.config)
    return executor


executor = Executor()


@executor.wrap(expected=val.iterate_input)
async def iterate(args: list, ctx: Context):
  """
  Iterates the current execution scope across the given arguments.

  If the argument is an array of numbers, the  behavior is similar to
  Python's `for i in range(...)`, adding the index to the context staack. 
  
  If given a list of key/value pairs (a dictionary or map), each iteration
  will have the set of keys and their values added to the context's keyword
  variables.
  """
  if type(args) != list:
    args = [args]
  config = ctx.executor.config
  if type(args) == list:
    if type(args[0]) == int:
      for i in range(*args):
        cpy = ctx.copy()
        cpy.path.append(f'{i}')
        cpy.args.append(i)
        await cpy.process(config)
    elif type(args[0]) == dict:
      for i, kwargs in enumerate(args):
        cpy = ctx.copy()
        cpy.path.append(f'{i}')
        cpy.kwargs.update(kwargs)
        await cpy.process(config)
    else:
      for i, item in enumerate(args):
        cpy = ctx.copy()
        cpy.path.append(f'{i}')
        cpy.args.append(item)
        await cpy.process(config)
  config.clear()


@executor.wrap(expected=val.map)
async def var(kwargs: dict, ctx: Context):
  """
  Given a mapping of key/value pairs, adds the map to the current
  context's keyword variables.
  """
  ctx.kwargs.update(kwargs)


@executor.wrap('print', expected=val.any_)
async def print_(message, ctx: Context):
  """Prints the given argument"""
  if isinstance(message, str) and '{' in message:
    message = message.format(*ctx.args, **ctx.kwargs_with_args)
  await ctx.print(message)


@executor.wrap(expected=val.any_)
async def error(message, ctx: Context):
  """Prints the given argument as an error message"""
  if isinstance(message, str) and '{' in message:
    message = message.format(*ctx.args, **ctx.kwargs_with_args)
  await ctx.error(message)


@executor.wrap(expected=val.numeric)
async def sleep(how_long: float, ctx: Context):
  await asyncio.sleep(how_long)


@executor.wrap(expected=val.string)
async def base(filename: str, ctx: Context):
  """Load an stl into the subject position."""
  ctx.shape = Shape.load(
    filename.format(*ctx.args, **ctx.kwargs_with_args))
  ctx.shape.zero()
  ctx.volume = ctx.shape.volume


@executor.wrap(expected=val.string)
async def load(filename: str, ctx: Context):
  """Load an stl into the object posiiton."""
  if ctx.other is not None:
    ctx.merge()
  ctx.other = Shape.load(
    filename.format(*ctx.args, **ctx.kwargs_with_args))
  ctx.other.zero()


@executor.wrap(expected=val.any_)
async def invert(_: any, ctx: Context):
  ctx.other.invert()


@executor.wrap(expected=val.numeric)
async def rotate_x(degrees: float, ctx: Context):
  """Rotates around the x axis in degrees"""
  ctx.other.mesh.rotate([0.5, 0, 0], np.radians(degrees))
  ctx.other.zero()


@executor.wrap(expected=val.numeric)
async def rotate_y(degrees: float, ctx: Context):
  """Rotates around the y axis in degrees"""
  ctx.other.mesh.rotate([0, 0.5, 0], np.radians(degrees))
  ctx.other.zero()


@executor.wrap(expected=val.numeric)
async def rotate_z(degrees: float, ctx: Context):
  """Rotates around the z axis in degrees"""
  ctx.other.mesh.rotate([0, 0, 0.5], np.radians(degrees))
  ctx.other.zero()


@executor.wrap(expected=val.or_(val.numeric, val.vec3_numeric))
async def scale(scale: list[float]|float, ctx: Context):
  """Scales the shape"""
  if type(scale) != list:
    scale = [scale] * 3
  ctx.other.scale(*scale)
  ctx.other.zero()
  

@executor.wrap(expected=val.vec3_numeric)
async def set_size(size: list[float], ctx: Context):
  ctx.other.set_size(*size)
  ctx.other.zero()


@executor.wrap(expected=val.vec3_numeric)
async def offset(offsets: list[float], ctx: Context):
  ctx.other.translate(*offsets)


@executor.wrap(expected=val.vec3_numeric)
async def offset_mask(offsets: list[float|int], ctx: Context):
  """
  Given an array of offset multiplyers, offsets
  """
  for i in ctx.args[::-1]:
    if type(i) != int:
      continue
    ctx.other.translate(
      *np.array([float(o) for o in offsets]) * float(i)
    )
    break
  else:
    raise ValueError(f'Unable to find integer in stack: {ctx.args}')


@executor.wrap(expected=val.vec3_numeric)
async def translate(offsets: list[float], ctx: Context):
  """Given a list of [x,y,z] offsets, translate the "object"."""
  ctx.other.translate(*[float(n) for n in offsets])


attachments =  {
  'back_center': (2, lambda b, o: b.back),
  'front_center': (2, lambda b, o: b.front - o.depth),
  'left_center': (0, lambda b, o: b .left - o.width),
  'right_center': (0, lambda b, o: b .right),
  'top_center': (1, lambda b, o: b .top),
  'bottom_center': (1, lambda b, o: b .bottom - o.height),
} 


@executor.wrap(expected=val.enum(sorted(attachments.keys())))
async def attach(style: str, ctx: Context):
  """
  Position the working shape relative to the base shape, relative to the cached
  volume of the base shape. The cached volume is not updated until the `rebase`
  command is called.
  """
  offset = None
  bvol = ctx.volume
  ovol = ctx.other.volume
  offset = [
     bvol.mid_x - ovol.width / 2, 
     bvol.mid_y - ovol.height / 2,
     bvol.mid_z - ovol.depth / 2,
  ]
  if style not in attachments:
    raise ValueError(f'Unrecognized attachment style: "{style}"')
  [i, val] = attachments[style]
  offset[i] = val(bvol, ovol)
  ctx.other.translate(*offset)


@executor.wrap(expected=val.any_)
async def rebase(_, ctx: Context):
  """Merges the shapes and recalculates the working volume."""
  ctx.merge()
  ctx.volume = ctx.shape.volume


@executor.wrap(expected=val.string)
async def save_as(filename: str, ctx: Context):
  """
  Merges the shapes and saves the STL with the given filename. Formatted
  expecting stack and keyword arguments.
  """
  await rebase(None, ctx)
  await ctx.save(filename.format(*ctx.args, **ctx.kwargs_with_args))


def _normalize_configs(configs: list[dict]|dict):
  if type(configs) == dict:
    configs = [configs]
  if type(configs) != list:
    raise ValueError(f"Expected list or dict, got {type(configs)}")
  return configs


@executor.wrap(expected=val.commands)
async def branch(configs: list[dict], ctx: Context):
  """
  Specify parellel execution paths, each with their own copy of the context.
  """
  configs = _normalize_configs(configs)
  for i, cfg in enumerate(configs):
    cpy = ctx.copy()
    cpy.path.append(f'{i}')
    await cpy.process(cfg)


@executor.wrap(expected=val.commands)
async def then(configs: list[dict]|dict, ctx: Context):
  """
  Specify parellel execution paths, with mutations carrying between them.
  """
  configs = _normalize_configs(configs)
  for i, cfg in enumerate(configs):
    ctx.path.append(f'{i}')
    await ctx.process(cfg)
    ctx.path.pop()

@executor.wrap(name='with', expected=val.commands)
async def with_(configs: list[dict]|dict, ctx: Context):
  """
  Starts a new primary shape, and upon exiting the block, switches the
  primary to the secondary.
  """
  configs = _normalize_configs(configs)
  cpy = ctx.copy()
  cpy.shape = None
  cpy.other = None
  for i, cfg in enumerate(configs):
    cpy.path.append(f'{i}')
    await cpy.process(cfg)
    cpy.path.pop()
  ctx.other = cpy.shape
