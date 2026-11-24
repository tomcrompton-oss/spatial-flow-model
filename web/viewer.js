/*
the browser viewer: a cut-down version of viewer/ (the desktop viewer) that runs in a browser with no server. it reads
a run's files as docs/archive/formats.md describes them - full.json, its prefs and config, the result csvs and their logs, and
background frames - and draws them; the physics stays in engine/, so nothing here works anything out beyond drawing
(the one formula is a horizon's radius, 2GM/c^2)

open a run: the Open button (a run folder), drop a folder on the plot, or web/index.html?run=<path to a .full.json>
when the project is served (python3 -m http.server from the project folder, then
http://localhost:8000/web/index.html?run=../logs/<study>/<run>/<view>.full.json)
*/
'use strict';

const G = 6.6743e-11, C = 299792458, AU = 1.495978707e11, MS = 1.989e30;
const UNITS = [['m', 1], ['km', 1e3], ['AU', AU], ['light-seconds', C]];
const SPEEDS = ['0.25', '0.5', '1', '2', '4'];
const SERIES = ['#2a78d6', '#eb6834', '#1baf7a', '#8a5cd8', '#d6a21e', '#d64c7a', '#4fb3c8', '#7a7a74'];
const DASHES = {solid: [], dashed: [8, 5], dotted: [2, 4]};
const MARGIN = {left: 78, right: 18, top: 16, bottom: 44};
const ARROW_SPACING = 40;   //pixels between background arrows
const REPLAY_SECONDS = 20;  //a whole run at 1x
const ALL = 'All environments', SELECTED = "Selected result's environment";
const PREFS = {unit: 0, equalAspect: true, showGrid: true, showFlow: true, showGravity: false, showScalar: true, showBodies: true,
               showSchwarzschild: true, showPathLegend: true, showFieldKey: true, replaySpeed: '1', replayLoop: false};

const state = {
  results: [],         //{name, file, data, paths, log, env, visible, color}
  environments: [],    //{key, name, bodies, frames}
  selected: null,
  view: null,          //[x0, x1, y0, y1] in metres
  prefs: {...PREFS},
  background: SELECTED,
  replay: {state: 'stopped', t: null, last: 0, mode: 'together'},   //mode 'together' or 'sequence' (in turn)
};

const $ = id => document.getElementById(id);
const canvas = $('plot'), ctx = canvas.getContext('2d');
const css = name => getComputedStyle(document.documentElement).getPropertyValue(name).trim();

//---------------------------------------------------------------- reading files

/* a source of files by name: the files of a chosen or dropped folder, or a folder on the server */
function folderSource(files) {
  const byName = new Map(files.map(f => [f.name, f]));
  return {names: () => [...byName.keys()], read: async name => {
    const f = byName.get(name);
    if (!f) throw new Error('missing ' + name);
    return f.text();
  }};
}

function urlSource(base) {
  return {names: () => [], read: async name => {
    const response = await fetch(new URL(name, base));
    if (!response.ok) throw new Error('could not fetch ' + name + ' (' + response.status + ')');
    return response.text();
  }};
}

/* a csv as columns of numbers (NaN where empty), split into rows; a row of empty cells ends a path */
function parseCsv(text) {
  const lines = text.split(/\r?\n/).filter(l => l.trim() && !l.trimStart().startsWith('#'));
  const names = lines[0].split(',').map(s => s.trim());
  const columns = Object.fromEntries(names.map(n => [n, new Float64Array(lines.length - 1)]));
  for (let i = 1; i < lines.length; i++) {
    const cells = lines[i].split(',');
    names.forEach((n, j) => { const c = (cells[j] || '').trim(); columns[n][i - 1] = c === '' ? NaN : +c; });
  }
  return {names, columns, rows: lines.length - 1};
}

/* the column pairs of a csv by name (pos_x with pos_y, posX with posY): [label, x, y] */
function pairs(names) {
  const out = [];
  for (const x of names) {
    const m = x.match(/^(.*?)(?<![A-Za-z])x(?![A-Za-z])(.*)$/) ;
    let y = null, label = null;
    if (m) { y = m[1] + 'y' + m[2]; label = (m[1] + m[2]).replace(/^[ _\-.:]+|[ _\-.:]+$/g, ''); }
    else if (/[a-z]X$/.test(x)) { y = x.slice(0, -1) + 'Y'; label = x.slice(0, -1); }
    if (y && names.includes(y)) out.push([label, x, y]);
  }
  return out;
}

/* the log lines a viewer reads (docs/archive/formats.md) */
function parseLog(text) {
  const bodies = [];
  for (const m of text.matchAll(/^body \d+: mass (\S+) kg .*?x (\S+) m\s+y (\S+) m\s+(black|white)(?:\s+spin (\S+))?/gm))
    bodies.push({mass: +m[1], x: +m[2], y: +m[3], black: m[4] === 'black', spin: m[5] ? +m[5] : 0});
  const frames = (text.match(/^background frames: (.+)$/m) || [])[1];
  const direction = (text.match(/^flow direction: (.+)$/m) || [])[1];
  const wave = (text.match(/^gravitational wave: (.+)$/m) || [])[1];
  const scalar = (text.match(/^background scalar: (.+)$/m) || [])[1];
  return {bodies, frames: frames && frames.trim(), direction, wave, scalar: scalar && scalar.trim()};
}

/* background frames (docs/archive/formats.md): the flow and its acceleration on a grid at a run of times - or, with
   the columns t, x, y, s, a scalar (a wave's strain, say), drawn as a colour map */
