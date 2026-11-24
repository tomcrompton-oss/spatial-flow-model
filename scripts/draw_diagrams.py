"""
the website's diagrams, each drawn once as a list of shapes and written as an SVG in each of three styles, so a style
can be chosen for the whole site:

  formal     thin black lines on white, serif italic labels: a textbook figure
  sketchy    a hand-drawn look: wobbly doubled pencil strokes, hatched fills, handwritten labels, on off-white paper
  blueprint  light technical lines on a blue grid

the site uses formal (CHOSEN); the other two are kept so a page can be tried in them

run: python3 scripts/draw_diagrams.py [--all]     (writes docs/part1/mechanics/images/<diagram>.svg, and the tests'
                                                    diagrams to docs/part1/tests/images/)
"""
import math
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'docs', 'part1', 'mechanics', 'images')

CHOSEN = 'formal'     #the site's style (chosen 2026-11-23); --all also writes the others, as <diagram>-<style>.svg

STYLES = {
  'formal': {'bg': '#ffffff', 'edge': '#d0d0d0', 'ink': '#1a1a1a', 'faint': '#b8b8b8', 'fill': '#f4f1ea',
             'u': '#1f63c4', 'w': '#1b8a4f', 'v': '#c4362a', 'grid': None, 'width': 1.4,
             'leaf': '#e3ecd9', 'bark': '#e2d3b8', 'apple': '#c4362a', 'skin': '#f3e1cf', 'sun': '#f6d98a',
             'font': "'STIX Two Text', 'Times New Roman', Times, serif", 'mathfont': "'STIX Two Math', 'Times New Roman', serif",
             'size': 15, 'caps': False},
  'sketchy': {'bg': '#fbf8ef', 'edge': None, 'ink': '#2b2b2b', 'faint': '#9a968c', 'fill': '#e9dfc4',
              'u': '#2f6fd0', 'w': '#2c9a5c', 'v': '#d0453a', 'grid': None, 'width': 1.6,
              'leaf': '#cfe0bf', 'bark': '#d8c3a0', 'apple': '#d0453a', 'skin': '#f0dcc8', 'sun': '#f2cf6b',
              'font': "'Bradley Hand', 'Segoe Print', 'Chalkboard SE', 'Comic Sans MS', cursive",
              'mathfont': "'Bradley Hand', 'Segoe Print', 'Chalkboard SE', 'Comic Sans MS', cursive", 'size': 17, 'caps': False},
  'blueprint': {'bg': '#17467d', 'edge': None, 'ink': '#e9f2ff', 'faint': '#7fa3cf', 'fill': '#1f5591',
                'u': '#7fd4ff', 'w': '#9df0b4', 'v': '#ffd27a', 'grid': '#245a96', 'width': 1.5,
                'leaf': '#1f5591', 'bark': '#1f5591', 'apple': '#ffd27a', 'skin': '#1f5591', 'sun': '#2a6bb0',
                'font': "'Avenir Next Condensed', 'Arial Narrow', 'Helvetica Neue', Arial, sans-serif",
                'mathfont': "'Avenir Next Condensed', 'Helvetica Neue', Arial, sans-serif", 'size': 14, 'caps': True},
}


# --- the shapes: each diagram is a list of these, in its own pixel coordinates (y down) ---------------------------

def line(a, b, colour='ink', dash=False, width=1.0):
  return ('line', a, b, colour, dash, width)

def arrow(a, b, colour='ink', width=2.0, dash=False):
  return ('arrow', a, b, colour, width, dash)

def rect(x, y, w, h, fill=None, dash=False, colour='ink', radius=0):
  return ('rect', x, y, w, h, fill, dash, colour, radius)

def ellipse(cx, cy, rx, ry, fill='ink', angle=0, colour='ink'):
  return ('ellipse', cx, cy, rx, ry, fill, angle, colour)

def text(x, y, s, colour='ink', size=1.0, anchor='start', math_=False, bold=False):
  return ('text', x, y, s, colour, size, anchor, math_, bold)

def poly(points, colour='ink', width=1.0, dash=False):
  """a curve through points, drawn as short straight pieces"""
  return [('poly', points, colour, width, dash)]

def circle_points(cx, cy, r, a0, a1, n=60):
  return [(cx + r*math.cos(a0 + (a1 - a0)*k/n), cy + r*math.sin(a0 + (a1 - a0)*k/n)) for k in range(n + 1)]

def clock(x, y, r=13):
  """a clock face: a ring and two hands"""
  return [ellipse(x, y, r, r, 'ink', 0, 'ink'), ellipse(x, y, r - 1.6, r - 1.6, 'bg', 0, 'bg'),
          line((x, y), (x, y - r*0.7), 'ink', width=1.0), line((x, y), (x + r*0.5, y + r*0.2), 'ink', width=1.0)]

def near(points, gap):
  """a test for inflow's skip: is (x, y) within gap of any of the points?"""
  return lambda x, y: any(abs(x - px) < gap and abs(y - py) < gap and math.hypot(x - px, y - py) < gap for px, py in points)

def inflow(cx, cy, body, boxes, skip=lambda x, y: False, step=64, length=30):
  """faint arrows of space flowing in towards a body at (cx, cy), shorter further out (as 1/sqrt r)"""
  out = []
  (x0, y0, x1, y1) = boxes
  for x in range(x0, x1 + 1, step):
    for y in range(y0, y1 + 1, step):
      dx, dy = cx - x, cy - y
      r = math.hypot(dx, dy)
      if r < body + 40 or skip(x, y):
        continue
      n = min(length*math.sqrt(160/r), 34)
      out.append(arrow((x, y), (x + dx/r*n, y + dy/r*n), 'faint', 1.0))
  return out

