"""the Replay tab: playing the shown runs back, drawing each path's trail as its data plays"""
from viewer.common import *


class Replay:
  """mixed into Viewer (viewer/app.py)"""

  def replayRange(self):
    """the global time span of the shown paths, or None"""
    ts = [p.tvals[np.isfinite(p.tvals)] for p in self.paths if p.tvals is not None]
    ts = [t for t in ts if t.size]
    if not ts:
      return None
    return min(float(t.min()) for t in ts), max(float(t.max()) for t in ts)

  def replayPlay(self):
    span = self.replayRange()
    if span is None:
      return
    start, end = span
    if self.replayState == 'stopped' or self.replayT is None or self.replayT >= end:
      #from the beginning, with the trail from there (a cleared trail stays cleared until it is restored)
      cleared = self.replayState != 'stopped' and self.trailStart is not None and self.trailStart > start
      self.replayT = start
      self.trailStart = self.replayT if cleared else start
    self.replayState = 'playing'
    self.replayLast = time.time()
    self.replayTick()

  def replayTick(self):
    self.replayJob = None
    if self.replayState != 'playing':
      return
    span = self.replayRange()
    if span is None:
      self.replayStop()
      return
    start, end = span
    now = time.time()
    speed = float(self.replaySpeed.get().rstrip('×'))
    self.replayT += speed * (end - start) / REPLAY_SECONDS * (now - self.replayLast)
    self.replayLast = now
    if self.replayT >= end:
      self.replayT = end
      self.replayState = 'paused'   #at the end: Play starts again from the beginning
    self.replayShow()
    if self.replayState == 'playing':
      self.replayJob = self.root.after(REPLAY_FRAME, self.replayTick)

  def replayPause(self):
    if self.replayState == 'playing':
      self.replayState = 'paused'
      if self.replayJob:
        self.root.after_cancel(self.replayJob)
        self.replayJob = None
      self.replayShow()

  def replayRewind(self):
    span = self.replayRange()
    if span is None:
      return
    self.replayT = self.trailStart = span[0]
    if self.replayState == 'stopped':
      self.replayState = 'paused'
    self.replayLast = time.time()
    self.replayShow()

  def replayStop(self):
    """back to showing every path in full"""
    if self.replayJob:
      self.root.after_cancel(self.replayJob)
      self.replayJob = None
    self.replayState = 'stopped'
    self.replayT = self.trailStart = None
    self.replayShow()

  def replayClear(self):
    """remove the trails drawn so far; the replay carries on drawing from here"""
    span = self.replayRange()
    if span is None:
      return
    if self.replayState == 'stopped':
      self.replayState = 'paused'
      self.replayT = span[1]   #everything cleared, at the end
    self.trailStart = self.replayT
    self.replayShow()

  def replayRestore(self):
    """bring back the whole trail, from the start up to the replay time"""
    span = self.replayRange()
    if span is None or self.replayState == 'stopped':
      return
    self.trailStart = span[0]
    self.replayShow()

  def replaySeek(self, f):
    """the slider: jump to a fraction f of the way through the time span"""
    if getattr(self, 'replaySetting', False):
      return
    span = self.replayRange()
    if span is None:
      return
    start, end = span
    if self.replayState == 'stopped':
      self.replayState = 'paused'
      self.trailStart = start
    self.replayT = start + f * (end - start)
    self.trailStart = min(self.trailStart, self.replayT)
    self.replayLast = time.time()
    self.replayShow()

  def replayShow(self):
    """redraw, and move the slider and label to the replay time"""
    span = self.replayRange()
    self.replaySetting = True
    if self.replayState == 'stopped' or span is None:
      self.replayPos.set(0.0)
      self.replayLabel.config(text='stopped - 1× plays the whole run in %d s' % REPLAY_SECONDS)
    else:
      start, end = span
      self.replayPos.set((self.replayT - start) / (end - start) if end > start else 1.0)
      self.replayLabel.config(text='%s  t = %s of %s s' % (self.replayState, formatValue(self.replayT), formatValue(end)))
    self.replaySetting = False
    self.redraw()

  def replayWindow(self, p):
    """the rows of p inside the replay's trail, or None when not replaying (or p has no global t)"""
    if self.replayState == 'stopped' or p.tvals is None:
      return None
    return (p.tvals >= self.trailStart) & (p.tvals <= self.replayT)

  def replayHead(self, p):
    """where p is at the replay time, in plotted space, and the row just before it; or None"""
    if self.replayState == 'stopped' or p.tvals is None:
      return None
    t = p.tvals
    j = np.searchsorted(t, self.replayT, side='right') - 1
    if j < 0 or self.replayT < self.trailStart:
      return None
    if j + 1 < t.size and t[j + 1] > t[j] and np.isfinite(p.x[j + 1]) and np.isfinite(p.y[j + 1]):
      f = (self.replayT - t[j]) / (t[j + 1] - t[j])
      return p.x[j] + f * (p.x[j + 1] - p.x[j]), p.y[j] + f * (p.y[j + 1] - p.y[j]), j
    return p.x[j], p.y[j], j