function parseFrames(text) {
  const lines = text.split(/\r?\n/).filter(l => l.trim());
  const header = lines[0].split(',').map(c => c.trim());
  const width = header.length, scalar = header[3] === 's';
  const n = lines.length - 1, raw = new Float64Array(n * width);
  for (let i = 0; i < n; i++) {
    const cells = lines[i + 1].split(',');
    for (let j = 0; j < width; j++) raw[i * width + j] = +cells[j];
  }
  const unique = k => [...new Set(Array.from({length: n}, (_, i) => raw[i * width + k]))].sort((a, b) => a - b);
  const times = unique(0), xs = unique(1), ys = unique(2);
  const u = new Float32Array(n * 2), a = new Float32Array(n * 2);
  const frames = {times, xs, ys, u, a, size: xs.length * ys.length};
  if (scalar) {
    const values = new Float32Array(n * 2);                  //two per point, so frameSample reads it as it does u
    for (let i = 0; i < n; i++) values[2 * i] = raw[i * width + 3];
    frames.s = values;
    frames.reference = {u: null, a: null, s: percentileOfSizes(values, 98)};
    return frames;
  }
  for (let i = 0; i < n; i++) {
    u[2 * i] = raw[i * width + 3]; u[2 * i + 1] = raw[i * width + 4];
    a[2 * i] = raw[i * width + 5]; a[2 * i + 1] = raw[i * width + 6];
  }
  frames.reference = {u: percentileOfSizes(u, 90), a: percentileOfSizes(a, 90)};   //one scale for the whole run
  return frames;
}

function percentileOfSizes(field, p) {
  const sizes = [];
  for (let i = 0; i < field.length; i += 2) {
    const s = Math.hypot(field[i], field[i + 1]);
    if (s > 0 && isFinite(s)) sizes.push(s);
  }
  if (!sizes.length) return null;
  sizes.sort((x, y) => x - y);
  return sizes[Math.min(sizes.length - 1, Math.floor(p / 100 * sizes.length))];
}

/* the field (u or a) at (x, y), time t: between the frames either side of t, bilinear within; null off the grid */
function frameSample(frames, field, x, y, t) {
  const {times, xs, ys} = frames, values = frames[field];
  const fx = locate(xs, x), fy = locate(ys, y);
  if (fx === null || fy === null) return null;
  let k = locate(times, t);
  if (k === null) k = t < times[0] ? 0 : times.length - 1;
  const k0 = Math.min(Math.floor(k), times.length - 1), k1 = Math.min(k0 + 1, times.length - 1), fk = k - k0;
  const i0 = Math.min(Math.floor(fx), xs.length - 2), j0 = Math.min(Math.floor(fy), ys.length - 2);
  const sx = fx - i0, sy = fy - j0, nx = xs.length;
  const at = (frame, i, j, c) => values[2 * (frame * frames.size + j * nx + i) + c];
  const out = [0, 0];
  for (const [frame, weight] of [[k0, 1 - fk], [k1, fk]])
    for (let c = 0; c < 2; c++)
      out[c] += weight * ((1 - sx) * (1 - sy) * at(frame, i0, j0, c) + sx * (1 - sy) * at(frame, i0 + 1, j0, c)
                          + (1 - sx) * sy * at(frame, i0, j0 + 1, c) + sx * sy * at(frame, i0 + 1, j0 + 1, c));
  return out;
}

/* where v falls in the ascending list as a fractional index, or null outside it */
function locate(list, v) {
  if (!(v >= list[0] && v <= list[list.length - 1])) return null;
  let lo = 0, hi = list.length - 1;
  while (hi - lo > 1) { const mid = (lo + hi) >> 1; if (list[mid] <= v) lo = mid; else hi = mid; }
  return lo + (hi > lo ? (v - list[lo]) / (list[hi] - list[lo]) : 0);
}

/* a run: its full.json (if any), prefs, config, results, logs and frames */
async function loadRun(source, fullName) {
  message('loading…');
  state.results = []; state.environments = []; state.selected = null; stopReplay();
  try {
    fullName = fullName || source.names().find(n => n.endsWith('.full.json'));
    let entries;
    if (fullName) {
      const full = JSON.parse(await source.read(fullName));
      if (full.preferences) Object.assign(state.prefs, pickPrefs(JSON.parse(await source.read(full.preferences)).preferences || {}));
      const config = full.config ? JSON.parse(await source.read(full.config)) : {results: []};
      entries = config.results || [];
      state.background = config.background === ALL ? ALL : SELECTED;
    } else {
      entries = source.names().filter(n => n.endsWith('.csv') && !n.startsWith('background_')).sort().map(n => ({relative: n}));
    }
    //every csv and log at once (one after another, each waits for the server), then every frames file they name
    let done = 0;
    const files = entries.map(entry => entry.relative || entry.path.split('/').pop());
    const read = name => source.read(name).finally(() => message('loading… ' + (++done) + ' files'));
    const texts = await Promise.all(files.map(file => Promise.all([
      read(file), read(file.replace(/\.csv$/, '.log')).catch(() => null)])));   //no log: no bodies
    const logs = texts.map(([, log]) => log === null ? {bodies: []} : parseLog(log));
    const frameCache = new Map(await Promise.all([...new Set(logs.map(l => l.frames).filter(Boolean))].map(async name => {
      try { return [name, parseFrames(await read(name))]; }
      catch (e) { message('no frames file ' + name); return [name, null]; }
    })));
    entries.forEach((entry, i) => {
      const file = files[i], log = logs[i];
      const result = {name: studyName(file), file, data: parseCsv(texts[i][0]), log, visible: entry.visible !== false,
                      color: SERIES[i % SERIES.length]};
      result.paths = buildPaths(result, entry);
      result.env = environmentFor(log, frameCache);
      state.results.push(result);
    });
    state.selected = state.results[0] || null;
    message(fullName ? fullName : state.results.length + ' results');
  } catch (e) {
    message('could not open the run: ' + e.message);
  }
  syncControls();
  fit();
}

