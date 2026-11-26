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
const TIME_COLUMN = /^(t|time|pt|proper_t|tau)$/;   //columns of time: against them bodies and horizons are lines
const UNITS = [['m', 1], ['km', 1e3], ['AU', AU], ['light-seconds', C]];
const SPEEDS = ['0.1', '0.2', '0.5', '1', '2', '5', '10'];
const speedName = s => '×' + s;   //×0.1 ... ×10
const SERIES = ['#2a78d6', '#eb6834', '#1baf7a', '#8a5cd8', '#d6a21e', '#d64c7a', '#4fb3c8', '#7a7a74'];
const DASHES = {solid: [], dashed: [8, 5], dotted: [2, 4]};
const MARGIN = {left: 78, right: 18, top: 16, bottom: 44};
const ARROW_SPACING = 40;   //pixels between background arrows
const PLAYER = new URLSearchParams(location.search).has('player');   //the cut-down player, for embedding in pages
const REPLAY_SECONDS = 20;  //a whole run at 1x
const ALL = 'All environments', SELECTED = "Selected result's environment";
const PREFS = {unit: 0, equalAspect: true, showGrid: true, showFlow: true, showGravity: false, showScalar: true, showTwist: true, showSeam: true,
               showBodies: true, showSchwarzschild: true, showSpin: false, showPathLegend: true, graduateOrbits: false, showFieldKey: true, replaySpeed: '1', replayLoop: false};

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
  const backgrounds = (text.match(/^backgrounds: (.+)$/m) || [])[1];
  return {bodies, frames: frames ? files(frames) : null, direction, wave, scalar: scalar && scalar.trim(),
          backgrounds: backgrounds && backgrounds.trim()};
}

/* a log's list of frames files, comma-separated (a colour map's, a flow's) */
function files(text) {
  return text.split(',').map(f => f.trim()).filter(Boolean);
}

/* background frames (docs/archive/formats.md): on a grid at a run of times, t, x, y and any of the flow (u_x, u_y),
   its acceleration (a_x, a_y) and a scalar s (a wave's strain, say) drawn as a colour map. nan where a field has no
   value (a flow worked out only near some points); a field a file doesn't carry has no reference, so isn't drawn */
