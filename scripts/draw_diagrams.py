"""
the website's diagrams, each drawn once as a list of shapes and written as an SVG in each of three styles, so a style
can be chosen for the whole site:

  formal     thin black lines on white, serif italic labels: a textbook figure
  sketchy    a hand-drawn look: wobbly doubled pencil strokes, hatched fills, handwritten labels, on off-white paper
  blueprint  light technical lines on a blue grid

the site uses formal (CHOSEN); the other two are kept so a page can be tried in them

run: python3 scripts/draw_diagrams.py [--all] [names]     (writes docs/part1/mechanics/images/<diagram>.svg, and the tests'
                                                    diagrams to docs/part1/tests/images/, the black holes page's to docs/part1/images/)
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

def inflow(cx, cy, body, boxes, skip=lambda x, y: False, step=64, length=30, colour='faint'):
  """arrows (faint by default) of space flowing in towards a body at (cx, cy), shorter further out (as 1/sqrt r)"""
  out = []
  (x0, y0, x1, y1) = boxes
  for x in range(x0, x1 + 1, step):
    for y in range(y0, y1 + 1, step):
      dx, dy = cx - x, cy - y
      r = math.hypot(dx, dy)
      if r < body + 40 or skip(x, y):
        continue
      n = min(length*math.sqrt(160/r), 34)
      out.append(arrow((x, y), (x + dx/r*n, y + dy/r*n), colour, 1.0))
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


def regions():
  """light crossing regions of space flowing downwards ever faster (0 to 0.8c): at each crossing the change in the
  flow is added to its velocity through space relativistically, so its w (green) turns upward while staying at c, and
  the path seen from outside (red, v = u + w) curves down"""
  W, H = 760, 440
  n, top, width, gap, shift = 6, 50, 92, 14, 12
  def add(a, b):
    """a seen from space moving at -b: a boosted by b (as engine/flow.py's add), in units of c"""
    bb = b[0]**2 + b[1]**2
    ab = a[0]*b[0] + a[1]*b[1]
    par = (b[0]*ab/bb, b[1]*ab/bb)
    per = (a[0] - par[0], a[1] - par[1])
    k = math.sqrt(1 - bb)
    return tuple((par[i] + b[i] + k*per[i])/(1 + ab) for i in range(2))
  shapes = []
  us = [-0.8*k/(n - 1) for k in range(n)]            #each region's flow, downwards (y up)
  w = (1.0, 0.0)
  x, y = 70.0, 170.0
  pts, marks = [(x, y)], []
  for k in range(n):
    x0 = 40 + k*(width + gap)
    shapes.append(rect(x0, top + k*shift, width, 220, dash=True, colour='faint'))
    if k:
      shapes.append(arrow((x0 + width/2, top + k*shift + 226), (x0 + width/2, top + k*shift + 232 + 60*abs(us[k])), 'u', 1.6))
    if k:
      w = add(w, (0.0, us[k - 1] - us[k]))           #crossing in: the change in the flow, added relativistically
    v = (w[0], w[1] + us[k])
    marks.append(((x, y), w, v))
    t = (x0 + width + gap/2 - x)/v[0] if k < n - 1 else (x0 + width - 20 - x)/v[0]
    x, y = x + v[0]*t, y - v[1]*t
    pts.append((x, y))
  shapes += poly(pts, 'v', 1.4, dash=True)
  L = 62
  for (px, py), w_, v_ in marks:
    shapes += [arrow((px, py), (px + L*w_[0], py - L*w_[1]), 'w', 1.6), ellipse(px, py, 4, 4, 'ink')]
  (px, py), w_, v_ = marks[-1]
  size = math.hypot(*v_)
  shapes.append(arrow((px, py), (px + L*v_[0]/size*1.1, py - L*v_[1]/size*1.1), 'v', 1.8))
  shapes += [text(40, 30, 'space flowing down, faster in each region:', 'ink', 0.85),
             text(40 + width/2, top + 220 + 24, 'still', 'faint', 0.8, anchor='middle'),
             text(40 + 5*(width + gap) + width/2 + 12, top + 5*shift + 232 + 60*0.8 - 4, '0.8c', 'u', 0.85),
             arrow((40, 415), (74, 415), 'u', 1.6), text(84, 420, 'u, the flow', 'ink', 0.85),
             arrow((200, 415), (234, 415), 'w', 1.6), text(244, 420, 'w, through its region: always c', 'ink', 0.85),
             line((460, 415), (494, 415), 'v', dash=True, width=1.4), text(504, 420, 'the path', 'ink', 0.85),
             arrow((590, 415), (624, 415), 'v', 1.8), text(634, 420, 'v, seen from outside', 'ink', 0.85)]
  return W, H, shapes


def spacefall():
  """the hypothesis: space falling into a body at the escape speed, faster closer in - the speed a particle falling
  from rest far away would have there"""
  W, H = 760, 400
  cx, cy, R = 220, 195, 60
  shapes = [ellipse(cx, cy, R, R, 'sun', 0, 'sun'), text(cx, cy + 5, 'body', 'ink', 0.9, anchor='middle')]
  for r, a0, n in ((1.45, 0.0, 12), (2.05, 0.26, 16), (2.75, 0.0, 20)):
    for k in range(n):
      a = a0 + 2*math.pi*k/n
      L = 40/math.sqrt(r)
      x, y = cx + R*r*math.cos(a), cy + R*r*math.sin(a)
      if a0 == 0.0 and r == 1.45 and k == 0:
        continue
      shapes.append(arrow((x, y), (x - L*math.cos(a), y - L*math.sin(a)), 'u', 1.4))
  #a particle falling from far away, beside the space at the same place: the same velocity
  px, py = cx + R*1.45 + 6, cy
  shapes += [ellipse(px + 10, py - 14, 6, 6, 'v'), arrow((px + 2, py - 14), (px + 2 - 40/math.sqrt(1.45), py - 14), 'v', 1.8)]
  x0 = 470
  shapes += [arrow((x0, 110), (x0 + 34, 110), 'u', 1.4), text(x0 + 44, 115, 'space falling in at the escape speed,', 'ink', 0.85),
             text(x0 + 44, 133, 'u = √(2GM/r): faster closer in', 'ink', 0.85, math_=False),
             ellipse(x0 + 17, 176, 6, 6, 'v'), text(x0 + 44, 181, 'a particle that has fallen from rest', 'ink', 0.85),
             text(x0 + 44, 199, 'far away: it moves just as the', 'ink', 0.85),
             text(x0 + 44, 217, 'space around it does', 'ink', 0.85),
             text(W/2, 372, 'Space flows straight in from every direction, with no swirl.', 'ink', 0.85, anchor='middle')]
  return W, H, shapes


def fourclocks():
  """the four clocks round a body with space falling in: 1 far away at rest (the base time), 2 falling from rest far
  away with the space (at rest in its space: no dilation), 3 held still on the surface (moving up through its space
  at u: dilated, as general relativity has it), 4 thrown up from the surface at the escape speed (moving through its
  space faster still: more dilated)"""
  W, H = 760, 470
  cx, cy, R = 140, 180, 62
  shapes = inflow(cx, cy, R, (30, 40, 430, 320), skip=near([(cx + R + 16, cy), (cx + 70, cy - 92), (cx + 96, cy + 70)], 44), step=58,
                  colour='u')
  shapes += [ellipse(cx, cy, R, R, 'sun', 0, 'sun'), text(cx, cy + 5, 'body', 'ink', 0.85, anchor='middle')]
  c3 = (cx + R + 15, cy)                                  #3 held still on the surface: moving up through space at u
  shapes += clock(*c3) + [arrow((c3[0] + 16, cy), (c3[0] + 66, cy), 'w', 2.2),
                          text(c3[0] + 42, cy - 10, 'w = u', 'w', 1.0, anchor='middle', math_=True),
                          text(c3[0], cy + 34, '3', 'ink', 1.15, anchor='middle', bold=True)]
  c2 = (cx + 70, cy - 92)                                 #2 falling with the space
  shapes += clock(*c2) + [arrow((c2[0] - 12, c2[1] + 11), (c2[0] - 40, c2[1] + 38), 'u', 2.2),
                          text(c2[0] + 20, c2[1] + 30, 'w = 0', 'u', 1.0, math_=True),
                          text(c2[0], c2[1] - 22, '2', 'ink', 1.15, anchor='middle', bold=True)]
  a = math.atan2(70, 96)
  c4 = (cx + 96, cy + 70)                                 #4 thrown up from the surface at the escape speed
  shapes += clock(*c4) + [arrow((c4[0] + 12*math.cos(a), c4[1] + 12*math.sin(a)), (c4[0] + 66*math.cos(a), c4[1] + 66*math.sin(a)), 'v', 2.2),
                          text(c4[0] + 66, c4[1] + 26, 'w ≈ 2u', 'v', 1.0, math_=True),
                          text(c4[0] - 22, c4[1] + 24, '4', 'ink', 1.15, anchor='middle', bold=True)]
  c1 = (620, 170)
  shapes += clock(*c1) + [text(c1[0], c1[1] + 34, '1', 'ink', 1.15, anchor='middle', bold=True),
                          text(c1[0] + 24, c1[1] + 5, 'at rest, far away', 'ink', 0.85)]
  shapes += [line((470, 40), (470, 320), 'faint', dash=True, width=0.8), text(500, 300, 'far away: space at rest', 'faint', 0.85)]
  rows = (('1', 'far away, at rest in still space', 'the base time'),
          ('2', 'falling in from rest far away, with the space: at rest in its space', 'keeps clock 1\'s time'),
          ('3', 'held still on the surface, where space falls past at u: moving up through it at u', 'runs slow'),
          ('4', 'thrown up from the surface at the escape speed: moving up through space faster than 3', 'runs slower still'))
  for k, (who, what, rate) in enumerate(rows):
    y = 360 + 24*k
    shapes += [text(40, y, who, 'ink', 0.95, bold=True), text(64, y, what, 'ink', 0.85),
               text(720, y, rate, 'ink', 0.85, anchor='end')]
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


def funnel():
  """general relativity's usual picture of a black hole: the curved space around it drawn as a funnel (Flamm's
  paraboloid, z = 2 sqrt(rs (r - rs))), a slice at one moment of Schwarzschild's time, bent into a direction that
  doesn't exist"""
  W, H = 760, 380
  cx, top, s, tilt, drop = 250, 70, 38, 0.3, 0.95
  RMAX = 5.6
  z = lambda r: 2*math.sqrt(max(r - 1, 0))
  P = lambda r, a: (cx + s*r*math.cos(a), top + s*tilt*RMAX + s*tilt*r*math.sin(a) + s*drop*(z(RMAX) - z(r)))
  shapes = []
  for r in (1.0, 1.08, 1.25, 1.55, 2.0, 2.7, 3.6, 4.6, 5.6):
    shapes += poly([P(r, 2*math.pi*k/120) for k in range(121)], 'ink' if r == 1.0 else 'faint', 1.6 if r == 1.0 else 1.0)
  for k in range(16):
    a = 2*math.pi*k/16
    shapes += poly([P(1 + (RMAX - 1)*(j/60)**2, a) for j in range(61)], 'faint', 1.0)
  m = P(2.7, 0.35)
  shapes += [ellipse(m[0], m[1] - 7, 7, 7, 'v'), arrow((m[0] - 12, m[1] + 2), (m[0] - 40, m[1] + 20), 'v', 1.6)]
  t = P(1.0, math.pi/2)
  shapes += [line((t[0], t[1] + 6), (t[0], t[1] + 34), 'ink', width=0.8),
             text(t[0], t[1] + 52, 'the horizon, rₛ', 'ink', 0.9, anchor='middle')]
  x = 530
  shapes += [text(x, 92, 'The usual picture: space around', 'ink', 0.95), text(x, 112, 'the hole as a curved sheet', 'ink', 0.95),
             text(x, 156, 'The dip is drawn into a direction', 'ink', 0.85), text(x, 174, 'that doesn\'t exist.', 'ink', 0.85),
             text(x, 210, 'A marble rolls in only because', 'ink', 0.85), text(x, 228, 'something already pulls it down.', 'ink', 0.85),
             text(x, 264, 'The sheet is one moment of', 'ink', 0.85), text(x, 282, 'Schwarzschild\'s time, and it stops', 'ink', 0.85),
             text(x, 300, 'at the horizon.', 'ink', 0.85)]
  return W, H, shapes


def falling():
  """the flow's picture of a black hole: space falling in everywhere, faster closer in, at c at the horizon and faster
  inside it; on the right, light sent outward against the flow at four distances"""
  W, H = 760, 460
  cx, cy, s, C = 210, 210, 54, 34          #s pixels to rs; an arrow of C pixels on the left is the speed of light
  shapes = [ellipse(cx, cy, s, s, 'fill', 0, 'fill')]
  shapes += poly(circle_points(cx, cy, s, 0, 2*math.pi, 90), 'ink', 1.2, dash=True)
  for r, a0 in ((1.4, 0), (1.95, 0.26), (2.6, 0), (3.3, 0.2)):
    n = 12 if r < 2 else 16 if r < 3 else 20
    for k in range(n):
      a = a0 + 2*math.pi*k/n
      L = C/math.sqrt(r)
      x, y = cx + s*r*math.cos(a), cy + s*r*math.sin(a)
      shapes.append(arrow((x, y), (x - L*math.cos(a), y - L*math.sin(a)), 'u', 1.4))
  shapes += [ellipse(cx, cy, 4, 4, 'ink'), text(cx, cy - 20, 'horizon:', 'ink', 0.75, anchor='middle'),
             text(cx, cy - 6, 'space at c', 'ink', 0.75, anchor='middle'),
             text(cx, cy + 24, 'faster inside', 'ink', 0.75, anchor='middle')]
  x0, xs, xl, L = 450, 600, 640, 56          #the right column: labels, space's arrow, light's arrow; L pixels is c
  shapes += [text(x0, 50, 'Light sent outward', 'ink', 0.95), text(xs, 76, 'space', 'u', 0.85, anchor='end'),
             text(xl, 76, 'light', 'v', 0.85)]
  for k, (r, words) in enumerate(((4, 'gains ground at 0.5c'), (2, 'gains slowly, at 0.29c'),
                                  (1, 'holds still'), (0.6, 'is carried in at 0.29c'))):
    y = 120 + 64*k
    u = 1/math.sqrt(r)
    shapes += [text(x0, y + 5, 'at %g rₛ' % r, 'ink', 0.9), text(x0, y + 25, words, 'ink', 0.8),
               arrow((xs, y), (xs - L*u, y), 'u', 1.6)]
    net = L*(1 - u)
    if abs(net) < 1:
      shapes.append(ellipse(xl + 4, y, 3.5, 3.5, 'v'))
    else:
      shapes.append(arrow((xl + max(0, -net), y), (xl + max(0, net), y), 'v', 1.6))
  shapes += [text(x0, 384, 'light as seen from outside:', 'faint', 0.8), text(x0, 400, 'c through space, less the flow', 'faint', 0.8),
             text(W/2, 432, 'Space falls in at u = c √(rₛ/r): half of c at 4 rₛ, c at the horizon, faster inside.',
                  'ink', 0.85, anchor='middle'),
             ]
  return W, H, shapes


def spacetime():
  """lines of space falling into a black hole, with light cones, drawn against Schwarzschild's time (left) and the
  flow's (Gullstrand-Painleve, right): r across in Schwarzschild radii, t up in rs/c, light at 45 degrees far out"""
  W, H = 760, 450
  PX, TOP, SIDE, RMAX, TMAX = 58, 52, 315, 5.4, 5.2
  f = lambda r: 2*math.sqrt(r) + math.log((math.sqrt(r) - 1)/(math.sqrt(r) + 1))   #GP less Schwarzschild time
  shapes = []
  for left, gp, title in ((48, False, 'against Schwarzschild\'s time'), (418, True, 'against the flow\'s time')):
    P = lambda r, t: (left + r*PX, TOP + SIDE - t*PX)
    inside = lambda r, t: 0 <= r <= RMAX and 0 <= t <= TMAX
    shapes += [arrow(P(0, 0), P(RMAX + 0.25, 0), 'ink', 1.0), arrow(P(0, 0), P(0, TMAX + 0.3), 'ink', 1.0),
               text(*P(RMAX + 0.1, -0.4), 'r', 'ink', 1.1, math_=True), text(*P(-0.35, TMAX + 0.1), 't', 'ink', 1.1, math_=True),
               text(*P(RMAX/2, TMAX + 0.55), title, 'ink', 0.95, anchor='middle')]
    for k in range(1, 6):
      shapes += [line(P(k, 0), P(k, -0.1), 'ink', width=0.8), text(P(k, 0)[0], P(k, -0.42)[1], '%d' % k, 'ink', 0.8, anchor='middle')]
    shapes += [line(P(1, 0), P(1, TMAX), 'ink', dash=True, width=0.9)]
    if gp:
      shapes += [text(P(1, 0)[0] + 5, P(0, TMAX - 0.15)[1], 'horizon', 'ink', 0.8)]
    #lines of falling space: r^1.5 = 1.5 (c0 - t) in the flow's time; Schwarzschild's time is less by f(r)
    for c0 in (1.0, 2.6, 4.0, 5.6, 7.2, 8.8, 10.4):
      pts = []
      for k in range(400):
        r = 0.02 + (RMAX - 0.02)*k/399
        t = c0 - (2/3)*r**1.5
        if not gp:
          if r <= 1.004:
            continue
          t = t - f(r) + f(3.3)        #the two panels agree where the observer (c0 = 4) starts, at t = 0
        if inside(r, t):
          pts.append(P(r, t))
      if len(pts) > 1:
        shapes += poly(pts, 'u' if c0 == 4.0 else 'faint', 2.0 if c0 == 4.0 else 1.0)
    #light cones: the future edges, dr/dt = -sqrt(rs/r) +- c in the flow's time, +-(1 - rs/r) in Schwarzschild's
    for r, t in (((0.5, 1.4), (1.0, 2.6), (1.7, 1.4), (2.7, 2.6), (4.2, 1.4)) if gp else
                 ((1.12, 2.6), (1.7, 1.4), (2.7, 2.6), (4.2, 1.4))):
      x, y = P(r, t)
      for s in ((-1/math.sqrt(r) + 1, -1/math.sqrt(r) - 1) if gp else ((1 - 1/r), -(1 - 1/r))):
        n = math.hypot(s, 1)
        shapes.append(line((x, y), (x + 30*s/n, y - 30/n), 'v', width=1.5))
      shapes.append(ellipse(x, y, 2.6, 2.6, 'v'))
  shapes += [text(W/2, 412, 'r in Schwarzschild radii, t in rₛ/c; light far out at 45°', 'faint', 0.85, anchor='middle'),
             line((60, 438), (94, 438), 'faint', width=1.0), text(104, 443, 'space falling in', 'ink', 0.85),
             line((250, 438), (284, 438), 'u', width=2.0), text(294, 443, 'an observer falling with it', 'ink', 0.85),
             line((500, 438), (534, 438), 'v', width=1.5), text(544, 443, 'light sent out and in', 'ink', 0.85)]
  return W, H, shapes


def twister():
  """a spinning hole from above, in the river model: the river flowing straight in (no swirl), its twist turning
  whatever it carries round with the spin (stronger close in), the horizon, and the ergosphere outside it"""
  W, H = 760, 440
  cx, cy, M = 230, 205, 34                  #M pixels to GM/c^2; spin 0.9
  a = 0.9
  rH = math.hypot(1 + math.sqrt(1 - a*a), a)*M          #flat distances R = sqrt(r^2 + a^2)
  rE = math.hypot(2, a)*M
  shapes = [ellipse(cx, cy, rH, rH, 'fill', 0, 'fill')]
  shapes += poly(circle_points(cx, cy, rH, 0, 2*math.pi, 90), 'ink', 1.2, dash=True)
  shapes += poly(circle_points(cx, cy, rE, 0, 2*math.pi, 120), 'faint', 1.4, dash=True)
  for r, a0, n in ((2.9, 0.0, 12), (3.9, 0.26, 16), (5.0, 0.0, 20)):
    for k in range(n):
      th = a0 + 2*math.pi*k/n
      x, y = cx + M*r*math.cos(th), cy + M*r*math.sin(th)
      L = 34/math.sqrt(r/2)
      shapes.append(arrow((x, y), (x - L*math.cos(th), y - L*math.sin(th)), 'u', 1.3))
  #twist arcs, anticlockwise (with the spin), sweeping further close in
  for r, a0, n in ((2.45, 0.13, 8), (3.4, 0.4, 10), (4.4, 0.15, 12)):
    sweep = 4.6*(2.45/r)**1.6
    for k in range(n):
      th = a0 + 2*math.pi*k/n
      x, y = cx + M*r*math.cos(th), cy + M*r*math.sin(th)
      pts = circle_points(x, y, 8, -math.pi/2, -math.pi/2 - sweep, 20)
      shapes += poly(pts, 'w', 1.2) + [arrow(pts[-3], pts[-1], 'w', 1.0)]
  shapes += [ellipse(cx, cy, 7, 7, 'ink')]
  spin = circle_points(cx, cy, 15, -math.pi/2, -math.pi/2 - 1.5*math.pi, 30)
  shapes += poly(spin, 'ink', 1.2) + [arrow(spin[-3], spin[-1], 'ink', 1.2)]
  x0 = 500
  shapes += [arrow((x0, 120), (x0 + 34, 120), 'u', 1.4), text(x0 + 44, 125, 'the river: straight in,', 'ink', 0.85),
             text(x0 + 44, 143, 'with no swirl', 'ink', 0.85)]
  arc = circle_points(x0 + 17, 190, 9, -math.pi/2, -math.pi/2 - 4.0, 20)
  shapes += poly(arc, 'w', 1.2) + [arrow(arc[-3], arc[-1], 'w', 1.0),
             text(x0 + 44, 186, 'its twist: turning what it', 'ink', 0.85), text(x0 + 44, 204, 'carries, with the spin', 'ink', 0.85)]
  shapes += [line((x0, 250), (x0 + 34, 250), 'ink', dash=True, width=1.2), text(x0 + 44, 255, 'the horizon', 'ink', 0.85),
             line((x0, 286), (x0 + 34, 286), 'faint', dash=True, width=1.4), text(x0 + 44, 291, 'the ergosphere', 'ink', 0.85),
             text(W/2, 425, 'A hole spinning anticlockwise at 0.9 of the most it can, seen from above its equator (not to scale)', 'ink', 0.85, anchor='middle')]
  return W, H, shapes


def bounce():
  """a ball bouncing, filmed and then run backwards: the same arcs, the same pull down, only the direction along them
  reversed"""
  W, H = 760, 330
  shapes = []
  for left, title, sense in ((40, 'forwards', 1), (410, 'run backwards', -1)):
    floor, x0, x1 = 250, left + 20, left + 300
    shapes += [line((left, floor), (left + 320, floor), 'ink', width=1.0), text(left + 160, 40, title, 'ink', 1.0, anchor='middle')]
    for k in range(8):
      shapes.append(line((left + 8 + 40*k, floor), (left + 40*k, floor + 8), 'faint', width=0.8))
    arcs = ((x0, x0 + 110, 120), (x0 + 110, x0 + 200, 80), (x0 + 200, x0 + 270, 52))
    pts = []
    for a, b, h in arcs:
      pts += [(a + (b - a)*j/30, floor - 9 - h*4*(j/30)*(1 - j/30)) for j in range(31)]
    if sense < 0:
      pts = [(2*left + 320 - x, y) for x, y in pts]
    shapes += poly(pts, 'u', 1.4)
    for j in (15, 45, 72):
      a, b = pts[j], pts[j + 2]
      shapes.append(arrow(a, (a[0] + (b[0] - a[0])*3, a[1] + (b[1] - a[1])*3), 'u', 1.6))
    bx, by = pts[-1]
    shapes.append(ellipse(bx, by, 8, 8, 'v'))
    for gx in (left + 140, left + 290):
      shapes += [arrow((gx, 62), (gx, 92), 'w', 1.6), text(gx + 8, 84, 'g', 'w', 1.0, math_=True)]
  shapes += [text(W/2, 304, 'The same arcs, either way: gravity pulls down in both, and the film run backwards is a motion that could happen.',
                  'ink', 0.85, anchor='middle')]
  return W, H, shapes


def reverse():
  """a black hole, and the same film run backwards: space and everything in it flowing out of the horizon - not
  something a black hole can do, but a different object, a white hole"""
  W, H = 760, 400
  shapes = []
  for cx, title, out in ((200, 'a black hole', False), (560, 'the film run backwards', True)):
    cy, s = 190, 50
    shapes += [ellipse(cx, cy, s, s, 'fill', 0, 'fill')] + poly(circle_points(cx, cy, s, 0, 2*math.pi, 90), 'ink', 1.2, dash=True)
    shapes += [ellipse(cx, cy, 4, 4, 'ink'), text(cx, 40, title, 'ink', 1.0, anchor='middle')]
    for k in range(12):
      a = 2*math.pi*k/12 + 0.26
      for r in (1.6, 2.5):
        x, y = cx + s*r*math.cos(a), cy + s*r*math.sin(a)
        L = 30/math.sqrt(r)
        d = 1 if out else -1
        if k in (0, 1) and r == 1.6:
          continue
        shapes.append(arrow((x, y), (x + d*L*math.cos(a), y + d*L*math.sin(a)), 'u', 1.2))
    #a traveller crossing the horizon: in, or (run backwards) out
    a = 0.13
    p0, p1 = (cx + s*2.3*math.cos(a), cy + s*2.3*math.sin(a)), (cx + s*0.45*math.cos(a), cy + s*0.45*math.sin(a))
    if out:
      p0, p1 = p1, p0
    shapes += [arrow(p0, p1, 'v', 2.2), ellipse(p0[0], p0[1], 5, 5, 'v')]
  shapes += [text(200, 352, 'space flows in; things cross the horizon inwards', 'ink', 0.85, anchor='middle'),
             text(200, 370, 'and never come out', 'ink', 0.85, anchor='middle'),
             text(560, 352, 'space flows out; things cross the horizon outwards,', 'ink', 0.85, anchor='middle'),
             text(560, 370, 'which a black hole forbids: this is a white hole', 'ink', 0.85, anchor='middle')]
  return W, H, shapes


def outflow():
  """the flow's picture of a white hole: space flowing out, slowing as it goes, so its acceleration g points in; on the
  right, something falling in from far away at four distances - its speed through space, its speed as seen from
  outside and its clock"""
  W, H = 760, 460
  cx, cy, s, C = 210, 210, 54, 34
  shapes = [ellipse(cx, cy, s, s, 'fill', 0, 'fill')]
  shapes += poly(circle_points(cx, cy, s, 0, 2*math.pi, 90), 'ink', 1.2, dash=True)
  for r, a0 in ((1.4, 0), (1.95, 0.26), (2.6, 0), (3.3, 0.2)):
    n = 12 if r < 2 else 16 if r < 3 else 20
    for k in range(n):
      a = a0 + 2*math.pi*k/n
      L = C/math.sqrt(r)
      x, y = cx + s*r*math.cos(a) - L/2*math.cos(a), cy + s*r*math.sin(a) - L/2*math.sin(a)
      shapes.append(arrow((x, y), (x + L*math.cos(a), y + L*math.sin(a)), 'u', 1.4))
  for k in range(6):
    a = 2*math.pi*k/6 + 0.52
    r = 2.3
    x, y = cx + s*r*math.cos(a), cy + s*r*math.sin(a)
    shapes.append(arrow((x, y), (x - 16*math.cos(a), y - 16*math.sin(a)), 'w', 2.0))
  shapes += [ellipse(cx, cy, 4, 4, 'ink'), text(cx, cy - 20, 'horizon:', 'ink', 0.75, anchor='middle'),
             text(cx, cy - 6, 'space at c', 'ink', 0.75, anchor='middle'),
             text(cx, cy + 24, 'faster inside', 'ink', 0.75, anchor='middle')]
  x0, xs, xw, L = 440, 610, 650, 56
  shapes += [text(x0, 50, 'Falling in from far away', 'ink', 0.95), text(xs, 76, 'space', 'u', 0.85, anchor='end'),
             text(xw, 76, 'faller', 'v', 0.85)]
  for k, r in enumerate((4, 2, 1.1, 1)):
    y = 120 + 64*k
    u = 1/math.sqrt(r)
    w = 2*u/(1 + u*u)
    v = w - u
    clock = (1 - u*u)/(1 + u*u)
    shapes += [text(x0, y + 5, 'at %g rₛ' % r, 'ink', 0.9),
               text(x0, y + 25, 'through space %.3gc, clock %s' % (w, '%.2f' % clock if clock > 0 else 'stopped'), 'ink', 0.8),
               arrow((xs - L*u, y), (xs, y), 'u', 1.6)]
    if v*L > 1:
      shapes.append(arrow((xw + v*L, y), (xw, y), 'v', 1.6))
    else:
      shapes.append(ellipse(xw + 4, y, 3.5, 3.5, 'v'))
  shapes += [text(x0, 384, 'faller as seen from outside:', 'faint', 0.8), text(x0, 400, 'its speed through space, less the flow', 'faint', 0.8),
             text(W/2, 432, 'Space flows out at u = c √(rₛ/r), slowing as it goes, so g (green) points in. Light moves at c through the space it is in.',
                  'ink', 0.85, anchor='middle')]
  return W, H, shapes


def whitetime():
  """the fall from far away, passing 1.8 rs at t = 0.8 rs/c, against each hole's own time: into a black hole (the flow's time, space falling in) it
  crosses the horizon; into a white hole (space flowing out) it only creeps towards it, as space carries it back out
  ever faster - the same path through spacetime, the same clock"""
  W, H = 760, 450
  PX, TOP, SIDE, RMAX, TMAX = 58, 52, 315, 5.4, 5.2
  f = lambda r: 2*math.sqrt(r) + math.log((math.sqrt(r) - 1)/(math.sqrt(r) + 1))
  shapes = []
  for left, white, title in ((48, False, 'a black hole, in its own time'), (418, True, 'a white hole, in its own time')):
    P = lambda r, t: (left + r*PX, TOP + SIDE - t*PX)
    inside = lambda r, t: 0 <= r <= RMAX and 0 <= t <= TMAX
    shapes += [arrow(P(0, 0), P(RMAX + 0.25, 0), 'ink', 1.0), arrow(P(0, 0), P(0, TMAX + 0.3), 'ink', 1.0),
               text(*P(RMAX + 0.1, -0.4), 'r', 'ink', 1.1, math_=True), text(*P(-0.35, TMAX + 0.1), 't', 'ink', 1.1, math_=True),
               text(*P(RMAX/2, TMAX + 0.55), title, 'ink', 0.95, anchor='middle')]
    for k in range(1, 6):
      shapes += [line(P(k, 0), P(k, -0.1), 'ink', width=0.8), text(P(k, 0)[0], P(k, -0.42)[1], '%d' % k, 'ink', 0.8, anchor='middle')]
    shapes += [line(P(1, 0), P(1, TMAX), 'ink', dash=True, width=0.9), text(P(1, 0)[0] + 5, P(0, TMAX - 0.15)[1], 'horizon', 'ink', 0.8)]
    #lines of space: in, r^1.5 = 1.5 (c0 - t), or out, r^1.5 = 1.5 (t - c0)
    for c0 in ((1.0, 2.6, 4.0, 5.6, 7.2, 8.8, 10.4) if not white else (-6.4, -4.8, -3.2, -1.6, 0.0, 1.6, 3.2, 4.8)):
      pts = []
      for k in range(400):
        r = 0.02 + (RMAX - 0.02)*k/399
        t = c0 + (2/3)*r**1.5 if white else c0 - (2/3)*r**1.5
        if inside(r, t):
          pts.append(P(r, t))
      if len(pts) > 1:
        shapes += poly(pts, 'faint', 1.0)
    #the fall, at 1.8 rs at t = 0.8 (and further out before): the black hole's time is its clock; the white hole's runs
    #ahead by 2 (f(1.8) - f(r))
    pts = []
    for k in range(3000):
      r = RMAX - (RMAX - (0.02 if not white else 1.0005))*k/2999
      tau = (2/3)*(1.8**1.5 - r**1.5)
      t = 0.8 + (tau - 2*(f(r) - f(1.8)) if white else tau)
      if inside(r, t):
        pts.append(P(r, t))
    shapes += poly(pts, 'v', 2.0)
    #light cones: future edges, dr/dt = -+sqrt(1/r) +- 1
    for r, t in (((0.5, 3.4), (1.0, 2.6), (2.0, 3.4), (2.7, 1.4), (4.2, 3.0)) if not white else
                 ((0.5, 1.4), (1.0, 0.7), (2.0, 4.2), (2.7, 1.4), (4.2, 3.0))):
      x, y = P(r, t)
      d = 1/math.sqrt(r)*(1 if white else -1)
      for sl in (d + 1, d - 1):
        n = math.hypot(sl, 1)
        shapes.append(line((x, y), (x + 30*sl/n, y - 30/n), 'u', width=1.5))
      shapes.append(ellipse(x, y, 2.6, 2.6, 'u'))
  shapes += [text(W/2, 412, 'r in Schwarzschild radii, t in rₛ/c; light far out at 45°', 'faint', 0.85, anchor='middle'),
             line((60, 438), (94, 438), 'faint', width=1.0), text(104, 443, 'lines of flowing space', 'ink', 0.85),
             line((270, 438), (304, 438), 'v', width=2.0), text(314, 443, 'falling in from far away', 'ink', 0.85),
             line((500, 438), (534, 438), 'u', width=1.5), text(544, 443, 'light sent out and in', 'ink', 0.85)]
  return W, H, shapes


def twobodies():
  """two equal bodies at rest: equipotentials of -GM/r1 - GM/r2 (separate rings round each body when deep, a figure
  eight through the centre, one ring round both further out), and space falling at the speed the potential sets,
  sqrt(2GM/r1 + 2GM/r2), along g - which at the centre has no direction"""
  W, H = 760, 440
  cx, cy, S = 320, 210, 112                 #the centre between the bodies, and pixels per unit (bodies at x = -1, +1)
  bodies = ((-1.0, 0.0), (1.0, 0.0))
  k = lambda x, y: sum(1/max(math.hypot(x - bx, y - by), 1e-9) for bx, by in bodies)     #-potential, GM = 1
  P = lambda x, y: (cx + S*x, cy - S*y)
  def crossing(ox, oy, a, level, last):
    """along the ray from (ox, oy) at angle a, the first (or last) r where k falls to level"""
    dx, dy = math.cos(a), math.sin(a)
    rs = [0.02*i for i in range(1, 260)]
    inside = [k(ox + r*dx, oy + r*dy) >= level for r in rs]
    idx = [i for i in range(1, len(rs)) if inside[i - 1] and not inside[i]]
    if not idx:
      return None
    i = idx[-1] if last else idx[0]
    lo, hi = rs[i - 1], rs[i]
    for _ in range(40):
      mid = (lo + hi)/2
      lo, hi = (mid, hi) if k(ox + mid*dx, oy + mid*dy) >= level else (lo, mid)
    return lo
  shapes = []
  #rings round each body (deep levels, and the figure eight's two halves), one ring round both further out
  for level in (3.2, 2.45, 2.0):
    for bx, by in bodies:
      pts = []
      for j in range(241):
        a = 2*math.pi*j/240
        r = crossing(bx, by, a, level, False)
        if r is not None:
          pts.append(P(bx + r*math.cos(a), by + r*math.sin(a)))
      shapes += poly(pts, 'faint', 1.2 if level == 2.0 else 1.0)
  for level in (1.55, 1.2):
    pts = []
    for j in range(241):
      a = 2*math.pi*j/240
      r = crossing(0.0, 0.0, a, level, True)
      pts.append(P(r*math.cos(a), r*math.sin(a)))
    shapes += poly(pts, 'faint', 1.0)
  #space falling at the speed the potential sets, along g
  step = 0.36
  for i in range(-7, 7):
    for j in range(-4, 5):
      x, y = i*step + step/2, j*step
      near = min(math.hypot(x - bx, y - by) for bx, by in bodies)
      if near < 0.36 or math.hypot(x, y) < 0.2:
        continue
      gx = sum((bx - x)/math.hypot(x - bx, y - by)**3 for bx, by in bodies)
      gy = sum((by - y)/math.hypot(x - bx, y - by)**3 for bx, by in bodies)
      g = math.hypot(gx, gy)
      if g == 0:
        continue
      u = math.sqrt(2*k(x, y))
      L = min(12*u, 30)
      a0 = P(x, y)
      shapes.append(arrow(a0, (a0[0] + L*gx/g, a0[1] - L*gy/g), 'u', 1.3))
  for bx, by in bodies:
    shapes += [ellipse(*P(bx, by), 22, 22, 'sun', 0, 'sun')]
  shapes += [text(*P(-1, -0.04), 'M', 'ink', 1.0, anchor='middle', math_=True), text(*P(1, -0.04), 'M', 'ink', 1.0, anchor='middle', math_=True),
             ellipse(cx, cy, 13, 13, 'v'), ellipse(cx, cy, 11, 11, 'bg', 0, 'bg'), text(cx, cy + 6, '?', 'v', 1.1, anchor='middle', bold=True)]
  x0 = 580
  shapes += [arrow((x0, 110), (x0 + 34, 110), 'u', 1.3), text(x0 + 44, 105, 'space falling at', 'ink', 0.85),
             text(x0 + 44, 123, 'the speed the', 'ink', 0.85), text(x0 + 44, 141, 'potential sets,', 'ink', 0.85),
             text(x0 + 44, 159, 'along g', 'ink', 0.85),
             line((x0, 200), (x0 + 34, 200), 'faint', width=1.0), text(x0 + 44, 205, 'equal potential', 'ink', 0.85),
             ellipse(x0 + 17, 250, 11, 11, 'v'), ellipse(x0 + 17, 250, 9, 9, 'bg', 0, 'bg'), text(x0 + 17, 255, '?', 'v', 0.9, anchor='middle', bold=True),
             text(x0 + 44, 246, 'the centre: no', 'ink', 0.85), text(x0 + 44, 264, 'pull, so no', 'ink', 0.85),
             text(x0 + 44, 282, 'direction', 'ink', 0.85),
             text(W/2, 420, 'Two equal bodies at rest. The figure eight is the potential through the centre.', 'ink', 0.85, anchor='middle')]
  return W, H, shapes


def hollowsphere():
  """a hollow sphere: space falls in outside it as round a single body; inside, there is no pull, the potential is
  the surface's everywhere, and the escape speed is the surface's - a speed for the flow, but no direction. right:
  the potential along a line through the centre, flat inside"""
  W, H = 760, 400
  cx, cy, R = 200, 190, 80
  shapes = []
  for k in range(20):
    a = 2*math.pi*k/20 + 0.16
    for r in (1.55, 2.15):
      x, y = cx + R*r*math.cos(a), cy + R*r*math.sin(a)
      L = 34/math.sqrt(r)
      shapes.append(arrow((x, y), (x - L*math.cos(a), y - L*math.sin(a)), 'u', 1.3))
  shapes += [ellipse(cx, cy, R + 7, R + 7, 'sun', 0, 'sun'), ellipse(cx, cy, R - 7, R - 7, 'bg', 0, 'bg')]
  shapes += [text(cx, cy - 24, 'no pull: g = 0', 'ink', 0.85, anchor='middle'),
             text(cx, cy - 4, 'escape speed:', 'ink', 0.85, anchor='middle'),
             text(cx, cy + 14, 'the surface\'s', 'ink', 0.85, anchor='middle'),
             ellipse(cx, cy + 42, 12, 12, 'v'), ellipse(cx, cy + 42, 10, 10, 'bg', 0, 'bg'),
             text(cx, cy + 47, '?', 'v', 1.0, anchor='middle', bold=True),
             text(30, 30, 'a hollow shell: mass M, radius R', 'ink', 0.85)]
  #the potential along the line through the centre
  x0, x1, top, base = 430, 730, 70, 300
  mid = (x0 + x1)/2
  sx = 38                                   #pixels per R
  phi = lambda x: -1/max(abs(x), 1.0)       #in GM/R
  pts = [(mid + sx*x, top + (base - top)*(-phi(x))) for x in [i/50 for i in range(-190, 191)]]
  shapes += [line((x0, top), (x1, top), 'ink', width=0.8), text(x1, top - 8, '0', 'ink', 0.8, anchor='end'),
             line((mid, top - 10), (mid, base + 30), 'faint', width=0.8)]
  shapes += poly(pts, 'v', 1.8)
  for sgn in (-1, 1):
    shapes.append(line((mid + sgn*sx, top), (mid + sgn*sx, base + 14), 'sun', width=3.0))
  shapes += [text(mid, top - 22, 'the potential along a line through the centre', 'ink', 0.85, anchor='middle'),
             text(mid, base + 20, '−GM/R, the same everywhere inside', 'ink', 0.8, anchor='middle'),
             text(x1 - 4, top + 52, '−GM/r outside', 'ink', 0.8, anchor='end'),
             text(mid - sx, base + 46, '−R', 'ink', 0.8, anchor='middle'), text(mid + sx, base + 46, 'R', 'ink', 0.8, anchor='middle'),
             text(W/2, 380, 'Outside, the shell is like a single body of the same mass. Inside, nothing pulls, but the potential is the surface\'s.',
                  'ink', 0.85, anchor='middle')]
  return W, H, shapes


def shelloptions():
  """four ways space could flow through a hollow sphere along the line an object falls through it, each at the
  surface's escape speed inside: the same way as it came in, the way it flows on the far side, towards the centre,
  and out from the centre - and where each meets the flow outside head on, or splits from it"""
  W, H = 760, 590
  left, right, mid = 60, 700, 380
  sx = 56                                   #pixels per R
  shapes = []
  rows = (('the faller', None), ('A  inside, as it came in', [1, 1]), ('B  inside, as on the far side', [-1, -1]),
          ('C  towards the centre', [1, -1]), ('D  out from the centre', [-1, 1]))
  for n, (label, inside) in enumerate(rows):
    y = 60 + 105*n
    shapes += [text(left, y - 22, label, 'ink', 0.9, bold=(n == 0)), line((left, y), (right, y), 'faint', width=0.8)]
    for sgn in (-1, 1):
      shapes.append(line((mid + sgn*sx, y - 16), (mid + sgn*sx, y + 16), 'sun', width=3.0))
    if inside is None:
      #the faller: from rest far to the left, through the sphere at the surface's speed, to rest far to the right
      for x in (-5.2, -4.0, -2.8, -1.7, -0.6, 0.5, 1.6, 2.7, 3.9, 5.1):
        speed = 1/math.sqrt(max(abs(x), 1.0))
        L = 34*speed
        px = mid + sx*x
        shapes.append(arrow((px - L/2, y), (px + L/2, y), 'v', 1.6))
      shapes.append(ellipse(mid + sx*(-5.6), y, 5, 5, 'v'))
      continue
    for x in (-5.2, -4.0, -2.8, -1.7, 1.7, 2.8, 4.0, 5.2):          #outside: in towards the sphere
      L = 34/math.sqrt(abs(x))
      d = 1 if x < 0 else -1
      px = mid + sx*x
      shapes.append(arrow((px - d*L/2, y), (px + d*L/2, y), 'u', 1.4))
    for x, d in ((-0.55, inside[0]), (0.55, inside[1])):           #inside: the surface's speed, each half its way
      px = mid + sx*x
      shapes.append(arrow((px - d*17, y), (px + d*17, y), 'u', 1.4))
    #where flows meet head on (or split apart): at each surface, and at the centre
    meets = []
    if inside[0] != 1:
      meets.append(-1)
    if inside[1] != -1:
      meets.append(1)
    if inside[0] != inside[1]:
      meets.append(0)
    for m in meets:
      shapes += [ellipse(mid + sx*m, y + 30, 4, 4, 'v')]
  shapes += [ellipse(left + 6, H - 26, 4, 4, 'v'), text(left + 18, H - 21, 'where the flow meets itself head on, or splits apart', 'ink', 0.85),
             arrow((470, H - 26), (504, H - 26), 'u', 1.4), text(514, H - 21, 'space', 'ink', 0.85),
             arrow((590, H - 26), (624, H - 26), 'v', 1.6), text(634, H - 21, 'the faller', 'ink', 0.85)]
  return W, H, shapes


def potentialflow():
  """the potential flow round two bodies at rest (the engine's exact two-body eikonal flow): the paths of things falling
  from rest far away, which space flows down, each body's region filled by those that fall into it, and the seam where
  the regions meet; between the bodies the flow leaves the seam on both sides - left, two equal bodies; right, one
  four times the other"""
  sys.path.insert(0, ROOT)
  import numpy as np
  from engine.flow import Body, SpecialFlowCalculator
  from engine.constants import MS, AU
  from engine.backgrounds import seamAround
  W, H = 760, 420
  shapes = []
  for left, masses, title in ((20, (1.0, 1.0), 'two equal bodies'), (400, (1.0, 0.25), 'one four times the other')):
    calc = SpecialFlowCalculator([Body(masses[0]*MS, x=-0.5*AU), Body(masses[1]*MS, x=0.5*AU)], 2, 'eikonal-exact')
    calc.warn = lambda m: None
    S, cx, cy = 118, left + 170, 200          #pixels per AU, the centre
    P = lambda x, y: (cx + S*x, cy - S*y)
    inside = lambda x, y: abs(x) < 1.42 and abs(y) < 1.45
    #paths in from far away, followed down the flow (its direction) until they reach a body
    starts = [(3.0*math.cos(a), 3.0*math.sin(a)) for a in [2*math.pi*(k + 0.5)/28 for k in range(28)]]
    #and paths that leave the seam, either side of it, all along it: between the bodies, space comes from the seam
    for y0 in [-1.3 + 2.6*k/10 for k in range(11)]:
      xs = [i/400 for i in range(-400, 401)]
      reg = [calc.region(np.array([x*AU, y0*AU])) for x in xs]
      cross = next(xs[i] for i in range(1, len(xs)) if reg[i] != reg[i - 1])
      for dx in (-0.004, 0.004):
        starts.append((cross + dx, y0))
    for sx, sy in starts:
      x, y = sx, sy
      pts = []
      for _ in range(4000):
        u = calc.flow(np.array([x*AU, y*AU]), calc.region(np.array([x*AU, y*AU])), 0.0)
        n = math.hypot(*u)
        if not n or min(math.hypot(x + 0.5, y), math.hypot(x - 0.5, y)) < 0.05:
          break
        x, y = x + 0.012*u[0]/n, y + 0.012*u[1]/n
        if inside(x, y):
          pts.append(P(x, y))
      if len(pts) > 6:
        shapes += poly(pts, 'u', 1.0)
        k = len(pts)//3
        shapes.append(arrow(pts[k - 2], pts[k], 'u', 1.2))
    for line_ in seamAround(lambda q: calc.region(q), np.zeros(2), 0.005*AU, 3*AU, cells=(120, 96)):
      pts = [P(q[0]/AU, q[1]/AU) for q in line_ if inside(q[0]/AU, q[1]/AU)]
      if len(pts) > 1:
        shapes += poly(pts, 'v', 1.8, dash=True)
    for (bx, m) in ((-0.5, masses[0]), (0.5, masses[1])):
      r = 16*math.sqrt(m)
      shapes.append(ellipse(*P(bx, 0), r, r, 'sun', 0, 'sun'))
    shapes += [text(cx, 24, title, 'ink', 0.95, anchor='middle')]
  shapes += [line((150, 400), (184, 400), 'u', width=1.0), text(194, 405, 'the flow: in from far away, or out of the seam', 'ink', 0.85),
             line((500, 400), (534, 400), 'v', dash=True, width=1.8), text(544, 405, 'the seam', 'ink', 0.85)]
  return W, H, shapes


def threebodies():
  """the potential flow round three equal bodies at the corners of a triangle (the engine's eikonal flow from tables):
  each body's region filled by the flow into it, and three seams meeting at the centre, where g is zero"""
  sys.path.insert(0, ROOT)
  import numpy as np
  from engine.flow import Body, SpecialFlowCalculator
  from engine.constants import MS, AU
  from engine.backgrounds import seamAround
  W, H = 760, 450
  side = 1.0
  bodies = [(side/math.sqrt(3)*math.cos(a), side/math.sqrt(3)*math.sin(a)) for a in (math.pi/2, math.pi/2 + 2*math.pi/3, math.pi/2 + 4*math.pi/3)]
  calc = SpecialFlowCalculator([Body(MS, x=bx*AU, y=by*AU) for bx, by in bodies], 2, 'eikonal')
  calc.warn = lambda m: None
  S, cx, cy = 150, 290, 220
  P = lambda x, y: (cx + S*x, cy - S*y)
  inside = lambda x, y: abs(x) < 1.75 and abs(y) < 1.3
  starts = [(3.0*math.cos(a), 3.0*math.sin(a)) for a in [2*math.pi*(k + 0.5)/30 for k in range(30)]]
  #and paths leaving each seam on both sides, all along it
  for a in (-math.pi/2, math.pi/6, 5*math.pi/6):
    for k in range(1, 9):
      d = 0.15*k
      x0, y0 = d*math.cos(a), d*math.sin(a)
      n = (-math.sin(a), math.cos(a))
      for s_ in (-0.004, 0.004):
        starts.append((x0 + s_*n[0], y0 + s_*n[1]))
  for sx, sy in starts:
    x, y = sx, sy
    pts = []
    for _ in range(3000):
      q = np.array([x*AU, y*AU])
      u = calc.flow(q, calc.region(q), 0.0)
      n_ = math.hypot(*u)
      if not n_ or min(math.hypot(x - bx, y - by) for bx, by in bodies) < 0.05:
        break
      x, y = x + 0.012*u[0]/n_, y + 0.012*u[1]/n_
      if inside(x, y):
        pts.append(P(x, y))
    if len(pts) > 6:
      shapes = locals().setdefault('shapes', [])
      shapes += poly(pts, 'u', 1.0)
      k = len(pts)//3
      shapes.append(arrow(pts[k - 2], pts[k], 'u', 1.2))
  shapes = locals()['shapes']
  for line_ in seamAround(lambda q: calc.region(q), np.zeros(2), 0.005*AU, 3*AU, cells=(160, 120)):
    pts = [P(q[0]/AU, q[1]/AU) for q in line_ if inside(q[0]/AU, q[1]/AU)]
    if len(pts) > 1:
      shapes += poly(pts, 'v', 1.8, dash=True)
  for bx, by in bodies:
    shapes.append(ellipse(*P(bx, by), 15, 15, 'sun', 0, 'sun'))
  x0 = 580
  shapes += [line((x0, 150), (x0 + 30, 150), 'u', width=1.0), text(x0 + 38, 146, 'the flow: in from', 'ink', 0.85),
             text(x0 + 38, 164, 'far away, or out of', 'ink', 0.85), text(x0 + 38, 182, 'a seam', 'ink', 0.85),
             line((x0, 222), (x0 + 30, 222), 'v', dash=True, width=1.8), text(x0 + 38, 218, 'the seams, meeting', 'ink', 0.85),
             text(x0 + 38, 236, 'at the centre, where', 'ink', 0.85), text(x0 + 38, 254, 'g is zero', 'ink', 0.85),
             text(W/2, 438, 'Three equal bodies at rest, at the corners of a triangle 1 AU across.', 'ink', 0.85, anchor='middle')]
  return W, H, shapes


def watershed():
  """the seam and the hollow sphere's boundaries, along a line: inside the hollow sphere (option D) space splits at the
  centre; between two bodies, the potential flow splits at the seam, flowing away towards each body - and something
  crossing either changes reference frame, keeping its velocity relative to the boundary"""
  W, H = 760, 300
  left, right, mid = 60, 700, 380
  sx = 56
  shapes = []
  #the hollow sphere, option D
  y = 70
  shapes += [text(left, y - 26, 'the hollow sphere, option D: space splits at the centre', 'ink', 0.9),
             line((left, y), (right, y), 'faint', width=0.8)]
  for sgn in (-1, 1):
    shapes.append(line((mid + sgn*sx*2, y - 16), (mid + sgn*sx*2, y + 16), 'sun', width=3.0))
  for x in (-5.2, -4.0, -2.9, 2.9, 4.0, 5.2):
    L = 34/math.sqrt(abs(x)/2)
    d = 1 if x < 0 else -1
    px = mid + sx*x
    shapes.append(arrow((px - d*L/2, y), (px + d*L/2, y), 'u', 1.4))
  for x, d in ((-1.0, -1), (1.0, 1)):
    shapes.append(arrow((mid + sx*x - d*17, y), (mid + sx*x + d*17, y), 'u', 1.4))
  shapes += [line((mid, y - 20), (mid, y + 20), 'v', dash=True, width=1.6)]
  #two bodies, the potential flow along the line through them
  y = 190
  shapes += [text(left, y - 26, 'two bodies, the potential flow: space splits at the seam', 'ink', 0.9),
             line((left, y), (right, y), 'faint', width=0.8)]
  for sgn in (-1, 1):
    shapes.append(ellipse(mid + sgn*sx*2.5, y, 12, 12, 'sun', 0, 'sun'))
  speed = lambda x: math.sqrt(1/abs(x + 2.5) + 1/abs(x - 2.5))
  for x in (-5.4, -4.3, -3.4, -1.6, -0.6, 0.6, 1.6, 3.4, 4.3, 5.4):
    towards = -2.5 if x < 0 else 2.5
    d = 1 if towards > x else -1
    L = min(16*speed(x), 40)
    px = mid + sx*x
    shapes.append(arrow((px - d*L/2, y), (px + d*L/2, y), 'u', 1.4))
  shapes += [line((mid, y - 20), (mid, y + 20), 'v', dash=True, width=1.6), text(mid, y + 36, 'seam: g = 0', 'v', 0.85, anchor='middle')]
  shapes += [line((70, 270), (104, 270), 'v', dash=True, width=1.6),
             text(114, 275, 'where space splits: crossing it, something changes reference frame, keeping its velocity relative to it', 'ink', 0.85)]
  return W, H, shapes


def stretched():
  """curved space round two bodies at rest: each small circle of space stretched across the potential flow, by u^2/c^2
  (much exaggerated: by u^2 here over the largest u^2 drawn), along the flow unchanged; the flow behind, faint"""
  sys.path.insert(0, ROOT)
  import numpy as np
  from engine.flow import Body, SpecialFlowCalculator
  from engine.constants import MS, AU
  W, H = 760, 430
  calc = SpecialFlowCalculator([Body(MS, x=-0.5*AU), Body(MS, x=0.5*AU)], 2, 'eikonal-exact')
  calc.warn = lambda m: None
  S, cx, cy = 140, 275, 210
  P = lambda x, y: (cx + S*x, cy - S*y)
  shapes = []
  #the flow, faint
  for k in range(24):
    a = 2*math.pi*(k + 0.5)/24
    x, y = 3.0*math.cos(a), 3.0*math.sin(a)
    pts = []
    for _ in range(3000):
      u = calc.flow(np.array([x*AU, y*AU]), calc.region(np.array([x*AU, y*AU])), 0.0)
      n = math.hypot(*u)
      if not n or min(math.hypot(x + 0.5, y), math.hypot(x - 0.5, y)) < 0.06:
        break
      x, y = x + 0.012*u[0]/n, y + 0.012*u[1]/n
      if abs(x) < 1.75 and abs(y) < 1.18:
        pts.append(P(x, y))
    if len(pts) > 4:
      shapes += poly(pts, 'faint', 0.8)
  #small circles of space, stretched across the flow
  #columns either side of the seam (x = 0), none on it, where the flow has two directions
  grid = [((i + 0.5)*0.25, j*0.25) for i in range(-7, 7) for j in range(-4, 5)]
  u2 = {}
  for x, y in grid:
    if min(math.hypot(x + 0.5, y), math.hypot(x - 0.5, y)) < 0.2 or abs(x) < 1e-9 and abs(y) < 1e-9:
      continue
    q = np.array([x*AU, y*AU])
    u = calc.flow(q, calc.region(q), 0.0)
    u2[(x, y)] = u
  top = max(float(u @ u) for u in u2.values())
  for (x, y), u in u2.items():
    a = math.atan2(-u[1], u[0])                           #the flow's direction on screen
    r0 = 8
    across = r0*(1 + 1.1*float(u @ u)/top)
    px, py = P(x, y)
    pts = [(px + r0*math.cos(t)*math.cos(a) - across*math.sin(t)*math.sin(a),
            py + r0*math.cos(t)*math.sin(a) + across*math.sin(t)*math.cos(a)) for t in [2*math.pi*k/40 for k in range(41)]]
    shapes += poly(pts, 'u', 1.1)
  shapes += [line(P(0, 1.2), P(0, -1.2), 'v', dash=True, width=1.4), text(P(0, 1.2)[0], P(0, 1.2)[1] - 8, 'seam', 'v', 0.85, anchor='middle')]
  for bx in (-0.5, 0.5):
    shapes.append(ellipse(*P(bx, 0), 13, 13, 'sun', 0, 'sun'))
  #the key: one small circle of space, enlarged - flat (dashed), and stretched across the flow
  kx, ky, r = 650, 150, 34
  shapes += poly(circle_points(kx, ky, r, 0, 2*math.pi, 60), 'faint', 1.0, dash=True)
  shapes += poly([(kx + r*math.cos(t), ky + 1.55*r*math.sin(t)) for t in [2*math.pi*k/60 for k in range(61)]], 'u', 1.6)
  shapes += [arrow((kx - 78, ky), (kx - 44, ky), 'ink', 1.6), text(kx - 82, ky + 22, 'the flow', 'ink', 0.8, anchor='middle'),
             arrow((kx, ky - r - 2), (kx, ky - 1.55*r - 2), 'v', 1.4), arrow((kx, ky + r + 2), (kx, ky + 1.55*r + 2), 'v', 1.4),
             text(kx + 12, ky - 1.55*r - 14, 'across the flow:', 'v', 0.8, anchor='middle'),
             text(kx + 12, ky - 1.55*r + 0, 'stretched by u²/c²', 'v', 0.8, anchor='middle'),
             line((kx - r, ky - 6), (kx - r, ky + 6), 'ink', width=1.2), line((kx + r, ky - 6), (kx + r, ky + 6), 'ink', width=1.2),
             text(kx, ky + 1.55*r + 34, 'along the flow: unchanged,', 'ink', 0.8, anchor='middle'),
             text(kx, ky + 1.55*r + 50, 'so shorter than across', 'ink', 0.8, anchor='middle'),
             text(kx, ky + 1.55*r + 82, 'dashed: the circle in', 'faint', 0.8, anchor='middle'),
             text(kx, ky + 1.55*r + 98, 'flat space', 'faint', 0.8, anchor='middle'),
             text(kx, ky + 1.55*r + 126, 'much exaggerated: at the', 'faint', 0.8, anchor='middle'),
             text(kx, ky + 1.55*r + 142, 'Earth\'s surface, 2 parts in 10⁸', 'faint', 0.8, anchor='middle'),
             text(W/2, 414, 'Space round two bodies at rest: along the flow, lengths are as before; across it, stretched.', 'ink', 0.85, anchor='middle')]
  return W, H, shapes


def lunarranging():
  """lunar laser ranging: laser pulses from the Earth to reflectors on the Moon and back, the Moon at angle D from the
  Sun; in flat flowing space, where the Moon is on the Sun's side of the seam (D within about 60 degrees of the Sun)
  the flow there points at the Sun, and the range comes out shorter - a term that follows D round each month"""
  W, H = 760, 420
  cx, cy, R = 340, 205, 140
  shapes = []
  #the Moon's orbit, the part on the Sun's side of the seam marked
  shapes += poly(circle_points(cx, cy, R, 0, 2*math.pi, 120), 'faint', 1.0)
  sunSide = circle_points(cx, cy, R, math.pi - math.radians(60), math.pi + math.radians(60), 60)
  shapes += poly(sunSide, 'sun', 5.0)
  #the seam between the Earth's region of flow and the Sun's (schematic): crossing the orbit 60 degrees either side
  a = math.radians(60)
  p1, p2 = (cx - R*math.cos(a), cy - R*math.sin(a)), (cx - R*math.cos(a), cy + R*math.sin(a))
  shapes += poly([(p1[0] + 30*(t - 0.5)**2*4 - 30, p1[1] - 50 + (p2[1] - p1[1] + 100)*t) for t in [k/40 for k in range(41)]], 'v', 1.4, dash=True)
  shapes += [text(p1[0] - 34, p1[1] - 56, 'seam', 'v', 0.85, anchor='middle')]
  #the Earth, the Moon at D = 35 degrees, and the laser
  D = math.radians(35)
  mx, my = cx - R*math.cos(D), cy - R*math.sin(D)
  shapes += [ellipse(cx, cy, 16, 16, 'u'), text(cx + 6, cy + 36, 'Earth', 'ink', 0.9, anchor='middle'),
             ellipse(mx, my, 9, 9, 'faint'), text(mx - 12, my - 16, 'Moon', 'ink', 0.9, anchor='end')]
  ux, uy = (mx - cx)/R, (my - cy)/R
  shapes += [arrow((cx + 18*ux, cy + 18*uy - 4), (mx - 11*ux, my - 11*uy - 4), 'v', 1.6),
             arrow((mx - 11*ux + 2, my - 11*uy + 5), (cx + 18*ux + 2, cy + 18*uy + 5), 'v', 1.6),
             text(mx + 58, my - 20, 'laser pulses,', 'v', 0.8), text(mx + 58, my - 6, 'there and back', 'v', 0.8)]
  #the angle D from the Sun's direction
  shapes += [line((cx - 20, cy), (cx - R - 40, cy), 'ink', dash=True, width=0.8)]
  shapes += poly(circle_points(cx, cy, 52, math.pi, math.pi + D, 20), 'ink', 0.9)
  shapes += [text(cx - 64, cy - 14, 'D', 'ink', 1.0, math_=True)]
  shapes += [arrow((cx - R - 50, cy), (30, cy), 'sun', 3.0), text(34, cy - 12, 'to the Sun, 1 AU', 'ink', 0.85)]
  x0 = 540
  shapes += [line((x0, 110), (x0 + 30, 110), 'sun', width=5.0), text(x0 + 40, 106, 'the Moon on the Sun\'s', 'ink', 0.85),
             text(x0 + 40, 124, 'side of the seam:', 'ink', 0.85), text(x0 + 40, 142, 'in flat flowing space,', 'ink', 0.85),
             text(x0 + 40, 160, 'the range is shorter', 'ink', 0.85),
             text(x0, 220, 'Measured: the term that', 'ink', 0.85), text(x0, 238, 'follows D is (2.8 ± 4.1) mm.', 'ink', 0.85),
             text(x0, 262, 'Flat flowing space: 11 cm.', 'ink', 0.85), text(x0, 286, 'Space stretched across', 'ink', 0.85),
             text(x0, 304, 'the flow: as general', 'ink', 0.85), text(x0, 322, 'relativity has it.', 'ink', 0.85),
             text(W/2, 400, 'Not to scale: the Moon is 384,000 km away, the Sun 150 million km.', 'faint', 0.85, anchor='middle')]
  return W, H, shapes


def jupiterlight():
  """light past Jupiter as radio telescopes see it: two sources, one whose light passes close to Jupiter and one far
  from it, and the angle between them at the telescope; in general relativity the bending with the Sun and Jupiter
  together is the two bendings added, in flat flowing space it is not"""
  W, H = 760, 400
  shapes = []
  tx, ty = 650, 190                      #the telescope
  jx, jy = 380, 222                      #Jupiter, below the ray passing it
  #the ray passing Jupiter, bent towards it; the reference ray, far from it
  near = [(60 + 630*t, 160 + 30*(1 - math.cos(math.pi*t))/2 + 18*math.exp(-((60 + 630*t - jx)/90)**2)*0) for t in [k/60 for k in range(61)]]
  bend = lambda x: 165 + 25*(1/(1 + math.exp(-(x - jx)/30)))
  near = [(x, bend(x)) for x in range(60, tx + 1, 10)]
  shapes += poly(near, 'v', 1.8)
  far = [(x, 60 + (ty - 60)*(x - 60)/(tx - 60)) for x in range(60, tx + 1, 10)]
  shapes += poly(far, 'v', 1.2, dash=True)
  shapes += [ellipse(jx, jy, 22, 22, 'sun', 0, 'sun'), text(jx, jy + 44, 'Jupiter', 'ink', 0.9, anchor='middle'),
             ellipse(60, 165, 5, 5, 'v'), text(60, 152, 'a source', 'ink', 0.8, anchor='middle'),
             ellipse(60, 60, 5, 5, 'v'), text(60, 47, 'a reference source', 'ink', 0.8, anchor='middle'),
             rect(tx - 8, ty - 8, 16, 16, fill='u', colour='u'), text(tx, ty + 30, 'radio telescopes', 'ink', 0.85, anchor='middle'),
             text(tx, ty + 48, 'on the Earth', 'ink', 0.85, anchor='middle')]
  shapes += poly(circle_points(tx, ty, 70, math.pi + 0.035, math.pi + math.atan2(ty - 60, tx - 60), 20), 'ink', 0.9)
  shapes += [text(tx - 60, ty - 62, 'the angle', 'ink', 0.8, anchor='end'), text(tx - 60, ty - 48, 'between them', 'ink', 0.8, anchor='end')]
  shapes += [arrow((jx + 140, 290), (jx + 140, 345), 'sun', 3.0), text(jx + 150, 330, 'to the Sun, 5.2 AU', 'ink', 0.85)]
  shapes += [text(40, 300, 'General relativity: the bending with the Sun and', 'ink', 0.85),
             text(40, 318, 'Jupiter together is each one\'s bending added.', 'ink', 0.85),
             text(40, 342, 'Flat flowing space: 300–400 µas more.', 'ink', 0.85),
             text(40, 360, 'Radio telescopes measure positions to under 10 µas.', 'ink', 0.85),
             text(W - 20, 385, 'the bending much exaggerated', 'faint', 0.8, anchor='end')]
  return W, H, shapes


def peeling():
  """outgoing light near a black hole's horizon, in the flow's time (exact general relativity): space falls in (faint);
  light sent out from just outside the horizon barely gains on the hole at first, its distance from the horizon
  growing tenfold every 4.6 rs/c - peeling away exponentially; light sent out from inside is carried in"""
  W, H = 760, 440
  PX, PT, X0, Y0 = 330, 17, 60, 390          #pixels per rs, per rs/c; r = 0.8 rs at X0; t = 0 at Y0
  P = lambda r, t: (X0 + (r - 0.8)*PX, Y0 - t*PT)
  RMAX, TMAX = 2.1, 21
  F = lambda r: (lambda s: s*s/2 + s + math.log(abs(s - 1)))(math.sqrt(r))
  shapes = [arrow(P(0.8, 0), P(RMAX + 0.04, 0), 'ink', 1.0), arrow(P(0.8, 0), P(0.8, TMAX + 0.6), 'ink', 1.0),
            text(*P(RMAX + 0.04, -2.6), 'r (rₛ)', 'ink', 0.9, anchor='end'), text(P(0.8, 0)[0] - 8, P(0, TMAX)[1], 't (rₛ/c)', 'ink', 0.9, anchor='end')]
  for r in (1.0, 1.5, 2.0):
    shapes += [line(P(r, 0), P(r, -0.35), 'ink', width=0.8), text(P(r, 0)[0], P(r, -1.4)[1], '%g' % r, 'ink', 0.8, anchor='middle')]
  for t in (5, 10, 15, 20):
    shapes += [line(P(0.8, t), (P(0.8, t)[0] - 6, P(0.8, t)[1]), 'ink', width=0.8), text(P(0.8, t)[0] - 10, P(0.8, t)[1] + 4, '%d' % t, 'ink', 0.8, anchor='end')]
  #space falling in: r^1.5 = 1.5 (c0 - t)
  for c0 in range(2, 40, 3):
    pts = []
    for k in range(200):
      r = 0.8 + (RMAX - 0.8)*k/199
      t = c0 - (2/3)*r**1.5
      if 0 <= t <= TMAX:
        pts.append(P(r, t))
    if len(pts) > 1:
      shapes += poly(pts, 'faint', 0.8)
  shapes += [line(P(1, 0), P(1, TMAX), 'ink', dash=True, width=1.2), text(P(1, TMAX)[0] + 6, P(1, TMAX)[1] + 4, 'horizon', 'ink', 0.85)]
  #outgoing light, exact: t = 2[F(r) - F(r0)]
  for eps in (0.3, 0.1, 0.03, 0.01, 0.003, 0.001, 0.0003):
    r0 = 1 + eps
    pts = []
    for k in range(400):
      r = r0 + (RMAX - r0)*(k/399)**2
      t = 2*(F(r) - F(r0))
      if t <= TMAX:
        pts.append(P(r, t))
    shapes += poly(pts, 'v', 1.5)
  for r0 in (0.97, 0.9):              #from inside: carried in
    pts = []
    for k in range(200):
      r = r0 - (r0 - 0.8)*k/199
      t = 2*(F(r) - F(r0))
      if 0 <= t <= TMAX:
        pts.append(P(r, t))
    shapes += poly(pts, 'u', 1.5)
  x0 = 545
  shapes += [line((x0, 90), (x0 + 30, 90), 'v', width=1.5), text(x0 + 38, 86, 'light sent out from', 'ink', 0.85),
             text(x0 + 38, 104, 'just outside', 'ink', 0.85),
             line((x0, 140), (x0 + 30, 140), 'u', width=1.5), text(x0 + 38, 136, 'light sent out from', 'ink', 0.85),
             text(x0 + 38, 154, 'inside: carried in', 'ink', 0.85),
             line((x0, 190), (x0 + 30, 190), 'faint', width=0.8), text(x0 + 38, 195, 'space falling in', 'ink', 0.85),
             text(x0, 250, 'Near the horizon, light\'s', 'ink', 0.85), text(x0, 268, 'distance from it grows', 'ink', 0.85),
             text(x0, 286, 'by a factor of e every', 'ink', 0.85), text(x0, 304, '2 rₛ/c: the rate the', 'ink', 0.85),
             text(x0, 322, 'inflow speeds up across', 'ink', 0.85), text(x0, 340, 'the horizon, c/2rₛ.', 'ink', 0.85)]
  return W, H, shapes


def pairs():
  """where the radiation's energy comes from: a pair from the vacuum's fluctuations at the horizon, one escaping with
  positive energy, its partner carried in with negative energy (as measured far away), so the hole's mass falls"""
  W, H = 760, 330
  hx, y = 330, 150
  shapes = [rect(40, 60, hx - 40, 180, fill='fill', colour='fill'), text(160, 200, 'inside the horizon', 'ink', 0.85, anchor='middle'),
            line((hx, 50), (hx, 250), 'ink', dash=True, width=1.4), text(hx, 40, 'horizon', 'ink', 0.85, anchor='middle')]
  for x in (90, 170, 250, 410, 500, 600, 690):
    for yy in (80, 220):
      L = 46*math.sqrt(140/max(abs(x - 40), 60))
      shapes.append(arrow((x, yy), (x - L, yy), 'u', 1.2))
  #the pair, just outside
  px = hx + 22
  shapes += [ellipse(px, y, 5, 5, 'ink'), text(px + 6, y + 30, 'a pair from the', 'ink', 0.8), text(px + 6, y + 46, 'vacuum\'s fluctuations', 'ink', 0.8)]
  wig = lambda xa, xb: [(xa + (xb - xa)*k/60, y - 2 + 5*math.sin(k/60*(xb - xa)/9)) for k in range(61)]
  shapes += poly(wig(px + 8, px + 230), 'v', 1.6) + [arrow((px + 222, y - 2), (px + 240, y - 2), 'v', 1.6)]
  shapes += poly(wig(px - 8, px - 200), 'u', 1.6) + [arrow((px - 192, y - 2), (px - 210, y - 2), 'u', 1.6)]
  shapes += [text(px + 120, y - 22, 'escapes: positive energy', 'v', 0.85, anchor='middle'),
             text(px + 120, y - 6, '', 'v', 0.85, anchor='middle'),
             text(px - 110, y - 22, 'carried in: negative energy', 'u', 0.85, anchor='middle'),
             text(W/2, 290, 'Each pair adds up to nothing. What escapes is the radiation; what falls in lowers the hole\'s mass by the same.',
                  'ink', 0.85, anchor='middle'),
             arrow((60, 312), (94, 312), 'u', 1.2), text(104, 317, 'space flowing in (energies as measured far away)', 'ink', 0.85)]
  return W, H, shapes


def dumbhole():
  """Unruh's dumb hole: a fluid speeding up through a narrowing channel; where it outruns sound there is a sonic
  horizon, beyond which sound sent upstream is swept downstream - the fluid's black hole"""
  W, H = 760, 330
  y0, top, bottom = 150, 60, 240
  width = lambda x: 90 - 60/(1 + math.exp(-(x - 330)/50))       #the channel's half width, narrowing downstream
  shapes = []
  shapes += poly([(x, y0 - width(x)) for x in range(40, 721, 10)], 'ink', 1.6)
  shapes += poly([(x, y0 + width(x)) for x in range(40, 721, 10)], 'ink', 1.6)
  speed = lambda x: 90/width(x)                                   #the flow speeds up as the channel narrows
  sonic = next(x for x in range(40, 721) if speed(x) >= 2.0)
  for x in range(70, 711, 64):
    L = 14*speed(x)
    shapes.append(arrow((x - L/2, y0), (x + L/2, y0), 'u', 1.3))
  shapes += [line((sonic, y0 - width(sonic) - 14), (sonic, y0 + width(sonic) + 14), 'v', dash=True, width=1.5),
             text(sonic, y0 - width(sonic) - 22, 'sonic horizon', 'v', 0.85, anchor='middle')]
  #sound sent upstream: makes it out on the slow side, swept back on the fast side
  for x, ok in ((200, True), (560, False)):
    yy = y0 + 32
    if ok:
      shapes += poly(circle_points(x, yy, 10, math.pi/2, 3*math.pi/2, 12), 'v', 1.2) + [arrow((x - 14, yy), (x - 44, yy), 'v', 1.2)]
      shapes += [text(x - 30, yy + 24, 'sound gets upstream', 'ink', 0.8, anchor='middle')]
    else:
      shapes += poly(circle_points(x, yy, 10, math.pi/2, 3*math.pi/2, 12), 'v', 1.2) + [arrow((x + 4, yy + 10), (x + 34, yy + 10), 'v', 1.2)]
      shapes += [text(x + 10, yy + 34, 'sound sent upstream', 'ink', 0.8, anchor='middle'), text(x + 10, yy + 50, 'is swept down', 'ink', 0.8, anchor='middle')]
  shapes += [text(40, 30, 'flow speeding up as the channel narrows', 'ink', 0.85),
             text(W/2, 305, 'A dumb hole (Unruh, 1981): sound plays the part of light, and the moving fluid the part of flowing space.',
                  'ink', 0.85, anchor='middle')]
  return W, H, shapes


def carrying():
  """a ball let go beside the moving Earth, both panels seen from the Earth (which moves up the page at V). left, the
  flow's pattern taken along: the space streams past at -V, bent in towards the Earth, and the ball, moving through it
  at V, is thrown forward and over the top (its path from studies/moving_bodies.py, let go one Earth radius up);
  right, the space carried: from the Earth it falls straight in, and the ball falls straight down"""
  W, H = 760, 440
  R = 30                                     #the Earth's radius, px
  V, s0 = 29.78, 11.19                       #km/s: the Earth's speed, and the escape speed at its surface
  #the ball's path taken along, in Earth radii from the Earth (moving_bodies.py, from 0 deg, every 300 s)
  path = [(-2.0, 0.0), (-1.98, 0.13), (-1.90, 0.52), (-1.67, 1.13), (-1.25, 1.86), (-0.67, 2.56), (-0.02, 3.18),
          (0.64, 3.73), (1.27, 4.21)]
  shapes = []
  for left, carried, title in ((20, False, 'the pattern taken along'), (390, True, 'the space carried')):
    ex, ey = left + 150, 250
    shapes += [text(left + 175, 34, title, 'ink', 0.95, anchor='middle', bold=True)]
    for gx in range(-4, 5):
      for gy in range(-5, 4):
        x, y = gx*0.9, gy*0.9 + 0.45           #in Earth radii; y up the page
        r = math.hypot(x, y)
        if r < 1.35 or abs(x) > 4.4 or y > 4.6 or y < -4.4:
          continue
        s = s0/math.sqrt(r)
        ux, uy = -s*x/r, -s*y/r
        if not carried:
          uy -= V
        k = (24/V) if not carried else (24/s0)
        px, py = ex + x*R, ey - y*R
        shapes.append(arrow((px, py), (px + ux*k, py - uy*k), 'faint', 1.1))
    shapes += [ellipse(ex, ey, R, R, 'u'), text(ex, ey + 5, 'Earth', 'fill', 0.8, anchor='middle')]
    bx, by = ex - 2*R, ey
    if carried:
      shapes.append(arrow((bx + 6, by), (ex - R - 3, by), 'w', 2.2))
      shapes.append(text(bx - 10, by + 26, 'falls straight', 'w', 0.85, anchor='end'))
      shapes.append(text(bx - 10, by + 42, 'down', 'w', 0.85, anchor='end'))
    else:
      pts = [(ex + x*R, ey - y*R) for x, y in path]
      shapes += poly(pts[:-1], 'w', 2.2, dash=True) + [arrow(pts[-2], pts[-1], 'w', 2.2)]
      shapes.append(text(bx - 8, by + 22, 'thrown forward', 'w', 0.85, anchor='end'))
      shapes.append(text(bx - 8, by + 38, 'and over the top', 'w', 0.85, anchor='end'))
    shapes += [ellipse(bx, by, 6, 6, 'w'), text(bx - 10, by + 5, 'ball', 'ink', 0.8, anchor='end')]
    shapes += [arrow((left + 330, ey + 20), (left + 330, ey - 40), 'ink', 2.0),
               text(left + 330, ey + 40, 'the Earth', 'ink', 0.8, anchor='middle'),
               text(left + 330, ey + 56, 'moves at V', 'ink', 0.8, anchor='middle')]
  shapes += [arrow((40, 418), (70, 418), 'faint', 1.1), text(78, 423, 'the space, as seen from the Earth', 'ink', 0.85),
             ellipse(410, 418, 6, 6, 'w'), text(424, 423, 'a ball let go at rest beside the Earth', 'ink', 0.85)]
  return W, H, shapes


def grazing():
  """light grazing the Sun on its way to the Earth: undeflected it would go straight on; general relativity bends it
  towards the Sun (870 mas at 2 solar radii); the turning flow, its space squeezed, bends it 9.6 mas less (both
  exaggerated)"""
  W, H = 760, 330
  sx, sy, R = 300, 210, 46
  b = sy - R - 24                              #the ray's closest approach, px
  shapes = [ellipse(sx, sy, R, R, 'sun', 0, 'sun'), text(sx, sy + 5, 'Sun', 'ink', 0.9, anchor='middle'),
            text(30, b - 30, 'a radio signal', 'ink', 0.85), text(30, b - 14, 'from a spacecraft', 'ink', 0.85)]
  x0, x1 = 40, 600
  shapes += [line((x0, b), (x1, b), 'faint', dash=True, width=1.0), text(x1, b - 8, 'undeflected', 'ink', 0.8, anchor='end')]
  W = 800
  def ray(bend):
    pts = []
    for k in range(121):
      x = x0 + (x1 - x0)*k/120
      d = (x - sx)/90.0
      y = b + 90*bend*(d + math.sqrt(1 + d*d))/2   #straight before, turned by bend (as a slope) after
      pts.append((x, y))
    return pts
  gr, turning = ray(0.17), ray(0.11)
  shapes += poly(gr[:-1], 'v', 2.2) + [arrow(gr[-2], gr[-1], 'v', 2.2)]
  shapes += poly(turning[:-1], 'u', 2.0, dash=True) + [arrow(turning[-2], turning[-1], 'u', 2.0, dash=True)]
  shapes += [text(x1 + 12, gr[-1][1] + 5, 'general relativity: 870 mas', 'v', 0.85),
             text(x1 + 12, turning[-1][1] + 5, 'the turning flow: 9.6 mas less', 'u', 0.85),
             text(x1 + 12, gr[-1][1] + 30, '(on to the Earth)', 'ink', 0.8),
             line((sx, sy - R), (sx, b), 'ink', width=0.8), text(sx - 8, sy - R - 4, '2 solar radii from its centre', 'ink', 0.75, anchor='end'),
             text(W/2, H - 12, 'Bends exaggerated, and the turning flow\'s shortfall far more so.', 'ink', 0.8, anchor='middle')]
  return W, H, shapes


def desitter():
  """the Moon's orbit as a gyroscope carried round the Sun: at four places on the Earth's orbit, a quarter of a year
  apart, the Moon's orbit's long axis is drawn against a fixed direction; it turns a little each time (de Sitter's
  precession, 19.2 mas a year, hugely exaggerated). the turning flow's Moon turns half as much"""
  W, H = 800, 460
  sx, sy, A = 290, 230, 170
  shapes = poly(circle_points(sx, sy, A, 0, 2*math.pi, 120), 'faint', 1.0, dash=True)
  shapes += [ellipse(sx, sy, 30, 30, 'sun', 0, 'sun'), text(sx, sy + 5, 'Sun', 'ink', 0.85, anchor='middle')]
  for k, place in enumerate((0.0, -0.5*math.pi, -math.pi, -1.5*math.pi)):
    ex, ey = sx + A*math.cos(place), sy + A*math.sin(place)
    turn = math.radians(12*k)                  #the axis, turned a little more each quarter (exaggerated)
    shapes += [line((ex - 40, ey), (ex + 40, ey), 'faint', dash=True, width=0.8)]
    pts = [(ex + 38*math.cos(a)*math.cos(turn) - 22*math.sin(a)*math.sin(turn),
            ey - 38*math.cos(a)*math.sin(turn) - 22*math.sin(a)*math.cos(turn)) for a in [2*math.pi*k/59 for k in range(60)]]
    shapes += poly(pts, 'w', 1.6)
    c, s_ = math.cos(turn), math.sin(turn)
    shapes += [line((ex - 38*c, ey + 38*s_), (ex + 38*c, ey - 38*s_), 'v', width=1.8), ellipse(ex, ey, 7, 7, 'u')]
  shapes += [arrow((sx + A*math.cos(0.35), sy - A*math.sin(0.35)), (sx + A*math.cos(0.6), sy - A*math.sin(0.6)), 'ink', 1.4),
             text(sx + A*math.cos(0.6) + 8, sy - A*math.sin(0.6) - 8, 'a year round', 'ink', 0.8)]
  x0 = 580
  shapes += [line((x0, 110), (x0 + 30, 110), 'v', width=1.8), text(x0 + 38, 114, 'the Moon\'s orbit\'s long axis', 'ink', 0.85),
             line((x0, 140), (x0 + 30, 140), 'faint', dash=True, width=0.8), text(x0 + 38, 144, 'a fixed direction', 'ink', 0.85),
             text(x0, 200, 'Each quarter of a year the', 'ink', 0.85), text(x0, 218, 'axis has turned a little', 'ink', 0.85),
             text(x0, 236, 'further: 19.2 mas a year in', 'ink', 0.85), text(x0, 254, 'general relativity, beyond', 'ink', 0.85),
             text(x0, 272, 'Newton. The turning flow\'s', 'ink', 0.85), text(x0, 290, 'Moon turns half as much.', 'ink', 0.85),
             text(x0, 326, '(Hugely exaggerated.)', 'ink', 0.8)]
  return W, H, shapes


def jupiterrays():
  """light past a moving Jupiter, as radio telescopes measured it in 2002: a quasar far away, two rays to one
  observer - one passing Jupiter close, one 100 Jupiter radii out - and the angle between them where they arrive.
  part of the near ray's bending comes from Jupiter's motion"""
  W, H = 760, 340
  jx, jy, R = 330, 200, 22
  qx, qy = 30, 140
  ox, oy = 720, 140
  shapes = [text(qx, qy - 22, 'a quasar', 'ink', 0.85), text(qx, qy - 6, 'far away', 'ink', 0.85),
            ellipse(qx + 6, qy + 10, 5, 5, 'ink')]
  near = [(qx + 6, qy + 10), (jx - 12, jy - R - 10), (jx + 12, jy - R - 10), (ox, oy)]
  far = [(qx + 6, qy + 10), (jx, 60), (ox, oy)]
  def smooth(pts):
    out = []
    for i in range(len(pts) - 1):
      for k in range(20):
        f = k/20
        out.append((pts[i][0] + (pts[i + 1][0] - pts[i][0])*f, pts[i][1] + (pts[i + 1][1] - pts[i][1])*f))
    return out + [pts[-1]]
  a, b2 = smooth(near), smooth(far)
  shapes += poly(a[:-1], 'v', 2.0) + [arrow(a[-2], a[-1], 'v', 2.0)]
  shapes += poly(b2[:-1], 'w', 1.6, dash=True) + [arrow(b2[-2], b2[-1], 'w', 1.6, dash=True)]
  shapes += [ellipse(jx, jy, R, R, 'sun', 0, 'sun'), text(jx, jy + 5, 'Jupiter', 'ink', 0.8, anchor='middle'),
             arrow((jx + R + 8, jy + 30), (jx + R + 58, jy + 30), 'ink', 1.8), text(jx + R + 64, jy + 35, '13 km/s', 'ink', 0.8),
             text(jx + 40, jy - R + 14, 'passing 1 to 10 Jupiter radii out', 'v', 0.8),
             text(jx, 50, 'a reference ray, 100 Jupiter radii out', 'w', 0.8, anchor='middle'),
             ellipse(ox, oy, 7, 7, 'u'), text(ox, oy + 26, 'radio', 'ink', 0.8, anchor='middle'),
             text(ox, oy + 42, 'telescopes', 'ink', 0.8, anchor='middle'),
             text(ox + 2, oy - 36, 'the angle', 'ink', 0.8, anchor='middle'), text(ox + 2, oy - 20, 'between them', 'ink', 0.8, anchor='middle'),
             text(W/2, H - 12, 'Not to scale. Part of the near ray\'s bending, about 50 µas, comes from Jupiter\'s motion.', 'ink', 0.8, anchor='middle')]
  return W, H, shapes


def binarypair(ax, ay, bx, by, ra, rb, shapes, own=(True, True), faint=False):
  """two bodies with inflow round each: own[i] False draws body i's flow dashed and faint (left out)"""
  for (cx, cy, r, keep) in ((ax, ay, ra, own[0]), (bx, by, rb, own[1])):
    for k in range(10):
      a = 2*math.pi*k/10 + 0.3
      for d in (r + 26, r + 56):
        x, y = cx + d*math.cos(a), cy + d*math.sin(a)
        L = 20*math.sqrt((r + 26)/d)
        if keep:
          shapes.append(arrow((x, y), (x - L*math.cos(a), y - L*math.sin(a)), 'u', 1.1))
        else:
          shapes.append(arrow((x, y), (x - L*math.cos(a), y - L*math.sin(a)), 'faint', 0.8, dash=True))


def selfmoving():
  """two bodies going round each other, each moved by the flow: each has its own flow, and moves through the
  space the other's flow makes; what it does in its own flow, where the flow is fastest, is the question"""
  W, H = 800, 380
  shapes = [text(W/2, 30, 'two bodies going round each other, each moved by the flow', 'ink', 0.9, anchor='middle')]
  cx, cy = 360, 200
  shapes += poly(circle_points(cx, cy, 110, 0, 2*math.pi, 100), 'faint', 1.0, dash=True)
  ax, ay, bx, by = cx - 110, cy, cx + 110, cy
  binarypair(ax, ay, bx, by, 18, 18, shapes)
  shapes += [ellipse(ax, ay, 18, 18, 'sun', 0, 'sun'), ellipse(bx, by, 18, 18, 'sun', 0, 'sun'),
             text(ax, ay + 5, 'A', 'ink', 0.9, anchor='middle'), text(bx, by + 5, 'B', 'ink', 0.9, anchor='middle'),
             arrow((ax, ay - 26), (ax, ay - 90), 'v', 2.2), arrow((bx, by + 26), (bx, by + 90), 'v', 2.2),
             text(ax - 10, ay - 70, 'v', 'v', 1.1, anchor='end', math_=True), text(bx + 10, by + 76, 'v', 'v', 1.1, math_=True),
             text(570, 120, 'Each body moves through', 'ink', 0.85), text(570, 138, 'the space round it. But', 'ink', 0.85),
             text(570, 156, 'much of that space is', 'ink', 0.85), text(570, 174, 'its own flow, falling in', 'ink', 0.85),
             text(570, 192, 'faster and faster the', 'ink', 0.85), text(570, 210, 'closer it gets. How does', 'ink', 0.85),
             text(570, 228, 'a body move in its own', 'ink', 0.85), text(570, 246, 'flow?', 'ink', 0.85),
             arrow((40, 350), (70, 350), 'u', 1.1), text(78, 355, 'space flowing in', 'ink', 0.85),
             arrow((260, 350), (290, 350), 'v', 2.0), text(298, 355, 'the body\'s velocity', 'ink', 0.85)]
  return W, H, shapes


def othersflow():
  """each body in the others' flow: two panels, the same pair; in each, one body moves as a test body in the
  other's flow, its own flow left out (dashed)"""
  W, H = 760, 360
  shapes = []
  for left, which in ((20, 0), (390, 1)):
    ax, ay, bx, by = left + 95, 180, left + 255, 180
    title = 'A moves in B\'s flow' if which == 0 else 'B moves in A\'s flow'
    shapes.append(text(left + 175, 34, title, 'ink', 0.95, anchor='middle', bold=True))
    binarypair(ax, ay, bx, by, 16, 16, shapes, own=(which == 1, which == 0))
    shapes += [ellipse(ax, ay, 16, 16, 'sun', 0, 'sun'), ellipse(bx, by, 16, 16, 'sun', 0, 'sun'),
               text(ax, ay + 5, 'A', 'ink', 0.9, anchor='middle'), text(bx, by + 5, 'B', 'ink', 0.9, anchor='middle')]
    mx = ax if which == 0 else bx
    shapes += [poly(circle_points(mx, ay, 24, 0, 2*math.pi, 40), 'v', 2.0)[0]]
  shapes += [arrow((40, 320), (70, 320), 'u', 1.1), text(78, 325, 'the flow the body moves in', 'ink', 0.85),
             arrow((330, 320), (360, 320), 'faint', 0.8, dash=True), text(368, 325, 'its own flow, left out', 'ink', 0.85),
             text(626, 325, 'the body moving', 'ink', 0.85)] + poly(circle_points(610, 320, 9, 0, 2*math.pi, 30), 'v', 2.0)
  return W, H, shapes


def ownspace():
  """a body moving with its own space: the flow round a body moving at v is v plus its own inflow, equal from every
  side; averaged over a small sphere round the body, the inflow cancels and what is left is v. left, the two parts of
  the flow round the moving body (the inflow drawn alone, and v); right, their average"""
  W, H = 760, 360
  shapes = [text(200, 34, 'round a moving body: its velocity, plus its inflow', 'ink', 0.95, anchor='middle', bold=True),
            text(570, 34, 'averaged over a small circle round it', 'ink', 0.95, anchor='middle', bold=True)]
  bx, by, R = 200, 190, 18
  V = (24, -13)
  for k in range(12):
    a = 2*math.pi*k/12 + 0.1
    for d in (48, 92):
      x, y = bx + d*math.cos(a), by + d*math.sin(a)
      L = 30*math.sqrt(48/d)
      ux, uy = -L*math.cos(a), -L*math.sin(a)
      shapes.append(arrow((x, y), (x + ux, y + uy), 'u', 1.1))
  shapes += poly(circle_points(bx, by, 48, 0, 2*math.pi, 60), 'faint', 1.0, dash=True)
  shapes += [ellipse(bx, by, R, R, 'sun', 0, 'sun'), arrow((bx + R + 4, by - 2), (bx + R + 4 + V[0]*1.6, by - 2 + V[1]*1.6), 'v', 2.4),
             text(bx + R + 8 + V[0]*1.6, by - 8 + V[1]*1.6, 'v', 'v', 1.1, math_=True)]
  cx, cy = 570, 190
  shapes += [text(cx - 110, cy - 70, 'its own inflow, the same', 'ink', 0.85), text(cx - 110, cy - 52, 'from every side: cancels', 'ink', 0.85),
             text(cx - 110, cy + 70, 'what is left: the body\'s', 'ink', 0.85), text(cx - 110, cy + 88, 'own velocity', 'ink', 0.85),
             ellipse(cx, cy, R, R, 'sun', 0, 'sun'), arrow((cx + R + 4, cy - 2), (cx + R + 4 + V[0]*1.6, cy - 2 + V[1]*1.6), 'v', 2.4),
             text(cx + R + 8 + V[0]*1.6, cy - 8 + V[1]*1.6, 'v', 'v', 1.1, math_=True)]
  shapes += poly(circle_points(cx, cy, 48, 0, 2*math.pi, 60), 'faint', 1.0, dash=True)
  shapes += [arrow((330, 190), (420, 190), 'ink', 1.6),
             text(W/2, 330, 'So a body moves with the space it is in, averaged round it: the rule general relativity uses.', 'ink', 0.85, anchor='middle')]
  return W, H, shapes


def squeeze():
  """the turning flow round the Sun: its paths' energy is the constant J chosen for the Earth, so u^2 = 2GM/r + 2J
  falls short of the escape speed's 2GM/r by the same amount everywhere, and reaches zero at 2/3 AU, where the Sun's
  flow stops; light passing the Sun goes through squeezed space and is bent less"""
  W, H = 760, 390
  X0, X1, Y0, Y1 = 90, 560, 320, 50                   #plot box: r 0.05 to 1 AU, u^2 in units of 2GM/AU, 0 to 6
  rmin, rmax, top = 0.08, 1.0, 6.0
  P = lambda r, v: (X0 + (r - rmin)/(rmax - rmin)*(X1 - X0), Y0 - v/top*(Y0 - Y1))
  J = -1.5                                            #2J in units of 2GM/AU: -3/2 GM/a over GM/a, the turning flow's
  shapes = [arrow((X0, Y0), (X1 + 14, Y0), 'ink', 1.0), arrow((X0, Y0), (X0, Y1 - 14), 'ink', 1.0),
            text((X0 + X1)/2, Y0 + 46, 'distance from the Sun (AU)', 'ink', 0.85, anchor='middle'),
            text(X0 - 10, Y1 - 20, 'u² (the speed of space, squared)', 'ink', 0.85)]
  for r in (0.25, 0.5, 0.75, 1.0):
    shapes += [line(P(r, 0), (P(r, 0)[0], Y0 + 6), 'ink', width=0.8), text(P(r, 0)[0], Y0 + 22, '%g' % r, 'ink', 0.8, anchor='middle')]
  esc = [P(r, 1/r) for r in [rmin + (rmax - rmin)*k/200 for k in range(201)] if 1/r <= top]
  turn = [P(r, 1/r + J) for r in [rmin + (rmax - rmin)*k/200 for k in range(201)] if 0 <= 1/r + J <= top]
  shapes += poly(esc, 'u', 1.6, dash=True) + poly(turn, 'u', 2.2)
  r0 = 2/3
  shapes += [line(P(r0, 0), P(r0, 2.2), 'v', dash=True, width=1.2), text(P(r0, 0)[0] + 6, P(0, 2.4)[1], '2/3 AU: the Sun\'s', 'v', 0.85),
             text(P(r0, 0)[0] + 6, P(0, 2.4)[1] + 16, 'flow stops', 'v', 0.85),
             arrow(P(0.2, 1/0.2), P(0.2, 1/0.2 + J), 'v', 1.4), text(P(0.2, 0)[0] + 14, P(0, 1/0.2 - 0.6)[1], '2J: the same', 'v', 0.85),
             text(P(0.2, 0)[0] + 14, P(0, 1/0.2 - 0.6)[1] + 16, 'everywhere', 'v', 0.85)]
  x0 = 590
  shapes += [line((x0, 110), (x0 + 30, 110), 'u', dash=True, width=1.6), text(x0 + 38, 106, 'the escape speed:', 'ink', 0.85),
             text(x0 + 38, 124, '2GM/r', 'ink', 0.85),
             line((x0, 170), (x0 + 30, 170), 'u', width=2.2), text(x0 + 38, 166, 'the turning flow:', 'ink', 0.85),
             text(x0 + 38, 184, '2GM/r + 2J', 'ink', 0.85),
             text(x0, 240, 'Space round the Sun', 'ink', 0.85), text(x0, 258, 'falls slower than its', 'ink', 0.85),
             text(x0, 276, 'escape speed: light', 'ink', 0.85), text(x0, 294, 'through it is bent', 'ink', 0.85),
             text(x0, 312, '9.6 mas less.', 'ink', 0.85)]
  return W, H, shapes


def onepotential():
  """the turning flow against one potential: left, the turning flow's paths share an energy J below zero, chosen for
  the Earth, so the Sun's flow stops at 2/3 AU and the Earth's region reaches far round it; right, J = 0: Bernoulli's
  equation with no constant, the Sun's flow reaching everywhere and the Earth's region only its own"""
  W, H = 760, 400
  shapes = []
  for left, one, title in ((20, False, 'the turning flow: energy J, chosen for the Earth'), (390, True, 'one potential: no constant, J = 0')):
    sx, sy = left + 125, 190
    ex, ey = left + 290, 190
    reach = 110
    shapes.append(text(left + 175, 34, title, 'ink', 0.9, anchor='middle'))
    seam = 40 if one else 55
    for k in range(14):
      a = 2*math.pi*k/14 + 0.15
      for r in (45, 75, 105, 135):
        if not one and r > reach - 8:
          continue
        x, y = sx + r*math.cos(a), sy + r*math.sin(a)
        if math.hypot(x - ex, y - ey) < seam + 6 or x > left + 345 or x < left + 5 or y < 55 or y > 320:
          continue
        L = 24*math.sqrt(45/r)
        shapes.append(arrow((x, y), (x - L*math.cos(a), y - L*math.sin(a)), 'u', 1.2))
    if not one:
      shapes += poly(circle_points(sx, sy, reach, 0, 2*math.pi, 80), 'v', 1.0, dash=True)
      shapes += [text(sx, sy - reach - 8, "the Sun's flow stops", 'v', 0.8, anchor='middle')]
    shapes += poly(circle_points(ex, ey, seam, 0, 2*math.pi, 80), 'v', 1.4, dash=True)
    for k in range(10):
      a = 2*math.pi*k/10 + 0.2
      for r in ((30,) if one else (30, 48)):
        x, y = ex + r*math.cos(a), ey + r*math.sin(a)
        if x > left + 348:
          continue
        L = 13*math.sqrt(30/r)
        shapes.append(arrow((x, y), (x - L*math.cos(a), y - L*math.sin(a)), 'u', 1.1))
    shapes += [ellipse(sx, sy, 24, 24, 'sun', 0, 'sun'), text(sx, sy + 5, 'Sun', 'ink', 0.85, anchor='middle'),
               ellipse(ex, ey, 8, 8, 'u'), text(ex, ey + seam + 18, "the Earth's region", 'ink', 0.8, anchor='middle')]
  shapes += [line((70, 360), (100, 360), 'v', dash=True, width=1.4), text(108, 365, 'a seam, or where a flow stops', 'ink', 0.85),
             arrow((420, 360), (450, 360), 'u', 1.2), text(458, 365, 'space flowing in', 'ink', 0.85)]
  return W, H, shapes


def box(x, y, w, h, title, lines=(), colour='ink', fill='fill', dash=False, code=True):
  """a labelled box: a title (code-like names in monospace are not available, so plain) and smaller lines under it"""
  out = [rect(x, y, w, h, fill=fill, dash=dash, colour=colour, radius=6),
         text(x + w/2, y + 22, title, colour if colour != 'faint' else 'ink', 0.9, anchor='middle', bold=True)]
  for k, line_ in enumerate(lines):
    out.append(text(x + w/2, y + 42 + 17*k, line_, 'ink', 0.78, anchor='middle'))
  return out


def pipeline():
  """how a simulation runs: a study sets up bodies and a calculator, the run loop steps a particle, the log folder
  holds the results, the viewer files and the backgrounds; the desktop viewer reads the folder, and publish_run copies
  it to docs/runs for the browser viewer in these pages"""
  W, H = 860, 480
  shapes = []
  shapes += box(20, 40, 180, 110, 'a study', ('studies/*.py', 'bodies, starts, models', 'what to compare'))
  shapes += box(240, 40, 180, 110, 'a calculator', ('engine/', 'the flow, or a spacetime', 'and its step'))
  shapes += box(460, 40, 180, 110, 'the run loop', ('step after step, until', 'an end condition', '(engine/run.py)'))
  shapes += box(680, 40, 160, 110, 'a log folder', ('logs/<study>/<run>/', '.log  .csv  summary.log', '.backgrounds.json'))
  shapes += box(680, 200, 160, 110, 'viewer files', ('<view>.full.json', '.prefs.json', '.config.json'))
  shapes += box(460, 200, 180, 110, 'publish_run.py', ('copies the folder to', 'docs/runs/<name>/,', 'paths made relative'))
  shapes += box(240, 200, 180, 110, 'browser viewer', ('web/ (docs/viewer/)', 'pan, zoom, replay,', 'backgrounds'), colour='w')
  shapes += box(20, 200, 180, 110, 'a page', ('an embedded player:', 'viewer/index.html', '?player&run=...'), colour='faint')
  shapes += box(680, 350, 160, 110, 'desktop viewer', ('viewer/csv_viewer.py', 'any run in logs/,', 'and a Sim tab'), colour='u')
  for a, b in (((200, 95), (236, 95)), ((420, 95), (456, 95)), ((640, 95), (676, 95)), ((760, 150), (760, 196)),
               ((680, 255), (644, 255)), ((460, 255), (424, 255)), ((240, 255), (204, 255)), ((760, 310), (760, 346))):
    shapes.append(arrow(a, b, 'ink', 1.6))
  return W, H, shapes


def classes():
  """the core classes: Body and Particle; the flow calculators (engine/flow.py), each giving the flow u and moving a
  particle through it; the spacetimes (engine/metric.py, engine/carried.py), each giving a lapse, a flow and a curved
  space, moved through by MetricCalculator; FlowSpacetime wraps any flow calculator"""
  W, H = 900, 580
  shapes = [text(225, 30, 'the flow model (engine/flow.py)', 'ink', 0.95, anchor='middle', bold=True),
            text(675, 30, 'spacetimes (engine/metric.py, carried.py)', 'ink', 0.95, anchor='middle', bold=True),
            line((450, 20), (450, 545), 'faint', dash=True, width=0.8)]
  shapes += box(20, 50, 180, 80, 'Body', ('mass, place, black/white', 'spin, velocity, circling'), colour='faint')
  shapes += box(240, 50, 190, 80, 'Particle', ('pos, v = u + w', 't, pt (proper time)'), colour='faint')
  shapes += box(95, 165, 230, 96, 'Calculator', ('flow(pos, region, t): u', 'combine, direction, seams', 'the run loop'))
  shapes += box(20, 310, 170, 80, 'NewtonianCalculator', ('Newton\'s g',))
  shapes += box(20, 440, 170, 80, 'GeodesicCalculator', ('the metric\'s own paths,', 'fourth-order steps'))
  shapes += box(230, 310, 200, 96, 'SpecialFlowCalculator', ('the flow model:', 'dx/dt = u + w', 'the momentum step'), colour='u')
  shapes += box(230, 440, 200, 80, 'KerrFlowCalculator', ('a rotating hole:', 'the river and its twist'), colour='u')
  bus = 210
  shapes += [line((bus, 300), (bus, 480), 'ink', width=1.2), line((bus, 280), (bus, 300), 'ink', width=1.2),
             arrow((bus, 285), (bus, 265), 'ink', 1.2),
             line((190, 350), (bus, 350), 'ink', width=1.2), line((190, 480), (bus, 480), 'ink', width=1.2),
             line((bus, 358), (230, 358), 'ink', width=1.2), arrow((330, 440), (330, 410), 'ink', 1.2)]
  shapes += box(560, 50, 230, 96, 'Spacetime', ('lapseOffset(x, t): N - 1', 'flow(x, t, region): u', 'space(x, t, region): gamma - delta'))
  shapes += box(470, 200, 190, 96, 'FlowSpacetime', ('any calculator\'s flow,', 'with a lapse and', 'a curved space'), colour='u')
  shapes += box(690, 200, 190, 96, 'PostNewtonian', ('general relativity,', 'first post-Newtonian,', 'the reference'), colour='w')
  shapes += box(470, 330, 190, 80, 'CarriedSpacetime', ('each body\'s flow', 'carried at its velocity'))
  shapes += box(690, 330, 190, 96, 'FreeFallTurning', ('general relativity in', 'the one-potential flow\'s', 'time (FreeFallPN)'), colour='w')
  bus = 675
  shapes += [line((bus, 170), (bus, 370), 'ink', width=1.2), arrow((bus, 170), (bus, 150), 'ink', 1.2)]
  for y, x0, x1 in ((248, 660, bus), (248, bus, 690), (370, 660, bus), (378, bus, 690)):
    shapes.append(line((x0, y), (x1, y), 'ink', width=1.2))
  shapes += box(530, 460, 290, 80, 'MetricCalculator', ('a Calculator: moves a particle through', 'any Spacetime, by Hamilton\'s equations'))
  shapes += [arrow((430, 358), (468, 262), 'u', 1.2, dash=True), text(455, 330, 'wraps', 'u', 0.8, anchor='end')]
  shapes += [arrow((40, 562), (70, 562), 'ink', 1.2), text(78, 566, 'is a kind of', 'ink', 0.8),
             arrow((200, 562), (230, 562), 'u', 1.2, dash=True), text(238, 566, 'holds one, and uses its flow', 'ink', 0.8)]
  return W, H, shapes


def midpoint():
  """the midpoint step, on Hamilton's equations: the rates at the start take x and p half a step on; the rates at
  that middle take the whole step from the start"""
  W, H = 760, 330
  a, b = (90, 250), (650, 200)
  half = (300, 95)
  d = ((b[0] - a[0])/4.0, (b[1] - a[1])/4.0)
  shapes = [ellipse(a[0], a[1], 7, 7, 'ink'), text(a[0] - 4, a[1] + 30, 'start: x, p', 'ink', 0.9, anchor='middle'),
            arrow(a, (half[0] - 6, half[1] + 4), 'faint', 1.6, dash=True),
            ellipse(half[0], half[1], 6, 6, 'faint'), text(half[0], half[1] - 16, 'the middle', 'ink', 0.85, anchor='middle'),
            text(150, 140, '1. half a step, at the', 'ink', 0.85), text(150, 158, 'start\'s rates', 'ink', 0.85),
            arrow((half[0] + 10, half[1]), (half[0] + 10 + d[0], half[1] + d[1]), 'w', 1.8),
            text(half[0] + 24 + d[0], half[1] + d[1] + 4, 'the rates there: dx/dt, dp/dt', 'w', 0.85),
            arrow(a, (b[0] - 8, b[1] + 2), 'v', 2.4), ellipse(b[0], b[1], 7, 7, 'ink'),
            text(b[0] + 6, b[1] + 30, 'the end', 'ink', 0.9, anchor='middle'),
            text(400, 270, '2. the whole step from the start,', 'ink', 0.85), text(400, 288, 'at the middle\'s rates', 'ink', 0.85)]
  return W, H, shapes


def movingbodies():
  """setting the scene for moving bodies: left, the Sun and the Earth held still (Part 2), the flow steady, a seam
  round the Earth's region; right, the Earth going round the Sun, carrying its region of flow and its seam with it,
  v from where it was to where it is - the flow now changes with time"""
  W, H = 760, 400
  shapes = []
  for left, moving, title in ((20, False, 'held still: the flow never changes'), (390, True, 'moving: the flow moves with the bodies')):
    sx, sy = left + 70, 200                      #the Sun
    ex, ey = left + 255, 200                     #the Earth
    shapes += [text(left + 175, 34, title, 'ink', 0.9, anchor='middle')]
    #the Sun's flow, in towards it
    for k in range(10):
      a = 2*math.pi*k/10 + 0.3
      for r in (55, 95):
        x, y = sx + r*math.cos(a), sy + r*math.sin(a)
        if math.hypot(x - ex, y - ey) < 70 or x > left + 345 or x < left + 5:
          continue
        L = 26*math.sqrt(55/r)
        shapes.append(arrow((x, y), (x - L*math.cos(a), y - L*math.sin(a)), 'u', 1.2))
    if moving:
      #the Earth's orbit, and where it was
      orbit = circle_points(sx, sy, ex - sx, -0.75, 0.75, 60)
      shapes += poly(orbit, 'faint', 1.0, dash=True)
      for a in (0.62,):
        px, py = sx + (ex - sx)*math.cos(a), sy + (ex - sx)*math.sin(a)
        shapes += poly(circle_points(px, py, 46, 0, 2*math.pi, 50), 'faint', 0.8, dash=True)
        shapes.append(ellipse(px, py, 5, 5, 'faint'))
    #the Earth's region: its own flow, and the seam round it
    shapes += poly(circle_points(ex, ey, 46, 0, 2*math.pi, 60), 'v', 1.4, dash=True)
    for k in range(8):
      a = 2*math.pi*k/8 + 0.2
      x, y = ex + 34*math.cos(a), ey + 34*math.sin(a)
      shapes.append(arrow((x, y), (x - 14*math.cos(a), y - 14*math.sin(a)), 'u', 1.1))
    shapes += [ellipse(sx, sy, 26, 26, 'sun', 0, 'sun'), text(sx, sy + 5, 'Sun', 'ink', 0.85, anchor='middle'),
               ellipse(ex, ey, 9, 9, 'u'), text(ex, ey + (-56 if moving else 66), 'Earth', 'ink', 0.85, anchor='middle')]
    if moving:
      #v: from where the Earth was to where it is now, along its orbit
      arc = circle_points(sx, sy, ex - sx, 0.58, 0.075, 30)
      mid = 0.33
      shapes += poly(arc[:-1], 'ink', 1.8) + [arrow(arc[-2], arc[-1], 'ink', 1.8),
                                              text(sx + (ex - sx + 14)*math.cos(mid), sy + (ex - sx + 14)*math.sin(mid) + 6, 'v', 'ink', 1.1, math_=True)]
  shapes += [line((70, 345), (100, 345), 'v', dash=True, width=1.4), text(108, 350, 'the seam round the Earth\'s region of flow', 'ink', 0.85),
             arrow((420, 345), (450, 345), 'u', 1.2), text(458, 350, 'space flowing in', 'ink', 0.85),
             line((70, 372), (100, 372), 'faint', dash=True, width=0.8), text(108, 377, 'where the Earth and its region were', 'ink', 0.85)]
  return W, H, shapes



# --- Part 2's Seams page -----------------------------------------------------------------------------------------

def twoCentre(masses=(1.0, 1.0), shift=0.0):
  """the engine's exact potential flow round two bodies 1 AU apart at x = -0.5 and +0.5 AU, its seam moved by shift
  (the constant between the two S, in units of S at the saddle)"""
  sys.path.insert(0, ROOT)
  from engine.flow import Body, SpecialFlowCalculator
  from engine.constants import MS, AU
  calc = SpecialFlowCalculator([Body(masses[0]*MS, x=-0.5*AU), Body(masses[1]*MS, x=0.5*AU)], 2, 'eikonal-exact')
  calc.warn = lambda m: None
  field = calc.rayField()
  if shift:
    field.offsets[1] += shift*field.action(field.saddle(0, 1), 0)
  return calc, field, AU


def tracePath(direction, start, P, inside, stop, step=0.012, n=4000):
  """a path down a direction field (unit vectors at a point in AU), as pixels, while inside"""
  x, y = start
  pts = []
  for _ in range(n):
    d = direction(x, y)
    if d is None or stop(x, y):
      break
    x, y = x + step*d[0], y + step*d[1]
    if inside(x, y):
      pts.append(P(x, y))
    elif pts:
      break
  return pts


def seamwhy():
  """why a seam: each body's own family of paths falling from rest far away (into it, in the pull of both) fills the
  space round the pair, so at every point there are two, one into each body; the flow must follow one. left: the two
  families over each other; right: the flow taking, at each point, the one with the smaller S, and the seam where
  that changes"""
  import numpy as np
  calc, field, AU = twoCentre()
  W, H = 760, 430
  shapes = []
  for left, title, both in ((20, 'two paths through every point', True), (400, 'the flow follows one: the seam', False)):
    S, cx, cy = 118, left + 170, 205
    P = lambda x, y, cx=cx, cy=cy, S=S: (cx + S*x, cy - S*y)
    inside = lambda x, y: abs(x) < 1.42 and abs(y) < 1.42
    stop = lambda x, y: min(math.hypot(x + 0.5, y), math.hypot(x - 0.5, y)) < 0.05
    for i, colour in ((0, 'u'), (1, 'v')):
      def direction(x, y, i=i):
        q = np.array([x*AU, y*AU])
        if not both and field.region(q) != i:
          return None
        d = field.sources[i].solve(q)[0]
        return d
      starts = [(3.0*math.cos(a), 3.0*math.sin(a)) for a in [2*math.pi*(k + 0.5)/24 for k in range(24)]]
      if not both:      #and paths out of the seam, both sides
        for y0 in [-1.3 + 2.6*k/10 for k in range(11)]:
          starts.append((0.004*(1 if i else -1), y0))
      for s in starts:
        pts = tracePath(direction, s, P, inside, stop)
        if len(pts) > 6:
          shapes += poly(pts, colour, 0.9)
          k = len(pts)//3
          shapes.append(arrow(pts[k - 2], pts[k], colour, 1.1))
    if both:
      #a point and its two paths' directions
      q = np.array([-0.15*AU, 0.62*AU])
      px, py = P(-0.15, 0.62)
      for i, colour, name in ((0, 'u', 'into the left body'), (1, 'v', 'into the right body')):
        d = field.sources[i].solve(q)[0]
        shapes.append(arrow((px, py), (px + 46*d[0], py - 46*d[1]), colour, 2.4))
      shapes += [ellipse(px, py, 4.5, 4.5, 'ink'), text(px - 8, py - 12, 'P', 'ink', 1.1, anchor='end', math_=True)]
    else:
      sys.path.insert(0, ROOT)
      from engine.backgrounds import seamAround
      for line_ in seamAround(lambda q: field.region(q), np.zeros(2), 0.005*AU, 3*AU, cells=(120, 96)):
        pts = [P(q[0]/AU, q[1]/AU) for q in line_ if inside(q[0]/AU, q[1]/AU)]
        if len(pts) > 1:
          shapes += poly(pts, 'ink', 1.8, dash=True)
    for bx in (-0.5, 0.5):
      shapes.append(ellipse(*P(bx, 0), 14, 14, 'sun', 0, 'sun'))
    shapes.append(text(cx, 24, title, 'ink', 0.95, anchor='middle'))
  shapes += [line((70, 402), (104, 402), 'u', width=1.2), text(112, 407, 'paths into the left body', 'ink', 0.85),
             line((300, 402), (334, 402), 'v', width=1.2), text(342, 407, 'paths into the right body', 'ink', 0.85),
             line((540, 402), (574, 402), 'ink', dash=True, width=1.8), text(582, 407, 'the seam', 'ink', 0.85)]
  return W, H, shapes


def seamprofile():
  """S along the line through two equal bodies: each body's S rises away from it; the flow takes the smaller, so the
  seam is where they cross, a ridge in S that the flow runs down on both sides. adding a constant to one body's S
  moves the crossing, and the seam with it"""
  W, H = 760, 400
  x0, x1, top, base = 70, 700, 70, 290
  mid = (x0 + x1)/2
  sx = (x1 - x0)/4.4                         #pixels per half separation; bodies at +-1
  #S_k along the axis: the integral of the flow's speed sqrt(1/|x+1| + 1/|x-1|) from body k (substituting x = b + s^2
  #to take out the square-root singularity at the body), on its own side of the other body
  speed = lambda x: math.sqrt(1/max(abs(x + 1), 1e-9) + 1/max(abs(x - 1), 1e-9))
  def S(b, x):
    if x == b:
      return 0.0
    n, top_s = 300, math.sqrt(abs(x - b))
    d = 1 if x > b else -1
    total = 0.0
    for j in range(n):
      s_ = (j + 0.5)/n*top_s
      total += speed(b + d*s_*s_)*2*s_*top_s/n
    return total
  xs0 = [-2.2 + (0.92 + 2.2)*i/600 for i in range(601)]
  xs1 = [-x for x in xs0]
  S0 = [S(-1, x) for x in xs0]
  S1 = [S(1, x) for x in xs1]
  top_ = max(S0)
  sy = (base - top)/top_*0.95
  P = lambda x, s: (mid + sx*x, base - sy*s)
  c = 1.0
  shapes = [line((x0, base), (x1, base), 'ink', width=0.8)]
  shapes += poly([P(x, s) for x, s in zip(xs0, S0)], 'u', 1.2, dash=True)
  shapes += poly([P(x, s) for x, s in zip(xs1, S1)], 'v', 1.2, dash=True)
  shapes += poly([P(x, s + c) for x, s in zip(xs1, S1) if s + c < top_], 'v', 1.0, dash=True)
  f0 = lambda x: S(-1, x) if x < 0.92 else 1e9
  f1 = lambda x: S(1, x) if x > -0.92 else 1e9
  xs = [-2.2 + 4.4*i/880 for i in range(881)]
  shapes += poly([P(x, min(f0(x), f1(x))) for x in xs], 'ink', 2.2)
  #where they cross: the engine's seam, and the moved one
  def cross(k):
    lo, hi = -0.9, 0.9
    for _ in range(50):
      m = (lo + hi)/2
      if f0(m) < f1(m) + k:
        lo = m
      else:
        hi = m
    return lo
  for k, label, dy in ((0.0, 'the seam', 20), (c, 'moved', 36)):
    x = cross(k)
    shapes += [line(P(x, 0), P(x, f0(x)), 'faint', dash=True, width=1.0),
               text(P(x, 0)[0], base + dy, label, 'ink', 0.8, anchor='middle')]
  for x in (-1, 1):
    shapes.append(ellipse(*P(x, 0), 11, 11, 'sun', 0, 'sun'))
  #the flow runs down S: arrows along the base, away from the seam between the bodies
  for x in (-0.7, -0.4, 0.4, 0.7):
    d = -1 if x < 0 else 1
    px, py = P(x, 0)
    shapes.append(arrow((px - d*12, py + 56), (px + d*12, py + 56), 'u', 1.4))
  shapes += [text(P(0, 0)[0], base + 80, 'the flow runs down S, away from the seam on both sides', 'ink', 0.8, anchor='middle'),
             text(x0, top - 22, 'S along the line through two equal bodies', 'ink', 0.9),
             line((x0 + 360, top - 27), (x0 + 394, top - 27), 'u', dash=True, width=1.2), text(x0 + 402, top - 22, "the left body's S₀", 'ink', 0.8),
             line((x0 + 360, top - 7), (x0 + 394, top - 7), 'v', dash=True, width=1.2), text(x0 + 402, top - 2, "the right body's S₁, and S₁ + c", 'ink', 0.8),
             line((x0, top - 7), (x0 + 34, top - 7), 'ink', width=2.2), text(x0 + 42, top - 2, 'the flow\'s S: the smaller', 'ink', 0.8)]
  return W, H, shapes


def seamlevels():
  """where a seam can go: any curve where the two bodies' S differ by a constant (the engine's passes through the
  saddle, where g = 0), between the bodies, two equal and one four times the other; and two that can't be seams"""
  import numpy as np
  W, H = 760, 440
  shapes = []
  for left, masses, title in ((20, (1.0, 1.0), 'two equal bodies'), (400, (1.0, 0.25), 'one four times the other')):
    S, cx, cy = 118, left + 170, 205
    P = lambda x, y, cx=cx, cy=cy, S=S: (cx + S*x, cy - S*y)
    inside = lambda x, y: abs(x) < 1.42 and abs(y) < 1.42
    sys.path.insert(0, ROOT)
    from engine.backgrounds import seamAround
    for shift, colour, dash, width in ((-0.3, 'u', True, 1.2), (-0.15, 'u', True, 1.2), (0.0, 'ink', True, 2.0),
                                       (0.15, 'v', True, 1.2), (0.3, 'v', True, 1.2)):
      calc, field, AU = twoCentre(masses, shift)
      for line_ in seamAround(lambda q: field.region(q), np.zeros(2), 0.005*AU, 3*AU, cells=(120, 96)):
        pts = [P(q[0]/AU, q[1]/AU) for q in line_ if inside(q[0]/AU, q[1]/AU)]
        if len(pts) > 1:
          shapes += poly(pts, colour, width, dash=dash)
    sad = field.saddle(0, 1)
    shapes.append(ellipse(*P(sad[0]/AU, 0), 3.5, 3.5, 'ink'))
    for bx, m in ((-0.5, masses[0]), (0.5, masses[1])):
      r = 14*math.sqrt(m)
      shapes.append(ellipse(*P(bx, 0), r, r, 'sun', 0, 'sun'))
    if left == 20:
      #not seams: a circle round one body, crossing the level sets
      shapes += poly(circle_points(*P(0.5, 0), 0.62*S, 0, 2*math.pi, 90), 'faint', 1.4)
      shapes += [text(*P(0.62, 0.72), '✗', 'v', 1.2, anchor='middle'),
                 text(P(0.95, 0.75)[0], P(0.95, 0.75)[1], 'a circle:', 'ink', 0.8),
                 text(P(0.95, 0.75)[0], P(0.95, 0.75)[1] + 16, 'not a seam', 'ink', 0.8)]
    shapes.append(text(cx, 24, title, 'ink', 0.95, anchor='middle'))
  shapes += [line((40, 400), (74, 400), 'ink', dash=True, width=2.0), text(82, 405, "the engine's seam, through the saddle (dot), where g = 0", 'ink', 0.85),
             line((40, 422), (74, 422), 'u', dash=True, width=1.2), line((80, 422), (114, 422), 'v', dash=True, width=1.2),
             text(122, 427, 'other seams: S₀ = S₁ + c, for other constants c, towards one body or the other', 'ink', 0.85)]
  return W, H, shapes


def seamrule():
  """crossing a seam at rest: left, the rule - the particle keeps its velocity v (to first order: its energy and its
  momentum along the seam), and its velocity relative to space, w, changes by the jump in the flow; right, no rule -
  w kept as it is, so v jumps by the flow's jump, and the path kinks"""
  W, H = 760, 400
  shapes = []
  for left, title, rule in ((20, 'with the rule: v kept', True), (400, 'without it: w kept', False)):
    cx, cy = left + 170, 200
    shapes += [line((cx, 50), (cx, 340), 'ink', dash=True, width=1.6), text(cx, 362, 'the seam', 'ink', 0.85, anchor='middle'),
               text(cx - 90, 70, 'region 0', 'ink', 0.85, anchor='middle'), text(cx + 90, 70, 'region 1', 'ink', 0.85, anchor='middle')]
    u0, u1 = (-60, 22), (60, 22)                     #the flow either side: away from the seam, the same along it
    for sx_, u in ((-1, u0), (1, u1)):
      for y in (110, 290):
        x = cx + sx_*120
        shapes.append(arrow((x - u[0]/2, y - u[1]/2), (x + u[0]/2, y + u[1]/2), 'faint', 1.0))
    #the particle comes in from the left, crossing at (cx, cy)
    v0 = (110, -38)
    w0 = (v0[0] - u0[0], v0[1] - u0[1])
    v1 = v0 if rule else (w0[0] + u1[0], w0[1] + u1[1])
    w1 = (v1[0] - u1[0], v1[1] - u1[1])
    a = (cx - 150, cy - 150*v0[1]/v0[0])
    shapes += poly([a, (cx, cy)], 'ink', 1.2)
    end = (cx + 150, cy + 150*v1[1]/v1[0])
    shapes += poly([(cx, cy), end], 'ink', 1.2)
    if not rule:
      shapes += poly([(cx, cy), (cx + 150, cy + 150*v0[1]/v0[0])], 'faint', 1.0, dash=True)
    #vectors before (at the left) and after (at the right): u then w from its tip, v from the start
    for (px, py), u, w, v, side in (((cx - 120, cy - 120*v0[1]/v0[0]), u0, w0, v0, 'before'), ((cx + 30, cy + 30*v1[1]/v1[0]), u1, w1, v1, 'after')):
      s = 0.55
      tip = (px + s*u[0], py + s*u[1])
      shapes += [arrow((px, py), tip, 'u', 2.0), arrow(tip, (tip[0] + s*w[0], tip[1] + s*w[1]), 'w', 2.0),
                 arrow((px, py), (px + s*v[0], py + s*v[1]), 'v', 2.2), ellipse(px, py, 3.5, 3.5, 'ink')]
    shapes.append(text(cx, 24, title, 'ink', 0.95, anchor='middle'))
    if not rule:
      shapes += [text(cx + 155, cy + 150*v1[1]/v1[0] + 8, 'kink', 'v', 0.85), text(cx + 120, cy + 150*v0[1]/v0[0] - 10, 'GR', 'faint', 0.8)]
  shapes += key(392, [(70, 'u', 'u', 'the flow'), (250, 'w', 'w', 'velocity through space'), (480, 'v', 'v', 'velocity, v = u + w')])
  return W, H + 10, shapes


def seamframes():
  """the seam belongs to the observers: left, the model's - falling straight in from rest far away in every direction,
  one body has no seam; right, observers arriving from rest far away on one side, on parabolas round the body: each
  point behind it is passed by one that came round above and one that came round below, and the time switches from
  one family to the other on the half-line behind the body, a seam"""
  W, H = 760, 420
  shapes = []
  #left: radial
  cx, cy = 190, 205
  for k in range(16):
    a = 2*math.pi*k/16
    shapes += poly([(cx + r*math.cos(a), cy + r*math.sin(a)) for r in (160, 22)], 'ink', 1.0)
    shapes.append(arrow((cx + 95*math.cos(a), cy + 95*math.sin(a)), (cx + 80*math.cos(a), cy + 80*math.sin(a)), 'ink', 1.2))
  shapes += [ellipse(cx, cy, 14, 14, 'sun', 0, 'sun'), text(cx, 24, 'falling straight in: no seam', 'ink', 0.95, anchor='middle')]
  #right: parabolas y^2 = 4q(q - x), arriving from the left and coming round the body at the origin: each family
  #drawn on its way in, to where it crosses the line behind the body
  cx, cy, S = 500, 205, 52
  inside = lambda x, y: -3.1 < x < 4.3 and abs(y) < 3.3
  for q in (0.15, 0.4, 0.75, 1.2, 1.8, 2.6):
    for sign, colour in ((1, 'u'), (-1, 'v')):
      xs = [-3.1 + (q + 3.1)*i/300 for i in range(301)]
      arm = [(x, sign*math.sqrt(max(0, 4*q*(q - x)))) for x in xs]
      arm = [(x, y) for x, y in arm if inside(x, y)]
      if len(arm) < 10:
        continue
      shapes += poly([(cx + S*x, cy - S*y) for x, y in arm], colour, 1.0)
      i = int(len(arm)*0.55)
      a0, a1 = arm[i - 4], arm[i]
      shapes.append(arrow((cx + S*a0[0], cy - S*a0[1]), (cx + S*a1[0], cy - S*a1[1]), colour, 1.2))
  shapes += [line((cx, cy), (cx + S*4.2, cy), 'ink', dash=True, width=2.0), ellipse(cx, cy, 12, 12, 'sun', 0, 'sun'),
             text(cx + S*2.75, cy + 22, 'their seam', 'ink', 0.85),
             text(cx + 20, 24, 'arriving from one side: a seam', 'ink', 0.95, anchor='middle')]
  shapes += [line((60, 392), (94, 392), 'u', width=1.2), text(102, 397, 'observers coming round above the body', 'ink', 0.85),
             line((400, 392), (434, 392), 'v', width=1.2), text(442, 397, 'observers coming round below it', 'ink', 0.85)]
  return W, H, shapes


def seamfold():
  """what a seam is: in space and time (x across, t up), the two bodies' world lines are still; the flow's time
  T = t + min(S0, S1)/c^2, so its surfaces of constant time are t = T - min(S0, S1)/c^2, each with a crease at the
  seam. the spacetime is smooth there; only the slicing folds"""
  W, H = 760, 380
  x0, x1, base = 80, 680, 320
  mid = (x0 + x1)/2
  sx = (x1 - x0)/4.4
  speed = lambda x: math.sqrt(1/max(abs(x + 1), 1e-3) + 1/max(abs(x - 1), 1e-3))
  xs = [-2.2 + 4.4*i/440 for i in range(441)]
  def S(b, x):
    n = 120
    return sum(speed(b + (x - b)*(j + 0.5)/n) for j in range(n))*abs(x - b)/n
  m = [min(S(-1, x), S(1, x)) for x in xs]
  scale = 22/max(m)
  shapes = [arrow((x0 - 30, base + 20), (x0 - 30, 50), 'ink', 1.2), text(x0 - 38, 58, 't', 'ink', 1.2, anchor='end', math_=True),
            arrow((x0 - 30, base + 20), (x1 + 20, base + 20), 'ink', 1.2), text(x1 + 24, base + 40, 'x', 'ink', 1.2, math_=True)]
  for k in range(5):
    T = base - 20 - 60*k
    shapes += poly([(mid + sx*x, T + scale*s*1.0 - 0) for x, s in zip(xs, m)], 'u', 1.4)
  for x in (-1, 1):
    shapes += [line((mid + sx*x, base + 20), (mid + sx*x, 50), 'sun', width=4.0)]
  shapes += [line((mid, 50), (mid, base + 20), 'ink', dash=True, width=1.2),
             text(mid, 40, 'the seam', 'ink', 0.85, anchor='middle'),
             text(mid + sx*1, 40, 'a body', 'ink', 0.85, anchor='middle'), text(mid - sx*1, 40, 'a body', 'ink', 0.85, anchor='middle'),
             text(x1 - 4, base - 30, 'T = const', 'u', 0.85, anchor='end'),
             text(W/2, base + 52, "The flow's moments, T = t + S/c²: each folds at the seam, where S switches from one body's to the other's.", 'ink', 0.82, anchor='middle')]
  return W, H + 10, shapes



def spinswirl():
  """a spinning body's flow in the many-body model: Part 1's inflow, plus a swirl from the body's rotating matter,
  2GJ x r/c^2 r^3, falling off as 1/r^2 - much faster than the inflow's 1/sqrt r - and their sum, space spiralling in,
  the spiral tighter close in"""
  W, H = 760, 330
  shapes = []
  panels = ((130, 'the inflow, as in Part 1'), (380, 'the swirl from its spin'), (630, 'together'))
  R = 95
  for cx, title in panels:
    cy = 160
    for ring in (0.45, 0.72, 1.0):
      for k in range(12):
        a = 2*math.pi*(k + (0.5 if ring == 0.72 else 0))/12
        r = R*ring
        x, y = cx + r*math.cos(a), cy + r*math.sin(a)
        rin = -1.0/math.sqrt(ring)*14                          #inward, as 1/sqrt r
        sw = 6.0/ring**2                                       #round, as 1/r^2 (anticlockwise on the page: -y is up)
        sw = min(sw, 30)
        if title.startswith('the inflow'):
          dx, dy = rin*math.cos(a), rin*math.sin(a)
        elif title.startswith('the swirl'):
          dx, dy = sw*math.sin(a), -sw*math.cos(a)
        else:
          dx, dy = rin*math.cos(a) + sw*math.sin(a), rin*math.sin(a) - sw*math.cos(a)
        shapes.append(arrow((x, y), (x + dx, y + dy), 'u', 1.2))
    shapes.append(ellipse(cx, cy, 13, 13, 'sun', 0, 'sun'))
    shapes.append(text(cx, 34, title, 'ink', 0.9, anchor='middle'))
  shapes += [text(255, 166, '+', 'ink', 1.8, anchor='middle'), text(505, 166, '=', 'ink', 1.8, anchor='middle'),
             text(130, 300, '√(2GM/r), straight in', 'ink', 0.8, anchor='middle'),
             text(380, 300, '2GJ × r / c²r³: falls off as 1/r²', 'ink', 0.8, anchor='middle'),
             text(630, 300, 'space spirals in, the way it spins', 'ink', 0.8, anchor='middle')]
  #the spin's sense: a curved arrow round the body in the middle panel
  pts = circle_points(380, 160, 24, math.radians(200), math.radians(-60), 30)
  shapes += poly(pts, 'v', 1.6)
  shapes.append(arrow(pts[-3], pts[-1], 'v', 1.6))
  return W, H, shapes

TESTS = os.path.join(ROOT, 'docs', 'part1', 'tests', 'images')
PART1 = os.path.join(ROOT, 'docs', 'part1', 'images')
PART2 = os.path.join(ROOT, 'docs', 'part2', 'images')
PART6 = os.path.join(ROOT, 'docs', 'part6', 'images')
PART3 = os.path.join(ROOT, 'docs', 'part3', 'images')
PART4 = os.path.join(ROOT, 'docs', 'part4', 'images')
SIMS = os.path.join(ROOT, 'docs', 'appendix-a', 'images')
DIAGRAMS = {'spinswirl': spinswirl, 'seamwhy': seamwhy, 'seamprofile': seamprofile, 'seamlevels': seamlevels, 'seamrule': seamrule, 'seamframes': seamframes, 'seamfold': seamfold, 'ants': ants, 'vectors': vectors, 'steps': steps, 'apple': apple, 'parallel': parallel, 'regions': regions, 'fourclocks': fourclocks,
            'redshift': redshift, 'bending': bending, 'precession': precession, 'shapiro': shapiro,
            'funnel': funnel, 'falling': falling, 'spacetime': spacetime,
            'spacefall': spacefall, 'twister': twister, 'twobodies': twobodies, 'movingbodies': movingbodies, 'pipeline': pipeline, 'classes': classes, 'midpoint': midpoint, 'onepotential': onepotential, 'squeeze': squeeze, 'selfmoving': selfmoving, 'othersflow': othersflow, 'ownspace': ownspace, 'grazing': grazing, 'desitter': desitter, 'jupiterrays': jupiterrays, 'carrying': carrying, 'peeling': peeling, 'pairs': pairs, 'dumbhole': dumbhole, 'hollowsphere': hollowsphere, 'shelloptions': shelloptions, 'potentialflow': potentialflow, 'threebodies': threebodies, 'watershed': watershed, 'stretched': stretched, 'lunarranging': lunarranging, 'jupiterlight': jupiterlight, 'bounce': bounce, 'reverse': reverse, 'outflow': outflow, 'whitetime': whitetime}
FOLDER = {'spinswirl': PART4, 'seamwhy': PART2, 'seamprofile': PART2, 'seamlevels': PART2, 'seamrule': PART2, 'seamframes': PART2, 'seamfold': PART2, 'redshift': TESTS, 'bending': TESTS, 'precession': TESTS, 'shapiro': TESTS,
          'funnel': PART1, 'falling': PART1, 'spacetime': PART1,
          'spacefall': PART1, 'twister': PART1, 'twobodies': PART2, 'movingbodies': PART3, 'pipeline': SIMS, 'classes': SIMS, 'midpoint': SIMS, 'onepotential': PART3, 'squeeze': PART3, 'selfmoving': PART4, 'othersflow': PART4, 'ownspace': PART4, 'grazing': PART3, 'desitter': PART3, 'jupiterrays': PART3, 'carrying': PART3, 'peeling': PART6, 'pairs': PART6, 'dumbhole': PART6, 'hollowsphere': PART2, 'shelloptions': PART2, 'potentialflow': PART2, 'threebodies': PART2, 'watershed': PART2, 'stretched': PART2, 'lunarranging': PART2, 'jupiterlight': PART2, 'bounce': PART1, 'reverse': PART1, 'outflow': PART1, 'whitetime': PART1}     #the rest go in OUT


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
  only = [a for a in sys.argv[1:] if not a.startswith('--')]      #names of diagrams to draw, or all
  for name, make in DIAGRAMS.items():
    if only and name not in only:
      continue
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