def ant(x, y, heading=0.0, colour='ink', scale=1.7):
  """an ant at (x, y) facing heading (radians, 0 = +x): three body segments, six legs and two feelers"""
  c, s = math.cos(heading), math.sin(heading)
  at = lambda f, g: (x + scale*(f*c - g*s), y + scale*(f*s + g*c))       #f forward, g to the side
  shapes = []
  for f1, g1, f2, g2 in ((-1, 0, -6, -7), (-1, 0, -6, 7), (1, 0, 1, -8), (1, 0, 1, 8), (2, 0, 7, -7), (2, 0, 7, 7)):
    shapes.append(line(at(f1, g1), at(f2, g2), colour, width=0.8))
  for f, rx, ry in ((-7, 5.0, 3.4), (1, 3.0, 2.4), (7, 2.8, 2.6)):
    cx, cy = at(f, 0)
    shapes.append(ellipse(cx, cy, rx*scale, ry*scale, colour, math.degrees(heading), colour))
  for g in (-1.2, 1.2):
    shapes.append(line(at(9, g), at(13, 3*g), colour, width=0.7))
  return shapes


def key(y, items):
  """a row of coloured arrows across the foot of a diagram, each with its symbol and a few words: (x, symbol,
  colour, words)"""
  shapes = []
  for x, sym, col, words in items:
    shapes.append(arrow((x, y - 5), (x + 34, y - 5), col, 2.2))
    shapes.append(text(x + 44, y, sym, col, 1.2, math_=True))
    shapes.append(text(x + 44 + 9.5*len(sym) + 8, y, words, 'ink', 0.9))
  return shapes


def ants():
  """the ants on a sheet of paper: still, then moved - each ant keeps its own w, and is seen moving at u + w"""
  W, H = 760, 340
  shapes = []
  sheet = (230, 160)
  walkers = [((50, 45), (0, 0)), ((70, 112), (55, 0)), ((165, 48), (20, 45))]     #(position on the paper, w)
  u = (62, 36)
  left, ghost = (45, 66), (420, 58)
  right = (ghost[0] + u[0], ghost[1] + u[1])
  shapes.append(text(left[0] + sheet[0]/2, 40, 'The paper still', anchor='middle', bold=True))
  shapes.append(text(right[0] + sheet[0]/2 - 30, 40, 'The paper moved', anchor='middle', bold=True))
  shapes.append(rect(left[0], left[1], *sheet, fill='fill'))
  shapes.append(rect(ghost[0], ghost[1], *sheet, dash=True, colour='faint'))
  shapes.append(rect(right[0], right[1], *sheet, fill='fill'))
  shapes.append(arrow((ghost[0] - 10, ghost[1] + 22), (ghost[0] - 10 + u[0], ghost[1] + 22 + u[1]), 'u', 2.4))
  shapes.append(text(ghost[0] - 14, ghost[1] + 62, 'u', 'u', 1.3, anchor='end', math_=True))
  for (px, py), (wx, wy) in walkers:
    heading = math.atan2(wy, wx) if (wx or wy) else -0.6
    for (ox, oy), moved in ((left, False), (right, True)):
      x, y = ox + px, oy + py
      if moved:
        shapes.append(arrow((x, y), (x + wx + u[0], y + wy + u[1]), 'v', 2.2))
      if wx or wy:
        shapes.append(arrow((x, y), (x + wx, y + wy), 'w', 2.2))
      shapes += ant(x, y, heading)
  shapes += key(305, ((45, 'w', 'w', 'the ant, on the paper'), (290, 'u', 'u', 'the paper'),
                     (450, 'v = u + w', 'v', 'the ant, from outside')))
  return W, H, shapes


def vectors():
  """a particle in a patch of flowing space: u, then w from its tip, and v = u + w"""
  W, H = 760, 330
  shapes = []
  x0, y0, w, h = 40, 40, 330, 250
  shapes.append(rect(x0, y0, w, h, fill='fill', radius=18))
  u = (35, 120)
  for sy, xs in ((x0 + 10, range(75, 330, 60)), (y0 + 122, range(45, 300, 60))):   #the space's flow, the same as u
    for sx in xs:
      shapes.append(arrow((sx, sy), (sx + u[0], sy + u[1]), 'faint', 1.0))
  p = (120, 95)
  wv = (150, -45)
  tip = (p[0] + u[0], p[1] + u[1])
  end = (tip[0] + wv[0], tip[1] + wv[1])
  shapes.append(arrow(p, tip, 'u', 2.6))
  shapes.append(arrow(tip, end, 'w', 2.6))
  shapes.append(arrow(p, end, 'v', 2.6))
  shapes.append(ellipse(p[0], p[1], 6, 6, 'ink'))
  shapes.append(text(p[0] - 30, p[1] - 14, 'particle', 'ink', 0.85, anchor='middle'))
  shapes.append(text(p[0] + u[0]/2 - 16, p[1] + u[1]/2 + 6, 'u', 'u', 1.4, anchor='end', math_=True))
  shapes.append(text(tip[0] + wv[0]/2 + 4, tip[1] + wv[1]/2 + 26, 'w', 'w', 1.4, math_=True))
  shapes.append(text(p[0] + (end[0] - p[0])/2 + 6, p[1] + (end[1] - p[1])/2 - 12, 'v', 'v', 1.4, math_=True))
  lx = 410
  for k, (sym, col, words) in enumerate((('u', 'u', ['the velocity of the space', 'the particle is in']),
                                         ('w', 'w', ["the particle's velocity", 'relative to that space']),
                                         ('v = u + w', 'v', ['its velocity as a distant', 'observer sees it']))):
    y = 85 + k*80
    shapes.append(arrow((lx, y - 5), (lx + 40, y - 5), col, 2.6))
    shapes.append(text(lx + 54, y, sym, col, 1.3, math_=True))
    for n, s in enumerate(words):
      shapes.append(text(lx + 54, y + 22 + n*18, s, 'ink', 0.95))
  return W, H, shapes