function pickPrefs(prefs) {
  const out = {};
  for (const key of Object.keys(PREFS)) if (key in prefs) out[key] = prefs[key];
  if (typeof prefs.unit === 'number') out.unit = Math.max(0, Math.min(UNITS.length - 1, prefs.unit - 1));   //the desktop's list starts with raw values
  return out;
}

function studyName(file) {
  return file.replace(/\.csv$/, '').replace(/_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}$/, '');
}

/* each selected pair of a result as a path: the rows, broken where a row is empty */
function buildPaths(result, entry) {
  const {names, columns} = result.data;
  let selection = (entry.selection || []).filter(p => names.includes(p[0]) && names.includes(p[1]));
  if (!selection.length) {
    const found = pairs(names), position = found.filter(p => !/^(v|u|w|a|vel|velocity|acc|accel|f|force)\d*$/i.test(p[0]));
    selection = (position.length ? position : found.slice(0, 1)).map(p => [p[1], p[2]]);
  }
  const time = columns.t || columns.time || null;
  return selection.map(([xc, yc]) => {
    const label = (pairs(names).find(p => p[1] === xc && p[2] === yc) || [xc + ' / ' + yc])[0];
    const style = (entry.styles || {})[label] || [];
    return {name: label, xName: xc, yName: yc, x: columns[xc], y: columns[yc], t: time, color: style[0] || null,
            style: style[1] || 'solid'};
  });
}

function environmentFor(log, frameCache) {
  const key = JSON.stringify([log.bodies, log.frames || null, log.direction || null]);
  let env = state.environments.find(e => e.key === key);
  if (env) return env;
  const frames = log.frames ? frameCache.get(log.frames) || null : null;
  env = {key, bodies: log.bodies, frames, scalar: log.scalar || 's', name: describe(log, frames)};
  state.environments.push(env);
  return env;
}

function describe(log, frames) {
  let name = log.bodies.length ? log.bodies.length + (log.bodies.length === 1 ? ' body: ' : ' bodies: ') + log.bodies.map(b =>
    (+(b.mass / MS).toPrecision(4)) + ' MS ' + (b.black ? 'black' : 'white') + ' at (' + fmt(b.x / AU) + ', ' + fmt(b.y / AU) + ') AU').join(', ')
    : 'No bodies';
  if (log.direction && log.direction.startsWith('down zero-energy paths'))
    name += log.direction.includes('exact two-body solution') ? ', eikonal flow (exact)' : ', eikonal flow';
  if (log.frames) name += (frames && frames.s ? ', ' + (log.scalar || 'a field') + ' (' :
                          frames && frames.times.length > 1 ? ', flow changing with time (' : ', flow frame (') +
                          studyName(log.frames.replace(/\.csv$/, '')) + ')';
  return name;
}

//---------------------------------------------------------------- the view

function plotRect() {
  const w = canvas.clientWidth, h = canvas.clientHeight;
  return {l: MARGIN.left, t: MARGIN.top, r: w - MARGIN.right, b: h - MARGIN.bottom};
}

function toScreen(x, y) {
  const {l, t, r, b} = plotRect(), [x0, x1, y0, y1] = state.view;
  return [l + (x - x0) / (x1 - x0) * (r - l), b - (y - y0) / (y1 - y0) * (b - t)];
}

function toData(sx, sy) {
  const {l, t, r, b} = plotRect(), [x0, x1, y0, y1] = state.view;
  return [x0 + (sx - l) / (r - l) * (x1 - x0), y0 + (b - sy) / (b - t) * (y1 - y0)];
}

function fit() {
  let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
  for (const r of state.results.filter(r => r.visible))
    for (const p of r.paths)
      for (let i = 0; i < p.x.length; i++)
        if (isFinite(p.x[i]) && isFinite(p.y[i])) {
          x0 = Math.min(x0, p.x[i]); x1 = Math.max(x1, p.x[i]); y0 = Math.min(y0, p.y[i]); y1 = Math.max(y1, p.y[i]);
        }
  if (!isFinite(x0)) { state.view = [-1, 1, -1, 1]; draw(); return; }
  const padX = (x1 - x0 || Math.abs(x0) || 1) * 0.08, padY = (y1 - y0 || Math.abs(y0) || 1) * 0.08;
  state.view = [x0 - padX, x1 + padX, y0 - padY, y1 + padY];
  equalise();
  draw();
}

/* with equal aspect, widen whichever axis needs it so a metre is as long across as up */
function equalise() {
  if (!state.prefs.equalAspect || !state.view) return;
  const {l, t, r, b} = plotRect();
  let [x0, x1, y0, y1] = state.view;
  const perX = (x1 - x0) / (r - l), perY = (y1 - y0) / (b - t);
  if (perX > perY) { const half = perX * (b - t) / 2, mid = (y0 + y1) / 2; y0 = mid - half; y1 = mid + half; }
  else { const half = perY * (r - l) / 2, mid = (x0 + x1) / 2; x0 = mid - half; x1 = mid + half; }
  state.view = [x0, x1, y0, y1];
}

