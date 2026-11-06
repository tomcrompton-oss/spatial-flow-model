"""
command-line runs for the study files: each study's parameters become options, and a value can be any expression
of the constants and calculators, e.g.

  python3 studies/descents.py astroDescend --m 4000000*MS --a 1.025*AU --dt 0.01
  python3 studies/orbits.py compareSingleBodyOrbits --days 24
  python3 studies/light.py list            (the studies in the file, with their defaults)
"""
import argparse
import inspect
import math
import engine.constants
import engine.flow


def value(text):
  """an option's value: an expression of the constants, the calculators, math and numbers; else the text itself"""
  names = dict(vars(engine.constants))
  names.update({k: v for k, v in vars(engine.flow).items() if not k.startswith('_')})
  names['math'] = math
  try:
    return eval(text, {'__builtins__': {}}, names)
  except Exception:
    return text


def main(studies, description):
  """
  studies: {name: (function, {parameter: default expression})} - run the one named on the command line
  """
  parser = argparse.ArgumentParser(description=description)
  sub = parser.add_subparsers(dest='study', metavar='study')
  sub.add_parser('list', help='list the studies and their defaults')
  for name, (function, defaults) in studies.items():
    doc = (inspect.getdoc(function) or '').split('\n')[0]
    p = sub.add_parser(name, help=doc or name, description=inspect.getdoc(function))
    for param in inspect.signature(function).parameters:
      p.add_argument('--' + param, default=defaults.get(param), metavar='EXPR',
                     help='default: %s' % defaults.get(param))
  args = parser.parse_args()
  if args.study in (None, 'list'):
    for name, (function, defaults) in studies.items():
      print('%s(%s)' % (name, ', '.join('%s=%s' % kv for kv in defaults.items())))
    return
  function, defaults = studies[args.study]
  kwargs = {param: value(getattr(args, param)) for param in inspect.signature(function).parameters
            if getattr(args, param) is not None}
  return function(**kwargs)