def steps():
  """the decomposition of a particle's velocity (v = u + w), and one step of the procedure: 1 to 2 with the space,
  2 to 3 through it"""
  W, H = 760, 340
  shapes = [text(190, 34, 'Decomposition of velocity', anchor='middle', bold=True),
            text(570, 34, 'Incremental steps', anchor='middle', bold=True)]
  p = (150, 120)
  shapes.append(rect(85, 70, 150, 125, fill='fill', dash=True, colour='faint', radius=8))
  shapes.append(text(92, 90, 'its space', 'faint', 0.85))
  u, w = (0, 140), (150, 0)
  shapes += [arrow(p, (p[0] + u[0], p[1] + u[1]), 'u', 2.6), arrow(p, (p[0] + w[0], p[1] + w[1]), 'w', 2.6),
             arrow(p, (p[0] + u[0] + w[0], p[1] + u[1] + w[1]), 'v', 2.6),
             line((p[0] + w[0], p[1]), (p[0] + w[0], p[1] + u[1]), 'faint', dash=True, width=0.8),
             line((p[0], p[1] + u[1]), (p[0] + w[0], p[1] + u[1]), 'faint', dash=True, width=0.8),
             ellipse(p[0], p[1], 6, 6, 'ink'),
             text(p[0] - 12, p[1] + 5, 'p', 'ink', 1.3, anchor='end', math_=True),
             text(p[0] - 10, p[1] + 80, 'u', 'u', 1.4, anchor='end', math_=True),
             text(p[0] + 100, p[1] - 10, 'w', 'w', 1.4, math_=True),
             text(p[0] + 82, p[1] + 66, 'v', 'v', 1.4, math_=True)]
  one, two = (480, 80), (480, 255)
  three = (680, 255)
  shapes += [arrow(one, (two[0], two[1] - 8), 'u', 2.6), arrow(two, (three[0] - 8, three[1]), 'w', 2.6),
             arrow(one, (three[0] - 6, three[1] - 6), 'v', 2.6)]
  for (x, y), n, dx, dy in ((one, '1', -14, 4), (two, '2', -14, 18), (three, '3', 12, 18)):
    shapes += [ellipse(x, y, 6, 6, 'ink'), text(x + dx, y + dy, n, 'ink', 1.0, anchor='middle')]
  shapes += [text(two[0] - 14, (one[1] + two[1])/2 + 6, 'u dt', 'u', 1.3, anchor='end', math_=True),
             text((two[0] + three[0])/2, two[1] + 30, 'w dt', 'w', 1.3, anchor='middle', math_=True),
             text((one[0] + three[0])/2 + 16, (one[1] + three[1])/2 - 8, 'v dt', 'v', 1.3, math_=True)]
  shapes += key(318, ((40, 'u', 'u', 'the space carries it, 1 to 2'), (300, 'w', 'w', 'it moves through the space, 2 to 3'),
                      (590, 'v', 'v', 'the result, 1 to 3')))
  return W, H, shapes