function niceStep(span, count) {
  const raw = span / Math.max(count, 1), mag = 10 ** Math.floor(Math.log10(raw));
  for (const m of [1, 2, 2.5, 5, 10]) if (raw <= m * mag) return m * mag;
  return 10 * mag;
}

function ticks(v0, v1, count) {
  const step = niceStep(v1 - v0, count), out = [];
  for (let v = Math.ceil(v0 / step) * step; v <= v1 + step * 1e-9; v += step) out.push(Math.abs(v) < step * 1e-9 ? 0 : v);
  return {values: out, step};
}

function fmt(v) {
  if (v === 0) return '0';
  const a = Math.abs(v);
  return a >= 1e5 || a < 1e-3 ? v.toExponential(2).replace(/\.?0+e/, 'e').replace('e+', 'e') : +v.toPrecision(4) + '';
}

//---------------------------------------------------------------- drawing

function draw() {
  const ratio = window.devicePixelRatio || 1, w = canvas.clientWidth, h = canvas.clientHeight;
  if (canvas.width !== Math.round(w * ratio) || canvas.height !== Math.round(h * ratio)) {
    canvas.width = Math.round(w * ratio); canvas.height = Math.round(h * ratio);
  }
  ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
  ctx.fillStyle = css('--page'); ctx.fillRect(0, 0, w, h);
  $('empty').style.display = state.results.length ? 'none' : 'flex';
  if (!state.view) return;
  const {l, t, r, b} = plotRect();
  ctx.fillStyle = css('--surface'); ctx.fillRect(l, t, r - l, b - t);
  ctx.save();
  ctx.beginPath(); ctx.rect(l, t, r - l, b - t); ctx.clip();
  drawAxes(true);
  const keys = [];
  for (const env of fieldEnvironments()) keys.push(...drawField(env));
  for (const result of state.results.filter(r => r.visible)) {
    const until = drawUntil(result);
    if (until !== false) for (const p of result.paths) drawPath(result, p, until);
  }
  flushDots();
  for (const env of fieldEnvironments()) drawBodies(env);
  ctx.restore();
  ctx.strokeStyle = css('--axis'); ctx.lineWidth = 1; ctx.strokeRect(l, t, r - l, b - t);
  drawAxes(false);
  if (state.prefs.showPathLegend) drawLegend();
  if (state.prefs.showFieldKey && keys.length) drawKey(keys);
}

/* each axis's label and scale, from the columns the first shown path plots: time in seconds, distances in the unit */
function axes() {
  const path = state.results.filter(r => r.visible).flatMap(r => r.paths)[0];
  const one = name => {
    if (/^(t|time|pt|proper_t|tau)$/.test(name || '')) return {label: name + ' (s)', scale: 1};
    const [unit, scale] = UNITS[state.prefs.unit];
    return {label: ({pos_x: 'x', pos_y: 'y'}[name] || name || 'x') + ' (' + unit + ')', scale};
  };
  return [one(path ? path.xName : 'pos_x'), one(path ? path.yName : 'pos_y')];
}

function drawAxes(grid) {
  const {l, t, r, b} = plotRect(), [x0, x1, y0, y1] = state.view, [ax, ay] = axes();
  const xt = ticks(x0 / ax.scale, x1 / ax.scale, (r - l) / 100), yt = ticks(y0 / ay.scale, y1 / ay.scale, (b - t) / 60);
  ctx.font = '11px -apple-system, Helvetica, Arial, sans-serif';
  if (grid) {
    if (!state.prefs.showGrid) return;
    ctx.strokeStyle = css('--grid'); ctx.lineWidth = 1;
    for (const v of xt.values) { const [sx] = toScreen(v * ax.scale, 0); line(sx, t, sx, b); }
    for (const v of yt.values) { const [, sy] = toScreen(0, v * ay.scale); line(l, sy, r, sy); }
    return;
  }
  ctx.fillStyle = css('--ink2'); ctx.textAlign = 'center'; ctx.textBaseline = 'top';
  for (const v of xt.values) { const [sx] = toScreen(v * ax.scale, 0); ctx.fillText(fmt(v), sx, b + 6); }
  ctx.textAlign = 'right'; ctx.textBaseline = 'middle';
  for (const v of yt.values) { const [, sy] = toScreen(0, v * ay.scale); ctx.fillText(fmt(v), l - 6, sy); }
  ctx.textAlign = 'center'; ctx.textBaseline = 'bottom';
  ctx.fillText(ax.label, (l + r) / 2, canvas.clientHeight - 6);
  ctx.save(); ctx.translate(16, (t + b) / 2); ctx.rotate(-Math.PI / 2); ctx.textBaseline = 'top';
  ctx.fillText(ay.label, 0, 0); ctx.restore();
}

function line(x0, y0, x1, y1) { ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x1, y1); ctx.stroke(); }

