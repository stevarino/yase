#!/bin/env/python3

# Modified from https://pypi.org/project/numpy-stl/#combining-multiple-stl-files

import sys
import yaml
import shutil
import re
import asyncio

from backend.executor import Context, AbortError, executor


def main(config_file: str):
  with open(config_file, 'r') as fp:
    config = yaml.safe_load(fp)
  try:
    asyncio.run(Context(executor).process(config))
  except AbortError:
    pass

def help(*args: str):
  try:
    term_width = shutil.get_terminal_size().columns
  except OSError:
    term_width = 80

  def wrap(msg: str, line_pre: str|None = None,
           first_line: str|None=None, double_line=True):
    for para_no, para in enumerate(msg.strip().split('\n\n')):
      # ignore single line breaks, normalize whitespace
      para = re.sub(r'\s+', ' ', para.replace('\n', ' ')).strip()
      def fmt(line: str, is_first=False):
        pre: str|None = None
        if is_first:
          pre = first_line
        if pre is None:
          pre = line_pre or ''
        return pre + line
      line = fmt(para, para_no == 0)
      while len(line) > term_width:
        i = term_width
        while line[i] != ' ':
          i -= 1
        print(line[:i])
        line = fmt(line[i:].strip())
      print(line)
      if double_line:
        print()

  if len(args) == 1 and args[0] in executor.map:
      print(args[0])
      ef = executor.map[args[0]]
      print(f'Expects: {ef.expects.doc}')
      wrap(ef.func.__doc__)
  else:
    longest = max(len(name) for name in executor.index)
    fmt = f'  {{:{longest}}} - '
    blank = f'  {" " * longest}   '
    for name in executor.index:
      func = executor.map[name].func
      desc = (func.__doc__ or '').split('\n\n')[0]
      wrap(desc, line_pre=blank, first_line=fmt.format(name), double_line=False)
    return

if __name__ == '__main__':
  if len(sys.argv) < 2:
    help()
  elif sys.argv[1] == '--help':
    help(*sys.argv[2:])
  elif sys.argv[1] == '--web':
    from backend.web import app
    app.run()
  else:
    main(sys.argv[1])