def apple():
  """Newton's apple, to scale, twice. left, Newtonian gravity: the apple at rest 11 m up the tree falls onto the head
  of Newton, sitting with his back to the trunk, at 1 m; faint apples every 0.25 s show it speeding up. right, the
  same in flowing space: space falls at u, and the apple, held still, moves up through it at w = -u"""
  W, H = 900, 500
  ground, m = 462, 30                       #the ground's y, and pixels per metre
  y = lambda h: ground - h*m
  g = 9.82
  t1 = math.sqrt(20/g)
  u = math.sqrt(2*6.6743e-11*5.972e24/(6371000 + 11.0))

  def scene(trunk, before_crown=()):
    """the ground, the tree, Newton and the apple at rest, for a tree at x = trunk; returns them and the apple's x"""
    ax = trunk + 24                         #the apple's line of fall: onto Newton's head
    out = [line((trunk - 150, ground), (trunk + 270, ground), 'ink', width=1.2)]
    for x in range(trunk - 140, trunk + 270, 14):
      out.append(line((x, ground + 1), (x - 8, ground + 9), 'faint', width=0.6))
    out += list(before_crown)
    for (bx, bh), (ex, eh) in (((trunk, 7.6), (trunk - 55, 9.8)), ((trunk, 7.9), (trunk + 55, 10.4)), ((trunk, 9.0), (ax + 14, 11.7))):
      out.append(line((bx, y(bh)), (ex, y(eh)), 'ink', width=1.8))
    out.append(rect(trunk - 13, y(8.0), 26, 8.0*m, fill='bark'))
    for cx, ch, r in ((-60, 10.3, 2.0), (0, 11.6, 2.4), (55, 10.5, 2.0), (-20, 9.4, 1.6), (25, 12.4, 1.6)):
      out.append(ellipse(trunk + cx, y(ch), r*m, r*m, 'leaf', 0, 'leaf'))
    out += [line((ax, y(11.0) - 6), (ax + 3, y(11.6)), 'ink', width=0.9),   #the stalk
            ellipse(ax, y(11), 7, 7, 'apple', 0, 'apple')]
    #Newton, sitting with his back against the trunk, facing away from it, the top of his head at 1 m
    hx = trunk + 18
    out += [line((hx - 1, y(0.08)), (hx + 3, y(0.66)), 'ink', width=2.8),                   #back, against the trunk
            line((hx + 1, y(0.08)), (hx + 23, y(0.42)), 'ink', width=2.8),                  #thigh, knee up
            line((hx + 23, y(0.42)), (hx + 35, y(0.0)), 'ink', width=2.8),                  #shin
            line((hx, y(0.58)), (hx + 19, y(0.40)), 'ink', width=2.2),                      #arm on the knee
            ellipse(ax, y(1.0) + 5, 5, 5, 'ink', 0, 'ink')]
    return out, ax

  shapes = [text(200, 26, 'Newtonian gravity', anchor='middle', bold=True),
            text(680, 26, 'Flowing space', anchor='middle', bold=True)]
  #left: the fall, with where it is every 0.25 s, and the heights
  left, ax = scene(130)
  shapes += left
  shapes.append(line((ax, y(11) + 8), (ax, y(1) - 6), 'faint', dash=True, width=0.8))
  for k in range(2, 6):                     #(0.25 s would hide behind the apple)
    h = 11 - g*(0.25*k)**2/2
    shapes += [('ellipse', ax, y(h), 6, 6, 'faint', 0, 'faint'), text(ax + 12, y(h) + 4, '%.2f s' % (0.25*k), 'faint', 0.75)]
  sx = 395
  shapes.append(line((sx, y(0)), (sx, y(11)), 'ink', width=1.0))
  for h in (0, 1, 11):
    shapes += [line((sx - 5, y(h)), (sx + 5, y(h)), 'ink', width=1.0), text(sx + 10, y(h) + 5, '%d m' % h, 'ink', 0.9)]
  shapes += [line((ax + 12, y(1)), (sx - 8, y(1)), 'faint', dash=True, width=0.8),
             line((ax + 12, y(11)), (sx - 8, y(11)), 'faint', dash=True, width=0.8),
             arrow((sx - 24, y(11) + 4), (sx - 24, y(1) - 2), 'v', 1.6),
             text(sx - 32, y(6), 'falls 10 m', 'v', 0.95, anchor='end'),
             text(sx - 32, y(6) + 18, 'in %.3f s' % t1, 'v', 0.95, anchor='end')]
  #right: space falling at u everywhere (behind the tree), and the apple, held still, moving up through it at -u
  trunk = 610
  field = [arrow((x, yy), (x, yy + 46), 'faint', 1.0) for x in range(trunk - 130, trunk + 271, 52)
           for yy in range(70, ground - 60, 92)]
  right, ax = scene(trunk, field)
  shapes += right
  shapes += [arrow((ax, y(11) + 9), (ax, y(11) + 75), 'u', 2.6), arrow((ax, y(11) - 9), (ax, y(11) - 75), 'w', 2.6),
             text(ax + 10, y(11) + 58, 'u', 'u', 1.3, math_=True), text(ax + 26, y(11) + 58, 'space falling at %.2f km/s' % (u/1e3), 'ink', 0.85),
             text(ax + 10, y(11) - 52, 'w = −u', 'w', 1.3, math_=True), text(ax + 84, y(11) - 52, 'the apple, moving up through it', 'ink', 0.85),
             text(ax + 16, y(11) + 5, 'v = 0', 'v', 1.3, math_=True), text(ax + 74, y(11) + 5, 'so it stays put', 'ink', 0.85)]
  return W, H, shapes

def parallel():
  """space flowing at 0.8c, with a particle moving through it at 0.6c and light at c, both along the flow: seen from
  outside they move at 1.4c and 1.8c"""
  W, H = 760, 330
  c = 190                                   #pixels for c
  x0, y0, w, h = 30, 36, 700, 198
  shapes = [rect(x0, y0, w, h, fill='fill', radius=14), text(x0 + 10, y0 + 18, 'space flowing at 0.8c', 'faint', 0.85)]
  for sy, xs in ((y0 + 30, (230, 480)), (y0 + 102, (480,)), (y0 + 178, (480,))):     #the flow, each arrow the length of u
    for sx in xs:
      shapes.append(arrow((sx, sy), (sx + 0.8*c, sy), 'faint', 1.0))
  for (name, py, wc) in (('particle', y0 + 62, 0.6), ('light', y0 + 140, 1.0)):
    px = 80
    ut, wt = px + 0.8*c, px + 0.8*c + wc*c
    shapes += [arrow((px, py), (ut, py), 'u', 2.6), arrow((ut, py), (wt, py), 'w', 2.6),
               arrow((px, py + 26), (wt, py + 26), 'v', 2.6),
               ellipse(px, py, 6, 6, 'ink'), text(px - 12, py + 5, name, 'ink', 0.85, anchor='end'),
               text((px + ut)/2, py - 9, 'u = 0.8c', 'u', 1.1, anchor='middle', math_=True),
               text((ut + wt)/2, py - 9, 'w = %sc' % ('0.6' if wc < 1 else ''), 'w', 1.1, anchor='middle', math_=True),
               text(wt + 10, py + 31, 'v = %.1fc' % (0.8 + wc), 'v', 1.1, math_=True)]
  shapes += [line((80, 262), (80 + c, 262), 'ink', width=1.0), line((80, 256), (80, 268), 'ink', width=1.0),
             line((80 + c, 256), (80 + c, 268), 'ink', width=1.0), text(80 + c/2, 282, 'c', 'ink', 1.1, anchor='middle', math_=True)]
  shapes += key(312, ((40, 'u', 'u', 'the space'), (200, 'w', 'w', 'through the space: never more than c'),
                      (510, 'v', 'v', 'seen from outside')))
  return W, H, shapes