/* a path: up to the replay time while replaying (with a dot where it is), else all of it; broken at empty rows */
function drawPath(result, p, until = replayTime()) {
  const colour = p.color || result.color;
  ctx.strokeStyle = colour; ctx.lineWidth = 1.6; ctx.setLineDash(DASHES[p.style] || []);
  ctx.beginPath();
  let pen = false;
  for (let i = 0; i < p.x.length; i++) {
    if (!(isFinite(p.x[i]) && isFinite(p.y[i]))) { pen = false; continue; }
    if (until !== null && p.t && p.t[i] > until) {
      //into the future: finish this stretch at the replay time, then skip to the next one
      if (pen && i > 0 && isFinite(p.x[i - 1])) {
        const f = (until - p.t[i - 1]) / (p.t[i] - p.t[i - 1]);
        const [sx, sy] = toScreen(p.x[i - 1] + f * (p.x[i] - p.x[i - 1]), p.y[i - 1] + f * (p.y[i] - p.y[i - 1]));
        ctx.lineTo(sx, sy); dot(sx, sy, colour);
      }
      pen = false;
      while (i + 1 < p.x.length && isFinite(p.x[i + 1])) i++;
      continue;
    }
    const [sx, sy] = toScreen(p.x[i], p.y[i]);
    if (pen) ctx.lineTo(sx, sy); else ctx.moveTo(sx, sy);
    pen = true;
  }
  ctx.stroke(); ctx.setLineDash([]);
}

const pendingDots = [];
function dot(sx, sy, colour) { pendingDots.push([sx, sy, colour]); }
function flushDots() {
  for (const [sx, sy, colour] of pendingDots.splice(0)) {
    ctx.fillStyle = colour; ctx.beginPath(); ctx.arc(sx, sy, 3.5, 0, 2 * Math.PI); ctx.fill();
  }
}

function drawBodies(env) {
  if (!state.prefs.showBodies && !state.prefs.showSchwarzschild) return;
  const scale = (toScreen(1, 0)[0] - toScreen(0, 0)[0]);
  for (const body of env.bodies) {
    const [sx, sy] = toScreen(body.x, body.y);
    if (state.prefs.showSchwarzschild) {
      const rs = 2 * G * body.mass / C / C * scale;
      if (rs > 2) { ctx.strokeStyle = css('--ink2'); ctx.setLineDash([2, 3]); ctx.beginPath(); ctx.arc(sx, sy, rs, 0, 2 * Math.PI); ctx.stroke(); ctx.setLineDash([]); }
    }
    if (state.prefs.showBodies) {
      ctx.fillStyle = body.black ? '#111' : '#fff'; ctx.strokeStyle = css('--ink'); ctx.lineWidth = 1;
      ctx.beginPath(); ctx.arc(sx, sy, 6, 0, 2 * Math.PI); ctx.fill(); ctx.stroke();
    }
  }
}

/* the environments whose backgrounds are drawn: all shown results' (All environments), or the selected result's */
function fieldEnvironments() {
  const shown = state.results.filter(r => r.visible);
  if (state.background === ALL) return [...new Set(shown.map(r => r.env))];
  const chosen = state.environments.find(e => e.name === state.background);
  if (chosen) return [chosen];
  const own = state.selected && state.selected.visible ? state.selected : shown[0];
  return own ? [own.env] : [];
}

/* u and g arrows from an environment's frames at the replay time (the start when stopped); returns key entries */
function drawField(env) {
  const keys = [], frames = env.frames;
  if (!frames) return keys;
  const t = fieldTime() ?? frames.times[0];
  const named = fieldEnvironments().length > 1 ? '  (' + env.name + ')' : '';
  if (frames.s && state.prefs.showScalar && frames.reference.s) {
    drawScalar(frames, t, frames.reference.s);
    const moment = frames.times.length > 1 ? '  at t = ' + fmt(t) + ' s' : '';
    keys.push([SCALAR_PLUS, env.scalar + ': red +' + fmt(frames.reference.s) + ', blue \u2212' + fmt(frames.reference.s) + moment + named]);
  }
  for (const [show, field, colour, label, offset] of [
      [state.prefs.showFlow, 'u', css('--muted'), 'u', 0],
      [state.prefs.showGravity, 'a', css('--g-arrow'), 'g, the acceleration of space', 0.5]]) {
    if (!show || !frames.reference[field]) continue;
    drawArrows(frames, field, t, colour, frames.reference[field], offset);
    const ref = frames.reference[field];
    const moment = frames.times.length > 1 ? '  at t = ' + fmt(t) + ' s' : '';
    keys.push([colour, label + '  ' + (field === 'u' ? speed(ref) : fmt(ref) + ' m/s²') + moment + named]);
  }
  return keys;
}

/* a scalar field as a colour map: cells of SCALAR_CELL pixels, red where it is positive, blue negative, their strength
   its size over the run's scale (capped); nothing off the grid or where it is not a number */
const SCALAR_CELL = 5, SCALAR_PLUS = '#d6452a', SCALAR_MINUS = '#2a6fd6';
function drawScalar(frames, t, reference) {
  const {l, t: top, r, b} = plotRect();
  for (let sy = top; sy < b; sy += SCALAR_CELL)
    for (let sx = l; sx < r; sx += SCALAR_CELL) {
      const [x, y] = toData(sx + SCALAR_CELL / 2, sy + SCALAR_CELL / 2), v = frameSample(frames, 's', x, y, t);
      if (!v || !isFinite(v[0]) || v[0] === 0) continue;
      ctx.globalAlpha = Math.min(1, Math.abs(v[0]) / reference) * 0.85;
      ctx.fillStyle = v[0] > 0 ? SCALAR_PLUS : SCALAR_MINUS;
      ctx.fillRect(sx, sy, SCALAR_CELL, SCALAR_CELL);
    }
  ctx.globalAlpha = 1;
}

function speed(v) { return v >= 1e3 ? fmt(v / 1e3) + ' km/s' : fmt(v) + ' m/s'; }

