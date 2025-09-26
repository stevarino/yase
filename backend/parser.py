"""
Handles variable and statement lookups, creating a syntax tree.

Pass strings to parse() to evaluate them. Use tokenize and parse_tokens()
for more controls over the processing.
"""

import re
import json

class TokenCache:
  def __init__(self):
    self.cache = {}

  def get(self, input: str):
    return self.cache.get(input)
  
  def set(self, input: str, token: 'Token'):
    self.cache[input] = token

global_cache = TokenCache()

def parse(input: str, kwargs: dict, cache: TokenCache|None=global_cache):
  token = None if cache is None else cache.get(input)
  if token is None:
    token = tokenize(input)
    if cache:
      cache.set(input, token)
  return parse_tokens(token, kwargs)


binary_operators = [
  ('*', lambda a, b: a * b),
  ('/', lambda a, b: a / b),
  ('%', lambda a, b: a % b),
  ('+', lambda a, b: a + b),
  ('-', lambda a, b: a - b),
]

functions = {
  'sum': lambda *args: sum(args),
  'avg': lambda *args: sum(args) * 1.0 / len(args),
  'len': lambda *args: len(args),
  'min': lambda *args: min(args),
  'max': lambda *args: max(args),
  'ord': lambda *args: args[0][args[1]],
}

class Token:
  # Set to a closing class if opening
  closer: type['Token'] = None
  is_closer = False
  # regex pattern
  pattern: str = ''
  regex: re.Pattern = None

  def __init__(self, char: int, str_value: str):
    self.char = char
    self.str_value = str_value.strip()
    # linked list
    self.next: 'Token' = None
    self.partner: 'Token' = None

  def value(self, kwargs: dict):
    raise NotImplemented(self.str_value)
  
  def get_next(self):
    if self.closer:
      return self.partner.get_next()
    return self.next
  
  def __repr__(self):
    return f'<{self.__class__.__name__} @ {self.char}>'
  
class ValueToken(Token):
  pass

class OperatorToken(Token):
  pass

class SyntaxToken(Token):
  pass

class Number(ValueToken):
  pattern =  r'-?[0-9.]+'

  def value(self, _):
    if '.' in self.str_value:
      return float(self.str_value)
    return int(self.str_value)

class ArrayEnd(SyntaxToken):
  is_closer = True
  pattern = r',?\s*\]'

class ArrayStart(ValueToken):
  closer = ArrayEnd
  pattern = r'\['

  def value(self, kwargs: dict):
    return list(parser(self.next, kwargs, stop=self.partner))

class Comma(SyntaxToken):
  pattern = r','

class CloseParen(SyntaxToken):
  is_closer = True
  pattern = r',?\s*\)'

class OpenParen(ValueToken):
  pattern = r'\('
  closer = CloseParen

  def value(self, kwargs):
    return next(parser(self.next, kwargs, self.partner))

class Function(ValueToken):
  pattern = r'[a-zA-Z][a-zA-Z0-9_]*\('
  closer = CloseParen

  def value(self, kwargs):
    name = self.str_value.strip('(')
    assert name in functions, f'Unrecognized function: "{name}"'
    args = list(parser(self.next, kwargs, self.partner))
    return functions[name](*args)

class Variable(ValueToken):
  pattern = r'[a-zA-Z][a-zA-Z0-9_]*'

  def value(self, kwargs):
    assert self.str_value in kwargs, f'Unrecognized variable: "{self.str_value}"'
    return kwargs[self.str_value]

class BinaryOp(OperatorToken):
  pattern = f'[{"".join(re.escape(o[0]) for o in binary_operators)}]'

  def value(self, kwargs):
    return self.str_value