def redshift():
  """light climbing out of a gravitational well: emitted by a clock deep in the well, which ticks slower, and received
  far out at a lower frequency - the same crests, spread out over a longer time"""
  W, H = 760, 340
  cx, cy, R = 70, 150, 62
  shapes = inflow(cx, cy, R, (40, 40, 740, 250), skip=lambda x, y: abs(y - cy) < 75, step=70)
  shapes.append(ellipse(cx, cy, R, R, 'sun', 0, 'sun'))
  shapes.append(text(cx, cy + 5, 'body', 'ink', 0.85, anchor='middle'))
  ex, rx = 160, 690
  shapes += clock(ex, cy) + clock(rx, cy)
  pts, x, phase = [], ex + 22, 0.0
  while x < rx - 24:
    lam = 18 + 70*((x - ex)/(rx - ex))**1.2          #the crests spread out as the light climbs
    pts.append((x, cy - 15*math.sin(phase)))
    phase += 2*math.pi*1.5/lam
    x += 1.5
  shapes += poly(pts, 'v', 2.0)
  shapes += [text(ex, cy - 32, 'emitter, at rₑ', 'ink', 0.9, anchor='middle'),
             text(ex, cy + 36, 'its clock', 'ink', 0.85, anchor='middle'),
             text(ex, cy + 53, 'runs slow', 'ink', 0.85, anchor='middle'),
             text(rx - 10, cy - 32, 'receiver, at rᵣ', 'ink', 0.9, anchor='middle'),
             text(rx, cy + 36, 'far out', 'ink', 0.85, anchor='middle'),
             text(425, cy + 44, 'the same crests, arriving further apart', 'v', 0.9, anchor='middle'),
             text(390, 286, 'fᵣ / fₑ = √[(1 − rₛ/rₑ) / (1 − rₛ/rᵣ)]', 'ink', 1.2, anchor='middle', math_=True)]
  shapes += [arrow((230, 324), (264, 324), 'faint', 1.0), text(274, 329, 'space flowing in', 'ink', 0.85),
             arrow((420, 324), (454, 324), 'v', 1.8), text(464, 329, 'the light, stretched out', 'ink', 0.85)]
  return W, H, shapes


def bending():
  """starlight grazing the Sun bends towards it, so the star is seen a little away from its true direction (the
  angle much exaggerated)"""
  W, H = 760, 380
  sx, sy, R = 380, 210, 34
  #the light: a path pulled towards the Sun, the pull exaggerated to bend it about 14 degrees
  x, y, vx, vy, k, pts = 40.0, 132.0, 1.0, 0.0, 9.5, []
  while x < 720:
    pts.append((x, y))
    dx, dy = sx - x, sy - y
    r3 = math.hypot(dx, dy)**3
    for _ in range(4):
      vx += k*dx/r3*0.25; vy += k*dy/r3*0.25
      x += vx*0.25; y += vy*0.25
  ex, ey = pts[-1]
  (ax, ay), (bx, by) = pts[-30], pts[-1]
  d = math.hypot(bx - ax, by - ay)
  back = (ex - (bx - ax)/d*700, ey - (by - ay)/d*700)
  t = (ex - 40)/(ex - back[0])
  apparent = (40, ey + (back[1] - ey)*t)
  lines = [(apparent[0] + (ex - apparent[0])*i/40, apparent[1] + (ey - apparent[1])*i/40) for i in range(41)]
  shapes = inflow(sx, sy, R, (40, 40, 740, 330), step=66,
                  skip=near(pts + lines + [(70, 40), (140, 40), (90, 112), (ex, ey + 20), (ex - 60, ey + 20)], 26))
  shapes.append(ellipse(sx, sy, R, R, 'sun', 0, 'sun'))
  shapes.append(text(sx, sy + 5, 'Sun', 'ink', 0.9, anchor='middle'))
  shapes += poly(pts, 'v', 2.2)
  shapes += [line((ex, ey), apparent, 'faint', dash=True, width=0.9), line((ex, ey), (40, 132), 'faint', dash=True, width=0.9)]
  #the angle between them, at the Earth
  a1, a2 = math.atan2(132 - ey, 40 - ex), math.atan2(apparent[1] - ey, 40 - ex)
  shapes += poly(circle_points(ex, ey, 230, a2, a1, 30), 'ink', 1.0)
  am = (a1 + a2)/2
  shapes.append(text(ex + 242*math.cos(am), ey + 242*math.sin(am) + 6, 'δφ', 'ink', 1.2, anchor='end', math_=True))
  for (px, py), name in (((40, 132), 'star'), (apparent, 'where it is seen')):
    shapes.append(ellipse(px, py, 5 if name == 'star' else 4, 5 if name == 'star' else 4, 'ink' if name == 'star' else 'faint'))
    shapes.append(text(px + 10, py - 10, name, 'ink' if name == 'star' else 'faint', 0.85))
  shapes += [ellipse(ex, ey, 6, 6, 'u'), text(ex + 2, ey + 24, 'Earth', 'ink', 0.9, anchor='middle')]
  #the closest approach
  closest = min(pts, key=lambda p: math.hypot(p[0] - sx, p[1] - sy))
  shapes += [line((sx, sy), closest, 'ink', width=0.9), text(closest[0] + 8, (sy - R + closest[1])/2 + 4, 'b', 'ink', 1.2, math_=True)]
  shapes += [arrow((40, 360), (74, 360), 'v', 1.8), text(84, 365, 'the light', 'ink', 0.85),
             arrow((190, 360), (224, 360), 'faint', 1.0), text(234, 365, 'space flowing in', 'ink', 0.85),
             text(730, 365, 'angle exaggerated: 1.75″ for light grazing the Sun', 'faint', 0.85, anchor='end')]
  return W, H, shapes