/* arrows on a screen grid, each from its grid point, its length in proportion to the field (capped at a full one) */
function drawArrows(frames, field, t, colour, reference, offset) {
  const {l, t: top, r, b} = plotRect(), longest = ARROW_SPACING * 0.8, shift = ARROW_SPACING * (0.5 + offset);
  ctx.strokeStyle = colour; ctx.fillStyle = colour; ctx.lineWidth = 1;
  for (let sy = top + shift; sy < b; sy += ARROW_SPACING)
    for (let sx = l + shift; sx < r; sx += ARROW_SPACING) {
      const [x, y] = toData(sx, sy), v = frameSample(frames, field, x, y, t);
      if (!v) continue;
      const size = Math.hypot(v[0], v[1]);
      if (!(size > 0)) continue;
      const length = longest * Math.min(1, size / reference), dx = v[0] / size * length, dy = -v[1] / size * length;
      arrow(sx, sy, sx + dx, sy + dy);
    }
}

function arrow(x0, y0, x1, y1) {
  line(x0, y0, x1, y1);
  const length = Math.hypot(x1 - x0, y1 - y0);
  if (length < 3) return;
  const ux = (x1 - x0) / length, uy = (y1 - y0) / length, head = Math.min(6, length * 0.6);
  ctx.beginPath(); ctx.moveTo(x1, y1);
  ctx.lineTo(x1 - head * ux + head * 0.4 * uy, y1 - head * uy - head * 0.4 * ux);
  ctx.lineTo(x1 - head * ux - head * 0.4 * uy, y1 - head * uy + head * 0.4 * ux);
  ctx.closePath(); ctx.fill();
}

function drawBox(lines, anchor) {
  ctx.font = '12px -apple-system, Helvetica, Arial, sans-serif';
  const {l, t, r, b} = plotRect(), rowH = 18, swatch = 26;
  const width = Math.max(...lines.map(([, text]) => ctx.measureText(text).width)) + swatch + 22;
  const height = rowH * lines.length + 8;
  const x = anchor === 'top-right' ? r - width - 8 : l + 8, y = anchor === 'top-right' ? t + 8 : b - height - 8;
  ctx.fillStyle = css('--surface'); ctx.strokeStyle = css('--grid');
  ctx.fillRect(x, y, width, height); ctx.strokeRect(x, y, width, height);
  lines.forEach(([colour, text, dash], i) => {
    const cy = y + 4 + rowH * i + rowH / 2;
    ctx.strokeStyle = colour; ctx.lineWidth = 1.6; ctx.setLineDash(dash || []);
    line(x + 8, cy, x + 8 + swatch, cy); ctx.setLineDash([]);
    ctx.fillStyle = css('--ink2'); ctx.textAlign = 'left'; ctx.textBaseline = 'middle';
    ctx.fillText(text, x + swatch + 14, cy);
  });
}

function drawLegend() {
  const lines = [];
  for (const r of state.results.filter(r => r.visible))
    for (const p of r.paths) lines.push([p.color || r.color, r.name + (r.paths.length > 1 ? ' ' + p.name : ''), DASHES[p.style]]);
  if (lines.length) drawBox(lines.slice(0, 16), 'top-right');
}

function drawKey(keys) { drawBox(keys, 'bottom-left'); }

//---------------------------------------------------------------- replay
/* the replay runs a clock across a timeline. played together (mode 'together') the timeline is the shown results'
   own times, all drawn up to the clock. played in turn ('sequence') each shown result's time range follows the last:
   the results before the clock's one are drawn whole, the current one up to its own time, the later ones not at all.
   with loop on, reaching the end clears the plot and starts again */

function timeRange(result) {
  let lo = Infinity, hi = -Infinity;
  for (const p of result.paths) if (p.t) for (const v of p.t) if (isFinite(v)) { lo = Math.min(lo, v); hi = Math.max(hi, v); }
  return isFinite(lo) ? [lo, hi] : null;
}

/* the shown results with times, end to end: {result, lo, hi, start} on the in-turn timeline */
function segments() {
  const out = [];
  let start = 0;
  for (const result of state.results.filter(r => r.visible)) {
    const range = timeRange(result);
    if (!range) continue;
    out.push({result, lo: range[0], hi: range[1], start});
    start += range[1] - range[0];
  }
  return out;
}

/* the clock's range: the shown results' times together, or their durations end to end */
function replayRange(mode = state.replay.mode) {
  const segs = segments();
  if (!segs.length) return null;
  if (mode === 'sequence') return [0, segs.reduce((sum, g) => sum + g.hi - g.lo, 0)];
  return [Math.min(...segs.map(g => g.lo)), Math.max(...segs.map(g => g.hi))];
}

/* in turn: the segment the clock is in, and the time within its result */
function currentSegment(clock = state.replay.t) {
  const segs = segments();
  let g = segs.find(g => clock < g.start + (g.hi - g.lo)) || segs[segs.length - 1];
  return g && {...g, index: segs.indexOf(g), count: segs.length, t: Math.min(g.hi, g.lo + Math.max(0, clock - g.start))};
}

function replayTime() { return state.replay.state === 'stopped' ? null : state.replay.t; }

/* how much of a result to draw: null for all of it, a time to draw it up to, or false for none of it yet */
function drawUntil(result) {
  const t = replayTime();
  if (t === null || state.replay.mode !== 'sequence') return t;
  const now = currentSegment(t);
  if (!now) return null;
  const mine = segments().find(g => g.result === result);
  if (!mine) return null;
  if (mine.start < now.start) return null;
  return mine.result === now.result ? now.t : false;
}

