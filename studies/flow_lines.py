"""
outward lines from a white hole and a black hole, 1 AU apart (the whiteAndBlackHole scenario in tests/test_flow_consistency.py)

20 points equally spaced around each body at RSUN from its centre; each starts at the escape speed there, |u|
from Calculator.flow (both bodies), heading directly away from that body's centre. each line is integrated (RK4)
under the combined g of the two bodies until it reaches the other body (within RSUN), comes back to its own
body, or gets MAX_DISTANCE from the origin

writes logs/flowlines/flowlines_<datetime>.log (bodies and where each line ended) and .csv (the lines, with the velocity v
and the flow u at each point) for the viewer

run: python3 studies/flow_lines.py
"""
import csv
import math
import numpy as np
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   #the project folder, for engine/
from engine.flow import Body, Calculator
from engine.logger import Log
from engine.constants import *
from engine.flow_lines import line, START, MAX_DISTANCE

SEP = 0.5*AU            #bodies at (-SEP, 0) and (+SEP, 0), 1 AU apart
LINES = 20              #lines from each body

BODIES = [Body(MS, -SEP, 0, black=False), Body(MS, SEP, 0)]


def main():
  calc = Calculator(BODIES)
  log = Log('flowlines', True, False)
  calc.log = log
  log.logBodies(calc)
  log.print('%d lines from each body, starting %g m out at the escape speed |u|, heading away from its centre'
            % (LINES, START))
  log.print('stop: within %g m of a body, or %g AU from the origin' % (START, MAX_DISTANCE/AU))
  log.print()
  log.print('  %-6s %6s %8s %-18s %-20s %10s %12s' % ('from', 'angle', 'steps', 'end (AU)', 'stopped', 'days', '|v| km/s'))
  ends = {}
  with open(log.file.name[:-4] + '.csv', 'w', newline='') as f:
    out = csv.writer(f)
    out.writerow(['elapsed', 'pos_x', 'pos_y', 'v_x', 'v_y', 'u_x', 'u_y'])
    for home in BODIES:
      name = 'black' if home.black else 'white'
      for n in range(LINES):
        angle = 2*math.pi*n/LINES
        rows, reason, steps = line(calc, home, angle)
        t, pos, v = rows[-1]
        ends[(name, reason)] = ends.get((name, reason), 0) + 1
        log.print('  %-6s %6.0f %8d %-18s %-20s %10.2f %12.2f' % (name, math.degrees(angle), steps,
                  '(%.3f, %.3f)' % (pos[0]/AU, pos[1]/AU), reason, t/DAY, np.linalg.norm(v)/1000))
        for t, pos, vel in rows:
          flow = calc.flow(pos)
          out.writerow([t, pos[0], pos[1], vel[0], vel[1], flow[0], flow[1]])
        out.writerow([''] * 7)   #an empty row ends the line
  log.print()
  for (name, reason), count in sorted(ends.items()):
    log.print('from %s: %d %s' % (name, count, reason))


if __name__ == '__main__':
  main()