def precession():
  """an orbit whose closest point to the Sun (the perihelion) moves on a little each time round (much exaggerated),
  against the Newtonian ellipse, which closes"""
  W, H = 760, 460
  sx, sy = 270, 232
  p, e, k = 92, 0.55, 0.92                  #r = p/(1 + e cos k theta): the perihelion advances 2 pi (1/k - 1) an orbit
  shapes = [ellipse(sx, sy, 14, 14, 'sun', 0, 'sun')]
  r = lambda th, k: p/(1 + e*math.cos(k*th))
  at = lambda th, k: (sx + r(th, k)*math.cos(th), sy - r(th, k)*math.sin(th))
  shapes += poly([at(2*math.pi*i/240, 1.0) for i in range(241)], 'faint', 1.0, dash=True)
  turns = 3
  shapes += poly([at(2*math.pi/k*turns*i/900, k) for i in range(901)], 'v', 1.8)
  for n in range(turns + 1):
    th = 2*math.pi*n/k
    px, py = at(th, k)
    shapes += [ellipse(px, py, 4.5, 4.5, 'ink'), text(px + 9*math.cos(th) + 4, py - 9*math.sin(th) + 4, str(n + 1), 'ink', 0.85)]
  th1 = 2*math.pi/k
  shapes += [line((sx, sy), at(0, k), 'ink', width=0.8), line((sx, sy), at(th1, k), 'ink', width=0.8)]
  shapes += poly(circle_points(sx, sy, 34, 0, -(th1 - 2*math.pi), 16), 'ink', 1.0)
  shapes.append(text(sx, sy + 32, 'Sun', 'ink', 0.85, anchor='middle'))
  lx = 520
  shapes += [line((lx, 96), (lx + 36, 96), 'faint', dash=True, width=1.0), text(lx + 46, 101, 'Newtonian: a fixed ellipse', 'ink', 0.9),
             line((lx, 146), (lx + 36, 146), 'v', width=1.8), text(lx + 46, 151, 'flowing space: the', 'ink', 0.9),
             text(lx + 46, 169, 'perihelion moves on', 'ink', 0.9), text(lx + 46, 187, 'each orbit', 'ink', 0.9),
             ellipse(lx + 18, 226, 4.5, 4.5, 'ink'), text(lx + 46, 231, 'successive perihelia', 'ink', 0.9),
             line((lx, 262), (lx + 30, 262), 'ink', width=0.8), line((lx, 262), (lx + 26, 246), 'ink', width=0.8),
             text(lx + 46, 263, 'the angle at the Sun:', 'ink', 0.9), text(lx + 46, 281, 'the advance in one orbit', 'ink', 0.9),
             text(lx, 340, "Mercury: 43″ a century,", 'faint', 0.85), text(lx, 358, '5 × 10⁻⁷ radians an orbit', 'faint', 0.85),
             text(lx, 376, '(here about 30°)', 'faint', 0.85)]
  return W, H, shapes