/* the time the background arrows are drawn at: the clock, or in turn the current result's own time */
function fieldTime() {
  const t = replayTime();
  if (t === null || state.replay.mode !== 'sequence') return t;
  const now = currentSegment(t);
  return now ? now.t : null;
}

function canPlayInTurn() { return segments().length > 1; }

function play(mode = 'together') {
  const rp = state.replay;
  if (rp.state === 'playing' && rp.mode === mode) { rp.state = 'paused'; showReplay(); return; }
  if (rp.mode !== mode) { rp.mode = mode; rp.state = 'stopped'; }
  const range = replayRange();
  if (!range) return;
  if (rp.state === 'stopped' || rp.t >= range[1]) rp.t = range[0];
  rp.state = 'playing'; rp.last = performance.now();
  requestAnimationFrame(tick);
  showReplay();
}

function tick() {
  const rp = state.replay, range = replayRange();
  if (rp.state !== 'playing' || !range) return;
  //the clock, not the frame's own timestamp: that can be earlier than play()'s start (in a background or embedded
  //frame), which ran the replay backwards out of the run
  const now = performance.now();
  rp.t = Math.max(range[0], rp.t + +state.prefs.replaySpeed * (range[1] - range[0]) / REPLAY_SECONDS * Math.max(0, now - rp.last) / 1000);
  rp.last = now;
  if (rp.t >= range[1]) {
    if (state.prefs.replayLoop) rp.t = range[0];      //clear, and go round again
    else { rp.t = range[1]; rp.state = 'paused'; }
  }
  showReplay();
  if (rp.state === 'playing') requestAnimationFrame(tick);
}

function stopReplay() { state.replay.state = 'stopped'; state.replay.t = null; }

function seek(f) {
  const range = replayRange();
  if (!range) return;
  if (state.replay.state === 'stopped') state.replay.state = 'paused';
  state.replay.t = range[0] + f * (range[1] - range[0]);
  showReplay();
}

const STOPPED_LABEL = 'stopped - 1× plays the whole run in ' + REPLAY_SECONDS + ' s';

/* the label for a state at a clock time: in turn, which result and the time within it */
function replayLabel(word, clock, range, mode = state.replay.mode) {
  if (mode !== 'sequence') return word + '  t = ' + fmt(clock) + ' of ' + fmt(range[1]) + ' s';
  const g = currentSegment(clock);
  return word + '  ' + (g.index + 1) + '/' + g.count + '  t = ' + fmt(g.t) + ' of ' + fmt(g.hi) + ' s';
}

/* the label's width: the widest text it can show for these results (every state and mode, t across the run), measured in its own
   font - fixed, so the controls don't change size or wrap as t's digits change during a replay */
let labelFit = {key: null, width: 0};
function fitReplayLabel() {
  const label = $('replayLabel');
  const key = segments().map(g => g.result.file + ':' + g.lo + ':' + g.hi).join();
  if (labelFit.key === key) return;
  const ctx = document.createElement('canvas').getContext('2d'), style = getComputedStyle(label);
  ctx.font = style.fontSize + ' ' + style.fontFamily;
  const texts = [STOPPED_LABEL];
  for (const mode of canPlayInTurn() ? ['together', 'sequence'] : ['together']) {    //both, so switching doesn't resize it
    const range = replayRange(mode);
    if (range) for (let i = 0; i <= 400; i++)
      for (const word of ['playing', 'paused']) texts.push(replayLabel(word, range[0] + i / 400 * (range[1] - range[0]), range, mode));
  }
  const width = Math.ceil(Math.max(...texts.map(s => ctx.measureText(s).width)) * 1.04) + 2;
  label.style.width = width + 'px';
  labelFit = {key, width};
}

function showReplay() {
  const rp = state.replay, range = replayRange();
  fitReplayLabel();
  $('play').textContent = rp.state === 'playing' && rp.mode === 'together' ? 'Pause' : 'Play';
  $('playInTurn').textContent = rp.state === 'playing' && rp.mode === 'sequence' ? 'Pause' : 'Play in turn';
  $('playInTurn').style.display = canPlayInTurn() ? '' : 'none';
  if (rp.mode === 'sequence' && !canPlayInTurn()) { rp.mode = 'together'; if (rp.state !== 'stopped') stopReplay(); }
  if (rp.state === 'stopped' || !range) {
    $('seek').value = 0; $('replayLabel').textContent = STOPPED_LABEL;
  } else {
    $('seek').value = Math.round((rp.t - range[0]) / (range[1] - range[0] || 1) * 1000);
    $('replayLabel').textContent = replayLabel(rp.state, rp.t, range);
  }
  $('replayLabel').title = $('replayLabel').textContent;
  draw();
}

//---------------------------------------------------------------- controls

function message(text) { $('message').textContent = text; }