function parseFrames(text) {
  const lines = text.split(/\r?\n/).filter(l => l.trim());
  const header = lines[0].split(',').map(c => c.trim()), col = name => header.indexOf(name);
  const width = header.length, n = lines.length - 1, raw = new Float64Array(n * width);
  for (let i = 0; i < n; i++) {
    const cells = lines[i + 1].split(',');
    for (let j = 0; j < width; j++) raw[i * width + j] = +cells[j];
  }
  const unique = k => [...new Set(Array.from({length: n}, (_, i) => raw[i * width + k]))].sort((a, b) => a - b);
  const times = unique(0), xs = unique(1), ys = unique(2);
  //each field two values a point, so frameSample reads them all alike (a scalar's second is 0)
  const field = (cx, cy) => {
    if (cx < 0) return null;
    const out = new Float32Array(n * 2);
    for (let i = 0; i < n; i++) { out[2 * i] = raw[i * width + cx]; out[2 * i + 1] = cy < 0 ? 0 : raw[i * width + cy]; }
    return out;
  };
  const u = field(col('u_x'), col('u_y')), a = field(col('a_x'), col('a_y')), s = field(col('s'), -1);
  const frames = {times, xs, ys, u, a, size: xs.length * ys.length};
  if (s) frames.s = s;
  frames.reference = {u: u && percentileOfSizes(u, 90), a: a && percentileOfSizes(a, 90),   //one scale for the run
                      s: s && percentileOfSizes(s, 98)};
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

/* an environment's frames from several files: each field (u, a, s) from the first file that has it */
function combineFrames(layers) {
  layers = layers.filter(Boolean);
  if (!layers.length) return null;
  const layer = {}, reference = {};
  for (const key of ['u', 'a', 's']) {
    layer[key] = layers.find(f => f.reference[key]) || null;
    reference[key] = layer[key] ? layer[key].reference[key] : null;
  }
  return {layer, reference};
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
  state.results = []; state.environments = []; state.selected = null; state.backgrounds = null; stopReplay();
  try {
    fullName = fullName || source.names().find(n => n.endsWith('.full.json'));
    let entries, chosen = null;
    if (fullName) {
      const full = JSON.parse(await source.read(fullName));
      if (full.preferences) Object.assign(state.prefs, pickPrefs(JSON.parse(await source.read(full.preferences)).preferences || {}));
      const config = full.config ? JSON.parse(await source.read(full.config)) : {results: []};
      entries = config.results || [];
      state.background = config.background === ALL ? ALL : SELECTED;
      chosen = config.background;
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
    const named = logs.flatMap(l => l.frames || []);
    const frameCache = new Map(await Promise.all([...new Set(named)].map(async name => {
      try { return [name, parseFrames(await read(name))]; }
      catch (e) { message('no frames file ' + name); return [name, null]; }
    })));
    //a backgrounds file (engine/backgrounds.py): its backgrounds make the Background menu, in place of environments'
    const manifests = [...new Set(logs.map(l => l.backgrounds).filter(Boolean))];
    for (const name of manifests) {
      try { state.backgrounds = (state.backgrounds || []).concat(parseBackgrounds(await read(name))); }
      catch (e) { message('could not read the backgrounds file ' + name + ': ' + e.message); }
    }
    if (state.backgrounds && state.backgrounds.length)
      state.background = (state.backgrounds.find(b => b.name === chosen) || state.backgrounds[0]).name;
    else state.backgrounds = null;
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

/* a result's environment (its bodies and background frames), shared by results with the same */
function environmentFor(log, frameCache) {
  const files = log.frames;
  const key = JSON.stringify([log.bodies, files || null, log.direction || null]);
  let env = state.environments.find(e => e.key === key);
  if (env) return env;
  const frames = files ? combineFrames(files.map(f => frameCache.get(f))) : null;
  env = {key, bodies: log.bodies, frames, scalar: log.scalar || 's', name: describe(log, frames, files)};
  state.environments.push(env);
  return env;
}

function describe(log, frames, files) {
  let name = log.bodies.length ? log.bodies.length + (log.bodies.length === 1 ? ' body: ' : ' bodies: ') + log.bodies.map(b =>
    (+(b.mass / MS).toPrecision(4)) + ' MS ' + (b.black ? 'black' : 'white') + ' at (' + fmt(b.x / AU) + ', ' + fmt(b.y / AU) + ') AU').join(', ')
    : 'No bodies';
  if (log.direction && log.direction.startsWith('down zero-energy paths'))
    name += log.direction.includes('exact two-body solution') ? ', eikonal flow (exact)' : ', eikonal flow';
  if (files && files.length) {
    const flow = frames && (frames.layer.u || frames.layer.a);
    name += (frames && frames.layer.s ? ', ' + (log.scalar || 'a field') : '') +
            (!flow ? '' : flow.times.length > 1 ? ', flow changing with time' : ', flow frame') +
            ' (' + files.map(f => studyName(f.replace(/\.csv$/, ''))).join(', ') + ')';
  }
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
  //against time, the bodies' lines are in view too
  const path = state.results.filter(r => r.visible).flatMap(r => r.paths)[0];
  const timeX = path && TIME_COLUMN.test(path.xName || ''), timeY = path && TIME_COLUMN.test(path.yName || '');
  if (state.prefs.showBodies && (timeX || timeY))
    for (const env of fieldEnvironments())
      for (const body of env.bodies) {
        const at = bodyCoordinate(timeY ? path.xName : path.yName, body);
        if (at === null) continue;
        if (timeY) { x0 = Math.min(x0, at); x1 = Math.max(x1, at); } else { y0 = Math.min(y0, at); y1 = Math.max(y1, at); }
      }
  //in x / y, a body just off the paths (light near a hole) is brought into view; one far away is left out
  else if (state.prefs.showBodies && /^(pos_)?x$/.test(path.xName || '') && /^(pos_)?y$/.test(path.yName || '')) {
    const size = Math.max(x1 - x0, y1 - y0);
    for (const env of fieldEnvironments())
      for (const body of env.bodies)
        if (Math.max(x0 - body.x, body.x - x1, y0 - body.y, body.y - y1) < size) {
          x0 = Math.min(x0, body.x); x1 = Math.max(x1, body.x); y0 = Math.min(y0, body.y); y1 = Math.max(y1, body.y);
        }
  }
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
  syncAvailable();
  $('empty').style.display = state.results.length ? 'none' : 'flex';
  if (!state.view) return;
  const {l, t, r, b} = plotRect();
  ctx.fillStyle = css('--surface'); ctx.fillRect(l, t, r - l, b - t);
  ctx.save();
  ctx.beginPath(); ctx.rect(l, t, r - l, b - t); ctx.clip();
  drawAxes(true);
  const keys = [];
  const background = currentBackground();
  if (background) keys.push(...drawBackground(background));
  else for (const env of fieldEnvironments()) keys.push(...drawField(env));
  for (const result of state.results.filter(r => r.visible)) {
    const until = drawUntil(result);
    if (until !== false) for (const p of result.paths) drawPath(result, p, until);
  }
  flushDots();
  spinning.length = 0;
  for (const env of fieldEnvironments()) drawBodies(env);
  drawSpinning();
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
    if (TIME_COLUMN.test(name || '')) return {label: name + ' (s)', scale: 1};
    if (/\(.+\)\s*$/.test(name || '')) return {label: name, scale: 1};     //a column that names its own unit
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

/* a path: up to the replay time while replaying (with a dot where it is), else all of it; broken at empty rows. with
   graduated orbits on, a path that goes round its body is drawn orbit by orbit: the current one (at the replay time, or
   the last) in full colour, each earlier one fainter, so the orbits' build-up shows */
function drawPath(result, p, until = replayTime()) {
  const colour = p.color || result.color;
  ctx.strokeStyle = colour; ctx.lineWidth = 1.6; ctx.setLineDash(DASHES[p.style] || []);
  const orbit = state.prefs.graduateOrbits ? orbitsOf(result, p) : null;
  let current = 0;
  if (orbit) {
    current = orbit[orbit.length - 1];
    if (until !== null && p.t) for (let i = 0; i < p.x.length; i++) { if (p.t[i] > until) break; current = orbit[i]; }
  }
  const shade = k => k <= 0 ? 1 : Math.max(0.12, 0.55 * Math.pow(0.8, k - 1));
  let stretch = orbit ? orbit[0] : 0;
  ctx.globalAlpha = orbit ? shade(current - stretch) : 1;
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
    if (orbit && orbit[i] !== stretch) {
      //a new orbit: finish the last one at this point, then carry on in the new one's shade
      if (pen) ctx.lineTo(sx, sy);
      ctx.stroke();
      stretch = orbit[i]; ctx.globalAlpha = shade(current - stretch);
      ctx.beginPath(); ctx.moveTo(sx, sy); pen = true;
      continue;
    }
    if (pen) ctx.lineTo(sx, sy); else ctx.moveTo(sx, sy);
    pen = true;
  }
  ctx.stroke(); ctx.setLineDash([]); ctx.globalAlpha = 1;
}

/* which orbit each point of a position path is in, counting whole turns round the result's first body from where it
   starts (null for paths that aren't positions, or don't go round once) */
function orbitsOf(result, p) {
  if (p.orbits !== undefined) return p.orbits;
  p.orbits = null;
  if (p.xName !== 'pos_x' || p.yName !== 'pos_y') return null;
  const body = (result.env && result.env.bodies && result.env.bodies[0]) || {x: 0, y: 0};
  const out = new Int32Array(p.x.length);
  let turned = 0, last = null;
  for (let i = 0; i < p.x.length; i++) {
    if (isFinite(p.x[i]) && isFinite(p.y[i])) {
      const angle = Math.atan2(p.y[i] - body.y, p.x[i] - body.x);
      if (last !== null) turned += ((angle - last + 3 * Math.PI) % (2 * Math.PI)) - Math.PI;
      last = angle;
    } else last = null;
    out[i] = Math.max(0, Math.floor(Math.abs(turned) / (2 * Math.PI) - 1e-3));   //a path ending on a whole turn ends its last orbit
  }
  if (out[out.length - 1] > 0) p.orbits = out;
  return p.orbits;
}

const pendingDots = [];
function dot(sx, sy, colour) { pendingDots.push([sx, sy, colour]); }
function flushDots() {
  for (const [sx, sy, colour] of pendingDots.splice(0)) {
    ctx.fillStyle = colour; ctx.beginPath(); ctx.arc(sx, sy, 3.5, 0, 2 * Math.PI); ctx.fill();
  }
}

/* the background checkboxes a run can use: greyed out, with a tip saying why, when no environment being drawn has
   the data (u, g or a colour map in its frames; bodies, and so horizons) */
function syncAvailable() {
  const envs = fieldEnvironments(), background = currentBackground();
  const has = background ? key => backgroundHas(background, key) : key => envs.some(e => e.frames && e.frames.reference[key]);
  const bodies = envs.some(e => e.bodies.length);
  const which = background ? 'this background' : state.background === ALL ? 'this run' : "the selected result's background";
  for (const [id, ok, missing] of [
      ['showFlow', has('u'), 'no flow of space (u) saved for ' + which],
      ['showGravity', has('a'), 'no acceleration of space (g) saved for ' + which],
      ['showScalar', has('s'), 'no colour-map field saved for ' + which],
      ['showTwist', has('t'), 'no twist saved for ' + which + ' (only a spinning hole\'s river has one)'],
      ['showSeam', has('seam'), 'no seam saved for ' + which + ' (only the eikonal flows have one)'],
      ['showBodies', bodies, 'no bodies in ' + which],
      ['showSchwarzschild', bodies, 'no bodies, so no horizons, in ' + which],
      ['showSpin', envs.some(e => e.bodies.some(b => b.spin)), 'no spinning bodies in ' + which]]) {
    const box = $(id);
    if (box.disabled === !ok) continue;
    box.disabled = !ok;
    box.parentElement.title = ok ? '' : 'Not available: ' + missing;
  }
}

/* a body's place on the axis a column plots: its x or y for a position, the origin for a distance from it; null
   for anything else */
function bodyCoordinate(name, body) {
  if (/^(pos_)?x$/.test(name || '')) return body.x;
  if (/^(pos_)?y$/.test(name || '')) return body.y;
  if (/^(r|d|dist|distance)$/.test(name || '')) return 0;
  return null;
}

function drawBodies(env) {
  if (!state.prefs.showBodies && !state.prefs.showSchwarzschild) return;
  const path = state.results.filter(r => r.visible).flatMap(r => r.paths)[0];
  const timeX = path && TIME_COLUMN.test(path.xName || ''), timeY = path && TIME_COLUMN.test(path.yName || '');
  if (timeX || timeY) {
    //against time a body stays where it is: a line along the time axis, and its horizon a dotted line either side
    const {l, t: top, r, b} = plotRect();
    const across = (at, dash, colour, width) => {
      const [sx, sy] = toScreen(timeY ? at : 0, timeY ? 0 : at);
      ctx.strokeStyle = colour; ctx.lineWidth = width; ctx.setLineDash(dash);
      if (timeY) line(sx, top, sx, b); else line(l, sy, r, sy);
      ctx.setLineDash([]); ctx.lineWidth = 1;
    };
    for (const body of env.bodies) {
      const at = bodyCoordinate(timeY ? path.xName : path.yName, body);
      if (at === null) continue;
      if (state.prefs.showSchwarzschild) {
        const rs = 2 * G * body.mass / C / C;
        for (const side of [-1, 1]) across(at + side * rs, [2, 3], css('--ink2'), 1);
      }
      if (state.prefs.showBodies) across(at, [], body.black ? '#111' : css('--ink'), 2.5);
    }
    return;
  }
  const scale = (toScreen(1, 0)[0] - toScreen(0, 0)[0]);
  for (const body of env.bodies) {
    const [sx, sy] = toScreen(body.x, body.y);
    if (state.prefs.showSchwarzschild) {
      //the horizon; a spinning hole's (Kerr, r+ = M + sqrt(M^2 - a^2)) at the flat distance R = sqrt(r^2 + a^2),
      //with its ergosphere, r = 2M in the equatorial plane, dashed outside it
      const M = G * body.mass / C / C, a = (body.spin || 0) * M;
      const ring = (R, dash) => {
        if (R * scale <= 2) return;
        ctx.strokeStyle = css('--ink2'); ctx.setLineDash(dash); ctx.beginPath(); ctx.arc(sx, sy, R * scale, 0, 2 * Math.PI); ctx.stroke(); ctx.setLineDash([]);
      };
      const rPlus = M + Math.sqrt(Math.max(M * M - a * a, 0));
      ring(Math.hypot(rPlus, a), [2, 3]);
      if (a) ring(Math.hypot(2 * M, a), [7, 5]);
    }
    if (state.prefs.showBodies && state.prefs.showSpin && body.spin) { spinning.push({sx, sy, body}); continue; }
    if (state.prefs.showBodies) {
      ctx.fillStyle = body.black ? '#111' : '#fff'; ctx.strokeStyle = css('--ink'); ctx.lineWidth = 1;
      ctx.beginPath(); ctx.arc(sx, sy, 6, 0, 2 * Math.PI); ctx.fill(); ctx.stroke();
    }
  }
}

/* spinning bodies, on a canvas over the plot so that they turn without the plot being redrawn: each a disc with
   three spokes turning the way the body spins (anticlockwise for positive spin) at SPIN_RATE times its spin (rad/s of
   the page's clock: a picture, not the real rate), and an arrow round it */
const SPIN_RATE = 2.5, spinning = [], spinCanvas = $('spinLayer'), spinCtx = spinCanvas.getContext('2d');
let spinFrame = null;
function drawSpinning() {
  if (spinning.length) { if (spinFrame === null) spinFrame = requestAnimationFrame(turnSpinning); }
  else turnSpinning();   //clears it
}
function turnSpinning(now = performance.now()) {
  if (spinFrame !== null) cancelAnimationFrame(spinFrame);
  spinFrame = null;
  const ratio = window.devicePixelRatio || 1, w = spinCanvas.clientWidth, h = spinCanvas.clientHeight;
  if (spinCanvas.width !== Math.round(w * ratio) || spinCanvas.height !== Math.round(h * ratio)) {
    spinCanvas.width = Math.round(w * ratio); spinCanvas.height = Math.round(h * ratio);
  }
  const c = spinCtx;
  c.setTransform(ratio, 0, 0, ratio, 0, 0);
  c.clearRect(0, 0, w, h);
  if (!spinning.length || !state.view) return;
  const {l, t, r, b} = plotRect();
  c.save(); c.beginPath(); c.rect(l, t, r - l, b - t); c.clip();
  for (const {sx, sy, body} of spinning) {
    const R = 10, turn = -Math.sign(body.spin) * SPIN_RATE * Math.min(1, Math.abs(body.spin)) * now / 1000;
    c.fillStyle = body.black ? '#111' : '#fff'; c.strokeStyle = css('--ink'); c.lineWidth = 1;
    c.beginPath(); c.arc(sx, sy, R, 0, 2 * Math.PI); c.fill(); c.stroke();
    c.strokeStyle = body.black ? '#fff' : css('--ink'); c.lineWidth = 1.6;
    for (let k = 0; k < 3; k++) {
      const a = turn + k * 2 * Math.PI / 3;
      c.beginPath(); c.moveTo(sx + 2.5 * Math.cos(a), sy + 2.5 * Math.sin(a)); c.lineTo(sx + (R - 2) * Math.cos(a), sy + (R - 2) * Math.sin(a)); c.stroke();
    }
    c.strokeStyle = css('--ink'); c.fillStyle = css('--ink'); c.lineWidth = 1.4;
    twistArc(c, sx, sy, R + 5, 1.5 * Math.PI, body.spin > 0, 7);   //an arrow three quarters of the way round
  }
  c.restore();
  spinFrame = requestAnimationFrame(turnSpinning);
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
  const first = frames.layer.s || frames.layer.u || frames.layer.a;
  const t = fieldTime() ?? first.times[0];
  const named = fieldEnvironments().length > 1 ? '  (' + env.name + ')' : '';
  const when = layer => layer.times.length > 1 ? '  at t = ' + fmt(t) + ' s' : '';
  if (frames.layer.s && state.prefs.showScalar) {
    drawScalar((x, y) => frameSample(frames.layer.s, 's', x, y, t), frames.reference.s);
    const moment = when(frames.layer.s);
    keys.push([SCALAR_PLUS, env.scalar + ': red +' + fmt(frames.reference.s) + ', blue \u2212' + fmt(frames.reference.s) + moment + named]);
  }
  for (const [show, field, colour, label, offset] of [
      [state.prefs.showFlow, 'u', css('--muted'), 'u', 0],
      [state.prefs.showGravity, 'a', css('--g-arrow'), 'g, the acceleration of space', 0.5]]) {
    if (!show || !frames.layer[field]) continue;
    drawArrows((x, y) => frameSample(frames.layer[field], field, x, y, t), colour, frames.reference[field], offset);
    const ref = frames.reference[field];
    const moment = when(frames.layer[field]);
    keys.push([colour, label + '  ' + (field === 'u' ? speed(ref) : fmt(ref) + ' m/s²') + moment + named]);
  }
  return keys;
}

//---------------------------------------------------------------- backgrounds files (engine/backgrounds.py)

/* a backgrounds file's backgrounds, each field's values decoded once */
function parseBackgrounds(text) {
  const doc = JSON.parse(text), shared = (doc.shared || []).map(decodeLayer);   //layers several backgrounds use
  return (doc.backgrounds || []).map(b => ({name: b.name, description: b.description || '', reference: b.reference || {},
    layers: (b.layers || []).map(l => 'shared' in l ? shared[l.shared] : decodeLayer(l)), cache: new Map()}));
}

/* a field layer's stored values (sign, then 1 + 800 (log10 |v/scale| + 20); 0 is 0, -32768 none) as numbers, two
   to a point per quantity (a colour map's second is 0) */
function decodeLayer(layer) {
  if (layer.type !== 'field') return layer;
  const raw = atob(layer.data), ints = new Int16Array(raw.length / 2);
  for (let i = 0; i < ints.length; i++) ints[i] = raw.charCodeAt(2 * i) | (raw.charCodeAt(2 * i + 1) << 8);
  const comps = layer.components, nc = comps.length, n = ints.length / nc, values = {};
  for (const c of comps) values[c[0]] = values[c[0]] || new Float32Array(n * 2);
  for (let i = 0; i < n; i++)
    for (let c = 0; c < nc; c++) {
      const q = ints[i * nc + c], name = comps[c], scale = layer.scale[name[0]];
      values[name[0]][2 * i + (name.endsWith('_y') ? 1 : 0)] =
        q === -32768 ? NaN : q === 0 ? 0 : Math.sign(q) * Math.pow(10, (Math.abs(q) - 1) / 800 - 20) * scale;
    }
  const g = layer.grid, size = g.kind === 'polar' ? g.nr * g.nt : g.nx * g.ny;
  return Object.assign({}, layer, {values, size, data: null});
}

function currentBackground() {
  if (!state.backgrounds) return null;
  return state.backgrounds.find(b => b.name === state.background) || state.backgrounds[0];
}

/* whether a background can draw u, a (g), s (a colour map), t (twist arcs) or lines (the seam) */
function backgroundHas(background, key) {
  return background.layers.some(l => l.type === 'field' ? !!l.values[key] : l.type === 'linear' ? key === 'u' || key === 'a'
                                                         : l.type === 'lines' && key === 'seam');
}

/* where along a list of times t falls, as a fractional index, held at the ends */
function timeIndex(times, t) {
  const k = locate(times, t);
  return k === null ? (t < times[0] ? 0 : times.length - 1) : k;
}

/* a frame's centre, angle, scale and quantity scales at t */
function frameAt(frame, t) {
  const k = timeIndex(frame.times, t), k0 = Math.floor(k), k1 = Math.min(k0 + 1, frame.times.length - 1), f = k - k0;
  const out = {};
  for (const key of ['x', 'y', 'angle', 'scale', 'u', 'a', 's']) out[key] = frame[key][k0] * (1 - f) + frame[key][k1] * f;
  return out;
}

/* a layer's u, a or s at the world point (x, y), time t: [vx, vy] (a colour map's [s, 0]), or null where it has none */
function sampleLayer(layer, key, x, y, t) {
  if (layer.type === 'linear') {
    if (key !== 'u' && key !== 'a') return null;
    const dx = x - layer.centre[0], dy = y - layer.centre[1];
    if (layer.radius !== null && Math.hypot(dx, dy) > layer.radius) return null;
    const k = timeIndex(layer.times, t), k0 = Math.floor(k), k1 = Math.min(k0 + 1, layer.times.length - 1), f = k - k0;
    const m = layer[key][k0].map((v, i) => v * (1 - f) + layer[key][k1][i] * f);
    return [m[0] * dx + m[1] * dy, m[2] * dx + m[3] * dy];
  }
  if (layer.type !== 'field' || !layer.values[key]) return null;
  const fr = layer.frame ? frameAt(layer.frame, t) : null;
  let px = x, py = y;
  if (fr) {
    const dx = x - fr.x, dy = y - fr.y, c = Math.cos(fr.angle), s = Math.sin(fr.angle);
    px = (c * dx + s * dy) / fr.scale; py = (-s * dx + c * dy) / fr.scale;
  }
  //the four grid points round it, and how far between
  const g = layer.grid;
  let i0, i1, j0, j1, fi, fj, across;
  if (g.kind === 'polar') {
    const r = Math.hypot(px, py);
    if (!(r >= g.r0 && r <= g.r1)) return null;
    const ring = Math.log(r / g.r0) / Math.log(g.r1 / g.r0) * (g.nr - 1);
    let angle = Math.atan2(py, px); if (angle < 0) angle += 2 * Math.PI;
    const a = angle / (2 * Math.PI) * g.nt;
    j0 = Math.min(Math.floor(ring), g.nr - 2); j1 = j0 + 1; fj = ring - j0;
    i0 = Math.floor(a) % g.nt; i1 = (i0 + 1) % g.nt; fi = a - Math.floor(a);
    across = g.nt;
  } else {
    const fx = (px - g.x0) / (g.x1 - g.x0) * (g.nx - 1), fy = (py - g.y0) / (g.y1 - g.y0) * (g.ny - 1);
    if (!(fx >= 0 && fx <= g.nx - 1 && fy >= 0 && fy <= g.ny - 1)) return null;
    i0 = Math.min(Math.floor(fx), g.nx - 2); i1 = i0 + 1; fi = fx - i0;
    j0 = Math.min(Math.floor(fy), g.ny - 2); j1 = j0 + 1; fj = fy - j0;
    across = g.nx;
  }
  const k = timeIndex(layer.times, t), k0 = Math.floor(k), k1 = Math.min(k0 + 1, layer.times.length - 1), fk = k - k0;
  const values = layer.values[key], out = [0, 0];
  for (const [frame, wt] of [[k0, 1 - fk], [k1, fk]]) {
    if (wt === 0) continue;
    const base = frame * layer.size;
    for (const [i, j, w] of [[i0, j0, (1 - fi) * (1 - fj)], [i1, j0, fi * (1 - fj)], [i0, j1, (1 - fi) * fj], [i1, j1, fi * fj]])
      for (let c = 0; c < 2; c++) out[c] += wt * w * values[2 * (base + j * across + i) + c];
  }
  if (!isFinite(out[0]) || !isFinite(out[1])) return null;
  if (!fr) return out;
  if (key === 's') return [out[0] * fr.s, 0];
  if (key === 't') return [out[0], 0];
  const c = Math.cos(fr.angle), s = Math.sin(fr.angle), m = fr[key];
  return [(c * out[0] - s * out[1]) * m, (s * out[0] + c * out[1]) * m];
}

/* a background's u, a or s at (x, y), time t: from the first of its layers that has a value there */
function sampleBackground(background, key, x, y, t) {
  for (const layer of background.layers) {
    const v = sampleLayer(layer, key, x, y, t);
    if (v) return v;
  }
  return null;
}

/* the size a full arrow (u, a) or the strongest colour (s) stands for: from what is on screen now - at eleven times
   through the replay, so it holds through it, and no one moment (a wave switching on) sets it - the 90th percentile
   of the sizes (98th for a colour map); the file's own reference if nothing is on screen */
function backgroundReference(background, key) {
  const {l, t: top, r, b} = plotRect(), range = replayRange() || [0, 0];
  const id = [key, state.view.join(), r - l, b - top, range.join()].join('|');
  if (!background.cache.has(id)) {
    const sizes = [], step = ARROW_SPACING / 2;
    for (const t of Array.from({length: 11}, (_, i) => range[0] + (range[1] - range[0]) * i / 10))
      for (let sy = top + step / 2; sy < b; sy += step)
        for (let sx = l + step / 2; sx < r; sx += step) {
          const [x, y] = toData(sx, sy), v = sampleBackground(background, key, x, y, t);
          if (v) { const size = Math.hypot(v[0], v[1]); if (size > 0) sizes.push(size); }
        }
    sizes.sort((x, y) => x - y);
    const p = key === 's' ? 0.98 : 0.9;
    background.cache.set(id, sizes.length ? sizes[Math.min(sizes.length - 1, Math.floor(p * sizes.length))]
                                          : background.reference[key] || null);
  }
  return background.cache.get(id);
}

/* a background's layers at the replay time (the start when stopped); returns key entries */
function drawBackground(background) {
  const keys = [], t = fieldTime() ?? 0;
  const moving = background.layers.some(l => (l.times && l.times.length > 1) || (l.frame && l.frame.times.length > 1));
  const moment = moving ? '  at t = ' + fmt(t) + ' s' : '';
  if (state.prefs.showScalar && backgroundHas(background, 's')) {
    const ref = backgroundReference(background, 's');
    if (ref) {
      drawScalar((x, y) => sampleBackground(background, 's', x, y, t), ref);
      const label = background.layers.find(l => l.type === 'field' && l.values.s).label;
      keys.push([SCALAR_PLUS, label + ': red +' + fmt(ref) + ', blue \u2212' + fmt(ref) + moment]);
    }
  }
  for (const [show, key, colour, label, offset] of [
      [state.prefs.showFlow, 'u', css('--muted'), 'u', 0],
      [state.prefs.showGravity, 'a', css('--g-arrow'), 'g, the acceleration of space', 0.5]]) {
    if (!show || !backgroundHas(background, key)) continue;
    const ref = backgroundReference(background, key);
    if (!ref) continue;
    drawArrows((x, y) => sampleBackground(background, key, x, y, t), colour, ref, offset);
    keys.push([colour, label + '  ' + (key === 'u' ? speed(ref) : fmt(ref) + ' m/s²') + moment]);
  }
  if (state.prefs.showTwist && backgroundHas(background, 't')) {
    const ref = backgroundReference(background, 't');
    if (ref) {
      drawTwist((x, y) => sampleBackground(background, 't', x, y, t), ref);
      const label = background.layers.find(l => l.type === 'field' && l.values.t).label;
      keys.push([TWIST, label + ': a full arc ' + fmt(ref) + ' rad/s' + moment]);
    }
  }
  if (state.prefs.showSeam)
    for (const layer of background.layers.filter(l => l.type === 'lines')) {
      const k = Math.floor(timeIndex(layer.times, t)), fr = layer.frame ? frameAt(layer.frame, t) : null;
      const c = fr ? Math.cos(fr.angle) : 1, s = fr ? Math.sin(fr.angle) : 0;
      ctx.strokeStyle = css('--ink'); ctx.lineWidth = 1.5; ctx.setLineDash([6, 4]);
      for (const flat of layer.lines[k]) {
        ctx.beginPath();
        for (let i = 0; i < flat.length; i += 2) {
          let x = flat[i], y = flat[i + 1];
          if (fr) [x, y] = [fr.x + fr.scale * (c * x - s * y), fr.y + fr.scale * (s * x + c * y)];
          const [sx, sy] = toScreen(x, y);
          if (i) ctx.lineTo(sx, sy); else ctx.moveTo(sx, sy);
        }
        ctx.stroke();
      }
      ctx.setLineDash([]);
      keys.push([css('--ink'), layer.label + moment, [6, 4]]);
    }
  if (keys.length) keys.push(['transparent', 'background: ' + background.name]);
  return keys;
}

/* a scalar field as a colour map: cells of SCALAR_CELL pixels, red where it is positive, blue negative, their strength
   its size over the run's scale (capped); nothing off the grid or where it is not a number */
const SCALAR_CELL = 5, SCALAR_PLUS = '#d6452a', SCALAR_MINUS = '#2a6fd6';
function drawScalar(sample, reference) {
  const {l, t: top, r, b} = plotRect();
  for (let sy = top; sy < b; sy += SCALAR_CELL)
    for (let sx = l; sx < r; sx += SCALAR_CELL) {
      const [x, y] = toData(sx + SCALAR_CELL / 2, sy + SCALAR_CELL / 2), v = sample(x, y);
      if (!v || !isFinite(v[0]) || v[0] === 0) continue;
      ctx.globalAlpha = Math.min(1, Math.abs(v[0]) / reference) * 0.85;
      ctx.fillStyle = v[0] > 0 ? SCALAR_PLUS : SCALAR_MINUS;
      ctx.fillRect(sx, sy, SCALAR_CELL, SCALAR_CELL);
    }
  ctx.globalAlpha = 1;
}

function speed(v) { return v >= 1e3 ? fmt(v / 1e3) + ' km/s' : fmt(v) + ' m/s'; }

/* arrows on a screen grid, each from its grid point, its length in proportion to the field (capped at a full one) */
/* twist arcs (a spinning hole's river): at each point of a grid a quarter of the way between the arrows', an arc turning the way space turns
   there (anticlockwise for a positive rate), its sweep the rate over reference (300 degrees at most); tiny ones left out */
const TWIST = '#0f766e';
function drawTwist(sample, reference) {
  const {l, t: top, r, b} = plotRect(), shift = ARROW_SPACING * 0.75, radius = ARROW_SPACING * 0.2;
  ctx.strokeStyle = TWIST; ctx.fillStyle = TWIST; ctx.lineWidth = 1;
  for (let sy = top + shift; sy < b; sy += ARROW_SPACING)
    for (let sx = l + shift; sx < r; sx += ARROW_SPACING) {
      const [x, y] = toData(sx, sy), v = sample(x, y);
      if (!v || !isFinite(v[0]) || v[0] === 0) continue;
      const sweep = 300 / 180 * Math.PI * Math.min(1, Math.abs(v[0]) / reference);
      if (sweep < Math.PI / 12) continue;
      twistArc(ctx, sx, sy, radius, sweep, v[0] > 0, 5);
    }
}

/* an arc round screen (sx, sy) from the top, anticlockwise on screen if anticlockwise, with an arrowhead at its end */
function twistArc(c, sx, sy, radius, sweep, anticlockwise, head) {
  const start = -Math.PI / 2, end = start + (anticlockwise ? -sweep : sweep);
  c.beginPath(); c.arc(sx, sy, radius, start, end, anticlockwise); c.stroke();
  const ex = sx + radius * Math.cos(end), ey = sy + radius * Math.sin(end);
  const dir = anticlockwise ? -1 : 1, tx = -Math.sin(end) * dir, ty = Math.cos(end) * dir;
  c.beginPath(); c.moveTo(ex + tx * head * 0.6, ey + ty * head * 0.6);
  c.lineTo(ex - tx * head * 0.6 + ty * head * 0.45, ey - ty * head * 0.6 - tx * head * 0.45);
  c.lineTo(ex - tx * head * 0.6 - ty * head * 0.45, ey - ty * head * 0.6 + tx * head * 0.45);
  c.closePath(); c.fill();
}

function drawArrows(sample, colour, reference, offset) {
  const {l, t: top, r, b} = plotRect(), longest = ARROW_SPACING * 0.8, shift = ARROW_SPACING * (0.5 + offset);
  ctx.strokeStyle = colour; ctx.fillStyle = colour; ctx.lineWidth = 1;
  for (let sy = top + shift; sy < b; sy += ARROW_SPACING)
    for (let sx = l + shift; sx < r; sx += ARROW_SPACING) {
      const [x, y] = toData(sx, sy), v = sample(x, y);
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
  const {l, t, r, b} = plotRect(), rowH = 18, swatch = 26;
  //the text shrinks (to 9px) to keep the box inside the plot
  let size = 12, widest;
  for (; ; size--) {
    ctx.font = size + 'px -apple-system, Helvetica, Arial, sans-serif';
    widest = Math.max(...lines.map(([, text]) => ctx.measureText(text).width));
    if (size <= 9 || widest + swatch + 22 <= r - l - 16) break;
  }
  const width = widest + swatch + 22;
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
  if (rp.state === 'playing' && rp.mode === mode) return;
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

const STOPPED_LABEL = 'stopped - ×1 plays the whole run in ' + REPLAY_SECONDS + ' s';

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
  //while playing, Pause and Restart stand in for Play and Play in turn; paused, Restart stays, to get back to the start
  const playing = rp.state === 'playing';
  $('play').style.display = playing ? 'none' : '';
  $('playInTurn').style.display = !playing && canPlayInTurn() ? '' : 'none';
  $('pause').style.display = playing ? '' : 'none';
  $('restart').style.display = rp.state === 'stopped' ? 'none' : '';
  if (rp.mode === 'sequence' && !canPlayInTurn()) { rp.mode = 'together'; if (rp.state !== 'stopped') stopReplay(); }
  if (rp.state === 'stopped' || !range) {
    $('seek').value = 0; $('replayLabel').textContent = STOPPED_LABEL;
  } else {
    $('seek').value = Math.round((rp.t - range[0]) / (range[1] - range[0] || 1) * 1000);
    $('replayLabel').textContent = replayLabel(rp.state, rp.t, range);
  }
  $('replayLabel').title = $('replayLabel').textContent;
  showPlayer();
  draw();
}

/* the player's icons */
const ICONS = {
  list: '<circle class="solid" cx="5" cy="6" r="1.6"/><circle class="solid" cx="5" cy="12" r="1.6"/><circle class="solid" cx="5" cy="18" r="1.6"/><path d="M10 6h10M10 12h10M10 18h10"/>',
  restart: '<path d="M5 5v14"/><path d="M19 6.5v11L10.5 12z"/>',
  play: '<path class="solid" d="M8.5 5.5c0-.8.9-1.3 1.6-.9l9 6.1c.6.4.6 1.3 0 1.7l-9 6.1c-.7.4-1.6-.1-1.6-.9z"/>',
  pause: '<rect class="solid" x="6.5" y="5" width="4" height="14" rx="1.2"/><rect class="solid" x="13.5" y="5" width="4" height="14" rx="1.2"/>',
  end: '<path d="M5 6.5v11L13.5 12z"/><path d="M19 5v14"/>',
  loop: '<path d="M20 12a8 8 0 1 1-2.4-5.7"/><path d="M20 4v5h-5"/>',
  full: '<path d="M4 9V4h5M15 4h5v5M20 15v5h-5M9 20H4v-5"/>',
  close: '<path d="M6 6l12 12M18 6L6 18"/>'};

let drawnButtons = '';
function showPlayer() {
  const rp = state.replay, playing = rp.state === 'playing';
  const sequence = rp.mode === 'sequence', loop = !!state.prefs.replayLoop;
  const svg = name => '<svg viewBox="0 0 24 24">' + ICONS[name] + '</svg>';
  const key = [playing, PLAYER].join();
  if (key !== drawnButtons) {
    drawnButtons = key;
    $('pMode').innerHTML = svg('list');
    $('pRestart').innerHTML = svg('restart');
    $('pPlay').innerHTML = svg(playing ? 'pause' : 'play');
    $('pEnd').innerHTML = svg('end');
    $('pLoop').innerHTML = svg('loop');
    $('pFull').innerHTML = svg(PLAYER ? 'full' : 'close');
  }
  const tips = {
    pMode: sequence ? 'Playing in turn, one result after another. Click to play them all together'
                    : 'Playing all the results together. Click to play them in turn, one after another',
    pRestart: 'Restart: stop, clear, and go back to the start',
    pPlay: playing ? 'Pause' : 'Play',
    pEnd: 'End: stop, and show the whole run',
    pLoop: loop ? 'Looping: starts again at the end. Click to play once' : 'Playing once. Click to loop, starting again at the end',
    pFull: PLAYER ? 'Full screen: open the full viewer, with every option' : 'Close the full viewer'};
  for (const [id, tip] of Object.entries(tips)) { $(id).dataset.tip = tip; $(id).setAttribute('aria-label', tip); }
  $('pMode').style.visibility = canPlayInTurn() ? '' : 'hidden';
  $('pMode').setAttribute('aria-pressed', String(sequence));
  $('pLoop').setAttribute('aria-pressed', String(loop));
  showTrack();
  showTime();
  if (tipFor) showTip(tipFor);
}

/* the progress track's markers: playing together, one, at the clock's place in the run; in turn, one for each result in
   its own colour, each crossing the whole track while its result plays (those before it at the end, those after at the
   start). stopped, the whole run is shown, so they are all at the end */
function showTrack() {
  const track = $('pTrack'), rp = state.replay, range = replayRange();
  const markers = [];
  if (range) {
    const at = rp.state === 'stopped' ? null : rp.t;
    if (rp.mode === 'sequence') {
      for (const g of segments()) {
        const f = at === null ? 1 : Math.max(0, Math.min(1, (at - g.start) / (g.hi - g.lo || 1)));
        const path = g.result.paths.find(p => p.color);
        markers.push([f, (path && path.color) || g.result.color, at !== null && f > 0 && f < 1]);   //the colour it is drawn in
      }
    } else {
      markers.push([at === null ? 1 : (at - range[0]) / (range[1] - range[0] || 1), css('--accent'), true]);
    }
  }
  const have = track.querySelectorAll('.marker');
  if (have.length !== markers.length) {
    have.forEach(m => m.remove());
    for (let i = 0; i < markers.length; i++) track.appendChild(Object.assign(document.createElement('div'), {className: 'marker'}));
  }
  track.querySelectorAll('.marker').forEach((m, i) => {
    const [f, colour, moving] = markers[i];
    m.style.left = 'calc(7px + ' + Math.max(0, Math.min(1, f)) + ' * (100% - 14px))';
    m.style.background = colour;
    m.style.zIndex = moving ? 2 : 1;
  });
}

/* the player's time: where the replay is, of the whole run (in turn, of the current result's run, with which result it
   is); stopped, the whole run is shown, so its end. its width is set from the widest it can be, so it doesn't jitter */
function showTime() {
  if (!PLAYER) return;
  const rp = state.replay, range = replayRange(), el = $('pTime');
  if (!range) { el.textContent = ''; return; }
  const text = (clock, mode) => {
    if (mode !== 'sequence') return fmt(clock) + ' / ' + fmt(range[1]) + ' s';
    const g = currentSegment(clock);
    return (g.index + 1) + '/' + g.count + '  ' + fmt(g.t) + ' / ' + fmt(g.hi) + ' s';
  };
  const key = rp.mode + ':' + range.join();
  if (el.dataset.fitted !== key) {
    el.dataset.fitted = key;
    el.style.width = '';
    let widest = 0;
    for (let i = 0; i <= 200; i++) {
      el.textContent = text(range[0] + i / 200 * (range[1] - range[0]), rp.mode);
      widest = Math.max(widest, el.scrollWidth);
    }
    el.style.width = widest + 2 + 'px';
  }
  el.textContent = text(rp.state === 'stopped' ? range[1] : rp.t, rp.mode);
}

function trackSeek(e) {
  const r = $('pTrack').getBoundingClientRect();
  seek(Math.max(0, Math.min(1, (e.clientX - r.left - 7) / (r.width - 14))));
}

/* hover text for the player's controls, straight away, above the control and kept inside the window */
let tipFor = null;
function showTip(el) {
  tipFor = el;
  const tip = $('tip');
  tip.textContent = el.dataset.tip;
  tip.style.display = 'block';
  const r = el.getBoundingClientRect(), w = tip.offsetWidth, h = tip.offsetHeight;
  tip.style.left = Math.max(4, Math.min(innerWidth - w - 4, r.left + r.width / 2 - w / 2)) + 'px';
  tip.style.top = (r.top - h - 6 < 4 ? r.bottom + 6 : r.top - h - 6) + 'px';
}
function hideTip() { tipFor = null; $('tip').style.display = 'none'; }

//---------------------------------------------------------------- controls

function message(text) { $('message').textContent = text; }

function syncControls() {
  for (const id of ['showFlow', 'showGravity', 'showScalar', 'showTwist', 'showSeam', 'showBodies', 'showSchwarzschild', 'showSpin', 'equalAspect', 'showGrid', 'showPathLegend', 'graduateOrbits', 'showFieldKey'])
    $(id).checked = !!state.prefs[id];
  $('unit').value = state.prefs.unit;
  $('loop').checked = !!state.prefs.replayLoop;
  $('speed').value = SPEEDS.includes(String(state.prefs.replaySpeed)) ? String(state.prefs.replaySpeed) : '1';
  $('pSpeed').value = $('speed').value;
  const background = $('background');
  background.innerHTML = '';
  const names = state.backgrounds ? state.backgrounds.map(b => b.name)
                                  : [SELECTED, ALL, ...state.environments.filter(e => e.bodies.length || e.frames).map(e => e.name)];
  for (const name of names) background.add(new Option(name, name));
  background.value = state.background;
  showDescription();
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

/* the chosen background's description, under the Background menu */
function showDescription() {
  const background = currentBackground();
  $('bgDescription').textContent = background ? background.description : '';
  $('bgDescription').style.display = background && background.description ? '' : 'none';
}

function setup() {
  UNITS.forEach(([name], i) => $('unit').add(new Option(name, i)));
  SPEEDS.forEach(s => { $('speed').add(new Option(speedName(s), s)); $('pSpeed').add(new Option(speedName(s), s)); });
  setupPlayer();
  for (const id of ['showFlow', 'showGravity', 'showScalar', 'showTwist', 'showSeam', 'showBodies', 'showSchwarzschild', 'showSpin', 'showGrid', 'showPathLegend', 'graduateOrbits', 'showFieldKey'])
    $(id).onchange = () => { state.prefs[id] = $(id).checked; draw(); };
  $('equalAspect').onchange = () => { state.prefs.equalAspect = $('equalAspect').checked; equalise(); draw(); };
  $('unit').onchange = () => { state.prefs.unit = +$('unit').value; draw(); };
  $('speed').onchange = () => { state.prefs.replaySpeed = $('speed').value; };
  $('background').onchange = () => { state.background = $('background').value; showDescription(); draw(); };
  $('fit').onclick = fit;
  $('play').onclick = () => play('together');
  $('playInTurn').onclick = () => play('sequence');
  $('loop').onchange = () => { state.prefs.replayLoop = $('loop').checked; };
  $('pause').onclick = () => { if (state.replay.state === 'playing') state.replay.state = 'paused'; showReplay(); };
  $('restart').onclick = () => { stopReplay(); showReplay(); };
  $('seek').oninput = () => seek($('seek').value / 1000);
  $('openFolder').onclick = () => $('folderInput').click();
  $('folderInput').onchange = () => openFiles([...$('folderInput').files]);

  //pan by dragging, zoom with the wheel at the pointer, fit with a double click (not in the player, which stays fitted)
  let dragging = null;
  if (!PLAYER) {
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
  }

  //drop a run folder (or its files) on the plot
  const wrap = $('plotWrap');
  wrap.ondragover = e => { e.preventDefault(); $('drop').style.display = 'flex'; };
  wrap.ondragleave = () => { $('drop').style.display = 'none'; };
  wrap.ondrop = async e => {
    e.preventDefault(); $('drop').style.display = 'none';
    openFiles(await droppedFiles(e.dataTransfer));
  };
  window.onresize = () => { if (PLAYER) fit(); else { equalise(); draw(); } };
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', draw);

  const run = new URLSearchParams(location.search).get('run');
  if (run) {
    const url = new URL(run, location.href);
    loadRun(urlSource(url), url.pathname.split('/').pop());
  } else {
    syncControls(); draw();
  }
}

/* the player: icons for the replay, like a music player's, and a button to open the run in the full viewer */
function setupPlayer() {
  if (PLAYER) document.body.classList.add('player');
  for (const el of document.querySelectorAll('#player [data-tip], #player button')) {
    el.addEventListener('pointerenter', () => showTip(el));
    el.addEventListener('pointerleave', hideTip);
  }
  showPlayer();
  const rp = state.replay;
  $('pPlay').onclick = () => {
    if (rp.state === 'playing') { rp.state = 'paused'; showReplay(); }
    else play(rp.mode);
  };
  $('pMode').onclick = () => {
    const mode = rp.mode === 'sequence' ? 'together' : 'sequence', playing = rp.state === 'playing';
    rp.mode = mode; stopReplay();
    if (playing) play(mode); else showReplay();
  };
  $('pRestart').onclick = () => {
    //stopped shows the whole run, so back to the start is paused at the start, with nothing drawn yet
    const range = replayRange();
    if (!range) return;
    rp.state = 'paused'; rp.t = range[0]; showReplay();
  };
  $('pEnd').onclick = () => { stopReplay(); showReplay(); };
  $('pLoop').onclick = () => { state.prefs.replayLoop = !state.prefs.replayLoop; $('loop').checked = state.prefs.replayLoop; showReplay(); };
  $('pSpeed').onchange = () => { state.prefs.replaySpeed = $('pSpeed').value; $('speed').value = $('pSpeed').value; };
  const track = $('pTrack');
  track.onpointerdown = e => { track.setPointerCapture(e.pointerId); trackSeek(e); };
  track.onpointermove = e => { if (track.hasPointerCapture(e.pointerId)) trackSeek(e); };
  $('pFull').onclick = () => {
    const url = new URL(location.href);
    if (PLAYER) { url.searchParams.delete('player'); window.open(url.toString(), '_blank'); return; }
    //opened from a player: close this tab; opened some other way (which a page may not close), go to the player
    if (window.opener) { window.close(); return; }
    url.searchParams.set('player', '');
    location.href = url.toString();
  };
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