def shapiro():
  """a radar pulse from the Earth to Venus, on the far side of the Sun, and its echo back: passing close to the Sun
  the round trip takes a little longer than at c in flat space"""
  W, H = 760, 340
  sx, sy, R = 390, 200, 28
  re, rv = 320, 232                         #the orbits' radii (1 and 0.72 AU)
  yl = sy - R - 6                            #the line the signal runs along, just grazing the Sun
  ex, vx = sx - math.sqrt(re**2 - (sy - yl)**2), sx + math.sqrt(rv**2 - (sy - yl)**2)
  shapes = inflow(sx, sy, R, (40, 40, 740, 320), skip=lambda x, y: 140 < y < 190 or y > 250, step=62)
  for rr, x in ((re, ex), (rv, vx)):
    a = math.atan2(yl - sy, x - sx)
    shapes += poly(circle_points(sx, sy, rr, a - 0.35, a + 0.35, 40), 'faint', 1.0, dash=True)
  shapes.append(ellipse(sx, sy, R, R, 'sun', 0, 'sun'))
  shapes.append(text(sx, sy + 5, 'Sun', 'ink', 0.85, anchor='middle'))
  dip = lambda x: 4*math.exp(-((x - sx)/120)**2)           #a little bend towards the Sun
  out = [(x, yl + dip(x)) for x in range(int(ex) + 8, int(vx) - 7, 4)]
  back = [(x, yl - 16 + dip(x)) for x in range(int(vx) - 8, int(ex) + 7, -4)]
  shapes += poly(out, 'v', 2.0) + [arrow(out[-3], (vx - 7, yl), 'v', 2.0)]
  shapes += poly(back, 'v', 1.6, dash=True) + [arrow(back[-3], (ex + 7, yl - 16), 'v', 1.6)]
  shapes += [ellipse(ex, yl, 7, 7, 'u'), text(ex, yl + 26, 'Earth', 'ink', 0.9, anchor='middle'),
             ellipse(vx, yl, 6, 6, 'ink'), text(vx, yl + 26, 'Venus', 'ink', 0.9, anchor='middle'),
             text(250, yl + 24, 'pulse out', 'v', 0.9, anchor='middle'), text(540, yl - 26, 'echo back', 'v', 0.9, anchor='middle'),
             line((sx, yl + 4), (sx, sy - R), 'ink', width=0.8),
             text(sx + 40, yl + 24, 'b ≈ 700,000 km', 'ink', 0.85)]
  shapes += [text(W/2, 282, 'Passing close to the Sun, the round trip takes about 200 µs longer than at c in flat space',
                  'ink', 0.9, anchor='middle'),
             arrow((60, 318), (94, 318), 'v', 1.8), text(104, 323, 'the radar signal', 'ink', 0.85),
             arrow((250, 318), (284, 318), 'faint', 1.0), text(294, 323, 'space flowing in', 'ink', 0.85),
             text(730, 323, 'not to scale', 'faint', 0.85, anchor='end')]
  return W, H, shapes


TESTS = os.path.join(ROOT, 'docs', 'part1', 'tests', 'images')
DIAGRAMS = {'ants': ants, 'vectors': vectors, 'steps': steps, 'apple': apple, 'parallel': parallel,
            'redshift': redshift, 'bending': bending, 'precession': precession, 'shapiro': shapiro}
FOLDER = {'redshift': TESTS, 'bending': TESTS, 'precession': TESTS, 'shapiro': TESTS}     #the rest go in OUT


# --- drawing ----------------------------------------------------------------------------------------------------------

def esc(s):
  return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