function syncControls() {
  for (const id of ['showFlow', 'showGravity', 'showScalar', 'showBodies', 'showSchwarzschild', 'equalAspect', 'showGrid', 'showPathLegend', 'showFieldKey'])
    $(id).checked = !!state.prefs[id];
  $('unit').value = state.prefs.unit;
  $('loop').checked = !!state.prefs.replayLoop;
  $('speed').value = SPEEDS.includes(String(state.prefs.replaySpeed)) ? String(state.prefs.replaySpeed) : '1';
  const background = $('background');
  background.innerHTML = '';
  for (const name of [SELECTED, ALL, ...state.environments.filter(e => e.bodies.length || e.frames).map(e => e.name)])
    background.add(new Option(name, name));
  background.value = state.background;
  const list = $('results');
  list.innerHTML = '';
  for (const r of state.results) {
    const row = document.createElement('div');
    row.className = 'result' + (r === state.selected ? ' selected' : '');
    row.title = r.file + '\n' + r.env.name;
    const box = document.createElement('input');
    box.type = 'checkbox'; box.checked = r.visible;
    box.onclick = e => { e.stopPropagation(); r.visible = box.checked; showReplay(); };
    const swatch = document.createElement('div');
    swatch.className = 'swatch'; swatch.style.background = (r.paths[0] && r.paths[0].color) || r.color;
    const name = document.createElement('span'); name.textContent = r.name;
    row.append(box, swatch, name);
    row.onclick = () => { state.selected = r; syncControls(); draw(); };
    list.append(row);
  }
  showReplay();
}

function setup() {
  UNITS.forEach(([name], i) => $('unit').add(new Option(name, i)));
  SPEEDS.forEach(s => $('speed').add(new Option(s + '×', s)));
  for (const id of ['showFlow', 'showGravity', 'showScalar', 'showBodies', 'showSchwarzschild', 'showGrid', 'showPathLegend', 'showFieldKey'])
    $(id).onchange = () => { state.prefs[id] = $(id).checked; draw(); };
  $('equalAspect').onchange = () => { state.prefs.equalAspect = $('equalAspect').checked; equalise(); draw(); };
  $('unit').onchange = () => { state.prefs.unit = +$('unit').value; draw(); };
  $('speed').onchange = () => { state.prefs.replaySpeed = $('speed').value; };
  $('background').onchange = () => { state.background = $('background').value; draw(); };
  $('fit').onclick = fit;
  $('play').onclick = () => play('together');
  $('playInTurn').onclick = () => play('sequence');
  $('loop').onchange = () => { state.prefs.replayLoop = $('loop').checked; };
  $('stop').onclick = () => { stopReplay(); showReplay(); };
  $('seek').oninput = () => seek($('seek').value / 1000);
  $('openFolder').onclick = () => $('folderInput').click();
  $('folderInput').onchange = () => openFiles([...$('folderInput').files]);

  //pan by dragging, zoom with the wheel at the pointer, fit with a double click
  let dragging = null;
  canvas.onpointerdown = e => { if (state.view) { dragging = [e.offsetX, e.offsetY, state.view.slice()]; canvas.setPointerCapture(e.pointerId); } };
  canvas.onpointermove = e => {
    if (!dragging) return;
    const {l, t, r, b} = plotRect(), [px, py, v] = dragging;
    const dx = (e.offsetX - px) / (r - l) * (v[1] - v[0]), dy = (e.offsetY - py) / (b - t) * (v[3] - v[2]);
    state.view = [v[0] - dx, v[1] - dx, v[2] + dy, v[3] + dy];
    draw();
  };
  canvas.onpointerup = () => { dragging = null; };
  canvas.ondblclick = fit;
  canvas.addEventListener('wheel', e => {
    if (!state.view) return;
    e.preventDefault();
    const factor = Math.exp(e.deltaY * 0.0015), [x, y] = toData(e.offsetX, e.offsetY), v = state.view;
    state.view = [x + (v[0] - x) * factor, x + (v[1] - x) * factor, y + (v[2] - y) * factor, y + (v[3] - y) * factor];
    draw();
  }, {passive: false});

  //drop a run folder (or its files) on the plot
  const wrap = $('plotWrap');
  wrap.ondragover = e => { e.preventDefault(); $('drop').style.display = 'flex'; };
  wrap.ondragleave = () => { $('drop').style.display = 'none'; };
  wrap.ondrop = async e => {
    e.preventDefault(); $('drop').style.display = 'none';
    openFiles(await droppedFiles(e.dataTransfer));
  };
  window.onresize = () => { equalise(); draw(); };
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', draw);

  const run = new URLSearchParams(location.search).get('run');
  if (run) {
    const url = new URL(run, location.href);
    loadRun(urlSource(url), url.pathname.split('/').pop());
  } else {
    syncControls(); draw();
  }
}

function openFiles(files) {
  if (!files.length) return;
  //a chosen folder may hold several runs: take the folder of the first full.json (else of the first csv)
  const first = files.find(f => f.name.endsWith('.full.json')) || files.find(f => f.name.endsWith('.csv'));
  if (!first) { message('no .full.json or .csv files there'); return; }
  const folder = (first.webkitRelativePath || first.relativePath || '').split('/').slice(0, -1).join('/');
  const same = files.filter(f => (f.webkitRelativePath || f.relativePath || '').split('/').slice(0, -1).join('/') === folder);
  loadRun(folderSource(same));
}

async function droppedFiles(transfer) {
  const out = [];
  const walk = async (entry, path) => {
    if (entry.isFile) {
      const file = await new Promise((ok, no) => entry.file(ok, no));
      file.relativePath = path + file.name;
      out.push(file);
    } else if (entry.isDirectory) {
      const reader = entry.createReader();
      for (let batch; (batch = await new Promise((ok, no) => reader.readEntries(ok, no))).length;)
        for (const child of batch) await walk(child, path + entry.name + '/');
    }
  };
  for (const item of transfer.items) {
    const entry = item.webkitGetAsEntry && item.webkitGetAsEntry();
    if (entry) await walk(entry, '');
  }
  return out;
}

setup();
