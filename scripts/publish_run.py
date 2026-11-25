"""
copy a run folder into the website (docs/runs/<name>/) so its pages can embed it in the browser viewer

the viewer configs a study writes name each csv by its absolute path as well as its relative one; the browser viewer
uses the relative one, so the absolute paths (which show where the project lives on this computer) are left out of
the copy, along with the selected result's. a run with a backgrounds file (engine/backgrounds.py) is drawn from it
in the browser, so the older background frames its logs also name (kept for the desktop viewer) are left out, and
their log lines with them

run: python3 scripts/publish_run.py logs/<study>/<run> [name]      (name defaults to the study's name, e.g. gravWave)
then embed it in a page:
  <iframe src="../viewer/index.html?run=../runs/<name>/<view>.full.json" width="100%" height="640"></iframe>
"""
import glob
import json
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNS = os.path.join(ROOT, 'docs', 'runs')


def publish(run, name=None):
  run = os.path.abspath(run)
  name = name or os.path.basename(run).split('_')[0]
  target = os.path.join(RUNS, name)
  if os.path.exists(target):
    shutil.rmtree(target)
  os.makedirs(target)
  logs = [open(p).read() for p in glob.glob(os.path.join(run, '*.log'))]
  skip = set()
  if any(re.search(r'^backgrounds: ', text, re.M) for text in logs):
    for text in logs:
      for line in re.findall(r'^background frames: (.+)$', text, re.M):
        skip.update(f.strip() for f in line.split(','))
  for entry in sorted(os.listdir(run)):
    source = os.path.join(run, entry)
    if not os.path.isfile(source) or entry in skip:
      continue
    if skip and entry.endswith('.log'):
      with open(source) as f:
        text = f.read()
      with open(os.path.join(target, entry), 'w') as f:
        f.write(re.sub(r'^background frames: .+\n', '', text, flags=re.M))
      continue
    if entry.endswith('.config.json'):
      with open(source) as f:
        config = json.load(f)
      for result in config.get('results', []):
        result.pop('path', None)
      config['selected'] = None
      with open(os.path.join(target, entry), 'w') as f:
        json.dump(config, f, indent=2)
    else:
      shutil.copy2(source, target)
  print('published', os.path.relpath(run, ROOT), 'as', os.path.relpath(target, ROOT))
  return target


if __name__ == '__main__':
  if len(sys.argv) < 2:
    sys.exit(__doc__)
  publish(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