def parser(token: Token, kwargs: dict, stop: Token|None = None):
  """Given a linked-list token, generate a flat statement and return its value."""
  statement = []
  while token:
    if token == stop:
      break
    if isinstance(token, Comma):
      yield evaluate_statment(statement)
      statement = []
    elif isinstance(token, (ValueToken, BinaryOp)):
      statement.append(token.value(kwargs))
    else:
      raise AssertionError(f'Unexpected token: {token.__class__.__name__} at {token.char}')
    token = token.get_next()
  if statement:
    yield evaluate_statment(statement)
  return

def parse_tokens(token: Token, kwargs: dict):
  values = list(parser(token, kwargs))
  if len(values) != 1:
    raise AssertionError(
      f'Expected (1) statement, got ({len(values)}) for token at character ({token.char})')
  return values[0]

    
def evaluate_statment(tokens: list[str|int|float|list]):
  """Given a list of flattened statements, evaluate binary operators."""
  def _error(msg):
    raise AssertionError(f'Unable to parse statement - {msg}: {json.dumps(tokens)}')

  if len(tokens) == 1:
    # if isinstance(tokens[0], str):
    #   _error('unexpected string')
    return tokens[0]

  # handle negative/minus - negative numbers should take precedence
  tokens_ = []
  for token in tokens:
    expect_operator = len(tokens_) % 2 == 1
    # expected operator, got something else:
    if expect_operator and not isinstance(token, str):
      # got a negative number, split it
      if isinstance(token, (float, int)) and token < 0:
        tokens_.extend(['-', token * -1])
      else:
        _error(f'expected operator, got "{token}"')
    elif not expect_operator and isinstance(token, str):
      _error(f'unexpected operator "{token}"')
    else:
      tokens_.append(token)
  tokens = tokens_[:]
  if len(tokens) % 2 != 1:
    _error('unbalanced operators')
  for (op, func) in binary_operators:
    queue = tokens_[1:]
    stack = tokens_[:1]
    while queue:
      token = queue.pop(0)
      rhv = queue.pop(0)
      if token != op:
        stack.extend([token, rhv])
        continue
      lhv = stack[-1]
      if isinstance(rhv, list) and not isinstance(lhv, list):
        lhv = [lhv] * len(rhv)
      if isinstance(lhv, list) and not isinstance(rhv, list):
        rhv = [rhv] * len(lhv)
      if isinstance(rhv, list) and isinstance(lhv, list):
        if len(rhv) != len(lhv):
          _error('operations with lists must be of equal size')
        stack[-1] = [func(lhv[i], rhv[i]) for i in range(len(lhv))]
      else:
        stack[-1] = func(lhv, rhv)
    tokens_ = stack
  if len(tokens_) != 1:
    _error('unknown error')
  return tokens_[0]


token_map: type[Token] = [
  OpenParen,
  CloseParen,
  ArrayStart,
  ArrayEnd,
  Comma,
  Number,
  Function,
  Variable,
  BinaryOp,
]

for token in token_map:
  token.regex = re.compile(r'^\s*' + token.pattern)

def tokenize(input: str):
  stack: list[Token] = []
  prev: Token = None
  char = 0
  first: Token|None = None
  while input:
    for token_class in token_map:
      m = token_class.regex.match(input)
      if m:
        token_str = m.group(0)
        input = input[len(token_str):].strip()
        token: Token = token_class(char, token_str)
        if not first:
          first = token
        if prev:
          prev.next = token
        if token.closer:
          stack.append(token)
        if token.is_closer:
          if not stack:
            raise AssertionError(
              f'Unexpected {token.__class__.__name__}'
            )
          if token_class == stack[-1].closer:
            other = stack.pop()
            other.partner = token
            token.partner = other
          else:
            raise AssertionError(
              f'Expected {stack[-1].__class__.__name__}, got {token.__class__.__name__}')

        char += len(token_str)
        prev = token
        break
    else:
      raise AssertionError(
        f'Unrecognized token at character ({char}): {input[:10]}')
  if stack:
    raise AssertionError(
      f'Unclosed f{stack[-1].__class__.__name__} at character ({stack[-1].char})')
  return first
