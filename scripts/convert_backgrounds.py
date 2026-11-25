"""
convert a published run's old background frames (background_*.csv, seam_*.csv: engine/background_frames.py) into a
backgrounds file (engine/backgrounds.py), without running its study again: the flow is rebuilt from what its logs say
- the bodies and the flow's direction, a plane wave through the plane, or the shear of studies/special_flow.py - and
its results are left as they are. the logs' 'background frames:' lines become 'backgrounds:' lines, and the old
frames files are deleted

  python3 scripts/convert_backgrounds.py docs/runs/<name> [...]

runs whose frames this cannot rebuild (a wave crossing the plane, the binaries' own) are left alone, and said so;
their studies write backgrounds files themselves
"""
import glob
import os
import re
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'studies'))
import numpy as np
from engine.flow import Body, SpecialFlowCalculator
from engine.waves import PlaneWave
from engine.backgrounds import Backgrounds, steadyBackground, LOG_LINE

FRAMES = re.compile(r'^background frames: (.+)$', re.M)
BODY = re.compile(r'^body \d+: mass (\S+) kg .*?x (\S+) m\s+y (\S+) m\s+(black|white)', re.M)
WAVE = re.compile(r'^gravitational wave: plane wave along z: h\+ (\S+), hx (\S+), (\S+) Hz \(phases (\S+), (\S+) rad\), '
                  r'from t = (\S+) s, centred at \((\S+), (\S+)\) m', re.M)


def framesInfo(path):
  """the old frames file's times and the box its grid covers"""
  data = np.loadtxt(path, delimiter=',', skiprows=1, usecols=(0, 1, 2), ndmin=2)
  return np.unique(data[:, 0]), (data[:, 1].min(), data[:, 1].max(), data[:, 2].min(), data[:, 2].max())


def calcFor(text):
  """the steady flow a log describes (bodies at rest), or None"""
  bodies = [Body(float(m), float(x), float(y), black == 'black') for m, x, y, black in BODY.findall(text)]
  if not bodies:
    if 'through u = (0, -k x)' in text or 'through the same flow' in text:   #studies/part1_examples.py's shear
      from special_flow import Shear
      return Shear(True)          #as studies/special_flow.py wrote its frames
    return None
  line = (re.search(r'^flow direction: (.+)$', text, re.M) or [None, ''])[1]
  if 'combined as vectors' in line:
    return SpecialFlowCalculator(bodies, 2, combine='vectors')
  direction = ('g' if line.startswith('along g') else 'eikonal-exact' if 'exact two-body' in line
               else 'eikonal' if 'zero-energy' in line else None)
  return SpecialFlowCalculator(bodies, 2, direction=direction)


def convert(folder):
  logs = sorted(glob.glob(os.path.join(folder, '*.log')))
  groups = {}
  for path in logs:
    text = open(path).read()
    m = FRAMES.search(text)
    if m:
      groups.setdefault(m.group(1).strip(), []).append((path, text))
  if not groups:
    print(folder + ': no background frames')
    return
  files = lambda line: [f.strip() for f in line.split(',')]
  waves = {key: WAVE.search(texts[0][1]) for key, texts in groups.items()}
  if all(waves.values()):
    #plane waves through the plane: one background, each ring's wave a flow straight in space about its centre
    bg = Backgrounds()
    rings = []
    for key, m in waves.items():
      plus, cross, freq, pp, pc, start, cx, cy = (float(v) for v in m.groups())
      wave = PlaneWave(plus=plus, cross=cross, frequency=freq, phasePlus=pp, phaseCross=pc, start=start, centre=(cx, cy))
      times, (x0, x1, y0, y1) = framesInfo(os.path.join(folder, files(key)[-1]))
      rings.append((key, wave, times, (x1 - x0)/2, (cx, cy),
                    'h+ %g, hx %g, %g Hz, phases %g and %g rad' % (plus, cross, freq, pp, pc)))
    b = bg.add('the waves\' flow', 'Each ring sits in its own plane gravitational wave passing straight through the '
               'plane (along z). In the flow model the wave is a flow of space, a shear about the ring\'s centre, '
               'u = (1/2) (h+\' X + hx\' Y, hx\' X - h+\' Y); g is its acceleration. Drawn round each ring: '
               + '; '.join('at (%g, %g) m, %s' % (c[0], c[1], d) for *_, c, d in rings) + '.')
    for key, wave, times, radius, centre, describe in rings:
      b.linear(describe, SpecialFlowCalculator([], 2, wave=wave), centre, radius, list(times))
    name = os.path.basename(os.path.normpath(folder)) + '.backgrounds.json'
    bg.write(os.path.join(folder, name))
    finish(folder, groups, {key: name for key in groups})
    return
  names = {}
  for key, texts in groups.items():
    calc = calcFor(texts[0][1])
    if calc is None:
      print('%s: %s left as frames (not a steady flow this can rebuild)' % (folder, key))
      continue
    flowFile = files(key)[-1]
    _, box = framesInfo(os.path.join(folder, flowFile))
    bg = Backgrounds()
    shear = not getattr(calc, 'bodies', None)
    steadyBackground(bg, calc, box, 'the flow',
                     'Space flowing downwards, ever faster to the right: u = (0, -k x) from x = 0 to %g m, where it'
                     ' reaches 0.8c; still to the left of x = 0, and at 0.8c beyond. Steady and straight down, so space'
                     ' moving with it does not speed up: g is zero.' % calc.WIDTH if shear else None)
    name = re.sub(r'^background_', '', flowFile)[:-4] + '.backgrounds.json'
    bg.write(os.path.join(folder, name))
    names[key] = name
  finish(folder, groups, names)


def finish(folder, groups, names):
  """the logs name the backgrounds files in place of the frames; the old frames files go"""
  for key, name in names.items():
    for path, text in groups[key]:
      with open(path, 'w') as f:
        f.write(text.replace('background frames: %s\n' % key, '%s %s\n' % (LOG_LINE, name)))
    for old in (f.strip() for f in key.split(',')):
      if os.path.exists(os.path.join(folder, old)):
        os.remove(os.path.join(folder, old))
    print('%s: %s -> %s (%.0f kB)' % (folder, key, name, os.path.getsize(os.path.join(folder, name))/1e3))


if __name__ == '__main__':
  for folder in sys.argv[1:]:
    convert(folder)