class Drawing:
  def __init__(self, style, seed):
    self.st = STYLES[style]
    self.sketchy = style == 'sketchy'
    self.rand = random.Random(seed)
    self.defs = []
    self.clips = 0

  def colour(self, name):
    return self.st.get(name, name) if name else 'none'

  def jitter(self, d):
    return self.rand.uniform(-d, d)

  def rough(self, a, b, colour, width, dash, passes=2):
    """a hand-drawn line: one or two strokes, each slightly bent and offset"""
    (x1, y1), (x2, y2) = a, b
    n = math.hypot(x2 - x1, y2 - y1)
    d = min(1.6, 0.4 + n/220)
    out = []
    for k in range(passes):
      ax, ay, bx, by = x1 + self.jitter(d), y1 + self.jitter(d), x2 + self.jitter(d), y2 + self.jitter(d)
      mx, my = (ax + bx)/2 + self.jitter(d*1.6), (ay + by)/2 + self.jitter(d*1.6)
      out.append('<path d="M%.1f %.1f Q%.1f %.1f %.1f %.1f" fill="none" stroke="%s" stroke-width="%.2f" '
                 'stroke-linecap="round"%s%s/>' % (ax, ay, mx, my, bx, by, colour, width*(1.0 if k == 0 else 0.7),
                 ' stroke-dasharray="6 5"' if dash else '', '' if k == 0 else ' opacity="0.75"'))
    return ''.join(out)

  def straight(self, a, b, colour, width, dash):
    return ('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="%.2f" stroke-linecap="round"%s/>'
            % (*a, *b, colour, width, ' stroke-dasharray="6 5"' if dash else ''))

  def seg(self, a, b, colour, width, dash=False, passes=2):
    return self.rough(a, b, colour, width, dash, passes) if self.sketchy else self.straight(a, b, colour, width, dash)

  def shape(self, s):
    kind = s[0]
    base = self.st['width']
    if kind == 'line':
      _, a, b, colour, dash, width = s
      return self.seg(a, b, self.colour(colour), base*width, dash, passes=1 if width < 1 else 2)
    if kind == 'arrow':
      _, a, b, colour, width, dash = s
      c = self.colour(colour)
      (x1, y1), (x2, y2) = a, b
      n = math.hypot(x2 - x1, y2 - y1)
      ux, uy = (x2 - x1)/n, (y2 - y1)/n
      head = 7 + 2.2*width
      spread = 0.42
      back = (x2 - ux*head*0.8, y2 - uy*head*0.8)
      left = (x2 - head*(ux*math.cos(spread) - uy*math.sin(spread)), y2 - head*(uy*math.cos(spread) + ux*math.sin(spread)))
      right = (x2 - head*(ux*math.cos(-spread) - uy*math.sin(-spread)), y2 - head*(uy*math.cos(-spread) + ux*math.sin(-spread)))
      body = self.seg(a, back if not self.sketchy else (x2, y2), c, width*base*0.8, dash)
      if self.sketchy:
        return body + self.rough(left, (x2, y2), c, width*base*0.8, False, 1) + self.rough(right, (x2, y2), c, width*base*0.8, False, 1)
      return body + '<path d="M%.1f %.1f L%.1f %.1f L%.1f %.1f Z" fill="%s"/>' % (*left, x2, y2, *right, c)
    if kind == 'poly':
      _, pts, colour, width, dash = s
      c = self.colour(colour)
      if self.sketchy and not dash:
        return ''.join(self.rough(a, b, c, base*width, False, 1) for a, b in zip(pts, pts[1:]))
      return ('<polyline points="%s" fill="none" stroke="%s" stroke-width="%.2f" stroke-linecap="round" '
              'stroke-linejoin="round"%s/>' % (' '.join('%.1f,%.1f' % p for p in pts), c, base*width,
                                               ' stroke-dasharray="6 5"' if dash else ''))
    if kind == 'rect':
      _, x, y, w, h, fill, dash, colour, radius = s
      c = self.colour(colour)
      if not self.sketchy:
        return ('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="%g" fill="%s" stroke="%s" stroke-width="%.2f"%s/>'
                % (x, y, w, h, radius, self.colour(fill) if fill else 'none', c, base,
                   ' stroke-dasharray="6 5"' if dash else ''))
      out = ''
      if fill:
        self.clips += 1
        cid = 'c%d' % self.clips
        self.defs.append('<clipPath id="%s"><rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="%g"/></clipPath>' % (cid, x, y, w, h, radius))
        hatch = ''.join(self.rough((x + k, y + h + 4), (x + k + h*0.55 + 8, y - 4), self.colour(fill), 1.6, False, 1)
                        for k in range(-int(h*0.6), int(w) + 10, 9))
        out += '<g clip-path="url(#%s)" opacity="0.6">%s</g>' % (cid, hatch)
      corners = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
      for i in range(4):
        out += self.rough(corners[i], corners[(i + 1) % 4], c, base, dash, 1 if dash else 2)
      return out
    if kind == 'ellipse':
      _, cx, cy, rx, ry, fill, angle, colour = s
      c = self.colour(colour)
      if not self.sketchy:
        return ('<ellipse cx="%.1f" cy="%.1f" rx="%.1f" ry="%.1f" fill="%s" transform="rotate(%.1f %.1f %.1f)"/>'
                % (cx, cy, rx, ry, self.colour(fill), angle, cx, cy))
      pts = []
      start = self.rand.uniform(0, 2*math.pi)
      for k in range(15):
        t = start + k/12*2*math.pi
        r = 1 + self.jitter(0.08)
        pts.append((rx*r*math.cos(t), ry*r*math.sin(t)))
      d = 'M' + ' L'.join('%.1f %.1f' % p for p in pts)
      return ('<g transform="translate(%.1f %.1f) rotate(%.1f)"><path d="%s" fill="%s" fill-opacity="0.85" stroke="%s" '
              'stroke-width="1" stroke-linejoin="round"/></g>' % (cx, cy, angle, d, self.colour(fill), c))
    if kind == 'text':
      _, x, y, words, colour, size, anchor, math_, bold = s
      st = self.st
      font = st['mathfont'] if math_ else st['font']
      if st['caps'] and not math_:
        words = words.upper()
      style = ''
      if math_ and not self.sketchy:
        style += ' font-style="italic"'
      if bold or (math_ and st['caps']):
        style += ' font-weight="600"'
      if st['caps'] and not math_:
        style += ' letter-spacing="0.08em"'
      return ('<text x="%.1f" y="%.1f" fill="%s" font-family="%s" font-size="%.1f" text-anchor="%s"%s>%s</text>'
              % (x, y, self.colour(colour), esc(font), st['size']*size*(0.92 if st['caps'] and not math_ else 1.0),
                 anchor, style, esc(words)))
    raise ValueError(kind)

  def svg(self, W, H, shapes, title):
    st = self.st
    body = ''.join(self.shape(s) for s in shapes)
    back = '<rect width="%d" height="%d" rx="10" fill="%s"%s/>' % (
      W, H, st['bg'], ' stroke="%s"' % st['edge'] if st['edge'] else '')
    if st['grid']:
      back += ''.join('<line x1="%d" y1="0" x2="%d" y2="%d" stroke="%s" stroke-width="%g"/>' % (x, x, H, st['grid'], 1.2 if x % 100 == 0 else 0.6)
                      for x in range(20, W, 20))
      back += ''.join('<line x1="0" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="%g"/>' % (y, W, y, st['grid'], 1.2 if y % 100 == 0 else 0.6)
                      for y in range(20, H, 20))
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" role="img">'
            '<title>%s</title><defs>%s</defs>%s%s</svg>\n' % (W, H, W, H, esc(title), ''.join(self.defs), back, body))


def main():
  for name, make in DIAGRAMS.items():
    W, H, shapes = make()
    folder = FOLDER.get(name, OUT)
    os.makedirs(folder, exist_ok=True)
    for style in (STYLES if '--all' in sys.argv else [CHOSEN]):
      path = os.path.join(folder, '%s.svg' % name if style == CHOSEN else '%s-%s.svg' % (name, style))
      with open(path, 'w') as f:
        f.write(Drawing(style, seed=name).svg(W, H, shapes, name))
      print('wrote', os.path.relpath(path, ROOT))


if __name__ == '__main__':
  main()
