/*
the browser viewer: a cut-down version of viewer/ (the desktop viewer) that runs in a browser with no server. it reads
a run's files as docs/appendix-a/formats.md describes them - full.json, its prefs and config, the result csvs and their logs, and
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
//the display options, by the desktop viewer's names (a run's prefs.json sets them); the ones the desktop viewer has on
//by default (markers, time markers) start off here, so a page's player shows only what its run's prefs ask for
const PREFS = {unit: 0, equalAspect: true, showGrid: true, showFlow: true, showGravity: false, showScalar: true, showTwist: true, showSeam: true,
               showBodies: true, showSchwarzschild: true, showSpin: false, showPathLegend: true, graduateOrbits: false, showFieldKey: true, replaySpeed: '1', replayLoop: false,
               mode: 'xy', logX: false, logY: false, ctTime: false, reverseX: true, showMarkers: false, showTimeMarks: false, timeColumn: 't',
               showContours: false, showFlowLines: false, showCones: false, showSpecialOrbits: false, showMarkNote: true, showMarkLabels: true,
               showBodyLabels: false, showPeri: false, showApo: false, apsisEvery: 1, showInfallArrows: false, showInfallRings: false};
//the columns each time option matches, by name, any case (the desktop's TIME_COLUMNS)
const TIME_OPTIONS = {t: ['t', 'time', 'coord_time'], pt: ['pt', 'tau', 'proper_time', 'proper_t']};
const TIME_LABELS = {t: 'global time (t)', pt: 'proper time (pt)'};
const MAX_TIME_MARKS = 5000;
const ZOOM_STEP = 1.5, PAN_STEP = 0.2;
const END_COLORS = ['#c2410c', '#0f766e', '#7c3aed', '#a16207'], END_LENGTH = 30;   //velocity arrows at path ends
const CONE = '#8a7fd0', FLOW_LINE = '#c4a46e', ISCO_COLOUR = '#a16207';            //light cones, flow lines, ISCOs
const WITH_DASH = [8, 4], AGAINST_DASH = [3, 3];   //circular orbits going round with a hole's spin, and against it
const FLOW_LINES = 20, CONTOUR_SPACING = 10, CONE_SIZE = 12;
//a path with more rows than THIN_ROWS leaves out rows closer than PATH_THIN pixels on screen to the last one drawn
let PATH_THIN = 0.35, THIN_ROWS = 20000;

/* each background layer's look, adjustable in the Background tab: its colour (a page colour by name, '--muted', or a
   hex), and density, size and line width as factors of the usual (density: arrows, arcs and cones closer together,
   more flow lines, more levels of |u|, finer colour-map cells). kept in this browser, not in the run's files */
const LAYERS = {
  u: {box: 'showFlow', name: 'u arrows', defaults: {colour: '--muted', density: 1, size: 1, width: 1}},
  g: {box: 'showGravity', name: 'g arrows', defaults: {colour: '--g-arrow', density: 1, size: 1, width: 1}},
  scalar: {box: 'showScalar', name: 'colour map', defaults: {plus: '#d6452a', minus: '#2a6fd6', density: 1, strength: 1}},
  twist: {box: 'showTwist', name: 'twist arcs', defaults: {colour: '#0f766e', density: 1, size: 1, width: 1}},
  seam: {box: 'showSeam', name: 'lines', defaults: {colour: '--ink', width: 1.5}},
  contours: {box: 'showContours', name: 'lines of equal |u|', defaults: {colour: '--axis', density: 1, width: 1.5}},
  flowLines: {box: 'showFlowLines', name: 'flow lines', defaults: {colour: '#c4a46e', density: 1, width: 1}},
  cones: {box: 'showCones', name: 'light cones', defaults: {colour: '#8a7fd0', density: 1, size: 1, width: 1}},
  infallArrows: {box: 'showInfallArrows', name: 'falling space (arrows)', defaults: {colour: '#2a78d6', density: 1, size: 1, width: 1.2, speed: 1}},
  infallRings: {box: 'showInfallRings', name: 'falling space (rings)', defaults: {colour: '#2a78d6', density: 1, width: 1.2, speed: 1}},
};
const layerColour = c => c && c.startsWith('--') ? css(c) : c;
/* a layer's settings: its defaults, with what has been changed */
const layerLook = name => layer(name);
function layer(name) {
  const out = {...LAYERS[name].defaults, ...(state.layers[name] || {})};
  for (const k of ['colour', 'plus', 'minus']) if (out[k]) out[k] = layerColour(out[k]);
  return out;
}

/* the replay is one clock for every view, so Play plays them all at once */
const replay = {state: 'stopped', t: null, last: 0, mode: 'together'};   //mode 'together' or 'sequence' (in turn)
const sharedLayers = {};   //each background layer's changed settings (LAYERS), by layer: the same in every view

/* a view's state: its results, settings and what it has worked out. the viewer can show two views side by side, each
   with its own; the panel shows the selected one's */
function makeState() {
  return {
    results: [],         //{name, file, data, paths, log, env, visible, color}
    environments: [],    //{key, name, bodies, frames}
    selected: null,
    view: null,          //[x0, x1, y0, y1] in metres
    prefs: {...PREFS},
    background: SELECTED,
    replay,
    trailStart: null,    //replay: paths drawn from this time, or from the start (null); nothing sets it at present (Clear trails was taken out)
    timeInterval: '',    //time markers: every this much of the marker column ('' = a round interval, about 10)
    sources: [],         //what is open: [{source, fullName}], for Reload
    layers: sharedLayers,
    marks: {note: '', column: null, interval: null, key: null},   //the time markers worked out (prepareTimeMarks)
    flowLineCache: {key: null, lines: []},
    boxes: {legend: {mode: 'max', out: false, from: null}, key: {mode: 'max', out: false, from: null}},
    boxButtons: [],      //this frame's legend-box buttons: {x, y, w, h, box, tip}
    boxRows: [],         //this frame's legend-box rows: {x, y, w, h, tip, path}
    frontPath: null,     //a path whose legend row is under the pointer: drawn last, on top
    boxZoom: null,       //a box being dragged out (shift-drag): [x0, y0, x1, y1] on screen
    spinning: [],        //spinning bodies drawn this frame, turned on the overlay
    follow: null,        //what the view keeps centred: {kind: 'body', index} or {kind: 'path', file, path}, or null
    measure: {on: false, points: []},   //the measuring tool: up to two points, each {x, y} plotted, or a row
    fitSpan: null,       //the fitted view's width, for the zoom slider
  };
}

const $ = id => document.getElementById(id);
/* the views: each a pane with its plot canvas, an overlay canvas for what moves on its own (spinning bodies, falling
   space) and its state. the globals below are the pane being drawn or handled: the selected one, except inside
   withPane */
const panes = [];
let active = null, state = null, canvas = null, ctx = null, overlay = null, overlayCtx = null, emptyNote = null;
function usePane(p) {
  state = p.state; canvas = p.canvas; ctx = p.ctx; overlay = p.overlay; overlayCtx = p.overlayCtx; emptyNote = p.empty;
}
function withPane(p, fn) {
  const was = currentPane();
  usePane(p);
  try { return fn(); } finally { if (was) usePane(was); }
}
const currentPane = () => panes.find(p => p.state === state) || null;
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
  return {url: String(base), names: () => [], read: async name => {
    const response = await fetch(new URL(name, base));
    if (!response.ok) throw new Error('could not fetch ' + name + ' (' + response.status + ')');
    return response.text();
  }};
}

/* a csv as columns of numbers (NaN where empty or not a number), split into rows; a row of empty cells ends a path.
   text(name) gives a column's cells as written, for a column of names (one path per value) */
function parseCsv(text) {
  const lines = text.split(/\r?\n/).filter(l => l.trim() && !l.trimStart().startsWith('#'));
  const names = lines[0].split(',').map(s => s.trim());
  const columns = Object.fromEntries(names.map(n => [n, new Float64Array(lines.length - 1)]));
  const rows = [];
  for (let i = 1; i < lines.length; i++) {
    const cells = lines[i].split(',');
    rows.push(cells);
    names.forEach((n, j) => { const c = (cells[j] || '').trim(); columns[n][i - 1] = c === '' ? NaN : +c; });
  }
  const texts = new Map();
  const textOf = n => {
    if (!texts.has(n)) { const j = names.indexOf(n); texts.set(n, rows.map(cells => (cells[j] || '').trim())); }
    return texts.get(n);
  };
  return {names, columns, rows: lines.length - 1, text: textOf};
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

/* the log lines a viewer reads (docs/appendix-a/formats.md) */
function parseLog(text) {
  const bodies = [];
  for (const m of text.matchAll(/^body \d+: mass (\S+) kg .*?x (\S+) m\s+y (\S+) m\s+(black|white)(?:\s+spin (\S+))?/gm))
    bodies.push({mass: +m[1], x: +m[2], y: +m[3], black: m[4] === 'black', spin: m[5] ? +m[5] : 0});
  const frames = (text.match(/^background frames: (.+)$/m) || [])[1];
  const direction = (text.match(/^flow direction: (.+)$/m) || [])[1];
  const wave = (text.match(/^gravitational wave: (.+)$/m) || [])[1];
  const scalar = (text.match(/^background scalar: (.+)$/m) || [])[1];
  const backgrounds = (text.match(/^backgrounds: (.+)$/m) || [])[1];
  //where each orbit ended (engine/run.py's OrbitCounter): 'orbit N: t ... s  periapsis ... m at (x, y)  apoapsis ...',
  //or in older logs 'orbit <days> days' with no apsides
  const clean = text.replace(/np\.float64\(([^()]*)\)/g, '$1');
  let orbitEnds = [...clean.matchAll(/^orbit \d+: t (\S+) s\s+periapsis \S+ m at \((\S+), (\S+)\)\s+apoapsis \S+ m at \((\S+), (\S+)\)/gm)]
    .map(m => ({t: +m[1], peri: [+m[2], +m[3]], apo: [+m[4], +m[5]]}));
  if (!orbitEnds.length) orbitEnds = [...clean.matchAll(/^orbit\s+(\S+) days/gm)].map(m => ({t: +m[1] * 86400, peri: null, apo: null}));
  return {bodies, frames: frames ? files(frames) : null, direction, wave, scalar: scalar && scalar.trim(),
          backgrounds: backgrounds && backgrounds.trim(), orbitEnds, text};
}

/* a log's list of frames files, comma-separated (a colour map's, a flow's) */
function files(text) {
  return text.split(',').map(f => f.trim()).filter(Boolean);
}

/* background frames (docs/appendix-a/formats.md): on a grid at a run of times, t, x, y and any of the flow (u_x, u_y),
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

/* a run: its full.json (if any), prefs, config, results, logs and frames. add: as well as what is open, not instead.
   keep: for a reload, what each result (by file) had set - shown, styles, options, hidden orbits - kept over the
   run's own config */
async function loadRun(source, fullName, {add = false, keep = null} = {}) {
  //the view it loads into, which may not stay the selected one while it waits for files: each wait hands the globals
  //back to the selected view, and takes them again after
  const pane = currentPane(), wait = async promise => { usePane(active); try { return await promise; } finally { usePane(pane); } };
  const progress = text => { message(text); pane.loadingNote.textContent = text; };
  pane.loading = true; pane.loadingNote.hidden = false;
  progress('loading…');
  if (!add) {
    state.results = []; state.environments = []; state.selected = null; state.backgrounds = null; state.sources = [];
    state.trailStart = null; state.timeInterval = '';
  }
  stopReplay();
  try {
    fullName = fullName || source.names().find(n => n.endsWith('.full.json'));
    state.sources.push({source, fullName});
    let entries, chosen = null;
    if (fullName) {
      const full = JSON.parse(await wait(source.read(fullName)));
      if (full.preferences && !keep) Object.assign(state.prefs, pickPrefs(JSON.parse(await wait(source.read(full.preferences))).preferences || {}));
      const config = full.config ? JSON.parse(await wait(source.read(full.config))) : {results: []};
      entries = config.results || [];
      if (!add) {
        state.background = config.background === ALL ? ALL : SELECTED;
        chosen = config.background;
        if (config.timeInterval && !keep) state.timeInterval = String(config.timeInterval);
        const view = config.view || {};
        if (!keep) Object.assign(state.prefs, pickPrefs({mode: view.mode, logX: view.logX, logY: view.logY, unit: view.unit}));
      }
    } else {
      entries = source.names().filter(n => n.endsWith('.csv') && !n.startsWith('background_')).sort().map(n => ({relative: n}));
    }
    //every csv and log at once (one after another, each waits for the server), then every frames file they name
    let done = 0;
    const files = entries.map(entry => entry.relative || entry.path.split('/').pop());
    const read = name => source.read(name).finally(() => progress('loading… ' + (++done) + ' of ' + (files.length * 2) + ' files'));
    const texts = await wait(Promise.all(files.map(file => Promise.all([
      read(file), read(file.replace(/\.csv$/, '.log')).catch(() => null)]))));   //no log: no bodies
    const logs = texts.map(([, log]) => log === null ? {bodies: []} : parseLog(log));
    const named = logs.flatMap(l => l.frames || []);
    const frameCache = new Map(await wait(Promise.all([...new Set(named)].map(async name => {
      try { return [name, parseFrames(await read(name))]; }
      catch (e) { message('no frames file ' + name); return [name, null]; }
    }))));
    //a backgrounds file (engine/backgrounds.py): its backgrounds make the Background menu, in place of environments'
    const manifests = [...new Set(logs.map(l => l.backgrounds).filter(Boolean))];
    for (const name of manifests) {
      try { state.backgrounds = (state.backgrounds || []).concat(parseBackgrounds(await wait(read(name)))); }
      catch (e) { message('could not read the backgrounds file ' + name + ': ' + e.message); }
    }
    if (state.backgrounds && state.backgrounds.length) {
      if (!add || !currentBackground()) state.background = (state.backgrounds.find(b => b.name === chosen) || state.backgrounds[0]).name;
    } else state.backgrounds = null;
    const first = state.results.length;
    entries.forEach((entry, i) => {
      const file = files[i], log = logs[i], kept = keep && keep.get(file);
      const settings = kept ? {...entry, ...kept} : entry;
      const result = {name: studyName(file), file, data: parseCsv(texts[i][0]), log, visible: settings.visible !== false,
                      color: SERIES[(first + i) % SERIES.length], source, ends: !!settings.ends,
                      tangent: {on: !!(settings.tangent ? settings.tangent.on : settings.straight), t: settings.tangent ? settings.tangent.t : null,
                                color: settings.tangent ? settings.tangent.color : null, style: settings.tangent ? settings.tangent.style : 'dashed'}};
      //the desktop's apsides are each result's; here they are the markers', on for all if a config asks for them
      if (!keep && settings.periapsis) state.prefs.showPeri = true;
      if (!keep && settings.apoapsis) state.prefs.showApo = true;
      result.paths = buildPaths(result, settings);
      result.env = environmentFor(log, frameCache);
      result.orbits = buildOrbits(result, settings.hiddenOrbits || []);
      result.orbitEvery = settings.orbitEvery || 1;
      state.results.push(result);
    });
    if (!state.selected) state.selected = state.results[0] || null;
    message(fullName ? fullName : state.results.length + ' results');
  } catch (e) {
    message('could not open the run: ' + e.message);
  }
  pane.loading = false; pane.loadingNote.hidden = true;
  invalidatePlot();
  if (pane === active) syncControls();
  fit();
  usePane(active);
}

/* the settings a result has now, as a config entry has them (for Reload, and Choose paths) */
function resultSettings(r) {
  return {visible: r.visible, straight: r.tangent.on, tangent: {...r.tangent}, ends: r.ends, orbitEvery: r.orbitEvery || 1,
          styles: Object.fromEntries(r.paths.map(p => [p.name, [p.color || r.color, p.style, p.color2 || null, p.mode]])),
          selection: r.selection, group: r.group,
          hiddenOrbits: (r.orbits || []).filter(o => !o.visible).map(o => o.name.split('  ')[0])};
}

/* read everything open again from where it came from, keeping each result's settings */
async function reload() {
  const pane = currentPane(), sources = state.sources.slice(), keep = new Map(state.results.map(r => [r.file, resultSettings(r)]));
  const selected = state.selected && state.selected.file, view = state.view && state.view.slice();
  const differences = derivedList(state);
  if (!sources.length) return;
  for (const [i, {source, fullName}] of sources.entries()) { usePane(pane); await loadRun(source, fullName, {add: i > 0, keep}); }
  withPane(pane, () => {
    remakeDerived(differences);
    state.selected = state.results.find(r => r.file === selected) || state.results[0] || null;
    if (view) { state.view = view; draw(); }
  });
  if (pane === active) syncControls();
}

/* the selected result taken out (the desktop's Close) */
function closeSelected() {
  const r = state.selected;
  if (!r) return;
  state.results = state.results.filter(x => x !== r);
  state.environments = state.environments.filter(e => state.results.some(x => x.env === e));
  state.selected = state.results[0] || null;
  syncControls(); draw();
}

function pickPrefs(prefs) {
  const out = {};
  for (const key of Object.keys(PREFS)) if (key in prefs && prefs[key] !== undefined) out[key] = prefs[key];
  if (typeof prefs.unit === 'number') out.unit = Math.max(0, Math.min(UNITS.length - 1, prefs.unit - 1));   //the desktop's list starts with raw values
  if (typeof prefs.timeColumn === 'string') out.timeColumn = /proper|pt/i.test(prefs.timeColumn) ? 'pt' : 't';   //'Global time (t)'
  if (typeof prefs.replaySpeed === 'string') out.replaySpeed = prefs.replaySpeed.replace('×', '').replace('0.25', '0.2');
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
  result.selection = selection;
  //one path per value of a column (the desktop's group): each path the rows with that value, the rest left empty
  result.group = entry.group && names.includes(entry.group) ? entry.group : null;
  const values = result.group ? [...new Set(result.data.text(result.group))] : [null];
  const out = [];
  for (const [xc, yc] of selection) {
    const pairName = (pairs(names).find(p => p[1] === xc && p[2] === yc) || [xc + ' / ' + yc])[0];
    for (const g of values) {
      const label = g === null ? pairName : selection.length > 1 ? g + ' ' + pairName : String(g);
      const style = (entry.styles || {})[label] || [];
      let x = columns[xc], y = columns[yc];
      if (g !== null) {
        const keepRow = result.data.text(result.group).map(v => v === g);
        x = x.map((v, i) => keepRow[i] ? v : NaN); y = y.map((v, i) => keepRow[i] ? v : NaN);
      }
      const color2 = style[2] && style[2] !== style[0] ? style[2] : null;
      //how the colour goes through the orbits: one colour, a transition from the first to the last, or earlier ones shaded
      const mode = ['single', 'transition', 'shade'].includes(style[3]) ? style[3] : color2 ? 'transition' : state.prefs.graduateOrbits ? 'shade' : 'single';
      out.push({name: label, xName: xc, yName: yc, x, y, t: time, color: style[0] || null, style: style[1] || 'solid', color2, mode});
    }
  }
  return out;
}

/* a result's column for a time option ('t' or 'pt'), matched by name in any case; null if it has none */
function timeColumnOf(result, option) {
  const names = result.data.names, lower = new Map(names.map(n => [n.toLowerCase(), n]));
  for (const c of TIME_OPTIONS[option]) if (lower.has(c)) return lower.get(c);
  return null;
}

/* a pair is a position unless its label looks like a velocity, acceleration or force (the desktop's isPositionLabel) */
const isPositionLabel = label => !/^(v|u|w|a|vel|velocity|acc|accel|f|force)\d*$/i.test(label);

/* the pairs drawn as arrows at the path ends (v, u, a ...): [label, x, y], four at most */
function endPairs(result) {
  return pairs(result.data.names).filter(p => !isPositionLabel(p[0])).slice(0, END_COLORS.length);
}

/* the result's velocity columns (v_x / v_y, vel_x ...), or null */
function velocityPair(result) {
  return pairs(result.data.names).find(p => /^(v|vel|velocity)\d*$/i.test(p[0])) || null;
}

/* a run split into its orbits, at the times its log says each orbit ended (any run that went round at least once: two
   orbit lines, the part orbit at the start and a whole one); a fall or flyby has none. each orbit is its rows i0..i1
   (and the first row of the next, so the line joins up), its times, periapsis and apoapsis ({x, y, t}) and whether it
   is shown. the apsides are the log's, at the time of the nearest row, or (older logs) the closest and farthest rows */
function buildOrbits(result, hidden) {
  const ends = result.log.orbitEnds || [], tName = timeColumnOf(result, 't'), path = result.paths[0];
  if (ends.length < 2 || !tName || !path) return [];
  const t = result.data.columns[tName], x = path.x, y = path.y, n = t.length;
  const part = i => { let k = 0; while (k < ends.length && t[i] >= ends[k].t) k++; return k; };
  const orbits = [];
  let i = 0;
  while (i < n && !isFinite(t[i])) i++;
  for (let k = 0; k <= ends.length && i < n; k++) {
    let j = i;
    while (j + 1 < n && (!isFinite(t[j + 1]) || part(j + 1) === k)) j++;
    if (part(i) !== k) continue;
    const t0 = k > 0 ? ends[k - 1].t : t[i], t1 = k < ends.length ? ends[k].t : t[j];
    const name = k === 0 ? 'start (to the first crossing)' : k === ends.length ? 'end (part orbit)'
               : 'orbit ' + k + '  (' + fmt((t1 - t0) / 86400) + ' days)';
    const nearest = (qx, qy) => {
      let best = i, bd = Infinity;
      for (let r = i; r <= j; r++) { const d = Math.hypot(x[r] - qx, y[r] - qy); if (d < bd) { bd = d; best = r; } }
      return {x: qx, y: qy, t: t[best]};
    };
    let peri = null, apo = null;
    if (k < ends.length && ends[k].peri) { peri = nearest(...ends[k].peri); apo = nearest(...ends[k].apo); }
    else {
      let lo = Infinity, hi = -Infinity;
      for (let r = i; r <= j; r++) {
        const d = Math.hypot(x[r], y[r]);
        if (d < lo) { lo = d; peri = {x: x[r], y: y[r], t: t[r]}; }
        if (d > hi) { hi = d; apo = {x: x[r], y: y[r], t: t[r]}; }
      }
    }
    orbits.push({name, i0: i, i1: Math.min(j + 1, n - 1), t0, t1, peri, apo, full: name.startsWith('orbit'),
                 visible: !hidden.includes(name.split('  ')[0])});
    i = j + 1;
  }
  result.rowOrbit = new Int32Array(n).fill(-1);   //the orbit each row is in (its own, not the one it closes)
  orbits.forEach((o, k) => { for (let r = o.i0; r <= (k + 1 < orbits.length ? o.i1 - 1 : o.i1); r++) result.rowOrbit[r] = k; });
  return orbits;
}

/* a path's last colour, for a transition: its own, or one far round the palette from its first */
function secondColour(result, p) {
  if (p.color2) return p.color2;
  const i = SERIES.indexOf(p.color || result.color);
  return SERIES[((i < 0 ? 0 : i) + 4) % SERIES.length];
}

/* the orbit each row of a path is in, and how many there are: the log's orbits where it has them, else whole turns
   round the result's first body counted along the path; null for a path that doesn't go round */
function pathOrbits(result, p) {
  if (result.orbits && result.orbits.length) return {index: result.rowOrbit, last: result.orbits.length - 1, log: true};
  const counted = orbitsOf(result, p);
  return counted ? {index: counted, last: counted[counted.length - 1], log: false} : null;
}

/* an orbit's colour on path p, for a transition: the first shown whole orbit p's colour, the last its second colour,
   those between an even mix; the parts before the first crossing and after the last take the first and last colours */
function orbitColour(result, p, k) {
  const first = p.color || result.color, second = secondColour(result, p);
  if (result.orbits && result.orbits.length) {
    const o = result.orbits[k];
    if (!o) return first;
    if (!o.full) return k === 0 ? first : second;
    const shown = result.orbits.filter(q => q.visible && q.full), f = shown.length > 1 ? shown.indexOf(o) / (shown.length - 1) : 0;
    return mixColour(first, second, Math.max(0, f));
  }
  const orbits = pathOrbits(result, p);
  return orbits && orbits.last > 0 ? mixColour(first, second, Math.min(1, k / orbits.last)) : first;
}

function mixColour(a, b, f) {
  const parse = c => [1, 3, 5].map(i => parseInt(c.slice(i, i + 2), 16));
  const [x, y] = [parse(a), parse(b)];
  return '#' + x.map((v, i) => Math.round(v + (y[i] - v) * f).toString(16).padStart(2, '0')).join('');
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
    (+(b.mass / MS).toPrecision(4)) + ' MS ' + (b.black ? 'black' : 'white') + (b.spin ? ', spin ' + (+b.spin.toPrecision(3)) : '') +
    ' at (' + fmt(b.x / AU) + ', ' + fmt(b.y / AU) + ') AU').join(', ')
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
/* what is plotted: in x / y mode a path's own columns; in distance / time mode its distance from the origin against
   the time column (t or pt), as ct if chosen. either axis can be logarithmic. state.view is in plotted values: metres
   (or seconds, or the column's own values) on a linear axis, log10 of the value in the axis's unit on a log one */

const timeMode = () => state.prefs.mode === 'time';
let plotKey = 0;                    //bumped when what is plotted changes, so paths work their plotted values out again
function invalidatePlot() { plotKey++; }

/* each axis: its label, the scale that turns its values into the shown unit, whether it is logarithmic, and what it
   holds ('position', 'distance', 'time' or 'other') */
function axes() {
  const [unit, scale] = UNITS[state.prefs.unit], logX = !!state.prefs.logX, logY = !!state.prefs.logY;
  const tag = (a, log) => Object.assign(a, {log, label: a.label + (log ? '  [log]' : '')});
  if (timeMode()) {
    const option = state.prefs.timeColumn, shown = state.results.find(r => r.visible && timeColumnOf(r, option));
    const name = shown ? timeColumnOf(shown, option) : option;
    const time = state.prefs.ctTime ? {label: (name === 't' ? 'ct' : 'c·' + name) + ' (' + unit + ')', scale, kind: 'time'}
                                    : {label: name + ' (s)', scale: 1, kind: 'time'};
    return [tag({label: 'distance from origin (' + unit + ')', scale, kind: 'distance'}, logX), tag(time, logY)];
  }
  const path = state.results.filter(r => r.visible).flatMap(r => r.paths)[0];
  const one = name => {
    if (TIME_COLUMN.test(name || '')) return {label: name + ' (s)', scale: 1, kind: 'time'};
    if (/\(.+\)\s*$/.test(name || '')) return {label: name, scale: 1, kind: 'other'};     //a column that names its own unit
    return {label: ({pos_x: 'x', pos_y: 'y'}[name] || name || 'x') + ' (' + unit + ')', scale, kind: 'position'};
  };
  return [tag(one(path ? path.xName : 'pos_x'), logX), tag(one(path ? path.yName : 'pos_y'), logY)];
}

/* whether the plot is the plane itself (x / y, linear), where bodies and backgrounds are drawn as they are (against a
   time column, bodies are drawn as lines, drawBodies) */
function planeView() {
  if (timeMode() || state.prefs.logX || state.prefs.logY) return false;
  const [ax, ay] = axes();
  return ax.kind === 'position' && ay.kind === 'position';
}

/* a value on an axis as plotted: as it is, or log10 of it in the axis's unit (NaN for 0 and below) */
const toAxis = (v, a) => a.log ? (v > 0 ? Math.log10(v / a.scale) : NaN) : v;
const fromAxis = (v, a) => a.log ? Math.pow(10, v) * a.scale : v;

/* positions (x, y in metres) at times (the global t, for ct) as plotted, by the result's columns: [X, Y] arrays */
function plotValues(result, xs, ys, tAxis) {
  const [ax, ay] = axes(), n = xs.length, X = new Float64Array(n), Y = new Float64Array(n);
  const factor = state.prefs.ctTime ? C : 1;
  for (let i = 0; i < n; i++) {
    if (timeMode()) { X[i] = toAxis(Math.hypot(xs[i], ys[i]), ax); Y[i] = toAxis(tAxis ? tAxis[i] * factor : NaN, ay); }
    else { X[i] = toAxis(xs[i], ax); Y[i] = toAxis(ys[i], ay); }
  }
  return [X, Y];
}

/* a path's plotted values, worked out once for each thing plotted */
function plotted(result, p) {
  if (p.plotKey !== plotKey) {
    const tName = timeMode() ? timeColumnOf(result, state.prefs.timeColumn) : null;
    [p.px, p.py] = plotValues(result, p.x, p.y, tName ? result.data.columns[tName] : null);
    p.plotKey = plotKey;
  }
  return p;
}

/* one point (x, y in metres, at global time t) as plotted, for a result */
function plotPoint(result, x, y, t) {
  const tName = timeMode() ? timeColumnOf(result, state.prefs.timeColumn) : null;
  let tAxis = t;
  if (tName && tName !== timeColumnOf(result, 't')) tAxis = interpolate(result.data.columns[timeColumnOf(result, 't')], result.data.columns[tName], t);
  const [X, Y] = plotValues(result, [x], [y], [tAxis]);
  return [X[0], Y[0]];
}

/* y at x along the rising list xs (NaN outside it) */
function interpolate(xs, ys, x) {
  if (!xs || !ys) return NaN;
  let lo = -1, hi = -1;
  for (let i = 0; i < xs.length; i++) {
    if (!isFinite(xs[i]) || !isFinite(ys[i])) continue;
    if (xs[i] <= x) lo = i;
    if (xs[i] >= x) { hi = i; break; }
  }
  if (lo < 0 || hi < 0) return NaN;
  return hi === lo ? ys[lo] : ys[lo] + (ys[hi] - ys[lo]) * (x - xs[lo]) / (xs[hi] - xs[lo]);
}

function plotRect() {
  const w = canvas.clientWidth, h = canvas.clientHeight, top = PLAYER ? MARGIN.top : MARGIN.top + 18;   //the viewer's title line
  return {l: MARGIN.left, t: top, r: w - MARGIN.right, b: h - MARGIN.bottom};
}

/* distance runs right to left in distance / time mode with Reverse on, 0 on the right */
const flipX = () => timeMode() && state.prefs.reverseX;

function toScreen(x, y) {
  const {l, t, r, b} = plotRect(), [x0, x1, y0, y1] = state.view, f = (x - x0) / (x1 - x0);
  return [flipX() ? r - f * (r - l) : l + f * (r - l), b - (y - y0) / (y1 - y0) * (b - t)];
}

function toData(sx, sy) {
  const {l, t, r, b} = plotRect(), [x0, x1, y0, y1] = state.view, f = flipX() ? (r - sx) / (r - l) : (sx - l) / (r - l);
  return [x0 + f * (x1 - x0), y0 + (b - sy) / (b - t) * (y1 - y0)];
}

function fit() {
  state.keepView = false;
  let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
  for (const r of state.results.filter(r => r.visible))
    for (const p of r.paths) {
      plotted(r, p);
      for (let i = 0; i < p.px.length; i++)
        if (isFinite(p.px[i]) && isFinite(p.py[i]) && shownRow(r, i)) {
          x0 = Math.min(x0, p.px[i]); x1 = Math.max(x1, p.px[i]); y0 = Math.min(y0, p.py[i]); y1 = Math.max(y1, p.py[i]);
        }
    }
  if (!isFinite(x0)) { state.view = [-1, 1, -1, 1]; draw(); return; }
  //against time, the bodies' lines are in view too
  const path = state.results.filter(r => r.visible).flatMap(r => r.paths)[0];
  const timeX = path && TIME_COLUMN.test(path.xName || ''), timeY = path && TIME_COLUMN.test(path.yName || '');
  if (!timeMode() && !state.prefs.logX && !state.prefs.logY && state.prefs.showBodies && (timeX || timeY))
    for (const env of fieldEnvironments())
      for (const body of env.bodies) {
        const at = bodyCoordinate(timeY ? path.xName : path.yName, body);
        if (at === null) continue;
        if (timeY) { x0 = Math.min(x0, at); x1 = Math.max(x1, at); } else { y0 = Math.min(y0, at); y1 = Math.max(y1, at); }
      }
  //in x / y, a body just off the paths (light near a hole) is brought into view; one far away is left out
  else if (state.prefs.showBodies && planeView() && /^(pos_)?x$/.test(path.xName || '') && /^(pos_)?y$/.test(path.yName || '')) {
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
  state.fitSpan = state.view[1] - state.view[0];
  draw();
}

/* a unit as long across as up: equal aspect in x / y, time as ct in distance / time; not with a log axis */
const aspectActive = () => (timeMode() ? state.prefs.ctTime : state.prefs.equalAspect && planeView()) && !state.prefs.logX && !state.prefs.logY;

/* with the aspect on, widen whichever axis needs it so a metre is as long across as up */
function equalise() {
  if (!aspectActive() || !state.view) return;
  const {l, t, r, b} = plotRect();
  let [x0, x1, y0, y1] = state.view;
  const perX = (x1 - x0) / (r - l), perY = (y1 - y0) / (b - t);
  if (perX > perY) { const half = perX * (b - t) / 2, mid = (y0 + y1) / 2; y0 = mid - half; y1 = mid + half; }
  else { const half = perY * (r - l) / 2, mid = (x0 + x1) / 2; x0 = mid - half; x1 = mid + half; }
  state.view = [x0, x1, y0, y1];
}

/* zoom by a factor about the view's centre (or a plotted point), keeping the aspect */
function zoom(factor, at) {
  if (!state.view) return;
  const v = state.view, [x, y] = at || [(v[0] + v[1]) / 2, (v[2] + v[3]) / 2];
  state.view = [x + (v[0] - x) * factor, x + (v[1] - x) * factor, y + (v[2] - y) * factor, y + (v[3] - y) * factor];
  moved(); scheduleDraw();
}

/* pan by fractions of the view (a fraction across the screen: reversed distance moves the other way) */
function pan(fx, fy) {
  if (!state.view) return;
  const v = state.view, dx = (v[1] - v[0]) * fx * (flipX() ? -1 : 1), dy = (v[3] - v[2]) * fy;
  state.view = [v[0] + dx, v[1] + dx, v[2] + dy, v[3] + dy];
  stopFollowing(); moved(); scheduleDraw();
}

/* the View tab's Range: the zoom slider (log10 of the zoom against the fitted view) and each axis's typed range,
   kept up to date as the view moves (but not a box being typed in) */
const RANGE_INPUTS = ['rangeX0', 'rangeX1', 'rangeY0', 'rangeY1'];
function syncRange() {
  const v = state.view, [ax, ay] = axes();
  $('xAxisName').textContent = ax.label; $('yAxisName').textContent = ay.label;
  if (state.fitSpan) {
    const level = state.fitSpan / (v[1] - v[0]);
    if (document.activeElement !== $('zoomSlider')) $('zoomSlider').value = Math.log10(level);
    $('zoomValue').textContent = '×' + (level >= 100 ? Math.round(level) : level >= 10 ? level.toFixed(1) : level.toPrecision(2));
  }
  const show = (x, a) => a.log ? fmt(Math.pow(10, x)) : fmt(x / a.scale);
  const values = [show(v[0], ax), show(v[1], ax), show(v[2], ay), show(v[3], ay)];
  RANGE_INPUTS.forEach((id, i) => { if (document.activeElement !== $(id)) $(id).value = values[i]; });
}

function applyRange() {
  const [ax, ay] = axes(), read = (id, a) => { const v = +$(id).value; return a.log ? (v > 0 ? Math.log10(v) : NaN) : v * a.scale; };
  const v = RANGE_INPUTS.map((id, i) => read(id, i < 2 ? ax : ay));
  if (v.some(x => !isFinite(x)) || v[1] <= v[0] || v[3] <= v[2]) { message('each range needs two numbers, the second larger (above 0 on a log axis)'); return; }
  stopFollowing(); state.view = v; draw();
}

/* the joystick: dragging the stick moves the view continuously, faster the further it is pushed (up to
   JOYSTICK_SPEED views a second); the buttons round it each move it by NUDGE_STEP of the view, repeating while held */
const JOYSTICK_SPEED = 1.5, NUDGE_STEP = 0.02;
function setupJoystick() {
  const pad = $('stickPad'), knob = $('stickKnob');
  let push = null, last = 0, frame = 0;
  const move = now => {
    if (!push) { frame = 0; return; }
    const dt = Math.min((now - last) / 1000, 0.1), [px, py] = push, d = Math.hypot(px, py);
    last = now;
    //pushed d of the way out, the view moves at JOYSTICK_SPEED d² views a second
    if (d > 0.08) { const speed = JOYSTICK_SPEED * d; pan(px * speed * dt, py * speed * dt); }
    frame = requestAnimationFrame(move);
  };
  const aim = e => {
    const r = pad.getBoundingClientRect(), half = r.width / 2;
    let x = (e.clientX - r.left - half) / half, y = (e.clientY - r.top - half) / half;
    const d = Math.hypot(x, y); if (d > 1) { x /= d; y /= d; }
    push = [x, -y];
    knob.style.transform = `translate(${x * half * 0.7}px, ${y * half * 0.7}px)`;
  };
  pad.onpointerdown = e => {
    if (!state.view) return;
    try { pad.setPointerCapture(e.pointerId); } catch (err) {}
    pad.classList.add('held'); aim(e);
    if (!frame) { last = performance.now(); frame = requestAnimationFrame(move); }
  };
  pad.onpointermove = e => { if (push) aim(e); };
  pad.onpointerup = pad.onpointercancel = pad.onlostpointercapture = () => {
    push = null; pad.classList.remove('held'); knob.style.transform = '';
  };
  for (const button of document.querySelectorAll('#joystick .nudge')) {
    const [dx, dy] = button.dataset.dir.split(',').map(Number);
    let timer = null;
    const stop = () => { clearTimeout(timer); clearInterval(timer); timer = null; };
    button.onpointerdown = e => {
      if (!state.view) return;
      e.preventDefault(); stop();
      pan(dx * NUDGE_STEP, dy * NUDGE_STEP);
      timer = setTimeout(() => { timer = setInterval(() => pan(dx * NUDGE_STEP, dy * NUDGE_STEP), 60); }, 400);
    };
    button.onpointerup = button.onpointerleave = button.onpointercancel = stop;
    button.onkeydown = e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); pan(dx * NUDGE_STEP, dy * NUDGE_STEP); } };
  }
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

/* an axis's ticks as [plotted value, label]: on a linear axis round values in its unit; on a log one powers of ten,
   or 1, 2, 5 in each decade over a few decades, or round values within one */
function axisTicks(v0, v1, a, count) {
  if (!a.log) return ticks(v0 / a.scale, v1 / a.scale, count).values.map(v => [v * a.scale, fmt(v)]);
  count = Math.max(2, Math.floor(count));
  if (v1 - v0 >= count / 2) {
    const step = Math.max(1, Math.ceil((v1 - v0) / count)), out = [];
    for (let e = Math.ceil(v0 / step) * step; e <= Math.floor(v1); e += step) out.push([e, '1e' + e]);
    return out;
  }
  if (v1 - v0 >= 0.5) {
    let vals = [];
    for (const mults of [[1], [1, 2, 5], [1, 2, 3, 4, 5, 6, 7, 8, 9]]) {
      vals = [];
      for (let e = Math.floor(v0); e <= Math.ceil(v1); e++) for (const m of mults) { const v = m * 10 ** e; if (Math.log10(v) >= v0 && Math.log10(v) <= v1) vals.push(v); }
      if (vals.length >= 4 || mults.length === 9) break;
    }
    return vals.map(v => [Math.log10(v), fmt(v)]);
  }
  return ticks(10 ** v0, 10 ** v1, count).values.filter(v => v > 0).map(v => [Math.log10(v), fmt(v)]);
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
  emptyNote.style.display = state.results.length || currentPane().loading ? 'none' : 'flex';
  if (!state.view) return;
  if (state.follow) applyFollow();
  if (!PLAYER) syncRange();
  const {l, t, r, b} = plotRect();
  ctx.fillStyle = css('--surface'); ctx.fillRect(l, t, r - l, b - t);
  ctx.save();
  ctx.beginPath(); ctx.rect(l, t, r - l, b - t); ctx.clip();
  drawAxes(true);
  const keys = [];
  prepareTimeMarks();
  if (planeView() || timeMode()) keys.push(...drawOverlaysUnder());
  if (planeView()) {
    const background = currentBackground();
    if (background) keys.push(...drawBackground(background));
    else for (const env of fieldEnvironments()) keys.push(...drawField(env));
  }
  if (timeMode()) keys.push(...drawTimeBackground());
  const shown = state.results.filter(r => r.visible);
  for (const result of shown) {
    const until = drawUntil(result);
    if (until === false) continue;
    for (const p of result.paths) {
      if (result.tangent.on) drawTangent(result, p, until);
      if (!state.frontPath || state.frontPath.p !== p) drawPath(result, p, until);
    }
  }
  if (state.frontPath && state.frontPath.result.visible) {
    const until = drawUntil(state.frontPath.result);
    if (until !== false) drawPath(state.frontPath.result, state.frontPath.p, until, 2.8);
  }
  labelCells.clear();
  for (const result of shown) {
    const until = drawUntil(result);
    if (until === false) continue;
    for (const p of result.paths) {
      drawTimeMarks(result, p, until);
      if (result.ends && planeView() && state.replay.state === 'stopped') drawEndArrows(result, p);
      if (result.orbits.length && (state.prefs.showPeri || state.prefs.showApo)) drawApsides(result, p, until);
      if (state.prefs.showMarkers) drawEnds(result, p, until);
    }
  }
  flushDots();
  if (state.measure.points.length) drawMeasure();
  state.spinning.length = 0;
  if (!state.prefs.logX && !state.prefs.logY) for (const env of fieldEnvironments()) drawBodies(env);
  drawSpinning();
  if (state.boxZoom) {
    ctx.strokeStyle = css('--accent'); ctx.lineWidth = 1; ctx.setLineDash([4, 3]);
    ctx.strokeRect(Math.min(state.boxZoom[0], state.boxZoom[2]), Math.min(state.boxZoom[1], state.boxZoom[3]), Math.abs(state.boxZoom[2] - state.boxZoom[0]), Math.abs(state.boxZoom[3] - state.boxZoom[1]));
    ctx.setLineDash([]);
  }
  ctx.restore();
  ctx.strokeStyle = css('--axis'); ctx.lineWidth = 1; ctx.strokeRect(l, t, r - l, b - t);
  drawAxes(false);
  keys.push(...pathKeys());
  state.boxButtons = []; state.boxRows = [];
  if (state.prefs.showPathLegend) drawLegend();
  if (state.prefs.showFieldKey && keys.length) drawKey(keys);
}

/* every view drawn again (the replay's clock moved, the window changed) */
function drawAll() { for (const p of panes) withPane(p, draw); }

function drawAxes(grid) {
  const {l, t, r, b} = plotRect(), [x0, x1, y0, y1] = state.view, [ax, ay] = axes();
  const xt = axisTicks(x0, x1, ax, (r - l) / 100), yt = axisTicks(y0, y1, ay, (b - t) / 60);
  ctx.font = '11px -apple-system, Helvetica, Arial, sans-serif';
  if (grid) {
    if (!state.prefs.showGrid) return;
    ctx.strokeStyle = css('--grid'); ctx.lineWidth = 1;
    for (const [v] of xt) { const [sx] = toScreen(v, y0); line(sx, t, sx, b); }
    for (const [v] of yt) { const [, sy] = toScreen(x0, v); line(l, sy, r, sy); }
    return;
  }
  ctx.fillStyle = css('--ink2'); ctx.textAlign = 'center'; ctx.textBaseline = 'top';
  for (const [v, label] of xt) { const [sx] = toScreen(v, y0); if (sx >= l - 1 && sx <= r + 1) ctx.fillText(label, sx, b + 6); }
  ctx.textAlign = 'right'; ctx.textBaseline = 'middle';
  for (const [v, label] of yt) { const [, sy] = toScreen(x0, v); if (sy >= t - 1 && sy <= b + 1) ctx.fillText(label, l - 6, sy); }
  ctx.textAlign = 'center'; ctx.textBaseline = 'bottom';
  ctx.fillText(ax.label, (l + r) / 2, canvas.clientHeight - 6);
  ctx.save(); ctx.translate(16, (t + b) / 2); ctx.rotate(-Math.PI / 2); ctx.textBaseline = 'top';
  ctx.fillText(ay.label, 0, 0); ctx.restore();
  if (!PLAYER) {
    //the title: the file, or how many results are shown; and the time markers' note, if there is no key for it
    const shown = state.results.filter(x => x.visible);
    const title = state.results.length === 1 ? state.results[0].file + (state.results[0].paths.length === 1 ? '  \u2014  ' + state.results[0].paths[0].name : '')
                : shown.length + ' of ' + state.results.length + ' results shown';
    ctx.fillStyle = css('--ink'); ctx.font = 'bold 13px -apple-system, Helvetica, Arial, sans-serif';
    ctx.textAlign = 'left'; ctx.textBaseline = 'bottom';
    ctx.fillText(title, l, t - 6);
    if (state.marks.note) {
      ctx.fillStyle = css('--ink2'); ctx.font = '11px -apple-system, Helvetica, Arial, sans-serif'; ctx.textAlign = 'right';
      ctx.fillText(state.marks.note, r, t - 6);
    }
  }
}

function line(x0, y0, x1, y1) { ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x1, y1); ctx.stroke(); }

/* whether a result's row is shown: not in a hidden orbit */
function shownRow(result, i) {
  if (!result.orbits || !result.orbits.length) return true;
  const k = result.rowOrbit[i];
  return k < 0 || result.orbits[k].visible;
}

/* a row's colour: its orbit's (first to last orbit, for a path with two colours), else the path's */
function rowColour(result, p, i) {
  if (p.mode === 'transition') {
    const orbits = pathOrbits(result, p);
    if (orbits && orbits.index[i] >= 0) return orbitColour(result, p, orbits.index[i]);
  }
  return p.color || result.color;
}

/* a path: up to the replay time while replaying (with a dot where it is), from the trails' start (Clear trails), else
   all of it; broken at empty rows and hidden orbits. a path with two colours goes from the first to the last through
   its orbits. with graduated orbits on, a path that goes round its body is drawn orbit by orbit: the current one (at
   the replay time, or the last) in full colour, each earlier one fainter, so the orbits' build-up shows */
function drawPath(result, p, until = replayTime(), width = 1.6) {
  plotted(result, p);
  const from = until !== null && state.trailStart !== null && p.t ? state.trailStart : null;
  ctx.lineWidth = width; ctx.setLineDash(DASHES[p.style] || []);
  const found = p.mode === 'shade' ? pathOrbits(result, p) : null, orbit = found && found.index;
  let current = 0;
  if (orbit) {
    current = orbit[orbit.length - 1];
    if (until !== null && p.t) for (let i = 0; i < p.x.length; i++) { if (p.t[i] > until) break; current = orbit[i]; }
  }
  const shade = k => k <= 0 || k > 1e9 ? 1 : Math.max(0.12, 0.55 * Math.pow(0.8, k - 1));
  //a new stroke for each orbit (its shade), and each change of colour
  let pen = false, colour = null, stretch = null, open = false, last = -1, drawnAt = [NaN, NaN];
  const thin = p.px.length > THIN_ROWS ? PATH_THIN : 0;
  const begin = (c, k) => {
    if (open) ctx.stroke();
    ctx.beginPath(); ctx.strokeStyle = colour = c; stretch = k; ctx.globalAlpha = orbit ? shade(current - k) : 1; open = true;
  };
  for (let i = 0; i < p.px.length; i++) {
    if (!(isFinite(p.px[i]) && isFinite(p.py[i])) || !shownRow(result, i) || (from !== null && p.t[i] < from)) { pen = false; continue; }
    if (until !== null && p.t && p.t[i] > until) {
      //into the future: finish this stretch at the replay time, then skip to the next one
      if (pen && last === i - 1) {
        const f = (until - p.t[i - 1]) / (p.t[i] - p.t[i - 1]);
        const [sx, sy] = toScreen(p.px[i - 1] + f * (p.px[i] - p.px[i - 1]), p.py[i - 1] + f * (p.py[i] - p.py[i - 1]));
        ctx.lineTo(sx, sy); dot(sx, sy, colour);
      }
      pen = false;
      while (i + 1 < p.px.length && isFinite(p.px[i + 1])) i++;
      continue;
    }
    const [sx, sy] = toScreen(p.px[i], p.py[i]);
    const c = rowColour(result, p, i), k = orbit ? orbit[i] : 0;
    //in a long path, rows closer together on screen than a pixel's fraction are left out of the line (a long run zoomed
    //out), except where the colour or the orbit changes, and the last row of each stretch
    if (thin && pen && c === colour && k === stretch && Math.abs(sx - drawnAt[0]) < thin && Math.abs(sy - drawnAt[1]) < thin
        && i + 1 < p.px.length && isFinite(p.px[i + 1]) && isFinite(p.py[i + 1])) { last = i; continue; }
    if (pen && (c !== colour || k !== stretch)) { ctx.lineTo(sx, sy); begin(c, k); ctx.moveTo(sx, sy); }
    else if (pen) ctx.lineTo(sx, sy);
    else { if (!open || c !== colour || k !== stretch) begin(c, k); ctx.moveTo(sx, sy); }
    pen = true; last = i; drawnAt = [sx, sy];
  }
  if (open) ctx.stroke();
  ctx.setLineDash([]); ctx.globalAlpha = 1;
  //a result with a value for each orbit: a dot at each, as they are few
  if (result.dots) {
    ctx.fillStyle = p.color || result.color;
    for (let i = 0; i < p.px.length; i++) {
      if (!(isFinite(p.px[i]) && isFinite(p.py[i])) || (until !== null && p.t && p.t[i] > until)) continue;
      const [sx, sy] = toScreen(p.px[i], p.py[i]);
      ctx.beginPath(); ctx.arc(sx, sy, 3, 0, 2 * Math.PI); ctx.fill();
    }
  }
}

/* a result's time for its tangent: its t column, else the row number (each row a step); and that time's range */
function tangentTimes(result) {
  const name = timeColumnOf(result, 't');
  const t = name ? result.data.columns[name] : Float64Array.from({length: result.data.rows}, (_, i) => i);
  let lo = Infinity, hi = -Infinity;
  for (const v of t) if (isFinite(v)) { lo = Math.min(lo, v); hi = Math.max(hi, v); }
  return {t, lo, hi, rows: !name};
}

/* the tangent's time: the one chosen, held inside the run, or the start */
function tangentAt(result) {
  const {lo, hi} = tangentTimes(result), T = result.tangent.t;
  return T === null || !isFinite(T) ? lo : Math.min(hi, Math.max(lo, T));
}

/* the path's tangent at the chosen time T: the straight line through where it is then, along its velocity then (the
   velocity columns, else the step either side), drawn across the run's whole time - where it would have gone with no
   gravity from T, and come from before it. a dot marks the point. replaying, drawn once the replay has passed T */
function drawTangent(result, p, until) {
  const {t, lo, hi} = tangentTimes(result), T = tangentAt(result);
  if (until !== null && until < T) return;
  let i = -1;
  for (let k = 0; k + 1 < t.length; k++)
    if (isFinite(t[k]) && isFinite(t[k + 1]) && isFinite(p.x[k]) && isFinite(p.x[k + 1]) && t[k] <= T && T <= t[k + 1]) { i = k; break; }
  if (i < 0) return;
  const f = t[i + 1] === t[i] ? 0 : (T - t[i]) / (t[i + 1] - t[i]), lerp = c => c[i] + f * (c[i + 1] - c[i]);
  const x0 = lerp(p.x), y0 = lerp(p.y), v = velocityPair(result), dt = t[i + 1] - t[i];
  const vx = v && !tangentTimes(result).rows ? lerp(result.data.columns[v[1]]) : (p.x[i + 1] - p.x[i]) / dt;
  const vy = v && !tangentTimes(result).rows ? lerp(result.data.columns[v[2]]) : (p.y[i + 1] - p.y[i]) / dt;
  if (!isFinite(vx) || !isFinite(vy)) return;
  //the time axis's values along the line, in distance / time mode (another time column only inside the run)
  const axisName = timeMode() ? timeColumnOf(result, state.prefs.timeColumn) : null, tName = timeColumnOf(result, 't');
  const n = 240, xs = [], ys = [], at = [];
  for (let k = 0; k <= n; k++) {
    const s = lo + (hi - lo) * k / n;
    xs.push(x0 + vx * (s - T)); ys.push(y0 + vy * (s - T));
    at.push(!axisName ? NaN : axisName === tName ? s : interpolate(result.data.columns[tName], result.data.columns[axisName], s));
  }
  const [X, Y] = plotValues(result, xs, ys, at), colour = result.tangent.color || p.color || result.color;
  ctx.strokeStyle = colour; ctx.lineWidth = 1.5; ctx.setLineDash(DASHES[result.tangent.style] || DASHES.dashed);
  ctx.beginPath();
  let pen = false;
  for (let k = 0; k <= n; k++) {
    if (!isFinite(X[k]) || !isFinite(Y[k])) { pen = false; continue; }
    const [sx, sy] = toScreen(X[k], Y[k]);
    if (pen) ctx.lineTo(sx, sy); else ctx.moveTo(sx, sy);
    pen = true;
  }
  ctx.stroke(); ctx.setLineDash([]);
  const [px, py] = plotValues(result, [x0], [y0], [axisName === tName ? T : axisName ? interpolate(result.data.columns[tName], result.data.columns[axisName], T) : NaN]);
  if (isFinite(px[0]) && isFinite(py[0])) {
    const [sx, sy] = toScreen(px[0], py[0]);
    ctx.fillStyle = colour; ctx.beginPath(); ctx.arc(sx, sy, 3.5, 0, 2 * Math.PI); ctx.fill();
  }
}

/* the start (open) and end (filled) of each stretch of a path that is shown; replaying, the start only */
function drawEnds(result, p, until) {
  plotted(result, p);
  const {l, t, r, b} = plotRect(), from = until !== null && state.trailStart !== null && p.t ? state.trailStart : null;
  const inside = i => isFinite(p.px[i]) && isFinite(p.py[i]) && shownRow(result, i) && (from === null || p.t[i] >= from)
                      && (until === null || !p.t || p.t[i] <= until);
  let first = -1, lastI = -1;
  for (let i = 0; i < p.px.length; i++) if (inside(i)) { if (first < 0) first = i; lastI = i; }
  if (first < 0) return;
  for (const [i, filled] of [[first, false], ...(until === null ? [[lastI, true]] : [])]) {
    const [sx, sy] = toScreen(p.px[i], p.py[i]);
    if (sx < l - 6 || sx > r + 6 || sy < t - 6 || sy > b + 6) continue;
    const c = rowColour(result, p, i);
    ctx.fillStyle = css('--surface'); ctx.beginPath(); ctx.arc(sx, sy, 6, 0, 2 * Math.PI); ctx.fill();
    ctx.strokeStyle = c; ctx.lineWidth = 2; ctx.fillStyle = filled ? c : css('--surface');
    ctx.beginPath(); ctx.arc(sx, sy, 4.5, 0, 2 * Math.PI); ctx.fill(); ctx.stroke();
  }
}

/* the periapsis (an open square) and apoapsis (an open diamond) of each shown whole orbit, as picked under Markers,
   on every Nth orbit (the first, then every N on), in the orbit's colour; replaying, only those already passed */
function drawApsides(result, p, until) {
  const {l, t, r, b} = plotRect(), every = Math.max(1, Math.round(+state.prefs.apsisEvery) || 1);
  let number = 0;
  result.orbits.forEach((o, k) => {
    if (!o.full) return;
    number++;
    if (!o.visible || (number - 1) % every) return;
    const colour = p.mode === 'transition' ? orbitColour(result, p, k) : p.color || result.color;
    for (const [on, point, kind] of [[state.prefs.showPeri, o.peri, 'peri'], [state.prefs.showApo, o.apo, 'apo']]) {
      if (!on || !point) continue;
      if (until !== null && !(point.t <= until && (state.trailStart === null || point.t >= state.trailStart))) continue;
      const [sx, sy] = toScreen(...plotPoint(result, point.x, point.y, point.t));
      if (!(sx >= l - 6 && sx <= r + 6 && sy >= t - 6 && sy <= b + 6)) continue;
      apsisMarker(ctx, sx, sy, kind, colour);
    }
  });
}

function apsisMarker(c, sx, sy, kind, colour) {
  c.strokeStyle = colour; c.lineWidth = 2; c.setLineDash([]);
  c.beginPath();
  if (kind === 'peri') c.rect(sx - 4.5, sy - 4.5, 9, 9);
  else { c.moveTo(sx, sy - 6); c.lineTo(sx + 6, sy); c.lineTo(sx, sy + 6); c.lineTo(sx - 6, sy); c.closePath(); }
  c.stroke();
}

/* the rows that end a stretch of the path (a row of empty cells in the csv ends a stretch) */
function stretchEnds(p) {
  const out = [];
  for (let i = 0; i < p.x.length; i++)
    if (isFinite(p.x[i]) && isFinite(p.y[i]) && !(i + 1 < p.x.length && isFinite(p.x[i + 1]) && isFinite(p.y[i + 1]))) out.push(i);
  return out;
}

/* the largest of a result's end vectors, which gets the longest arrow */
function endReference(result) {
  let most = 0;
  for (const p of result.paths) for (const i of stretchEnds(p)) for (const [, vx, vy] of endPairs(result)) {
    const size = Math.hypot(result.data.columns[vx][i], result.data.columns[vy][i]);
    if (isFinite(size)) most = Math.max(most, size);
  }
  return most;
}

/* an arrow at the end of each stretch of the path for each velocity-like pair, all to one scale (x / y only) */
function drawEndArrows(result, p) {
  const reference = endReference(result);
  if (!(reference > 0)) return;
  endPairs(result).forEach(([, vx, vy], k) => {
    ctx.strokeStyle = ctx.fillStyle = END_COLORS[k]; ctx.lineWidth = 1.5;
    for (const i of stretchEnds(p)) {
      const ax = result.data.columns[vx][i], ay = result.data.columns[vy][i];
      if (!isFinite(ax) || !isFinite(ay)) continue;
      const [sx, sy] = toScreen(p.x[i], p.y[i]);
      arrow(sx, sy, sx + ax / reference * END_LENGTH, sy - ay / reference * END_LENGTH);
    }
  });
}

/* key entries for the paths' extras: end arrows, apsides, time markers (in the player, whose title line isn't drawn) */
function pathKeys() {
  const keys = [], shown = state.results.filter(r => r.visible);
  if (planeView() && state.replay.state === 'stopped')
    for (const r of shown.filter(r => r.ends)) {
      const reference = endReference(r);
      endPairs(r).forEach(([label], k) => {
        const text = label + ' at the path ends  ' + speed(reference);
        if (!keys.some(e => e[1] === text)) keys.push([END_COLORS[k], text]);
      });
    }
  const every = Math.max(1, Math.round(+state.prefs.apsisEvery) || 1), which = every === 1 ? 'each orbit' : 'every ' + every + ' orbits';
  if (shown.some(r => r.orbits.length) && state.prefs.showPeri) keys.push([css('--ink2'), 'periapsis of ' + which, null, null, 'peri']);
  if (shown.some(r => r.orbits.length) && state.prefs.showApo) keys.push([css('--ink2'), 'apoapsis of ' + which, null, null, 'apo']);
  if (PLAYER && state.marks.note) keys.push(['transparent', state.marks.note]);
  return keys;
}

//---------------------------------------------------------------- time markers
/* dots along each path at every interval of a time column (the desktop's time markers): the column chosen under Time
   markers, or in distance / time mode the other one (the chosen one is on the axis). the interval is a round one giving
   about ten, unless one is typed in. a note says the interval, or why there are none */
const labelCells = new Set();   //screen cells already holding a marker's time, so labels don't overlap

function markerOption() {
  if (!timeMode()) return state.prefs.timeColumn;
  return state.prefs.timeColumn === 't' ? 'pt' : 't';
}

/* a round interval giving about ten markers over the shown results' marker column, or null */
function autoInterval() {
  let lo = Infinity, hi = -Infinity;
  for (const r of state.results.filter(r => r.visible)) {
    const c = timeColumnOf(r, markerOption());
    if (c) for (const v of r.data.columns[c]) if (isFinite(v)) { lo = Math.min(lo, v); hi = Math.max(hi, v); }
  }
  return hi > lo ? niceStep(hi - lo, 10) : null;
}

function prepareTimeMarks() {
  const option = markerOption(), typed = String(state.timeInterval).trim();
  const key = [plotKey, option, typed, state.prefs.showTimeMarks, state.results.filter(r => r.visible).map(r => r.file).join()].join('|');
  if (state.marks.key === key) return;
  state.marks.key = key; state.marks.note = ''; state.marks.interval = null; state.marks.column = null;
  for (const r of state.results) for (const p of r.paths) p.marks = null;
  if (!state.prefs.showTimeMarks || !state.results.length) return;
  if (!state.results.some(r => r.visible && timeColumnOf(r, option))) {
    state.marks.note = timeMode() ? 'no second time column for markers' : 'no ' + option + ' column for markers';
    return;
  }
  const interval = typed === '' ? autoInterval() : +typed;
  if (!(interval > 0)) { state.marks.note = typed === '' ? '' : 'the time markers\' interval must be a number above 0'; return; }
  state.marks.interval = interval;
  for (const r of state.results.filter(r => r.visible)) {
    const c = timeColumnOf(r, option), g = timeColumnOf(r, 't');
    if (!c) continue;
    state.marks.column = c;
    const tc = r.data.columns[c], gc = g ? r.data.columns[g] : null;
    const axisName = timeMode() ? timeColumnOf(r, state.prefs.timeColumn) : null, axis = axisName ? r.data.columns[axisName] : null;
    for (const p of r.paths) {
      //the path's rows in order, where its time rises; a gap (a hidden orbit, an empty row) gets no markers
      const rows = [];
      for (let i = 0; i < tc.length; i++) if (isFinite(tc[i]) && isFinite(p.x[i]) && isFinite(p.y[i]) && shownRow(r, i)) rows.push(i);
      if (rows.length < 2) continue;
      if (rows.some((row, k) => k && tc[row] < tc[rows[k - 1]])) { state.marks.note = c + ' does not always increase along ' + p.name; continue; }
      const T = [], xs = [], ys = [], at = [], G = [];
      const first = Math.ceil(tc[rows[0]] / interval - 1e-9), last = Math.floor(tc[rows[rows.length - 1]] / interval + 1e-9);
      if (last - first > MAX_TIME_MARKS) { state.marks.note = 'interval too small (' + (last - first + 1) + ' markers): try a larger one'; continue; }
      let k = 0;
      for (let m = first; m <= last; m++) {
        const v = m * interval;
        while (k + 1 < rows.length && tc[rows[k + 1]] < v) k++;
        const i = rows[k], j = rows[Math.min(k + 1, rows.length - 1)];
        if (j !== i + 1 && tc[i] !== v && tc[j] !== v) continue;   //across a gap
        const f = tc[j] === tc[i] ? 0 : (v - tc[i]) / (tc[j] - tc[i]), mix = col => col ? col[i] + f * (col[j] - col[i]) : NaN;
        T.push(v); xs.push(p.x[i] + f * (p.x[j] - p.x[i])); ys.push(p.y[i] + f * (p.y[j] - p.y[i])); at.push(mix(axis)); G.push(mix(gc));
      }
      const [X, Y] = plotValues(r, xs, ys, at);
      p.marks = {T, X, Y, G};
    }
  }
  if (!state.marks.note && state.marks.interval && state.prefs.showMarkNote && state.marks.column)
    state.marks.note = '\u25cf  every ' + fmt(state.marks.interval) + ' of ' + state.marks.column;
}

/* a path's markers: dots, each labelled with its time where no other label is near; replaying, only along the trail */
function drawTimeMarks(result, p, until) {
  if (!p.marks) return;
  const {l, t, r, b} = plotRect(), colour = p.color || result.color, {T, X, Y, G} = p.marks;
  ctx.font = '10px -apple-system, Helvetica, Arial, sans-serif'; ctx.textAlign = 'left'; ctx.textBaseline = 'middle';
  for (let k = 0; k < T.length; k++) {
    if (until !== null && !(G[k] <= until && (state.trailStart === null || G[k] >= state.trailStart))) continue;
    const [sx, sy] = toScreen(X[k], Y[k]);
    if (!(sx >= l - 5 && sx <= r + 5 && sy >= t - 5 && sy <= b + 5)) continue;
    ctx.fillStyle = css('--surface'); ctx.beginPath(); ctx.arc(sx, sy, 4.5, 0, 2 * Math.PI); ctx.fill();
    ctx.fillStyle = colour; ctx.beginPath(); ctx.arc(sx, sy, 3, 0, 2 * Math.PI); ctx.fill();
    if (!state.prefs.showMarkLabels) continue;
    const cx = Math.floor(sx / 48), cy = Math.floor(sy / 16);
    let near = false;
    for (let dx = -1; dx <= 1 && !near; dx++) for (let dy = -1; dy <= 1; dy++) if (labelCells.has((cx + dx) + ',' + (cy + dy))) { near = true; break; }
    if (near) continue;
    ctx.fillStyle = css('--ink2'); ctx.fillText(fmt(T[k]), sx + 8, sy - 1);
    labelCells.add(cx + ',' + cy);
  }
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
      ['showSpin', envs.some(e => e.bodies.some(b => b.spin)), 'no spinning bodies in ' + which],
      ['showInfallArrows', planeView() && (background ? has('u') : envs.some(e => (e.frames && e.frames.layer.u) || e.bodies.length)),
       !planeView() ? 'falling space is drawn only in the x / y view' : 'no flow of space (u) for ' + which],
      ['showInfallRings', planeView() && (background ? has('u') : true) && envs.some(e => e.bodies.length),
       !planeView() ? 'falling space is drawn only in the x / y view' : 'no bodies, or no flow of space, for ' + which]]) {
    const box = $(id), label = box.parentElement;
    if (box.disabled === !ok) continue;
    box.disabled = !ok;
    if (label.dataset.help === undefined) label.dataset.help = label.dataset.tip || '';
    label.dataset.tip = ok ? label.dataset.help : 'Not available: ' + missing + (label.dataset.help ? '. ' + label.dataset.help : '');
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

/* a body's horizon (the Schwarzschild radius, or a spinning hole's r+ at flat distance sqrt(r+^2 + a^2)), its
   ergosphere's edge (r = 2M, flat distance sqrt(4M^2 + a^2)) and ring singularity (r = 0, flat distance a), in metres:
   [radius, label, dash, width] */
function bodyCircles(body) {
  const M = G * body.mass / C / C, a = (body.spin || 0) * M, rPlus = M + Math.sqrt(Math.max(M * M - a * a, 0));
  const out = [[Math.hypot(rPlus, a), a ? 'r+' : 'Rs', [2, 3], 1]];
  if (a) out.push([Math.hypot(2 * M, a), 'ergo', [7, 5], 1], [Math.abs(a), 'ring', [], 1]);
  return out;
}

/* a body's name for its label: its mass in solar masses, and its spin */
function bodyLabel(body) {
  return (+(body.mass / MS).toPrecision(4)) + ' MS' + (body.spin ? ', spin ' + (+body.spin.toPrecision(3)) : '');
}

function drawBodies(env) {
  if (!state.prefs.showBodies && !state.prefs.showSchwarzschild) return;
  if (timeMode()) {
    //distance / time: a body is a line up the time axis at its distance, its circles lines either side, labelled
    const {t: top, b, l, r} = plotRect();
    ctx.font = '10px -apple-system, Helvetica, Arial, sans-serif'; ctx.textBaseline = 'top';
    const up = (d, dash, colour, width, label) => {
      if (d < 0) return;
      const [sx] = toScreen(toAxis(d, axes()[0]), 0);
      if (!(sx >= l && sx <= r)) return;
      ctx.strokeStyle = colour; ctx.lineWidth = width; ctx.setLineDash(dash); line(sx, top, sx, b); ctx.setLineDash([]);
      if (label) { ctx.fillStyle = css('--ink2'); ctx.textAlign = flipX() ? 'right' : 'left'; ctx.fillText(label, sx + (flipX() ? -4 : 4), top + 4); }
    };
    for (const body of env.bodies) {
      const d = Math.hypot(body.x, body.y);
      if (state.prefs.showSchwarzschild) for (const [R, label, dash, width] of bodyCircles(body)) for (const side of [-1, 1]) up(d + side * R, dash, css('--ink2'), width, side > 0 ? label : '');
      if (state.prefs.showBodies) up(d, [], body.black ? '#111' : css('--ink'), 2.5, state.prefs.showBodyLabels ? bodyLabel(body) : '');
    }
    ctx.lineWidth = 1;
    return;
  }
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
    if (state.prefs.showSchwarzschild)
      //the horizon, and a spinning hole's ergosphere (dashed outside it) and ring singularity
      for (const [R, , dash] of bodyCircles(body)) {
        if (R * scale <= 2) continue;
        ctx.strokeStyle = css('--ink2'); ctx.lineWidth = 1.6; ctx.setLineDash(dash); ctx.beginPath(); ctx.arc(sx, sy, R * scale, 0, 2 * Math.PI); ctx.stroke(); ctx.setLineDash([]);
      }
    if (state.prefs.showBodies && state.prefs.showBodyLabels) {
      ctx.fillStyle = css('--ink2'); ctx.font = '10px -apple-system, Helvetica, Arial, sans-serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'top';
      ctx.fillText(bodyLabel(body), sx, sy + (state.prefs.showSpin && body.spin ? 18 : 10));
    }
    if (state.prefs.showBodies && state.prefs.showSpin && body.spin) { state.spinning.push({sx, sy, body}); continue; }
    if (state.prefs.showBodies) {
      ctx.fillStyle = body.black ? '#111' : '#fff'; ctx.strokeStyle = css('--ink'); ctx.lineWidth = 1;
      ctx.beginPath(); ctx.arc(sx, sy, 6, 0, 2 * Math.PI); ctx.fill(); ctx.stroke();
    }
  }
}

/* what moves on its own, on each view's overlay canvas over the plot, so it moves without the plot being redrawn:
   spinning bodies, each a disc with three spokes turning the way the body spins (anticlockwise for positive spin) at
   SPIN_RATE times its spin (rad/s of the page's clock: a picture, not the real rate), and an arrow round it; and falling
   space (drawInfall). where the browser asks for reduced motion they are drawn still */
const SPIN_RATE = 2.5;
const REDUCED_MOTION = window.matchMedia ? matchMedia('(prefers-reduced-motion: reduce)') : {matches: false};
const stillMotion = () => REDUCED_MOTION.matches;

/* after each draw of a view: start its overlay's animation, or (nothing moving, or reduced motion) paint it once */
function drawSpinning() {
  const pane = currentPane();
  if (!pane) return;
  const moving = state.spinning.length > 0 || infallShown();
  if (moving && !stillMotion()) {
    if (pane.frame == null) { pane.last = performance.now(); pane.frame = requestAnimationFrame(now => animate(pane, now)); }
    return;
  }
  if (pane.frame != null) { cancelAnimationFrame(pane.frame); pane.frame = null; }
  paintOverlay(pane, performance.now(), 0);
}

function animate(pane, now) {
  pane.frame = null;
  if (!panes.includes(pane)) return;
  const dt = Math.min(0.1, Math.max(0, now - pane.last) / 1000);
  pane.last = now;
  const moving = withPane(pane, () => paintOverlay(pane, now, dt));
  if (moving && !stillMotion()) pane.frame = requestAnimationFrame(t => animate(pane, t));
}

/* the overlay at a moment, dt seconds after the last: whether anything on it moves */
function paintOverlay(pane, now, dt) {
  const ratio = window.devicePixelRatio || 1, w = overlay.clientWidth, h = overlay.clientHeight;
  if (overlay.width !== Math.round(w * ratio) || overlay.height !== Math.round(h * ratio)) {
    overlay.width = Math.round(w * ratio); overlay.height = Math.round(h * ratio);
  }
  const c = overlayCtx;
  c.setTransform(ratio, 0, 0, ratio, 0, 0);
  c.clearRect(0, 0, w, h);
  if (!state.view) return false;
  const {l, t, r, b} = plotRect();
  c.save(); c.beginPath(); c.rect(l, t, r - l, b - t); c.clip();
  const falling = infallShown();
  if (falling) drawInfall(pane, c, dt);
  const turnAt = stillMotion() ? 0 : now;
  for (const {sx, sy, body} of state.spinning) {
    const R = 10, turn = -Math.sign(body.spin) * SPIN_RATE * Math.min(1, Math.abs(body.spin)) * turnAt / 1000;
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
  return falling || state.spinning.length > 0;
}

//---------------------------------------------------------------- falling space
/* space falling in, drawn moving: points carried by the flow u (arrows, each along u where it is), or rings of space,
   each a loop of points carried by u, falling into the black bodies (or out of white ones). the motion is a picture:
   the view's typical |u| moves INFALL_SPEED pixels a second (times the layer's speed), and faster or slower where u is,
   so where space falls faster the points do too. a point is gone where it reaches a horizon, leaves the view or the
   flow has no value; arrows come back somewhere else, and rings start again outside */
const INFALL_SPEED = 30;
const infallShown = () => planeView() && (state.prefs.showInfallArrows || state.prefs.showInfallRings) && infallHas().some(Boolean);
/* whether the view has a flow for the arrows, and bodies for the rings */
function infallHas() {
  const background = currentBackground(), envs = fieldEnvironments();
  const flow = background ? backgroundHas(background, 'u') : envs.some(e => (e.frames && e.frames.layer.u) || e.bodies.length);
  const env = overlayEnv();
  return [flow && state.prefs.showInfallArrows, flow && !!(env && env.bodies.length) && state.prefs.showInfallRings];
}

/* metres per pixel, and the view's typical |u| (the median over a coarse grid), worked out again when the view moves */
function infallScale(pane, t) {
  const {l, t: top, r, b} = plotRect(), v = state.view;
  const key = [v.join(), r - l, b - top, t, currentBackground() && currentBackground().name, overlayEnv() && overlayEnv().key].join('|');
  if (pane.infallScale && pane.infallScale.key === key) return pane.infallScale;
  const speeds = [];
  for (let i = 0; i < 9; i++) for (let j = 0; j < 9; j++) {
    const [x, y] = toData(l + (i + 0.5) / 9 * (r - l), top + (j + 0.5) / 9 * (b - top)), u = flowAt(x, y, t);
    if (u) { const s = Math.hypot(u[0], u[1]); if (isFinite(s) && s > 0) speeds.push(s); }
  }
  speeds.sort((p, q) => p - q);
  pane.infallScale = {key, perPixel: Math.abs(toData(l + 1, top)[0] - toData(l, top)[0]), typical: speeds.length ? speeds[speeds.length >> 1] : 0};
  return pane.infallScale;
}

/* how close to a body a point is gone: inside half its horizon (a black body's) */
function swallowed(x, y) {
  const env = overlayEnv();
  if (!env) return false;
  for (const body of env.bodies) if (body.black && Math.hypot(x - body.x, y - body.y) < 0.5 * bodyCircles(body)[0][0]) return true;
  return false;
}

/* a point carried by u for dt seconds of the picture's clock, in steps of at most a few pixels: its new place, or null
   where it is gone */
function carry(x, y, dt, metresPerSecond, t, perPixel) {
  let left = dt;
  for (let k = 0; k < 24 && left > 0; k++) {
    const u = flowAt(x, y, t);
    if (!u || !isFinite(u[0]) || !isFinite(u[1])) return null;
    const size = Math.hypot(u[0], u[1]);
    if (!(size > 0)) return [x, y];
    const step = Math.min(left, 4 * perPixel / (size * metresPerSecond));   //4 pixels at most
    x += u[0] * metresPerSecond * step; y += u[1] * metresPerSecond * step; left -= step;
    if (swallowed(x, y)) return null;
  }
  return [x, y];
}

function drawInfall(pane, c, dt) {
  const t = fieldTime() ?? 0, scale = infallScale(pane, t), [arrowsOn, ringsOn] = infallHas();
  if (!(scale.typical > 0)) return;
  const env = overlayEnv(), key = [env && env.key, currentBackground() && currentBackground().name].join('|');
  if (!pane.infall || pane.infall.key !== key) pane.infall = {key, tracers: [], rings: [], wait: 0};
  const state_ = pane.infall, {l, t: top, r, b} = plotRect(), v = state.view, perPixel = scale.perPixel;
  //seconds of flow for a second of the picture, for each layer's speed
  const rate = speedSetting => INFALL_SPEED * speedSetting * perPixel / scale.typical;
  const inView = (x, y, margin) => { const [sx, sy] = toScreen(x, y); return sx > l - margin && sx < r + margin && sy > top - margin && sy < b + margin; };

  if (arrowsOn) {
    const look = layer('infallArrows'), spacing = ARROW_SPACING * 1.15 / look.density;
    const count = Math.min(1500, Math.round((r - l) * (b - top) / (spacing * spacing)));
    const spawn = p => {
      for (let k = 0; k < 6; k++) {
        const [x, y] = toData(l + Math.random() * (r - l), top + Math.random() * (b - top));
        if (flowAt(x, y, t) && !swallowed(x, y)) return Object.assign(p, {x, y, age: 0, life: 2 + 4 * Math.random()});
      }
      return Object.assign(p, {x: NaN, y: NaN, age: 0, life: 0.5});
    };
    const list = state_.tracers;
    while (list.length < count) list.push(Object.assign(spawn({}), {age: Math.random() * 3}));
    list.length = count;
    const k = rate(look.speed);
    c.strokeStyle = c.fillStyle = look.colour; c.lineWidth = look.width;
    for (const p of list) {
      p.age += dt;
      const moved = isFinite(p.x) && dt > 0 ? carry(p.x, p.y, dt, k, t, perPixel) : [p.x, p.y];
      if (!moved || p.age > p.life || !inView(moved[0], moved[1], 10)) { spawn(p); continue; }
      [p.x, p.y] = moved;
      const u = flowAt(p.x, p.y, t);
      if (!u) continue;
      const size = Math.hypot(u[0], u[1]), length = 9 * look.size, [sx, sy] = toScreen(p.x, p.y);
      if (!(size > 0)) continue;
      c.globalAlpha = 0.85 * Math.max(0, Math.min(1, p.age / 0.4, (p.life - p.age) / 0.4));
      const dx = u[0] / size * length, dy = -u[1] / size * length;
      overlayArrow(c, sx - dx / 2, sy - dy / 2, sx + dx / 2, sy + dy / 2);
    }
    c.globalAlpha = 1;
  } else state_.tracers.length = 0;

  if (ringsOn) {
    const look = layer('infallRings'), k = rate(look.speed), spacingPx = 55 / look.density;
    const black = env.bodies.filter(b => b.black), white = env.bodies.filter(b => !b.black);
    const corners = [[v[0], v[2]], [v[0], v[3]], [v[1], v[2]], [v[1], v[3]]];
    //a ring falling in: round the black bodies' centre of mass, from outside the view; one going out: from round a white body
    const ring = (cx, cy, R) => {
      const n = Math.max(48, Math.min(720, Math.round(2 * Math.PI * R / perPixel / 5)));
      return Array.from({length: n}, (_, i) => [cx + R * Math.cos(2 * Math.PI * i / n), cy + R * Math.sin(2 * Math.PI * i / n)]);
    };
    const sources = [];
    if (black.length) {
      const m = black.reduce((sum, q) => sum + q.mass, 0);
      const cx = black.reduce((sum, q) => sum + q.mass * q.x, 0) / m, cy = black.reduce((sum, q) => sum + q.mass * q.y, 0) / m;
      sources.push({cx, cy, R: Math.max(...corners.map(([x, y]) => Math.hypot(x - cx, y - cy))) * 1.02, inward: true});
    }
    for (const q of white) sources.push({cx: q.x, cy: q.y, R: Math.max(1.5 * bodyCircles(q)[0][0], 6 * perPixel), inward: false});
    //at the start, rings already on their way in, so the view isn't empty while the first ones arrive
    if (!state_.rings.length && !state_.started) {
      state_.started = true;
      for (const src of sources.filter(q => q.inward))
        for (let R = src.R; R > 4 * perPixel; R -= spacingPx * perPixel) state_.rings.push(ring(src.cx, src.cy, R));
    }
    state_.wait -= dt;
    if (state_.wait <= 0) {
      for (const src of sources) state_.rings.push(ring(src.cx, src.cy, src.R));
      //the next when this one has moved a ring's spacing: at the speed of the flow where it starts
      const src = sources[0], u = src && flowAt(src.cx + src.R, src.cy, t), speedPx = u ? Math.hypot(u[0], u[1]) * k / perPixel : 0;
      state_.wait = speedPx > 0 ? Math.min(6, spacingPx / speedPx) : 2;
    }
    c.strokeStyle = look.colour; c.lineWidth = look.width; c.globalAlpha = 0.8;
    const reach = Math.max(...corners.map(([x, y]) => Math.hypot(x - (v[0] + v[1]) / 2, y - (v[2] + v[3]) / 2))) * 1.6;
    state_.rings = state_.rings.filter(points => {
      let alive = 0;
      for (let i = 0; i < points.length; i++) {
        const p = points[i];
        if (!p) continue;
        const moved = dt > 0 ? carry(p[0], p[1], dt, k, t, perPixel) : p;
        if (!moved || Math.hypot(moved[0] - (v[0] + v[1]) / 2, moved[1] - (v[2] + v[3]) / 2) > reach) { points[i] = null; continue; }
        points[i] = moved; alive++;
      }
      if (alive < 3) return false;
      //the loop, broken where a point is gone or two neighbours have pulled far apart
      c.beginPath();
      let pen = false, last = null;
      for (let i = 0; i <= points.length; i++) {
        const p = points[i % points.length];
        if (!p) { pen = false; continue; }
        const [sx, sy] = toScreen(p[0], p[1]);
        if (pen && Math.hypot(sx - last[0], sy - last[1]) > 40) pen = false;
        if (pen) c.lineTo(sx, sy); else c.moveTo(sx, sy);
        pen = true; last = [sx, sy];
      }
      c.stroke();
      return true;
    });
    c.globalAlpha = 1;
  } else { state_.rings.length = 0; state_.started = false; }
}

function overlayArrow(c, x0, y0, x1, y1) {
  c.beginPath(); c.moveTo(x0, y0); c.lineTo(x1, y1); c.stroke();
  const length = Math.hypot(x1 - x0, y1 - y0);
  if (length < 3) return;
  const ux = (x1 - x0) / length, uy = (y1 - y0) / length, head = Math.min(5, length * 0.55);
  c.beginPath(); c.moveTo(x1, y1);
  c.lineTo(x1 - head * ux + head * 0.45 * uy, y1 - head * uy - head * 0.45 * ux);
  c.lineTo(x1 - head * ux - head * 0.45 * uy, y1 - head * uy + head * 0.45 * ux);
  c.closePath(); c.fill();
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
    keys.push([layer('scalar').plus, env.scalar + ': red +' + fmt(frames.reference.s) + ', blue \u2212' + fmt(frames.reference.s) + moment + named]);
  }
  for (const [show, field, look, label, offset] of [
      [state.prefs.showFlow, 'u', layer('u'), 'u', 0],
      [state.prefs.showGravity, 'a', layer('g'), 'g, the acceleration of space', 0.5]]) {
    if (!show || !frames.layer[field]) continue;
    const colour = look.colour;
    drawArrows((x, y) => frameSample(frames.layer[field], field, x, y, t), look, frames.reference[field], offset);
    const ref = frames.reference[field];
    const moment = when(frames.layer[field]);
    keys.push([colour, label + '  ' + (field === 'u' ? speed(ref) : fmt(ref) + ' m/s²') + moment + named, null, null, 'arrow']);
  }
  return keys;
}

//---------------------------------------------------------------- overlays: equal-u lines, flow lines, special orbits, light cones
/* drawn from the background's u where it has one (else an older run's frames), and otherwise, as the desktop viewer
   does, from the bodies: |u| = sqrt(sum 2GM/d), the escape speed from them all (d from a spinning hole's ring), in
   towards a black body and out of a white one, along g where there are several. the photon orbits and innermost
   stable orbits are Kerr's (Bardeen, Press & Teukolsky) */

/* the environment the overlays are for: the first one drawn */
const overlayEnv = () => fieldEnvironments()[0] || null;

/* the flow u at (x, y), time t, as [ux, uy], or null where there is none */
function flowAt(x, y, t) {
  const background = currentBackground();
  if (background) return backgroundHas(background, 'u') ? sampleBackground(background, 'u', x, y, t) : null;
  const env = overlayEnv();
  if (!env) return null;
  if (env.frames && env.frames.layer.u) return frameSample(env.frames.layer.u, 'u', x, y, t ?? env.frames.layer.u.times[0]);
  if (!env.bodies.length) return null;
  let square = 0, gx = 0, gy = 0;
  for (const body of env.bodies) {
    const ring = ((body.spin || 0) * G * body.mass / C / C) ** 2, dx = x - body.x, dy = y - body.y, d2 = dx * dx + dy * dy;
    if (!(d2 > ring)) return null;
    const d = Math.sqrt(d2 - ring);
    square += 2 * G * body.mass / d;
    const pull = G * body.mass / (d2 * Math.sqrt(d2)) * (body.black ? 1 : -1);
    gx -= pull * dx; gy -= pull * dy;
  }
  const size = Math.sqrt(square), g = Math.hypot(gx, gy);
  return g > 0 ? [gx / g * size, gy / g * size] : null;
}

/* where u comes from, for the key */
function flowSource() {
  const background = currentBackground(), env = overlayEnv();
  if (background) return 'background: ' + background.name;
  if (env && env.frames && env.frames.layer.u) return "the run's flow frames";
  return env && env.bodies.length > 1 ? 'the escape speed from the bodies, along g' : 'the escape speed';
}

/* a distance for the key: in M = GM/c^2 too when there is one hole */
function inM(R) {
  const env = overlayEnv(), hole = env && env.bodies.length === 1 && env.bodies[0].black ? env.bodies[0] : null;
  const metres = fmt(+R.toPrecision(4)) + ' m';
  return hole ? fmt(+(R / (G * hole.mass / C / C)).toPrecision(3)) + ' M (' + metres + ')' : metres;
}

/* the one hole's circular photon orbits and innermost stable circular orbits, at flat distance sqrt(r^2 + a^2):
   [kind, 'with' / 'against' the spin or null, R in metres] */
function specialOrbits() {
  const env = overlayEnv();
  if (!env || env.bodies.length !== 1 || !env.bodies[0].black) return [];
  const body = env.bodies[0], M = G * body.mass / C / C, spin = Math.min(Math.abs(body.spin || 0), 1), a = spin * M;
  const photon = pro => 2 * M * (1 + Math.cos(2 / 3 * Math.acos((pro ? -1 : 1) * spin)));
  const isco = pro => {
    const z1 = 1 + Math.cbrt(1 - spin * spin) * (Math.cbrt(1 + spin) + Math.cbrt(1 - spin)), z2 = Math.sqrt(3 * spin * spin + z1 * z1);
    return M * (3 + z2 - (pro ? 1 : -1) * Math.sqrt((3 - z1) * (3 + z1 + 2 * z2)));
  };
  const out = [];
  for (const [kind, radius] of [['photon', photon], ['isco', isco]]) {
    if (spin) for (const pro of [true, false]) out.push([kind, pro === (body.spin > 0) ? 'with' : 'against', Math.hypot(radius(pro), a)]);
    else out.push([kind, null, radius(true)]);
  }
  return out;
}

/* overlays drawn under the paths, in the plane or against time: equal-u lines, photon orbits and ISCOs, flow lines
   (the plane's), and the horizons' key; returns key entries */
function drawOverlaysUnder() {
  const keys = [], env = overlayEnv(), t = fieldTime() ?? 0;
  if (state.prefs.showContours && drawContours(t)) keys.push([layer('contours').colour, 'lines of equal |u|, km/s (' + flowSource() + ')']);
  if (state.prefs.showSpecialOrbits) {
    const orbits = specialOrbits();
    for (const [kind, sense, R] of orbits) {
      const colour = kind === 'photon' ? CONE : ISCO_COLOUR, dash = sense === 'against' ? AGAINST_DASH : WITH_DASH;
      const label = (kind === 'photon' ? 'photon' : 'ISCO') + ({with: ' +', against: ' \u2212'}[sense] || '');
      drawCircleAround(env.bodies[0], R, colour, dash, 1.5, timeMode() ? label : '');
    }
    for (const [kind, colour, name] of [['photon', CONE, 'circular photon orbit'], ['isco', ISCO_COLOUR, 'innermost stable circular orbit']]) {
      const found = orbits.filter(o => o[0] === kind);
      if (found.length) keys.push([colour, name + ': ' + found.map(([, sense, R]) => (sense ? sense + ' the spin ' : '') + inM(R)).join(', '), WITH_DASH]);
    }
    if (orbits.some(o => o[1] === 'against')) keys.push([css('--muted'), 'short dashes: going round against the spin', AGAINST_DASH]);
  }
  if (infallShown()) {
    const [arrows, rings] = infallHas();
    if (arrows) keys.push([layer('infallArrows').colour, 'falling space: points carried by u, moving at a picture speed (faster where u is)', null, null, 'arrow']);
    if (rings) keys.push([layer('infallRings').colour, 'falling space: rings of space carried by u, at a picture speed']);
  }
  if (planeView() && state.prefs.showFlowLines && drawFlowLines(t)) {
    const one = env && env.bodies.length === 1;
    keys.push([layer('flowLines').colour, one ? 'flow lines: the paths of space, straight ' + (env.bodies[0].black ? 'in to the hole' : 'out of the body')
                              : 'flow lines: ' + flowLineCount() + ' per body, out against the flow (' + flowSource() + ')']);
  }
  if (!PLAYER && state.prefs.showSchwarzschild && env && env.bodies.length) {
    const radii = [...new Set(env.bodies.map(b => bodyCircles(b)[0][0]))].sort((a, b) => a - b);
    keys.push([css('--ink2'), (env.bodies.some(b => b.spin) ? 'horizon (Kerr r+, at flat distance \u221a(r+\u00b2 + a\u00b2))' : 'Schwarzschild radius 2GM/c\u00b2')
               + ': ' + radii.map(inM).join(', '), [2, 3]]);
    const spun = env.bodies.find(b => b.spin);
    if (spun) {
      const [, ergo, ring] = bodyCircles(spun);
      keys.push([css('--ink2'), 'ergosphere edge, r = 2M, where the river reaches c: ' + inM(ergo[0]), [7, 5]]);
      keys.push([css('--ink2'), 'ring singularity, r = 0: ' + inM(ring[0]) + ' (no river inside)']);
    }
  }
  return keys;
}

/* a circle of radius R round a body: in the plane, round it; against time, a line up the time axis either side */
function drawCircleAround(body, R, colour, dash, width, label) {
  ctx.strokeStyle = colour; ctx.lineWidth = width; ctx.setLineDash(dash);
  if (timeMode()) {
    const {t: top, b, l, r} = plotRect(), d = Math.hypot(body.x, body.y);
    ctx.font = '10px -apple-system, Helvetica, Arial, sans-serif'; ctx.textBaseline = 'top';
    for (const edge of [d - R, d + R]) {
      if (edge < 0) continue;
      const [sx] = toScreen(toAxis(edge, axes()[0]), 0);
      if (!(sx >= l && sx <= r)) continue;
      line(sx, top, sx, b);
      if (label) { ctx.fillStyle = css('--ink2'); ctx.textAlign = flipX() ? 'right' : 'left'; ctx.fillText(label, sx + (flipX() ? -4 : 4), top + 4); }
    }
  } else {
    const [sx, sy] = toScreen(body.x, body.y), radius = Math.abs(toScreen(body.x + R, body.y)[0] - sx);
    if (radius > 1) { ctx.beginPath(); ctx.arc(sx, sy, radius, 0, 2 * Math.PI); ctx.stroke(); }
  }
  ctx.setLineDash([]); ctx.lineWidth = 1;
}

/* |u| on a screen grid, the plane's or along the distance axis (at (d, 0)); [xs, ys, rows of speeds] */
function speedGrid(t) {
  const {l, t: top, r, b} = plotRect(), xs = [], ys = [], grid = [];
  for (let sx = l; sx <= r + CONTOUR_SPACING; sx += CONTOUR_SPACING) xs.push(sx);
  for (let sy = top; sy <= b + CONTOUR_SPACING; sy += CONTOUR_SPACING) ys.push(sy);
  const along = timeMode() ? new Map() : null;
  for (const sy of ys) {
    const row = [];
    for (const sx of xs) {
      const [X, Y] = toData(sx, sy);
      let u;
      if (along) {
        const d = fromAxis(X, axes()[0]);
        if (!along.has(sx)) { const v = d > 0 ? flowAt(d, 0, t) : null; along.set(sx, v ? Math.hypot(v[0], v[1]) : NaN); }
        u = along.get(sx);
      } else { const v = flowAt(X, Y, t); u = v ? Math.hypot(v[0], v[1]) : NaN; }
      row.push(u);
    }
    grid.push(row);
  }
  return [xs, ys, grid];
}

/* lines of equal |u|, traced by marching squares, each level labelled once (in km/s); whether any were drawn */
function drawContours(t) {
  const [xs, ys, grid] = speedGrid(t), finite = grid.flat().filter(isFinite).sort((a, b) => a - b);
  if (finite.length < 4) return false;
  const lo = finite[Math.floor(0.02 * finite.length)], hi = finite[Math.floor(0.98 * finite.length)];
  if (!(hi > lo)) return false;
  const look = layer('contours'), step = niceStep(hi - lo, 8 * look.density), labelled = [];
  ctx.lineWidth = look.width; ctx.strokeStyle = look.colour;
  let drawn = false;
  for (let level = Math.ceil(lo / step) * step; level < hi; level += step) {
    const segments = [];
    for (let j = 0; j + 1 < ys.length; j++)
      for (let i = 0; i + 1 < xs.length; i++) {
        const a = grid[j][i], bb = grid[j][i + 1], cc = grid[j + 1][i + 1], d = grid[j + 1][i];
        const cross = (p, q) => isFinite(p) && isFinite(q) && (p >= level) !== (q >= level), f = (p, q) => (level - p) / (q - p);
        const hits = [];
        if (cross(a, bb)) hits.push([xs[i] + f(a, bb) * (xs[i + 1] - xs[i]), ys[j]]);
        if (cross(bb, cc)) hits.push([xs[i + 1], ys[j] + f(bb, cc) * (ys[j + 1] - ys[j])]);
        if (cross(d, cc)) hits.push([xs[i] + f(d, cc) * (xs[i + 1] - xs[i]), ys[j + 1]]);
        if (cross(a, d)) hits.push([xs[i], ys[j] + f(a, d) * (ys[j + 1] - ys[j])]);
        if (hits.length === 2) segments.push([...hits[0], ...hits[1]]);
        if (hits.length === 4) segments.push([...hits[0], ...hits[3]], [...hits[1], ...hits[2]]);
      }
    if (!segments.length) continue;
    drawn = true;
    ctx.beginPath();
    for (const [x0, y0, x1, y1] of segments) { ctx.moveTo(x0, y0); ctx.lineTo(x1, y1); }
    ctx.stroke();
    //label it at the segment furthest right that is clear of the other labels
    for (const [x0, y0, x1, y1] of segments.sort((p, q) => (q[0] + q[2]) - (p[0] + p[2]))) {
      const mx = (x0 + x1) / 2, my = (y0 + y1) / 2;
      if (!labelled.every(([lx, ly]) => Math.hypot(mx - lx, my - ly) > 40)) continue;
      const text = fmt(+(level / 1000).toPrecision(3));
      ctx.font = '9px -apple-system, Helvetica, Arial, sans-serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      const w = ctx.measureText(text).width;
      ctx.fillStyle = css('--surface'); ctx.fillRect(mx - w / 2 - 2, my - 6, w + 4, 12);
      ctx.fillStyle = css('--muted'); ctx.fillText(text, mx, my);
      labelled.push([mx, my]);
      break;
    }
  }
  return drawn;
}

/* flow lines in the plane: for one body straight lines from it (from a spinning hole's ring) out past the view; for
   several, each body's lines followed out against the flow (with it, from a white body), until they leave the view,
   meet the flow coming the other way (a seam), or the flow has no value; worked out once for each view */
const flowLineCount = () => Math.max(2, Math.round(FLOW_LINES * layer('flowLines').density));
function drawFlowLines(t) {
  const env = overlayEnv();
  if (!env || !env.bodies.length) return false;
  const v = state.view, {l, r} = plotRect(), perPixel = (v[1] - v[0]) / (r - l);
  const count = flowLineCount(), key = [env.key, v.join(), r - l, currentBackground() && currentBackground().name, t, count].join('|');
  const same = state.flowLineCache.key && state.flowLineCache.key.split('|').filter((x, i) => i !== 1 && i !== 2).join('|') === key.split('|').filter((x, i) => i !== 1 && i !== 2).join('|');
  if (state.flowLineCache.key !== key && !(interacting() && same)) {
    const lines = [], span = Math.max(v[1] - v[0], v[3] - v[2]);
    const inReach = (x, y) => x > v[0] - span && x < v[1] + span && y > v[2] - span && y < v[3] + span;
    if (env.bodies.length === 1) {
      const body = env.bodies[0], start = Math.abs((body.spin || 0) * G * body.mass / C / C);
      const reach = Math.max(...[[v[0], v[2]], [v[0], v[3]], [v[1], v[2]], [v[1], v[3]]].map(([x, y]) => Math.hypot(x - body.x, y - body.y)));
      for (let n = 0; n < count; n++) {
        const a = 2 * Math.PI * n / count, c = Math.cos(a), s = Math.sin(a);
        lines.push([[body.x + start * c, body.y + start * s], [body.x + reach * c, body.y + reach * s]]);
      }
    } else for (const body of env.bodies) {
      const sense = body.black ? -1 : 1;
      for (let n = 0; n < count; n++) {
        const a = 2 * Math.PI * n / count;
        let x = body.x + 4 * perPixel * Math.cos(a), y = body.y + 4 * perPixel * Math.sin(a), last = null;
        const points = [[x, y]];
        for (let k = 0; k < 4000; k++) {
          const u = flowAt(x, y, t);
          if (!u) break;
          const size = Math.hypot(u[0], u[1]);
          if (!(size > 0)) break;
          const dx = sense * u[0] / size, dy = sense * u[1] / size;
          if (last && dx * last[0] + dy * last[1] < 0) break;     //turned back: the seam
          const near = Math.min(...env.bodies.map(o => Math.hypot(x - o.x, y - o.y)));
          const ds = Math.max(perPixel, Math.min(8 * perPixel, 0.01 * near));
          x += dx * ds; y += dy * ds; last = [dx, dy];
          points.push([x, y]);
          if (!inReach(x, y)) break;
        }
        if (points.length > 1) lines.push(points);
      }
    }
    state.flowLineCache = {key, lines};
  }
  const look = layer('flowLines');
  ctx.strokeStyle = look.colour; ctx.lineWidth = look.width;
  for (const points of state.flowLineCache.lines) {
    ctx.beginPath();
    points.forEach(([x, y], i) => { const [sx, sy] = toScreen(x, y); if (i) ctx.lineTo(sx, sy); else ctx.moveTo(sx, sy); });
    ctx.stroke();
  }
  return state.flowLineCache.lines.length > 0;
}

/* distance / time mode's backgrounds: the flow line, repeated up the time axis, and light cones; both need global time
   (t) on the time axis. returns key entries */
function drawTimeBackground() {
  const keys = [], t = fieldTime() ?? 0;
  if (!state.prefs.showFlowLines && !state.prefs.showCones) return keys;
  if (state.prefs.logX || state.prefs.logY) return keys;
  if (state.prefs.timeColumn !== 't') {
    keys.push(['transparent', 'flow lines and light cones need global time (t) on the time axis']);
    return keys;
  }
  if (state.prefs.showFlowLines) {
    const every = drawFlowLinesTime(t);
    if (every) keys.push([layer('flowLines').colour, 'flow line: space moving at u (dd/dt = u), repeated every ' + fmt(every) + ' s']);
  }
  if (state.prefs.showCones && drawCones(t)) keys.push([layer('cones').colour, 'light cones: the local speed of light outwards and inwards, u \u00b1 c', null, null, 'cone']);
  return keys;
}

/* u along the distance axis at distance d (at (d, 0)): the flow's x part, or NaN */
function uAlong(d, t) {
  const u = d > 0 ? flowAt(d, 0, t) : null;
  return u ? u[0] : NaN;
}

/* the flow line across the screen: space moving at u, dd/dt = u, so t(d) = integral of dd / u (the same line from
   any start time), in runs where u keeps its sign; copies at whole multiples of a round time step, so they stay put
   as the view pans. returns the step, or null if none was drawn */
function drawFlowLinesTime(t) {
  const v = state.view, tf = state.prefs.ctTime ? C : 1, n = 600, d = [], u = [];
  for (let i = 0; i <= n; i++) { const x = Math.max(v[0], 0) + (v[1] - Math.max(v[0], 0)) * i / n; d.push(x); u.push(uAlong(x, t)); }
  const runs = [];
  let start = 0;
  for (let i = 1; i <= d.length; i++)
    if (i === d.length || !(isFinite(u[i]) && u[i] !== 0 && Math.sign(u[i]) === Math.sign(u[i - 1]))) {
      if (i - start >= 2 && u.slice(start, i).every(w => isFinite(w) && w !== 0)) {
        const ts = [0];
        for (let k = start + 1; k < i; k++) ts.push(ts[ts.length - 1] + (d[k] - d[k - 1]) * (1 / u[k] + 1 / u[k - 1]) / 2);
        runs.push([d.slice(start, i), ts]);
      }
      start = i;
    }
  if (!runs.length) return null;
  const look = layer('flowLines'), y0 = v[2] / tf, y1 = v[3] / tf, every = niceStep(y1 - y0, 8 * look.density);
  ctx.strokeStyle = look.colour; ctx.lineWidth = look.width;
  let drawn = false;
  for (const [xs, ts] of runs) {
    const lo = Math.min(...ts), hi = Math.max(...ts);
    let first = Math.floor((y0 - hi) / every), last = Math.ceil((y1 - lo) / every);
    if (last - first > 320) { first = Math.max(first, Math.floor((y0 - lo) / every) - 16); last = Math.min(last, first + 32); }
    for (let k = first; k <= last; k++) {
      ctx.beginPath();
      let pen = false;
      for (let i = 0; i < xs.length; i++) {
        const tt = k * every + ts[i];
        if (tt < y0 - (y1 - y0) || tt > y1 + (y1 - y0)) { pen = false; continue; }
        const [sx, sy] = toScreen(xs[i], tt * tf);
        if (pen) ctx.lineTo(sx, sy); else ctx.moveTo(sx, sy);
        pen = true; drawn = true;
      }
      ctx.stroke();
    }
  }
  return drawn ? every : null;
}

/* a light cone at each point of a grid: light sent outwards and inwards by something moving with the flow, at u + c and
   u - c along the distance axis; each side runs along that light's path, the same length on screen, and an ellipse
   joins their ends, like a cone's cap in perspective. whether any were drawn */
function drawCones(t) {
  const {l, t: top, r, b} = plotRect(), v = state.view, tf = state.prefs.ctTime ? C : 1;
  const kd = (flipX() ? -1 : 1) * (r - l) / (v[1] - v[0]), kt = (b - top) * tf / (v[3] - v[2]);   //pixels per metre, per second
  const look = layer('cones'), spacing = ARROW_SPACING / look.density, side = 2.2 * CONE_SIZE * look.size, shift = spacing * 0.25;
  ctx.strokeStyle = ctx.fillStyle = look.colour; ctx.lineWidth = look.width;
  let drawn = false;
  const [gx, gy] = gridStart(l, top, spacing, shift);
  for (let sy = gy; sy < b; sy += spacing)
    for (let sx = gx; sx < r; sx += spacing) {
      const [X] = toData(sx, sy), u = uAlong(X, t);
      if (!isFinite(u)) continue;
      let [[ox, oy], [ix, iy]] = [u + C, u - C].map(speed => {
        const dx = speed * kd, dy = -kt, n = Math.hypot(dx, dy);
        return [sx + side * dx / n, sy + side * dy / n];
      });
      let a = Math.hypot(ox - ix, oy - iy) / 2;
      if (a > 0.45 * spacing) {
        const f = 0.45 * spacing / a;
        [ox, oy, ix, iy] = [sx + (ox - sx) * f, sy + (oy - sy) * f, sx + (ix - sx) * f, sy + (iy - sy) * f];
        a = Math.hypot(ox - ix, oy - iy) / 2;
      }
      if (a > 0) {
        ctx.beginPath();
        ctx.ellipse((ox + ix) / 2, (oy + iy) / 2, a, Math.max(2, 0.3 * a), Math.atan2(oy - iy, ox - ix), 0, 2 * Math.PI);
        ctx.stroke();
      }
      ctx.beginPath(); ctx.moveTo(ix, iy); ctx.lineTo(sx, sy); ctx.lineTo(ox, oy); ctx.stroke();
      ctx.beginPath(); ctx.arc(sx, sy, 1.5, 0, 2 * Math.PI); ctx.fill();
      drawn = true;
    }
  return drawn;
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
  //while the view is moving, the scale from before (worked out again when it stops)
  background.last = background.last || {};
  if (!background.cache.has(id) && interacting() && background.last[key] !== undefined) return background.last[key];
  if (!background.cache.has(id)) {
    if (background.cache.size > 200) background.cache.clear();
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
  background.last[key] = background.cache.get(id);
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
      keys.push([layer('scalar').plus, label + ': red +' + fmt(ref) + ', blue \u2212' + fmt(ref) + moment]);
    }
  }
  for (const [show, key, look, label, offset] of [
      [state.prefs.showFlow, 'u', layer('u'), 'u', 0],
      [state.prefs.showGravity, 'a', layer('g'), 'g, the acceleration of space', 0.5]]) {
    if (!show || !backgroundHas(background, key)) continue;
    const ref = backgroundReference(background, key);
    if (!ref) continue;
    const colour = look.colour;
    drawArrows((x, y) => sampleBackground(background, key, x, y, t), look, ref, offset);
    keys.push([colour, label + '  ' + (key === 'u' ? speed(ref) : fmt(ref) + ' m/s²') + moment, null, null, 'arrow']);
  }
  if (state.prefs.showTwist && backgroundHas(background, 't')) {
    const ref = backgroundReference(background, 't');
    if (ref) {
      drawTwist((x, y) => sampleBackground(background, 't', x, y, t), ref);
      const label = background.layers.find(l => l.type === 'field' && l.values.t).label;
      keys.push([layer('twist').colour, label + ': a full arc ' + fmt(ref) + ' rad/s' + moment, null, null, 'twist']);
    }
  }
  if (state.prefs.showSeam)
    for (const layer of background.layers.filter(l => l.type === 'lines')) {
      const k = Math.floor(timeIndex(layer.times, t)), fr = layer.frame ? frameAt(layer.frame, t) : null;
      const c = fr ? Math.cos(fr.angle) : 1, s = fr ? Math.sin(fr.angle) : 0;
      const look = layerLook('seam');
      ctx.strokeStyle = look.colour; ctx.lineWidth = look.width; ctx.setLineDash([6, 4]);
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
      keys.push([look.colour, layer.label + moment, [6, 4]]);
    }
  if (keys.length) keys.push(['transparent', 'background: ' + background.name]);
  return keys;
}

/* a scalar field as a colour map: cells of SCALAR_CELL pixels, red where it is positive, blue negative, their strength
   its size over the run's scale (capped); nothing off the grid or where it is not a number */
const SCALAR_CELL = 5, SCALAR_PLUS = '#d6452a', SCALAR_MINUS = '#2a6fd6';
function drawScalar(sample, reference) {
  const {l, t: top, r, b} = plotRect(), look = layer('scalar'), cell = Math.max(2, Math.round(SCALAR_CELL / look.density));
  const [gx, gy] = gridStart(l, top, cell, 0);
  for (let sy = gy - cell; sy < b; sy += cell)
    for (let sx = gx - cell; sx < r; sx += cell) {
      const [x, y] = toData(sx + cell / 2, sy + cell / 2), v = sample(x, y);
      if (!v || !isFinite(v[0]) || v[0] === 0) continue;
      ctx.globalAlpha = Math.min(1, Math.min(1, Math.abs(v[0]) / reference) * 0.85 * look.strength);
      ctx.fillStyle = v[0] > 0 ? look.plus : look.minus;
      ctx.fillRect(sx, sy, cell, cell);
    }
  ctx.globalAlpha = 1;
}

/* where a background's screen grid starts: fixed to the plot's own coordinates, so arrows, arcs, cones and colour-map
   cells move with the plot when it is panned, while their spacing on screen stays the same at any zoom. the grid goes
   through the screen point of the plot's origin, shifted by shift pixels; returns the first grid point at or after
   (l, top) */
function gridStart(l, top, spacing, shift) {
  let [ox, oy] = toScreen(0, 0);
  if (!isFinite(ox)) ox = l;
  if (!isFinite(oy)) oy = top;
  const mod = (v, m) => ((v % m) + m) % m;
  return [l + mod(ox + shift - l, spacing), top + mod(oy + shift - top, spacing)];
}

function speed(v) { return v >= 1e3 ? fmt(v / 1e3) + ' km/s' : fmt(v) + ' m/s'; }

/* arrows on a screen grid, each from its grid point, its length in proportion to the field (capped at a full one) */
/* twist arcs (a spinning hole's river): at each point of a grid a quarter of the way between the arrows', an arc turning the way space turns
   there (anticlockwise for a positive rate), its sweep the rate over reference (300 degrees at most); tiny ones left out */
const TWIST = '#0f766e';
function drawTwist(sample, reference) {
  const look = layer('twist'), spacing = ARROW_SPACING / look.density;
  const {l, t: top, r, b} = plotRect(), shift = spacing * 0.75, radius = spacing * 0.2 * look.size;
  ctx.strokeStyle = look.colour; ctx.fillStyle = look.colour; ctx.lineWidth = look.width;
  const [gx, gy] = gridStart(l, top, spacing, shift);
  for (let sy = gy; sy < b; sy += spacing)
    for (let sx = gx; sx < r; sx += spacing) {
      const [x, y] = toData(sx, sy), v = sample(x, y);
      if (!v || !isFinite(v[0]) || v[0] === 0) continue;
      const sweep = 300 / 180 * Math.PI * Math.min(1, Math.abs(v[0]) / reference);
      if (sweep < Math.PI / 12) continue;
      twistArc(ctx, sx, sy, radius, sweep, v[0] > 0, 5 * Math.max(0.6, look.size));
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

/* look: the layer's colour, density (arrows closer together), size (a full arrow longer) and line width */
function drawArrows(sample, look, reference, offset) {
  const spacing = ARROW_SPACING / look.density;
  const {l, t: top, r, b} = plotRect(), longest = spacing * 0.8 * look.size, shift = spacing * (0.5 + offset);
  ctx.strokeStyle = look.colour; ctx.fillStyle = look.colour; ctx.lineWidth = look.width;
  const [gx, gy] = gridStart(l, top, spacing, shift);
  for (let sy = gy; sy < b; sy += spacing)
    for (let sx = gx; sx < r; sx += spacing) {
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

/* the legend boxes (the paths' names, top right; the background's key, bottom left) each have three states:
   'hidden', just a button in the plot's corner; 'min', just the lines; 'max', the lines and their names. the one
   button, beside the box's inner corner (top left of the top right box, bottom right of the bottom left one), is a
   chevron: pointing into the plot it pulls the box out a step (hidden, then lines, then names), pointing back to the
   edge it tucks it away a step. at either end it turns round. the box slides sideways from its edge, animated */
const BOX_ANIM_MS = 220;
const BOX_WIDTH = {hidden: 0, min: 1, max: 2};          //how far out each state is
const BOX_OUT = {hidden: 'min', min: 'max'}, BOX_IN = {max: 'min', min: 'hidden'};
let boxFrame = null;

const ease = f => f < 0.5 ? 2 * f * f : 1 - 2 * (1 - f) * (1 - f);
const inside = (h, x, y) => x >= h.x && x <= h.x + h.w && y >= h.y && y <= h.y + h.h;

/* where a box's animation is now, 0 (hidden) to 1 (lines) to 2 (names), easing to its state's */
function boxProgress(box) {
  const goal = BOX_WIDTH[box.mode];
  if (!box.from) return goal;
  const f = stillMotion() ? 1 : Math.min(1, (performance.now() - box.from.at) / BOX_ANIM_MS);
  if (f >= 1) { box.from = null; return goal; }
  return box.from.w + (goal - box.from.w) * ease(f);
}

/* which way the button points: out at hidden, in at max, and between, the way it was last going */
const boxGoesOut = box => box.mode === 'hidden' ? true : box.mode === 'max' ? false : box.out;

function stepBox(name) {
  const box = state.boxes[name], out = boxGoesOut(box);
  box.from = {w: boxProgress(box), at: performance.now()};
  box.mode = out ? BOX_OUT[box.mode] : BOX_IN[box.mode];
  box.out = out;
  //each view with a box on the move drawn again, until they have all arrived
  const step = () => {
    let moving = false;
    for (const p of panes) withPane(p, () => { if (Object.values(state.boxes).some(b => b.from)) { draw(); moving = true; } });
    boxFrame = moving ? requestAnimationFrame(step) : null;
  };
  if (boxFrame === null) boxFrame = requestAnimationFrame(step);
}

/* the button: a chevron, < or > */
function drawBoxButton(x, y, size, left) {
  ctx.fillStyle = css('--surface'); ctx.strokeStyle = css('--grid'); ctx.lineWidth = 1; ctx.setLineDash([]);
  ctx.fillRect(x, y, size, size); ctx.strokeRect(x, y, size, size);
  const cx = x + size / 2, cy = y + size / 2, k = size * 0.2, d = left ? 1 : -1;
  ctx.strokeStyle = css('--ink2'); ctx.lineWidth = 1.6; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  ctx.beginPath(); ctx.moveTo(cx + d * k * 0.6, cy - k * 1.3); ctx.lineTo(cx - d * k * 0.6, cy); ctx.lineTo(cx + d * k * 0.6, cy + k * 1.3); ctx.stroke();
  ctx.lineCap = 'butt'; ctx.lineJoin = 'miter';
}

//each button's tip: what a press does, from a state, going out or in
const BOX_TIPS = {legend: {'hidden>': 'Show the paths\' lines', 'min>': 'Show the paths\' names',
                           'max<': 'Hide the paths\' names', 'min<': 'Hide the paths\' legend'},
                  key: {'hidden>': 'Show the key\'s lines', 'min>': 'Show the key\'s names',
                        'max<': 'Hide the key\'s names', 'min<': 'Hide the key'}};

/* lines: [colour, text, dash, path] - path, for a path's row, is {result, p} */
function drawBox(lines, anchor, name) {
  const {l, t, r, b} = plotRect(), rowH = 18, swatch = 26, btn = 18;
  const box = state.boxes[name], f = boxProgress(box), right = anchor === 'top-right';
  //the text shrinks (to 9px) to keep the box inside the plot
  let size = 12, widest;
  for (; ; size--) {
    ctx.font = size + 'px -apple-system, Helvetica, Arial, sans-serif';
    widest = Math.max(...lines.map(([, text]) => ctx.measureText(text).width));
    if (size <= 9 || widest + swatch + 22 + btn <= r - l - 16) break;
  }
  const full = widest + swatch + 22, slim = swatch + 16;
  const width = f <= 1 ? slim * f : slim + (full - slim) * (f - 1);
  const height = rowH * lines.length + 8;
  //the box keeps its edge, sliding out from it: the right edge at the top right, the left at the bottom left
  const x = right ? r - 8 - width : l + 8;
  const y = right ? t + 8 : b - 8 - height;
  //the button beside the box's inner corner: left of the top right box's top, right of the bottom left box's bottom;
  //hidden, in the plot's corner
  const bx = right ? x - btn - (width > 0 ? 2 : 0) : x + width + (width > 0 ? 2 : 0), by = right ? y : y + height - btn;
  if (width >= 1) {
    ctx.save();
    ctx.fillStyle = css('--surface'); ctx.strokeStyle = css('--grid'); ctx.lineWidth = 1;
    ctx.fillRect(x, y, width, height); ctx.strokeRect(x, y, width, height);
    ctx.beginPath(); ctx.rect(x, y, width, height); ctx.clip();
    //the rows slide with the box's inner edge: from hidden to the lines, they come out from the edge
    const lx = x - Math.max(0, slim - width) * (right ? 0 : 1);
    lines.forEach(([colour, text, dash, path, shape], i) => {
      const ry = y + 4 + rowH * i, cy = ry + rowH / 2, mid = lx + 8 + swatch / 2;
      ctx.strokeStyle = ctx.fillStyle = colour; ctx.lineWidth = 1.6; ctx.setLineDash(dash || []);
      //the swatch: a line, or the mark itself (an apsis, an arrow, a light cone, a time marker)
      if (shape === 'peri' || shape === 'apo') apsisMarker(ctx, mid, cy, shape, colour);
      else if (shape === 'arrow') { ctx.lineWidth = 1; arrow(lx + 8, cy, lx + 8 + swatch, cy); }
      else if (shape === 'cone') { ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(lx + 8 + swatch, cy - 6); ctx.lineTo(lx + 8, cy); ctx.lineTo(lx + 8 + swatch, cy + 6); ctx.stroke();
                                   ctx.beginPath(); ctx.ellipse(lx + 8 + swatch, cy, 2, 6, 0, 0, 2 * Math.PI); ctx.stroke(); }
      else if (shape === 'dot') { ctx.beginPath(); ctx.arc(mid, cy, 3, 0, 2 * Math.PI); ctx.fill(); }
      else if (shape === 'twist') { ctx.lineWidth = 1; twistArc(ctx, mid, cy, 6, 300 / 180 * Math.PI, true, 5); }
      else line(lx + 8, cy, lx + 8 + swatch, cy);
      ctx.setLineDash([]);
      ctx.fillStyle = css('--ink2'); ctx.textAlign = 'left'; ctx.textBaseline = 'middle';
      ctx.globalAlpha = 0.25 + 0.75 * Math.max(0, f - 1);
      ctx.fillText(text, lx + swatch + 14, cy);
      ctx.globalAlpha = 1;
      state.boxRows.push({x, y: ry, w: width, h: rowH, tip: text, path});
    });
    ctx.restore();
  }
  const out = boxGoesOut(box);
  //pointing into the plot pulls the box out: < at the top right, > at the bottom left
  drawBoxButton(bx, by, btn, right ? out : !out);
  state.boxButtons.push({x: bx, y: by, w: btn, h: btn, box: name, tip: BOX_TIPS[name][box.mode + (out ? '>' : '<')]});
}

/* a press on a box's button: a step out or in; true if it was one */
function boxPress(e) {
  const hit = state.boxButtons.find(h => inside(h, e.offsetX, e.offsetY));
  if (!hit) return false;
  stepBox(hit.box);
  $('tip').style.display = 'none';           //the button moves: its tip comes back with the next move of the pointer
  return true;
}

/* a position as the axes show it: each coordinate its own line */
function positionLines(x, y) {
  const [ax, ay] = axes();
  return [ax.label + ': ' + fmt(x / ax.scale), ay.label + ': ' + fmt(y / ay.scale)];
}

/* hover text on the plot, as lines (a description, then each value on its own): a box's button or row, a body, or
   the nearest drawn path within a few pixels */
function hoverText(sx, sy) {
  const button = state.boxButtons.find(h => inside(h, sx, sy));
  if (button) return {lines: [button.tip], pointer: true};
  const row = state.boxRows.find(h => inside(h, sx, sy));
  if (row) return {lines: [row.tip], path: row.path};
  const {l, t, r, b} = plotRect();
  if (sx < l || sx > r || sy < t || sy > b || !state.view) return null;
  if (state.prefs.showBodies && planeView()) for (const env of fieldEnvironments()) for (const body of env.bodies || []) {
    const [bx, by] = toScreen(body.x, body.y);
    if (Math.hypot(sx - bx, sy - by) <= 8) {
      const m = body.mass / MS;
      return {lines: [body.black ? 'a black hole' : 'a body', 'mass: ' + (+m.toPrecision(4)) + ' solar mass' + (m === 1 ? '' : 'es'),
                      ...(body.spin ? ['spin: ' + (+body.spin.toPrecision(3))] : []), ...positionLines(body.x, body.y)]};
    }
  }
  let best = null, bestD = 6;
  for (const result of state.results.filter(r => r.visible)) {
    const until = drawUntil(result);
    if (until === false) continue;
    for (const p of result.paths) {
      plotted(result, p);
      let last = null;
      for (let i = 0; i < p.px.length; i++) {
        if (until !== null && p.t && p.t[i] > until) break;
        if (!(isFinite(p.px[i]) && isFinite(p.py[i])) || !shownRow(result, i)) { last = null; continue; }
        const [px, py] = toScreen(p.px[i], p.py[i]);
        if (last) {
          const [qx, qy] = last, dx = px - qx, dy = py - qy, len2 = dx * dx + dy * dy;
          const f = len2 ? Math.max(0, Math.min(1, ((sx - qx) * dx + (sy - qy) * dy) / len2)) : 0;
          const d = Math.hypot(sx - qx - f * dx, sy - qy - f * dy);
          if (d < bestD) {
            bestD = d;
            //the nearer row's values, column by column (the first twelve), as the desktop shows them
            const row = f < 0.5 ? i - 1 : i, names = result.data.names;
            best = [result.name + (result.paths.length > 1 ? ' ' + p.name : '') + (result.orbits.length && result.rowOrbit[row] >= 0
                    ? '  (' + result.orbits[result.rowOrbit[row]].name.split('  ')[0] + ')' : '')];
            for (const n of names.slice(0, 12)) { const v = result.data.columns[n][row]; best.push(n + ': ' + (isFinite(v) ? fmt(v) : result.data.text(n)[row])); }
            if (names.length > 12) best.push('\u2026 ' + (names.length - 12) + ' more columns');
          }
        }
        last = [px, py];
      }
    }
  }
  return best ? {lines: best} : null;
}

function hoverAt(e) {
  const found = hoverText(e.offsetX, e.offsetY);
  canvas.style.cursor = found && found.pointer ? 'pointer' : state.measure.on ? 'crosshair' : '';
  const front = found && found.path || null;
  if ((front && front.p) !== (state.frontPath && state.frontPath.p)) { state.frontPath = front; draw(); }
  const tip = $('tip');
  if (!found) { if (!tipFor) tip.style.display = 'none'; return; }
  tipFor = null;
  tip.textContent = found.lines.join('\n');
  tip.style.whiteSpace = 'pre-line';
  tip.style.display = 'block';
  const w = tip.offsetWidth, h = tip.offsetHeight;
  tip.style.left = Math.max(4, Math.min(innerWidth - w - 4, e.clientX + 12)) + 'px';
  tip.style.top = (e.clientY - h - 10 < 4 ? e.clientY + 16 : e.clientY - h - 10) + 'px';
}

function drawLegend() {
  const lines = [];
  for (const r of state.results.filter(r => r.visible))
    for (const p of r.paths) lines.push([p.color || r.color, r.name + (r.paths.length > 1 ? ' ' + p.name : ''), DASHES[p.style], {result: r, p}]);
  if (lines.length) drawBox(lines.slice(0, 16), 'top-right', 'legend');
}

function drawKey(keys) { drawBox(keys, 'bottom-left', 'key'); }

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

/* the clock's range across every view: from the earliest start to the latest end, so each view is drawn at the same
   time while the replay runs (a view whose run is over shows all of it) */
function clockRange(mode = replay.mode) {
  let lo = Infinity, hi = -Infinity;
  for (const p of panes) {
    const range = withPane(p, () => replayRange(mode));
    if (range) { lo = Math.min(lo, range[0]); hi = Math.max(hi, range[1]); }
  }
  return isFinite(lo) ? [lo, hi] : null;
}

function canPlayInTurn() { return panes.some(p => withPane(p, () => segments().length > 1)); }

function play(mode = 'together') {
  const rp = state.replay;
  if (rp.state === 'playing' && rp.mode === mode) return;
  if (rp.mode !== mode) { rp.mode = mode; rp.state = 'stopped'; }
  const range = clockRange();
  if (!range) return;
  if (rp.state === 'stopped' || rp.t >= range[1]) rp.t = range[0];
  rp.state = 'playing'; rp.last = performance.now();
  requestAnimationFrame(tick);
  showReplay();
}

function tick() {
  const rp = state.replay, range = clockRange();
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
  const range = clockRange();
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
  if (!g) return word + '  t = ' + fmt(clock) + ' s';
  return word + '  ' + (g.index + 1) + '/' + g.count + '  t = ' + fmt(g.t) + ' of ' + fmt(g.hi) + ' s';
}

/* the label's width: the widest text it can show for these results (every state and mode, t across the run), measured in its own
   font - fixed, so the controls don't change size or wrap as t's digits change during a replay */
let labelFit = {key: null, width: 0};
function fitReplayLabel() {
  const label = $('replayLabel');
  const key = panes.map(p => withPane(p, () => segments().map(g => g.result.file + ':' + g.lo + ':' + g.hi).join())).join('/');
  if (labelFit.key === key) return;
  const ctx = document.createElement('canvas').getContext('2d'), style = getComputedStyle(label);
  ctx.font = style.fontSize + ' ' + style.fontFamily;
  const texts = [STOPPED_LABEL];
  for (const mode of canPlayInTurn() ? ['together', 'sequence'] : ['together']) {    //both, so switching doesn't resize it
    const range = clockRange(mode);
    if (range) for (let i = 0; i <= 400; i++)
      for (const word of ['playing', 'paused']) texts.push(replayLabel(word, range[0] + i / 400 * (range[1] - range[0]), range, mode));
  }
  const width = Math.ceil(Math.max(...texts.map(s => ctx.measureText(s).width)) * 1.04) + 2;
  label.style.width = width + 'px';
  labelFit = {key, width};
}

function showReplay() {
  const rp = state.replay, range = clockRange();
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
  drawAll();
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
  const track = $('pTrack'), rp = state.replay, range = clockRange();
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
  const rp = state.replay, range = clockRange(), el = $('pTime');
  if (!range) { el.textContent = ''; return; }
  const text = (clock, mode) => {
    if (mode !== 'sequence') return fmt(clock) + ' / ' + fmt(range[1]) + ' s';
    const g = currentSegment(clock);
    if (!g) return fmt(clock) + ' s';
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
  tip.style.whiteSpace = 'pre-line';
  tip.style.display = 'block';
  const r = el.getBoundingClientRect(), w = tip.offsetWidth, h = tip.offsetHeight;
  tip.style.left = Math.max(4, Math.min(innerWidth - w - 4, r.left + r.width / 2 - w / 2)) + 'px';
  tip.style.top = (r.top - h - 6 < 4 ? r.bottom + 6 : r.top - h - 6) + 'px';
}
function hideTip() { tipFor = null; $('tip').style.display = 'none'; }

//---------------------------------------------------------------- moving smoothly
/* while the view is being moved (dragged, zoomed, the joystick), redraws wait for the next frame, and what is slow to
   work out (the background's arrow scale, flow lines) is kept from before; a moment after it stops, the view is drawn
   again with everything worked out afresh */
let drawRequest = null, movingUntil = 0, settleTimer = null;
function scheduleDraw() {
  const pane = currentPane();
  if (pane) pane.dirty = true;
  if (drawRequest === null) drawRequest = requestAnimationFrame(() => {
    drawRequest = null;
    for (const p of panes) if (p.dirty) { p.dirty = false; withPane(p, draw); }
  });
}
const interacting = () => performance.now() < movingUntil;
function moved() {
  movingUntil = performance.now() + 180;
  clearTimeout(settleTimer);
  const pane = currentPane();
  settleTimer = setTimeout(() => { if (pane && panes.includes(pane)) withPane(pane, draw); }, 220);
}

//---------------------------------------------------------------- following a body or a path
/* the view kept centred on a body, or on where a path is at the replay's time (its end when stopped): the view's size
   stays as it is, and zooming is about the centre. moving the view by hand stops it */
function stopFollowing() {
  if (!state.follow) return;
  state.follow = null;
  if (!PLAYER && state === active.state) syncFollow();
}

/* the followed thing's place as plotted: [X, Y] (Y null where only X is known), or null */
function followTarget() {
  const f = state.follow, [ax, ay] = axes();
  if (!f) return null;
  if (f.kind === 'body') {
    const env = overlayEnv(), body = env && env.bodies[f.index];
    if (!body) return null;
    if (timeMode()) return [toAxis(Math.hypot(body.x, body.y), ax), null];
    if (ax.kind !== 'position' || ay.kind !== 'position') return null;
    return [toAxis(body.x, ax), toAxis(body.y, ay)];
  }
  const result = state.results.find(r => r.file === f.file && r.visible), p = result && result.paths.find(q => q.name === f.path);
  if (!p) return null;
  plotted(result, p);
  const until = drawUntil(result);
  if (until === false) return null;
  let last = -1;
  for (let i = 0; i < p.px.length; i++) {
    if (!(isFinite(p.px[i]) && isFinite(p.py[i])) || !shownRow(result, i)) continue;
    if (until !== null && p.t && p.t[i] > until) {
      //between the last row and this one, at the replay's time
      if (last >= 0 && i === last + 1 && p.t[i] > p.t[last]) {
        const k = (until - p.t[last]) / (p.t[i] - p.t[last]);
        return [p.px[last] + k * (p.px[i] - p.px[last]), p.py[last] + k * (p.py[i] - p.py[last])];
      }
      break;
    }
    last = i;
  }
  return last >= 0 ? [p.px[last], p.py[last]] : null;
}

function applyFollow() {
  const at = followTarget();
  if (!at) return;
  const v = state.view, hx = (v[1] - v[0]) / 2, hy = (v[3] - v[2]) / 2;
  state.view = [at[0] - hx, at[0] + hx, at[1] === null ? v[2] : at[1] - hy, at[1] === null ? v[3] : at[1] + hy];
}

/* the Centre on menu: nothing, each body of the background drawn, each shown result's paths */
function syncFollow() {
  const menu = $('follow');
  if (!menu) return;
  menu.innerHTML = '';
  menu.add(new Option('nothing (the view stays put)', ''));
  const env = overlayEnv();
  (env ? env.bodies : []).forEach((b, i) => menu.add(new Option('body ' + (i + 1) + ': ' + bodyLabel(b) + (b.black ? ' black' : ''), 'body:' + i)));
  for (const r of state.results.filter(r => r.visible))
    for (const p of r.paths) menu.add(new Option('path: ' + r.name + (r.paths.length > 1 ? ' ' + p.name : ''), 'path:' + r.file + '\n' + p.name));
  const f = state.follow, value = !f ? '' : f.kind === 'body' ? 'body:' + f.index : 'path:' + f.file + '\n' + f.path;
  menu.value = [...menu.options].some(o => o.value === value) ? value : '';
}

function chooseFollow(value) {
  if (!value) state.follow = null;
  else if (value.startsWith('body:')) state.follow = {kind: 'body', index: +value.slice(5)};
  else { const [file, path] = value.slice(5).split('\n'); state.follow = {kind: 'path', file, path}; }
  draw();
}

//---------------------------------------------------------------- measuring
/* the measuring tool: a click puts a point on the plot (on the nearest path's row, if one is within a few pixels, else
   where the click was); two points give the distance between them. a third click starts again. a point can also be put
   on the selected result's row at a time typed in */
function nearestRow(sx, sy) {
  let best = null, bestD = 8;
  for (const result of state.results.filter(r => r.visible)) {
    const until = drawUntil(result);
    if (until === false) continue;
    for (const p of result.paths) {
      plotted(result, p);
      for (let i = 0; i < p.px.length; i++) {
        if (until !== null && p.t && p.t[i] > until) break;
        if (!(isFinite(p.px[i]) && isFinite(p.py[i])) || !shownRow(result, i)) continue;
        const [qx, qy] = toScreen(p.px[i], p.py[i]), d = Math.hypot(sx - qx, sy - qy);
        if (d < bestD) { bestD = d; best = {file: result.file, path: p.name, row: i}; }
      }
    }
  }
  return best;
}

function measureAt(sx, sy) {
  const m = state.measure;
  if (m.points.length >= 2) m.points = [];
  const row = nearestRow(sx, sy);
  if (row) m.points.push(row);
  else { const [X, Y] = toData(sx, sy); m.points.push({X, Y}); }
  showMeasure(); draw();
}

/* a measured point as plotted, with its row's result and path if it has one */
function measurePoint(pt) {
  if (pt.row === undefined) return {X: pt.X, Y: pt.Y};
  const result = state.results.find(r => r.file === pt.file), p = result && result.paths.find(q => q.name === pt.path);
  if (!p) return null;
  plotted(result, p);
  return {X: p.px[pt.row], Y: p.py[pt.row], result, p, row: pt.row};
}

function pinRowAt() {
  const r = state.selected, T = +$('measureT').value, name = r && timeColumnOf(r, 't');
  if (!r || !name || !isFinite(T)) { message(r && !name ? 'the selected result has no t column' : 'type a time in seconds'); return; }
  const t = r.data.columns[name];
  let best = -1;
  for (let i = 0; i < t.length; i++) if (isFinite(t[i]) && (best < 0 || Math.abs(t[i] - T) < Math.abs(t[best] - T))) best = i;
  if (best < 0) return;
  const m = state.measure;
  if (m.points.length >= 2) m.points = [];
  m.points.push({file: r.file, path: r.paths[0].name, row: best});
  showMeasure(); draw();
}

/* the points, the line between them and a label, drawn on the plot */
function drawMeasure() {
  const pts = state.measure.points.map(measurePoint).filter(Boolean);
  if (!pts.length) return;
  const screen = pts.map(q => toScreen(q.X, q.Y));
  ctx.strokeStyle = css('--accent'); ctx.fillStyle = css('--accent'); ctx.lineWidth = 1.5; ctx.setLineDash([]);
  if (screen.length === 2) { ctx.setLineDash([5, 3]); line(screen[0][0], screen[0][1], screen[1][0], screen[1][1]); ctx.setLineDash([]); }
  screen.forEach(([sx, sy], i) => {
    ctx.beginPath(); ctx.arc(sx, sy, 5, 0, 2 * Math.PI); ctx.stroke();
    line(sx - 8, sy, sx + 8, sy); line(sx, sy - 8, sx, sy + 8);
    ctx.font = 'bold 11px -apple-system, Helvetica, Arial, sans-serif'; ctx.textAlign = 'left'; ctx.textBaseline = 'bottom';
    ctx.fillText('AB'[i], sx + 6, sy - 5);
  });
  if (screen.length === 2) {
    const text = measureLines().distance;
    if (text) {
      const mx = (screen[0][0] + screen[1][0]) / 2, my = (screen[0][1] + screen[1][1]) / 2;
      ctx.font = '11px -apple-system, Helvetica, Arial, sans-serif';
      const w = ctx.measureText(text).width;
      ctx.fillStyle = css('--surface'); ctx.fillRect(mx - w / 2 - 4, my - 9, w + 8, 18);
      ctx.strokeStyle = css('--accent'); ctx.lineWidth = 1; ctx.strokeRect(mx - w / 2 - 4, my - 9, w + 8, 18);
      ctx.fillStyle = css('--ink'); ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(text, mx, my);
    }
  }
}

/* what the measured points say: each point's lines, and the distance between them */
function measureLines() {
  const pts = state.measure.points.map(measurePoint).filter(Boolean), [ax, ay] = axes(), out = {points: [], distance: ''};
  const value = (v, a) => a.log ? Math.pow(10, v) : v / a.scale, unitOf = a => (a.label.match(/\(([^)]*)\)/) || [])[1] || '';
  pts.forEach((q, i) => {
    const lines = ['ABCD'[i] + ': ' + ax.label.replace('  [log]', '') + ' ' + fmt(value(q.X, ax)) + ', ' + ay.label.replace('  [log]', '') + ' ' + fmt(value(q.Y, ay))];
    if (q.result) {
      const t = timeColumnOf(q.result, 't');
      lines.push('   ' + q.result.name + (q.result.paths.length > 1 ? ' ' + q.p.name : '') + ', row ' + (q.row + 1) +
                 (t ? ', t = ' + fmt(q.result.data.columns[t][q.row]) + ' s' : ''));
    }
    out.points.push(...lines);
  });
  if (pts.length === 2) {
    const [a, b] = pts;
    if (!ax.log && !ay.log && ax.kind === ay.kind && ax.scale === ay.scale && ax.kind !== 'time')
      out.distance = 'AB = ' + fmt(Math.hypot(b.X - a.X, b.Y - a.Y) / ax.scale) + ' ' + unitOf(ax);
    else out.distance = (ax.log ? 'x × ' + fmt(value(b.X, ax) / value(a.X, ax)) : 'Δx = ' + fmt(value(b.X, ax) - value(a.X, ax)) + ' ' + unitOf(ax)) + ',  ' +
                        (ay.log ? 'y × ' + fmt(value(b.Y, ay) / value(a.Y, ay)) : 'Δy = ' + fmt(value(b.Y, ay) - value(a.Y, ay)) + ' ' + unitOf(ay));
    const ta = a.result && timeColumnOf(a.result, 't'), tb = b.result && timeColumnOf(b.result, 't');
    if (ta && tb) out.distance += ',  Δt = ' + fmt(b.result.data.columns[tb][b.row] - a.result.data.columns[ta][a.row]) + ' s';
  }
  return out;
}

function showMeasure() {
  if (PLAYER || !$('measureOut') || state !== active.state) return;
  const m = state.measure, lines = measureLines();
  $('measure').setAttribute('aria-pressed', String(m.on));
  $('measure').textContent = m.on ? 'Measuring: on' : 'Measure';
  $('measureOut').textContent = lines.points.length ? [...lines.points, lines.distance].filter(Boolean).join('\n')
                                : m.on ? 'Click the plot to put point A, then B. Esc clears them.' : '';
}

//---------------------------------------------------------------- results made from others (Add…)
/* new results worked out from the open ones, each a value against t, chosen in the Add dialog:
   - difference: at each row of a result, another result at the same t (interpolated), and the difference between them
   - orbits: a value for each whole orbit of a result, at the orbit's periapsis, apoapsis or end (from the orbits its
     log gives): how its closest and farthest points, their directions, its period and shape change
   - path: a value at each row of a result: its distances, speeds and the angle it has gone round
   distances and angles are from the result's first body (the origin if it has none). each is kept as {kind, a, b,
   column} on the result, so it is made again after a reload, in a link and in a copied view */
const DERIVED = {
  difference: {
    apart: ['distance apart', 'How far apart the two are, |rA − rB|'],
    radial: ['difference in distance from origin', 'The first one\'s distance from the origin less the second one\'s'],
    dx: ['difference in x', 'The first one\'s x less the second one\'s'],
    dy: ['difference in y', 'The first one\'s y less the second one\'s'],
  },
  orbits: {
    periDistance: ['periapsis distance', 'Each orbit\'s closest distance to the body, at the time of its periapsis'],
    apoDistance: ['apoapsis distance', 'Each orbit\'s farthest distance from the body, at the time of its apoapsis'],
    periAngle: ['periapsis direction (deg)', 'The direction of each orbit\'s periapsis from the body, in degrees, counted on round: its rise is the orbit\'s precession'],
    apoAngle: ['apoapsis direction (deg)', 'The direction of each orbit\'s apoapsis from the body, in degrees, counted on round'],
    precession: ['periapsis shift per orbit (arcsec)', 'How far each orbit\'s periapsis has turned since the last orbit\'s, in seconds of arc'],
    period: ['period (days)', 'Each orbit\'s time from start to end, in days, at its end'],
    eccentricity: ['eccentricity (ratio)', 'Each orbit\'s (apoapsis − periapsis) / (apoapsis + periapsis), at its end'],
    semiMajor: ['semi-major axis', 'Each orbit\'s (periapsis + apoapsis) / 2, at its end'],
  },
  path: {
    origin: ['distance from origin', 'How far the path is from the origin, at each row'],
    body: ['distance from body', 'How far the path is from the result\'s first body, at each row'],
    speed: ['speed (m/s)', 'The path\'s speed, from its velocity columns (or the change between rows)'],
    radial: ['radial speed (m/s)', 'How fast the path moves away from the body (negative: towards it)'],
    angle: ['angle round body (deg)', 'How far the path has gone round the body since it started, in degrees, counted on round'],
  },
};
const DERIVED_KINDS = {difference: 'Difference', orbits: 'Each orbit', path: 'Along the path'};

/* a result's centre for distances and angles: its first body, or the origin */
function centreOf(r) {
  const body = r.env && r.env.bodies && r.env.bodies[0];
  return body ? [body.x, body.y] : [0, 0];
}

/* angles (radians, -pi..pi) counted on round, in degrees */
function unwrapDegrees(angles) {
  const out = [];
  let last = null, turned = 0;
  for (const a of angles) {
    if (!isFinite(a)) { out.push(NaN); continue; }
    if (last !== null) turned += ((a - last + 3 * Math.PI) % (2 * Math.PI)) - Math.PI;
    else turned = a;
    last = a;
    out.push(turned * 180 / Math.PI);
  }
  return out;
}

/* the columns {t, value} for a choice, or a reason there are none */
function derivedColumns(spec) {
  const a = state.results.find(r => r.file === spec.a), [label] = DERIVED[spec.kind][spec.column];
  if (!a) return 'the result it was made from is not open';
  const ta = timeColumnOf(a, 't'), pa = a.paths[0];
  if (!ta || !pa) return a.name + ' has no t column';
  const t = a.data.columns[ta], [cx, cy] = centreOf(a);
  if (spec.kind === 'difference') {
    const b = state.results.find(r => r.file === spec.b), tb = b && timeColumnOf(b, 't');
    if (!b || !tb) return 'the second result has no t column';
    const pb = b.paths[0], tB = b.data.columns[tb];
    const order = [...tB.keys()].filter(i => isFinite(tB[i]) && isFinite(pb.x[i]) && isFinite(pb.y[i])).sort((i, j) => tB[i] - tB[j]);
    const at = (xs, T) => {
      let lo = 0, hi = order.length - 1;
      if (!order.length || T < tB[order[0]] || T > tB[order[hi]]) return NaN;
      while (hi - lo > 1) { const mid = (lo + hi) >> 1; if (tB[order[mid]] <= T) lo = mid; else hi = mid; }
      const i = order[lo], j = order[hi], f = tB[j] === tB[i] ? 0 : (T - tB[i]) / (tB[j] - tB[i]);
      return xs[i] + f * (xs[j] - xs[i]);
    };
    const T = [], V = [];
    for (let i = 0; i < t.length; i++) {
      const xb = at(pb.x, t[i]), yb = at(pb.y, t[i]);
      if (!(isFinite(t[i]) && isFinite(pa.x[i]) && isFinite(xb))) continue;
      T.push(t[i]);
      V.push({apart: Math.hypot(pa.x[i] - xb, pa.y[i] - yb), radial: Math.hypot(pa.x[i], pa.y[i]) - Math.hypot(xb, yb),
              dx: pa.x[i] - xb, dy: pa.y[i] - yb}[spec.column]);
    }
    return {t: T, v: V, label, name: a.name + ' − ' + b.name + ': ' + label};
  }
  if (spec.kind === 'orbits') {
    const whole = (a.orbits || []).filter(o => o.full && o.peri && o.apo);
    if (!whole.length) return a.name + ' has no whole orbits in its log';
    const dist = q => Math.hypot(q.x - cx, q.y - cy), angle = q => Math.atan2(q.y - cy, q.x - cx);
    const periAngles = unwrapDegrees(whole.map(o => angle(o.peri)));
    const T = [], V = [];
    whole.forEach((o, k) => {
      const rp = dist(o.peri), ra = dist(o.apo);
      const value = {periDistance: [o.peri.t, rp], apoDistance: [o.apo.t, ra], periAngle: [o.peri.t, periAngles[k]],
                     apoAngle: [o.apo.t, null], precession: [o.peri.t, k ? (periAngles[k] - periAngles[k - 1]) * 3600 : NaN],
                     period: [o.t1, (o.t1 - o.t0) / 86400], eccentricity: [o.t1, (ra - rp) / (ra + rp)], semiMajor: [o.t1, (ra + rp) / 2]}[spec.column];
      T.push(value[0]); V.push(value[1]);
    });
    if (spec.column === 'apoAngle') unwrapDegrees(whole.map(o => angle(o.apo))).forEach((v, k) => { V[k] = v; });
    //in order of time, those with a value
    const rows = T.map((x, k) => [x, V[k]]).filter(([x, v]) => isFinite(x) && isFinite(v)).sort((p, q) => p[0] - q[0]);
    return {t: rows.map(r => r[0]), v: rows.map(r => r[1]), label, name: a.name + ': ' + label, dots: true};
  }
  //along the path
  const v = velocityPair(a), n = t.length, V = new Array(n).fill(NaN);
  const vel = i => {
    if (v) return [a.data.columns[v[1]][i], a.data.columns[v[2]][i]];
    const j = i + 1 < n && isFinite(pa.x[i + 1]) ? i + 1 : i - 1;
    if (j < 0 || !isFinite(pa.x[j]) || t[j] === t[i]) return [NaN, NaN];
    const [p, q] = j > i ? [i, j] : [j, i];
    return [(pa.x[q] - pa.x[p]) / (t[q] - t[p]), (pa.y[q] - pa.y[p]) / (t[q] - t[p])];
  };
  if (spec.column === 'angle') unwrapDegrees(Array.from(pa.x, (x, i) => Math.atan2(pa.y[i] - cy, x - cx))).forEach((d, i) => { V[i] = d; });
  else for (let i = 0; i < n; i++) {
    const dx = pa.x[i] - cx, dy = pa.y[i] - cy, d = Math.hypot(dx, dy);
    if (spec.column === 'origin') V[i] = Math.hypot(pa.x[i], pa.y[i]);
    else if (spec.column === 'body') V[i] = d;
    else { const [vx, vy] = vel(i); V[i] = spec.column === 'speed' ? Math.hypot(vx, vy) : (vx * dx + vy * dy) / d; }
  }
  const T = [], W = [];
  for (let i = 0; i < n; i++) if (isFinite(t[i]) && isFinite(V[i])) { T.push(t[i]); W.push(V[i]); }
  return {t: T, v: W, label, name: a.name + ': ' + label};
}

/* the result for a choice: its columns as a csv's, drawn as value against t, or null (with a message) */
function makeDerived(spec) {
  const made = derivedColumns(spec);
  if (typeof made === 'string') { message(made); return null; }
  if (!made.t.length) { message('no values for ' + DERIVED[spec.kind][spec.column][0]); return null; }
  const cols = {t: Float64Array.from(made.t), [made.label]: Float64Array.from(made.v)};
  const data = {names: Object.keys(cols), columns: cols, rows: made.t.length, text: name => Array.from(cols[name], x => isFinite(x) ? String(x) : '')};
  const log = {bodies: [], orbitEnds: [], text: 'Made in the viewer from ' + spec.a + (spec.b ? ' and ' + spec.b : '') + ': ' + made.label +
               ' against t (' + DERIVED_KINDS[spec.kind].toLowerCase() + ').'};
  const result = {name: made.name, file: 'added: ' + [spec.kind, spec.a, spec.b || '', spec.column].join(' | '), data, log, visible: true,
                  color: SERIES[state.results.length % SERIES.length], source: null, ends: false, orbitEvery: 1, dots: !!made.dots,
                  tangent: {on: false, t: null, color: null, style: 'dashed'}, derived: {kind: spec.kind, a: spec.a, b: spec.b || null, column: spec.column}};
  result.paths = buildPaths(result, {selection: [['t', made.label]]});
  result.env = environmentFor(log, new Map());
  result.orbits = [];
  return result;
}

/* the dialog's choices added as results (any already open replaced), the last selected */
function addDerived(specs) {
  let last = null;
  for (const spec of specs) {
    const r = makeDerived(spec);
    if (!r) continue;
    state.results = state.results.filter(x => x.file !== r.file);
    state.results.push(r);
    last = r;
  }
  if (!last) return false;
  state.selected = last;
  if (timeMode()) message('added results are drawn against t: choose the x / y view (View tab) to see them');
  resultsChanged(); fit();
  return true;
}

/* added results made again after a reload or from a link */
function remakeDerived(list) {
  for (const d of list) {
    const r = makeDerived(d.kind ? d : {kind: 'difference', ...d});   //older links: differences only
    if (r && d.settings) Object.assign(r, {visible: d.settings.visible});
    if (r) state.results.push(r);
  }
}
const derivedList = st => st.results.filter(r => r.derived).map(r => ({...r.derived, settings: {visible: r.visible}}));

/* the Add dialog: what kind of result, made from which, and which values (several at once) */
function openAddDialog() {
  const dialog = $('addDialog'), base = state.results.filter(r => !r.derived);
  if (!base.length) { message('open a run first'); return; }
  const kind = $('addKind'), from = $('addFrom'), other = $('addOther'), values = $('addValues');
  from.innerHTML = ''; other.innerHTML = '';
  for (const r of base) { from.add(new Option(r.name, r.file)); other.add(new Option(r.name, r.file)); }
  if (state.selected && !state.selected.derived) from.value = state.selected.file;
  const show = () => {
    const k = kind.value, a = base.find(r => r.file === from.value);
    $('addOtherRow').style.display = k === 'difference' ? '' : 'none';
    if (k === 'difference' && other.value === from.value) other.value = (base.find(r => r.file !== from.value) || {}).file || '';
    values.innerHTML = '';
    for (const [column, [label, tip]] of Object.entries(DERIVED[k])) {
      const why = !a ? '' : !timeColumnOf(a, 't') ? 'it has no t column'
                : k === 'orbits' && !(a.orbits || []).some(o => o.full && o.peri) ? 'its log has no whole orbits'
                : k === 'path' && (column === 'body' || column === 'radial' || column === 'angle') && !(a.env && a.env.bodies.length) ? 'it has no bodies (the origin is used)' : '';
      const box = Object.assign(document.createElement('input'), {type: 'checkbox', value: column, disabled: why && !why.includes('origin')});
      const line = document.createElement('label');
      line.className = 'check'; line.dataset.tip = tip + (why ? '. ' + (why.includes('origin') ? 'Note: ' : 'Not available: ') + why : '');
      line.append(box, ' ' + label);
      values.append(line);
    }
    $('addNote').textContent = {difference: 'The first result less the second, at the first one\'s times (the second interpolated to them).',
                                orbits: 'One value for each whole orbit the result\'s log gives, measured from its first body.',
                                path: 'A value at each row of the result\'s first path, measured from its first body.'}[k];
  };
  kind.onchange = from.onchange = other.onchange = show;
  show();
  $('addOk').onclick = e => {
    e.preventDefault();
    const chosen = [...values.querySelectorAll('input:checked')].map(b => b.value);
    if (!chosen.length) { $('addNote').textContent = 'Tick at least one value.'; return; }
    if (kind.value === 'difference' && other.value === from.value) { $('addNote').textContent = 'Choose two different results.'; return; }
    if (addDerived(chosen.map(column => ({kind: kind.value, a: from.value, b: kind.value === 'difference' ? other.value : null, column})))) dialog.close();
  };
  $('addCancel').onclick = () => dialog.close();
  //hover help over the dialog: the tip goes into it while it is open (a modal dialog is drawn over everything else)
  dialog.append($('tip'));
  dialog.onclose = () => { hideTip(); $('app').append($('tip')); };
  dialog.showModal();
}

//---------------------------------------------------------------- export
function download(blob, name) {
  const a = Object.assign(document.createElement('a'), {href: URL.createObjectURL(blob), download: name});
  document.body.append(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 2000);
}
const exportName = ext => (state.results.length === 1 ? state.results[0].name : (state.sources[0] && state.sources[0].fullName || 'plot').replace(/\.full\.json$/, '')) + '.' + ext;

/* the selected view as a picture: the plot and what moves over it, as they are now */
function exportPng() {
  const out = document.createElement('canvas');
  out.width = canvas.width; out.height = canvas.height;
  const c = out.getContext('2d');
  c.drawImage(canvas, 0, 0);
  if (overlay.width === canvas.width) c.drawImage(overlay, 0, 0);
  out.toBlob(blob => download(blob, exportName('png')), 'image/png');
}

/* the selected view drawn again into an SVG (SvgContext stands in for the canvas), so it can be scaled and edited */
function exportSvg() {
  const w = canvas.clientWidth, h = canvas.clientHeight, svg = new SvgContext(w, h), real = ctx;
  ctx = svg;
  try {
    draw();
    for (const {sx, sy, body} of state.spinning) {   //spinning bodies, still
      ctx.fillStyle = body.black ? '#111' : '#fff'; ctx.strokeStyle = css('--ink'); ctx.lineWidth = 1;
      ctx.beginPath(); ctx.arc(sx, sy, 10, 0, 2 * Math.PI); ctx.fill(); ctx.stroke();
      ctx.strokeStyle = css('--ink'); ctx.fillStyle = css('--ink'); ctx.lineWidth = 1.4;
      twistArc(ctx, sx, sy, 15, 1.5 * Math.PI, body.spin > 0, 7);
    }
  } finally { ctx = real; draw(); }
  download(new Blob([svg.toString()], {type: 'image/svg+xml'}), exportName('svg'));
}

/* the shown rows of the shown results (not in hidden orbits; up to the replay's time while it runs), one csv, with a
   column naming each row's result */
function exportCsv() {
  const shown = state.results.filter(r => r.visible), names = [...new Set(shown.flatMap(r => r.data.names))];
  const quote = v => /[",\n]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v;
  const lines = [['result', ...names].map(quote).join(',')];
  for (const r of shown) {
    const until = drawUntil(r), t = r.paths[0] && r.paths[0].t;
    if (until === false) continue;
    for (let i = 0; i < r.data.rows; i++) {
      if (!shownRow(r, i) || (until !== null && t && t[i] > until)) continue;
      lines.push([quote(r.name), ...names.map(n => r.data.columns[n] ? quote(r.data.text(n)[i] || '') : '')].join(','));
    }
  }
  download(new Blob([lines.join('\n') + '\n'], {type: 'text/csv'}), exportName('csv'));
}

/* a stand-in for a canvas's 2d context that writes SVG: the drawing calls the viewer makes, arcs and ellipses as short
   straight pieces, text as text */
class SvgContext {
  constructor(w, h) {
    this.w = w; this.h = h; this.defs = []; this.root = {open: '', children: []}; this.ids = 0;
    this.st = {m: [1, 0, 0, 1, 0, 0], group: this.root, fillStyle: '#000', strokeStyle: '#000', lineWidth: 1, globalAlpha: 1, dash: [],
               font: '10px sans-serif', textAlign: 'start', textBaseline: 'alphabetic', lineCap: 'butt', lineJoin: 'miter'};
    this.stack = []; this.d = ''; this.at = null;
    this.measure = document.createElement('canvas').getContext('2d');
  }
  get fillStyle() { return this.st.fillStyle; } set fillStyle(v) { this.st.fillStyle = v; }
  get strokeStyle() { return this.st.strokeStyle; } set strokeStyle(v) { this.st.strokeStyle = v; }
  get lineWidth() { return this.st.lineWidth; } set lineWidth(v) { this.st.lineWidth = v; }
  get globalAlpha() { return this.st.globalAlpha; } set globalAlpha(v) { this.st.globalAlpha = v; }
  get font() { return this.st.font; } set font(v) { this.st.font = v; }
  get textAlign() { return this.st.textAlign; } set textAlign(v) { this.st.textAlign = v; }
  get textBaseline() { return this.st.textBaseline; } set textBaseline(v) { this.st.textBaseline = v; }
  get lineCap() { return this.st.lineCap; } set lineCap(v) { this.st.lineCap = v; }
  get lineJoin() { return this.st.lineJoin; } set lineJoin(v) { this.st.lineJoin = v; }
  setLineDash(d) { this.st.dash = d.slice(); }
  setTransform() { this.st.m = [1, 0, 0, 1, 0, 0]; }   //the device-pixel scale: not wanted in an SVG
  save() { this.stack.push({...this.st, m: this.st.m.slice(), dash: this.st.dash.slice()}); }
  restore() { if (this.stack.length) this.st = this.stack.pop(); }
  transform(a, b, c, d, e, f) { const m = this.st.m; this.st.m = [m[0] * a + m[2] * b, m[1] * a + m[3] * b, m[0] * c + m[2] * d, m[1] * c + m[3] * d, m[0] * e + m[2] * f + m[4], m[1] * e + m[3] * f + m[5]]; }
  translate(x, y) { this.transform(1, 0, 0, 1, x, y); }
  rotate(a) { const c = Math.cos(a), s = Math.sin(a); this.transform(c, s, -s, c, 0, 0); }
  pt(x, y) { const m = this.st.m; return [m[0] * x + m[2] * y + m[4], m[1] * x + m[3] * y + m[5]]; }
  n(v) { return Math.round(v * 100) / 100; }
  beginPath() { this.d = ''; this.at = null; }
  moveTo(x, y) { const [a, b] = this.pt(x, y); this.d += 'M' + this.n(a) + ' ' + this.n(b); this.at = [x, y]; this.start = [x, y]; }
  lineTo(x, y) { if (!this.at) { this.moveTo(x, y); return; } const [a, b] = this.pt(x, y); this.d += 'L' + this.n(a) + ' ' + this.n(b); this.at = [x, y]; }
  closePath() { this.d += 'Z'; if (this.start) this.at = this.start; }
  rect(x, y, w, h) { this.moveTo(x, y); this.lineTo(x + w, y); this.lineTo(x + w, y + h); this.lineTo(x, y + h); this.closePath(); }
  ellipse(cx, cy, rx, ry, rot, a0, a1, anticlockwise) {
    let sweep = a1 - a0;
    if (anticlockwise && sweep > 0) sweep -= 2 * Math.PI * Math.ceil(sweep / (2 * Math.PI));
    if (!anticlockwise && sweep < 0) sweep += 2 * Math.PI * Math.ceil(-sweep / (2 * Math.PI));
    if (Math.abs(sweep) > 2 * Math.PI) sweep = Math.sign(sweep) * 2 * Math.PI;
    const steps = Math.max(8, Math.min(180, Math.ceil(Math.abs(sweep) * Math.max(rx, ry) / 2))), c = Math.cos(rot), s = Math.sin(rot);
    for (let k = 0; k <= steps; k++) {
      const a = a0 + sweep * k / steps, ex = rx * Math.cos(a), ey = ry * Math.sin(a), x = cx + c * ex - s * ey, y = cy + s * ex + c * ey;
      if (k === 0 && this.at) this.lineTo(x, y); else if (k === 0) this.moveTo(x, y); else this.lineTo(x, y);
    }
  }
  arc(cx, cy, r, a0, a1, anticlockwise) { this.ellipse(cx, cy, r, r, 0, a0, a1, anticlockwise); }
  esc(t) { return String(t).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;'); }
  paint(kind) {
    if (!this.d) return;
    const st = this.st, alpha = st.globalAlpha < 1 ? ' opacity="' + this.n(st.globalAlpha) + '"' : '';
    if (kind === 'fill') this.add('<path d="' + this.d + '" fill="' + this.esc(st.fillStyle) + '"' + alpha + '/>');
    else this.add('<path d="' + this.d + '" fill="none" stroke="' + this.esc(st.strokeStyle) + '" stroke-width="' + this.n(st.lineWidth) + '"' +
                  (st.dash.length ? ' stroke-dasharray="' + st.dash.join(' ') + '"' : '') + (st.lineCap !== 'butt' ? ' stroke-linecap="' + st.lineCap + '"' : '') +
                  (st.lineJoin !== 'miter' ? ' stroke-linejoin="' + st.lineJoin + '"' : '') + alpha + '/>');
  }
  add(el) { this.st.group.children.push(el); }
  fill() { this.paint('fill'); }
  stroke() { this.paint('stroke'); }
  fillRect(x, y, w, h) { const d = this.d, at = this.at; this.beginPath(); this.rect(x, y, w, h); this.fill(); this.d = d; this.at = at; }
  strokeRect(x, y, w, h) { const d = this.d, at = this.at; this.beginPath(); this.rect(x, y, w, h); this.stroke(); this.d = d; this.at = at; }
  clearRect() {}
  clip() {
    const id = 'c' + (++this.ids);
    this.defs.push('<clipPath id="' + id + '"><path d="' + this.d + '"/></clipPath>');
    const group = {open: '<g clip-path="url(#' + id + ')">', children: []};
    this.st.group.children.push(group);
    this.st.group = group;
  }
  measureText(t) { this.measure.font = this.st.font; return this.measure.measureText(t); }
  fillText(text, x, y) {
    const st = this.st, size = +(st.font.match(/(\d+(?:\.\d+)?)px/) || [0, 10])[1], bold = /bold/.test(st.font);
    const anchor = {center: 'middle', right: 'end', end: 'end'}[st.textAlign] || 'start';
    const shift = {top: 0.8, middle: 0.35, bottom: -0.2, alphabetic: 0}[st.textBaseline] || 0, m = st.m;
    this.add('<text transform="matrix(' + m.map(v => this.n(v)).join(' ') + ')" x="' + this.n(x) + '" y="' + this.n(y + shift * size) + '" font-size="' + size +
             '" font-family="-apple-system, Helvetica, Arial, sans-serif"' + (bold ? ' font-weight="bold"' : '') + ' text-anchor="' + anchor + '" fill="' +
             this.esc(st.fillStyle) + '"' + (st.globalAlpha < 1 ? ' opacity="' + this.n(st.globalAlpha) + '"' : '') + ' xml:space="preserve">' + this.esc(text) + '</text>');
  }
  toString() {
    const out = g => g.open + g.children.map(c => typeof c === 'string' ? c : out(c)).join('\n') + (g.open ? '</g>' : '');
    return '<svg xmlns="http://www.w3.org/2000/svg" width="' + this.w + '" height="' + this.h + '" viewBox="0 0 ' + this.w + ' ' + this.h + '">\n<defs>' +
           this.defs.join('') + '</defs>\n' + out(this.root) + '\n</svg>\n';
  }
}

//---------------------------------------------------------------- links
/* the views as they are, in the address: each view's runs (only runs the viewer reads from a web address can be
   linked), settings, framing and what it follows, and each result's options; and the background layers' looks. the
   link's state is compressed where the browser can */
function linkPaths(url) {
  //a run's address relative to the viewer's own folder, so a link or an embedded player works where the site is
  const here = new URL('.', location.href), there = new URL(url, location.href);
  if (there.origin !== here.origin) return there.href;
  const from = here.pathname.split('/').filter(Boolean), to = there.pathname.split('/').filter(Boolean);
  let k = 0;
  while (k < from.length && k < to.length - 1 && from[k] === to[k]) k++;
  return '../'.repeat(from.length - k) + to.slice(k).join('/');
}

function viewLinkState() {
  const views = [];
  for (const p of panes) {
    const st = p.state;
    if (!st.sources.length) continue;
    if (st.sources.some(s => !s.source.url)) return {error: 'only runs opened from a web address can be linked (not a folder from this computer)'};
    const prefs = {};
    for (const [k, v] of Object.entries(st.prefs)) if (PREFS[k] !== v) prefs[k] = v;
    const results = {};
    for (const r of st.results.filter(r => !r.derived)) results[r.file] = resultSettings(r);
    views.push({runs: st.sources.map(s => [linkPaths(new URL(s.fullName || '', s.source.url).href), s.fullName]), prefs, results,
                view: st.view, background: st.background, timeInterval: st.timeInterval, follow: st.follow,
                selected: st.selected && st.selected.file, differences: derivedList(st)});
  }
  if (!views.length) return {error: 'nothing open to link to'};
  return {v: 1, views, active: Math.max(0, panes.indexOf(active)), layers: sharedLayers};
}

async function encodeState(obj) {
  const bytes = new TextEncoder().encode(JSON.stringify(obj));
  const b64 = u8 => btoa(String.fromCharCode(...u8)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
  if (window.CompressionStream) {
    try {
      const packed = new Uint8Array(await new Response(new Blob([bytes]).stream().pipeThrough(new CompressionStream('deflate-raw'))).arrayBuffer());
      return 'z' + b64(packed);
    } catch (e) { /* plain, below */ }
  }
  return 'j' + b64(bytes);
}

async function decodeState(text) {
  const raw = atob(text.slice(1).replace(/-/g, '+').replace(/_/g, '/')), bytes = Uint8Array.from(raw, ch => ch.charCodeAt(0));
  const plain = text[0] === 'z' ? new Uint8Array(await new Response(new Blob([bytes]).stream().pipeThrough(new DecompressionStream('deflate-raw'))).arrayBuffer()) : bytes;
  return JSON.parse(new TextDecoder().decode(plain));
}

async function copyText(text, what) {
  try { await navigator.clipboard.writeText(text); message(what + ' copied'); }
  catch (e) { window.prompt('Copy the ' + what.toLowerCase() + ':', text); }
}

async function copyLink(embed) {
  const linked = viewLinkState();
  if (linked.error) { message(linked.error); return; }
  const code = await encodeState(linked), url = new URL(location.href);
  url.search = '';
  if (embed) {
    const src = '../viewer/index.html?player&state=' + code;
    copyText('<iframe src="' + src + '" width="100%" height="520"\n        loading="lazy" title="What the run shows"></iframe>', 'Player embed');
  } else {
    url.searchParams.set('state', code);
    copyText(url.href.replace('state=' + encodeURIComponent(code), 'state=' + code), 'Link');
  }
}

/* open the views a link holds */
async function openLinked(linked) {
  while (panes.length < linked.views.length) addPane(makeState());
  Object.assign(sharedLayers, linked.layers || {});
  for (const [i, saved] of linked.views.entries()) {
    const pane = panes[i], keep = new Map(Object.entries(saved.results || {}));
    for (const [k, [path, fullName]] of saved.runs.entries()) {
      const url = new URL(path, location.href);
      usePane(pane);
      const source = urlSource(new URL('.', url));
      await loadRun(source, url.pathname.split('/').pop() || fullName, {add: k > 0, keep});
    }
    withPane(pane, () => {
      state.prefs = {...PREFS, ...(saved.prefs || {})};
      state.background = saved.background || state.background;
      state.timeInterval = saved.timeInterval || '';
      state.follow = saved.follow || null;
      remakeDerived(saved.differences || []);
      state.selected = state.results.find(r => r.file === saved.selected) || state.results[0] || null;
      invalidatePlot(); state.marks.key = null;
      if (saved.view) { state.view = saved.view.slice(); state.keepView = true; equalise(); } else fit();
    });
  }
  activate(panes[Math.min(linked.active || 0, panes.length - 1)]);
  syncControls(); drawAll();
}

//---------------------------------------------------------------- controls

function message(text) { $('message').textContent = text; }

//the checkboxes that are just a display option, by the option's name
const OPTION_BOXES = ['showFlow', 'showGravity', 'showScalar', 'showTwist', 'showSeam', 'showBodies', 'showSchwarzschild', 'showSpin',
                      'showGrid', 'showPathLegend', 'showPeri', 'showApo', 'showFieldKey', 'showMarkers', 'showTimeMarks', 'showContours',
                      'showFlowLines', 'showSpecialOrbits', 'showCones', 'showMarkNote', 'showMarkLabels', 'showBodyLabels', 'reverseX',
                      'showInfallArrows', 'showInfallRings'];
//those that change what is plotted (the paths' plotted values), or the aspect
const PLOT_BOXES = ['logX', 'logY', 'ctTime', 'equalAspect'];
const LEGEND_BOXES = ['showPathLegend', 'showFieldKey', 'showMarkNote', 'showMarkLabels', 'showBodyLabels'];

function syncControls() {
  for (const id of [...OPTION_BOXES, ...PLOT_BOXES]) $(id).checked = !!state.prefs[id];
  $('unit').value = state.prefs.unit;
  $('mode').value = timeMode() ? 'time' : 'xy';
  document.body.classList.toggle('time', timeMode());
  $('loop').checked = !!state.prefs.replayLoop;
  $('speed').value = SPEEDS.includes(String(state.prefs.replaySpeed)) ? String(state.prefs.replaySpeed) : '1';
  $('pSpeed').value = $('speed').value;
  //time columns: only those the open results have
  const options = Object.keys(TIME_OPTIONS).filter(o => state.results.some(r => timeColumnOf(r, o)));
  const column = $('timeColumn');
  column.innerHTML = '';
  for (const o of options.length ? options : ['t']) column.add(new Option(TIME_LABELS[o], o));
  if (options.length && !options.includes(state.prefs.timeColumn)) state.prefs.timeColumn = options[0];
  column.value = state.prefs.timeColumn;
  $('timeColumnLabel').textContent = timeMode() ? 'Time axis (markers use the other)' : 'Markers use';
  $('timeInterval').value = state.timeInterval;
  $('apsisEvery').value = Math.max(1, Math.round(+state.prefs.apsisEvery) || 1);
  $('timeInterval').placeholder = autoInterval() ? 'auto (' + fmt(autoInterval()) + ')' : 'auto';
  const background = $('background');
  background.innerHTML = '';
  const names = state.backgrounds ? state.backgrounds.map(b => b.name)
                                  : [SELECTED, ALL, ...state.environments.filter(e => e.bodies.length || e.frames).map(e => e.name)];
  for (const name of names) background.add(new Option(name, name));
  background.value = state.background;
  showDescription();
  showResults();
  showDetails();
  syncFollow();
  showMeasure();
  showReplay();
}

/* the results tree: each environment (the bodies results share), its results, and each result's orbits, every level
   folding open and shut. a level's box shows or hides everything under it (a dash: some of it is hidden) */
const folds = new Map();     //'env:<key>' or 'res:<file>' -> open
const isOpen = (key, otherwise) => folds.has(key) ? folds.get(key) : otherwise;
function showResults() {
  const list = $('results');
  list.innerHTML = '';
  if (!state.results.length) { list.innerHTML = '<p class="note">No results open.</p>'; return; }
  const envs = [...new Set(state.results.map(r => r.env))], drawn = fieldEnvironments();
  const node = (cls, tip) => { const n = document.createElement('div'); n.className = 'node ' + cls; n.dataset.tip = tip; return n; };
  const fold = (key, open, count, what) => {
    const f = document.createElement('span');
    f.className = 'fold' + (count ? (open ? ' open' : ' shut') : '');
    if (count) {
      f.dataset.tip = (open ? 'Hide' : 'List') + ' its ' + count + ' ' + what;
      f.onclick = e => { e.stopPropagation(); folds.set(key, !open); showResults(); };
    }
    return f;
  };
  const box = (on, some, tip, change) => {
    const b = document.createElement('input');
    b.type = 'checkbox'; b.checked = on; b.indeterminate = some; b.dataset.tip = tip;
    b.onclick = e => { e.stopPropagation(); change(b.checked); };
    return b;
  };
  const text = (t, cls = 'name') => { const s = document.createElement('span'); s.className = cls; s.textContent = t; return s; };
  for (const env of envs) {
    const results = state.results.filter(r => r.env === env), key = 'env:' + env.key, open = isOpen(key, true);
    const shown = results.filter(r => r.visible).length;
    const head = node('env', env.name + (drawn.includes(env) ? '\nIts background is the one drawn' : '') + '\nClick to fold its results away, or open them');
    head.append(fold(key, open, results.length, 'results'),
                box(shown > 0, shown > 0 && shown < results.length, 'Show or hide every result in this environment',
                    on => { results.forEach(r => { r.visible = on; }); resultsChanged(); }),
                text(env.name));
    if (drawn.includes(env)) head.append(text('◆', 'mark'));
    head.onclick = () => { folds.set(key, !open); showResults(); };
    list.append(head);
    if (!open) continue;
    for (const r of results) {
      const rkey = 'res:' + r.file, ropen = isOpen(rkey, false), end = endTime(r);
      const row = node('res' + (r === state.selected ? ' selected' : ''),
                       r.name + ': ' + r.data.rows + ' rows' + (end !== null ? ', to t = ' + fmt(end) + ' s' : '') + '\n' + r.file +
                       '\nClick to select it (its options are below); double-click to show only it');
      const swatch = document.createElement('div');
      swatch.className = 'swatch';
      swatch.style.background = r.paths.length > 1 || r.paths.some(p => p.mode === 'transition')
        ? 'linear-gradient(90deg,' + r.paths.flatMap(p => [p.color || r.color, p.mode === 'transition' ? secondColour(r, p) : p.color || r.color]).join(',') + ')'
        : (r.paths[0] && r.paths[0].color) || r.color;
      row.append(fold(rkey, ropen, r.orbits.length, 'orbits'),
                 box(r.visible, r.visible && r.orbits.some(o => !o.visible), 'Show or hide this result' + (r.orbits.length ? ' (a dash: some of its orbits are hidden)' : ''),
                     on => { r.visible = on; resultsChanged(); }),
                 swatch, text(r.name));
      row.onclick = () => { state.selected = r; showResults(); showDetails(); draw(); };
      row.ondblclick = () => { for (const x of state.results) x.visible = x === r; resultsChanged(); };
      list.append(row);
      if (!ropen) continue;
      r.orbits.forEach((o, k) => {
        const orow = node('orb', o.name + ': from t = ' + fmt(o.t0) + ' to ' + fmt(o.t1) + ' s\nShow or hide this orbit');
        const sw = document.createElement('div');
        sw.className = 'swatch'; sw.style.background = r.paths[0] ? (r.paths[0].mode === 'transition' ? orbitColour(r, r.paths[0], k) : r.paths[0].color || r.color) : r.color;
        orow.append(box(o.visible, false, 'Show or hide this orbit', on => { o.visible = on; orbitsChanged(r); }), sw, text(o.name));
        orow.onclick = () => { o.visible = !o.visible; orbitsChanged(r); };
        list.append(orow);
      });
    }
  }
}

function endTime(r) {
  const c = timeColumnOf(r, 't');
  if (!c) return null;
  const col = r.data.columns[c];
  for (let i = col.length - 1; i >= 0; i--) if (isFinite(col[i])) return col[i];
  return null;
}

function resultsChanged() { invalidatePlot(); state.marks.key = null; showResults(); showDetails(); syncFollow(); showReplay(); }
function orbitsChanged(r) { invalidatePlot(); state.marks.key = null; showResults(); showDetails(); draw(); }

/* the selected result, in three tabs: Appearance (each path's colour, how it goes through the orbits and its line;
   the tangent; end arrows; orbits shown), Details (a summary and the log) and Choose paths (which columns are drawn) */
let detailTab = 'appearance';
function showDetails() {
  const box = $('details'), r = state.selected;
  $('markersHolder').append($('markersBlock'));   //the markers' controls, kept while the panel is rebuilt
  box.innerHTML = '';
  if (!r || !state.results.includes(r)) return;
  const el = (tag, props = {}, ...children) => {
    const {tip, ...rest} = props, e = Object.assign(document.createElement(tag), rest);
    if (tip) e.dataset.tip = tip;
    e.append(...children); return e;
  };
  const check = (label, value, change, tip) => {
    const input = el('input', {type: 'checkbox', checked: value});
    input.onchange = () => change(input.checked);
    return el('label', {className: 'check', tip}, input, ' ' + label);
  };
  const styleSelect = (value, change, tip) => {
    const select = el('select', {tip});
    for (const s of Object.keys(DASHES)) select.add(new Option(s, s));
    select.value = value; select.onchange = () => change(select.value);
    return select;
  };
  box.append(el('h3', {textContent: r.name, tip: 'The selected result: pick another in the list above'}));
  const tabs = el('div', {className: 'subtabs', role: 'tablist'});
  for (const [name, label, tip] of [['appearance', 'Appearance', 'How the selected result is drawn: colours, lines, its tangent and end arrows'],
                                    ['details', 'Details', 'A summary of the selected result, and its log'],
                                    ['paths', 'Choose paths', 'Which of the result\'s csv columns are drawn as paths']]) {
    const b = el('button', {textContent: label, tip, role: 'tab'});
    b.setAttribute('aria-selected', String(detailTab === name));
    b.onclick = () => { detailTab = name; remember('detailTab', name); showDetails(); };
    tabs.append(b);
  }
  box.append(tabs);
  if (detailTab === 'details') { showSummary(r, box, el); return; }
  if (detailTab === 'paths') { showChoosePaths(r, box, el); return; }

  //each path: its colour (one, a transition from the first orbit to the last, or earlier orbits shaded) and line
  const orbits = r.paths.map(p => pathOrbits(r, p));
  for (const [k, p] of r.paths.entries()) {
    const block = el('div', {className: 'pathBlock'});
    const row = el('div', {className: 'pathRow'});
    const first = el('input', {type: 'color', value: p.color || r.color, tip: p.mode === 'transition' ? 'The first orbit\'s colour (click to change)' : 'The line\'s colour (click to change)'});
    first.oninput = () => { p.color = first.value; showResults(); draw(); };
    row.append(first);
    if (p.mode === 'transition') {
      const second = el('input', {type: 'color', value: secondColour(r, p), tip: 'The last orbit\'s colour (click to change); the orbits between are a mix of the two'});
      second.oninput = () => { p.color2 = second.value; showResults(); draw(); };
      row.append('→', second);
    }
    row.append(styleSelect(p.style, v => { p.style = v; draw(); }, 'The line\'s style: solid, dashed or dotted'), el('span', {textContent: p.name}));
    block.append(row);
    const modes = el('div', {className: 'modes'});
    for (const [mode, label, tip] of [['single', 'single colour', 'The whole path in one colour'],
                                      ['transition', 'transition', 'The colour goes from a first to a last through the orbits'],
                                      ['shade', 'shade', 'The current orbit (at the replay\'s time, or the last) in full colour, each earlier one fainter']]) {
      const radio = el('input', {type: 'radio', name: 'mode' + k, checked: p.mode === mode, disabled: mode !== 'single' && !orbits[k]});
      radio.onchange = () => { p.mode = mode; showResults(); showDetails(); draw(); };
      modes.append(el('label', {tip: mode !== 'single' && !orbits[k] ? 'Not available: this path doesn\'t go round its body' : tip}, radio, label));
    }
    block.append(modes);
    box.append(block);
  }
  //the tangent: where the path would go with no gravity from a moment chosen along it
  const tg = r.tangent, times = tangentTimes(r);
  box.append(check('tangent', tg.on, v => { tg.on = v; showDetails(); draw(); },
                   'A straight line along the path at a chosen moment: where it would go (and have come from) with no gravity'));
  if (tg.on) {
    const panel = el('div', {className: 'tangent'});
    const colour = el('input', {type: 'color', value: tg.color || (r.paths[0] && r.paths[0].color) || r.color, tip: 'The tangent\'s colour (click to change)'});
    colour.oninput = () => { tg.color = colour.value; draw(); };
    panel.append(el('div', {className: 'pathRow'}, colour, styleSelect(tg.style, v => { tg.style = v; draw(); }, 'The tangent\'s line style')));
    const T = tangentAt(r), span = times.hi - times.lo || 1;
    const slider = el('input', {type: 'range', min: 0, max: 1000, step: 1, value: Math.round((T - times.lo) / span * 1000),
                                tip: 'Drag to the moment the tangent is drawn at'});
    const entry = el('input', {value: fmt(T), size: 10, tip: 'The moment the tangent is drawn at, ' + (times.rows ? 'as a row number (this result has no t column)' : 'in seconds of t') + ': type one in'});
    slider.oninput = () => { tg.t = times.lo + slider.value / 1000 * span; entry.value = fmt(tg.t); draw(); };
    entry.onchange = () => { const v = +entry.value; if (isFinite(v)) { tg.t = v; slider.value = Math.round((tangentAt(r) - times.lo) / span * 1000); entry.value = fmt(tangentAt(r)); draw(); } };
    panel.append(slider, el('label', {className: 'row', tip: 'From ' + fmt(times.lo) + ' to ' + fmt(times.hi) + (times.rows ? ' (rows)' : ' s')}, (times.rows ? 'row ' : 't = '), entry, times.rows ? '' : ' s'));
    box.append(panel);
  }
  if (endPairs(r).length) box.append(check('end arrows', r.ends, v => { r.ends = v; draw(); }, 'An arrow at the end of each stretch of the path for each velocity-like pair (x / y only)'));
  if (r.orbits.length) {
    const whole = r.orbits.filter(o => o.full).length, shown = r.orbits.filter(o => o.full && o.visible).length;
    const row = el('div', {className: 'buttons'}, el('span', {className: 'note', textContent: 'Orbits: ' + shown + ' of ' + whole + ' shown'}));
    const all = el('button', {textContent: 'All', tip: 'Show every orbit'}), none = el('button', {textContent: 'None', tip: 'Hide every orbit'});
    all.onclick = () => { r.orbitEvery = 1; r.orbits.forEach(o => { o.visible = true; }); orbitsChanged(r); };
    none.onclick = () => { r.orbits.forEach(o => { o.visible = false; }); orbitsChanged(r); };
    row.append(all, none);
    box.append(row);
    //every Nth whole orbit shown (the first, then every N on), the rest hidden; the parts before the first and after the
    //last stay as they are
    const every = el('input', {type: 'number', min: 1, step: 1, value: r.orbitEvery || 1, id: 'orbitEvery'});
    every.onchange = () => {
      const n = Math.max(1, Math.round(+every.value) || 1);
      r.orbitEvery = n;
      let number = 0;
      for (const o of r.orbits) if (o.full) { number++; o.visible = (number - 1) % n === 0; }
      orbitsChanged(r);
    };
    box.append(el('label', {className: 'row', tip: 'Show only every Nth orbit (the first, then every N on) and hide the rest: 1 shows them all'}, 'show every ', every, ' orbits'));
  }
  box.append($('markersBlock'));   //the markers (for every result) belong with how things are drawn
}

/* Details: the summary, and the log */
function showSummary(r, box, el) {
  const table = el('table', {tip: 'A summary of the run, from its data and log'});
  for (const [label, value] of summaryRows(r)) table.append(el('tr', {}, el('td', {textContent: label}), el('td', {textContent: value})));
  box.append(table, el('div', {className: 'file', textContent: r.file}));
  const log = el('details');
  log.append(el('summary', {textContent: 'Log', tip: 'The run\'s log: its setup, bodies, calculator and results'}), el('pre', {textContent: r.log.text || '(no log)'}));
  box.append(log);
}

/* Choose paths: which column pairs are drawn, any two columns as a pair, and one path per value of a column */
function showChoosePaths(r, box, el) {
  const found = pairs(r.data.names).map(p => [p[1], p[2]]);
  const options = [...found, ...r.selection.filter(s => !found.some(f => f[0] === s[0] && f[1] === s[1]))];
  box.append(el('p', {className: 'note', textContent: 'The column pairs found in the csv:'}));
  const picks = options.map(([x, y]) => {
    const input = el('input', {type: 'checkbox', checked: r.selection.some(s => s[0] === x && s[1] === y)});
    box.append(el('label', {className: 'check', tip: 'Draw ' + y + ' against ' + x}, input, ' ' + y + '  vs  ' + x));
    return [[x, y], input];
  });
  const numeric = r.data.names.filter(n => Array.from(r.data.columns[n]).some(isFinite));
  const xs = el('select', {tip: 'The column across'}), ys = el('select', {tip: 'The column up'});
  for (const n of numeric) { xs.add(new Option(n, n)); ys.add(new Option(n, n)); }
  if (numeric.length > 1) ys.selectedIndex = 1;
  const add = el('button', {textContent: 'Add pair', tip: 'Draw the chosen y column against the chosen x column as another path'});
  const group = el('select', {tip: 'Split the rows into one path for each value of this column (a column naming each object, say)'});
  group.add(new Option('(none)', ''));
  for (const n of r.data.names) group.add(new Option(n, n));
  group.value = r.group || '';
  const apply = el('button', {textContent: 'Apply', tip: 'Draw the ticked pairs, split by the chosen column'});
  const chosen = () => picks.filter(([, i]) => i.checked).map(([s]) => s);
  add.onclick = () => {
    const selection = chosen();
    if (!selection.some(s => s[0] === xs.value && s[1] === ys.value)) selection.push([xs.value, ys.value]);
    rebuildPaths(r, selection, group.value || null);
  };
  apply.onclick = () => {
    const selection = chosen();
    if (!selection.length) { message('choose at least one pair'); return; }
    rebuildPaths(r, selection, group.value || null);
  };
  box.append(el('label', {className: 'row', tip: 'Any two columns as a new pair: x across, y up'}, 'x ', xs, ' y ', ys, add));
  box.append(el('label', {className: 'row', tip: 'Split the rows into one path for each value of this column'}, 'one path per value of ', group));
  box.append(apply);
}

/* a result's paths built again from a selection of column pairs (and a column to split them by), keeping styles */
function rebuildPaths(r, selection, group) {
  const settings = resultSettings(r);
  r.paths = buildPaths(r, {...settings, selection, group});
  r.orbits = buildOrbits(r, settings.hiddenOrbits);
  invalidatePlot(); state.marks.key = null;
  showResults(); showDetails(); fit();
}

/* facts about a result, from its data and log (the desktop's summary) */
function summaryRows(r) {
  const rows = [['Environment', r.env.name]], log = r.log.text || '';
  const whole = r.orbits.filter(o => o.full);
  if (whole.length) {
    const periods = whole.map(o => (o.t1 - o.t0) / 86400);
    rows.push(['Orbits', whole.length + ', mean period ' + fmt(periods.reduce((a, b) => a + b) / periods.length) + ' days (' +
               fmt(Math.min(...periods)) + ' to ' + fmt(Math.max(...periods)) + ')']);
  }
  const calc = log.match(/^calc:\s*(.*)$/m);
  if (calc) rows.push(['Calculator', (calc[1].match(/<[\w.]*?(\w+) object/) || [])[1] || calc[1]]);
  const dt = log.match(/^dt:?\s+(\S+)/m);
  if (dt) rows.push(['dt', dt[1] + ' s']);
  rows.push(['Rows', r.data.rows + ' in ' + r.paths.length + ' path' + (r.paths.length === 1 ? '' : 's')]);
  for (const o of Object.keys(TIME_OPTIONS)) {
    const c = timeColumnOf(r, o);
    if (!c) continue;
    const v = Array.from(r.data.columns[c]).filter(isFinite);
    if (v.length) rows.push([c, fmt(v[0]) + ' → ' + fmt(v[v.length - 1]) + ' s']);
  }
  const p = r.paths[0];
  if (p) {
    const d = [];
    for (let i = 0; i < p.x.length; i++) { const v = Math.hypot(p.x[i], p.y[i]); if (isFinite(v)) d.push(v); }
    const both = v => fmt(v) + ' m (' + fmt(+(v / AU).toPrecision(4)) + ' AU)';
    if (d.length) rows.push(['Distance', both(d[0]) + ' → ' + both(d[d.length - 1])], ['Closest', both(Math.min(...d))]);
    const v = velocityPair(r);
    if (v) {
      const sp = [];
      for (let i = 0; i < p.x.length; i++) { const s = Math.hypot(r.data.columns[v[1]][i], r.data.columns[v[2]][i]); if (isFinite(s)) sp.push(s); }
      if (sp.length) rows.push(['Speed |v|', (sp[0] / C).toPrecision(4) + ' → ' + (sp[sp.length - 1] / C).toPrecision(4) + ' c']);
    }
  }
  for (const line of log.split('\n').filter(l => /accuracy|predicted/i.test(l)).slice(0, 6))
    rows.push(['Result', line.trim().length <= 110 ? line.trim() : line.trim().slice(0, 107) + '...']);
  return rows;
}

/* the chosen background's description, under the Background menu */
function showDescription() {
  const background = currentBackground();
  $('bgDescription').textContent = background ? background.description : '';
  $('bgDescription').style.display = background && background.description ? '' : 'none';
}

/* the status line: what is shown, and the plotted point under the pointer in the axes' units */
function showStatus(sx, sy) {
  const shown = state.results.filter(r => r.visible);
  let text = state.results.length ? shown.length + ' of ' + state.results.length + ' results shown, ' +
             shown.reduce((n, r) => n + r.data.rows, 0) + ' rows, ' + shown.reduce((n, r) => n + r.paths.length, 0) + ' paths' : '';
  const rect = plotRect();
  if (sx !== undefined && state.view && sx >= rect.l && sx <= rect.r && sy >= rect.t && sy <= rect.b) {
    const [X, Y] = toData(sx, sy), [ax, ay] = axes();
    const show = (v, a) => a.log ? fmt(Math.pow(10, v)) : fmt(v / a.scale);
    text += '    ' + ax.label.replace('  [log]', '') + ' ' + show(X, ax) + ',  ' + ay.label.replace('  [log]', '') + ' ' + show(Y, ay);
  }
  $('status').textContent = text;
}

/* the mode or a log axis changed: work the plotted values out again, and fit */
function plotChanged() {
  invalidatePlot(); state.marks.key = null;
  state.measure.points = state.measure.points.filter(q => q.row !== undefined);   //a point off the paths was in the old axes
  document.body.classList.toggle('time', timeMode());
  syncControls();
  fit();
}


/* a view's pane: made from the template, its handlers wired, and added after the others */
function addPane(st) {
  const el = $('paneTemplate').content.firstElementChild.cloneNode(true);
  const canvas = el.querySelector('canvas.plot'), overlay = el.querySelector('canvas.overlay');
  if (!panes.length) canvas.id = 'plot';
  const pane = {state: st, el, canvas, ctx: canvas.getContext('2d'), overlay, overlayCtx: overlay.getContext('2d'),
                empty: el.querySelector('.empty'), loadingNote: el.querySelector('.loading'), frame: null, loading: false};
  $('panes').append(el);
  panes.push(pane);
  wirePane(pane);
  layoutPanes();
  return pane;
}

/* the panel shows the selected view's settings */
function activate(pane) {
  if (active === pane) return;
  active = pane;
  usePane(pane);
  layoutPanes();
  if (setupDone) syncControls();
}
let setupDone = false;

function layoutPanes() {
  const split = panes.length > 1;
  $('panes').classList.toggle('split', split);
  panes.forEach((p, i) => {
    p.el.classList.toggle('active', p === active);
    p.el.querySelector('.paneTag').textContent = 'View ' + (i + 1);
  });
  if (!PLAYER && $('splitView')) {
    $('splitView').textContent = split ? 'One view' : 'Split view';
    $('splitView').dataset.tip = split ? 'Back to one view: the selected view stays, the other is closed'
                                       : 'Two views side by side, each with its own results and settings: the new one starts as a copy of this one. Click a view to select it; Play plays both';
  }
}

/* Split view: a second view, a copy of the selected one; One view: the selected one only */
function toggleSplit() {
  if (panes.length > 1) {
    for (const p of panes.filter(p => p !== active)) { if (p.frame != null) cancelAnimationFrame(p.frame); p.el.remove(); panes.splice(panes.indexOf(p), 1); }
    layoutPanes();
  } else {
    const copy = cloneState(state);
    const pane = addPane(copy);
    withPane(pane, () => invalidatePlot());
    activate(pane);
  }
  //each view's width has changed: keep a metre as long across as up
  for (const p of panes) withPane(p, () => { if (state.view) equalise(); });
  drawAll();
}

/* a copy of a view's state: the same runs, read once and shared, with each result's own settings copied */
function cloneState(from) {
  const st = makeState();
  Object.assign(st, {prefs: {...from.prefs}, view: from.view && from.view.slice(), background: from.background, backgrounds: from.backgrounds,
                     environments: from.environments.slice(), sources: from.sources.slice(), timeInterval: from.timeInterval,
                     fitSpan: from.fitSpan, follow: from.follow && {...from.follow}});
  st.results = from.results.map(r => {
    const settings = resultSettings(r);
    const copy = {name: r.name, file: r.file, data: r.data, log: r.log, visible: r.visible, color: r.color, source: r.source, ends: r.ends,
                  tangent: {...r.tangent}, env: r.env, orbitEvery: r.orbitEvery, derived: r.derived, dots: r.dots};
    withState(st, () => { copy.paths = buildPaths(copy, settings); copy.orbits = buildOrbits(copy, settings.hiddenOrbits); });
    return copy;
  });
  st.selected = st.results[from.results.indexOf(from.selected)] || st.results[0] || null;
  return st;
}
function withState(st, fn) { const was = state; state = st; try { return fn(); } finally { state = was; } }

/* a view's plot: hover text, the legend boxes' buttons (in the player too), and (not in the player, which stays as its
   page set it) pan by dragging, zoom to a box with shift-drag, zoom with the wheel at the pointer, fit with a double
   click, and the measuring tool. a press selects the view */
function wirePane(pane) {
  const canvas = pane.canvas, here = fn => e => withPane(pane, () => fn(e));
  let hoverFrame = null, hoverEvent = null;
  canvas.addEventListener('pointermove', e => {
    hoverEvent = e;
    if (hoverFrame === null) hoverFrame = requestAnimationFrame(() => { hoverFrame = null; withPane(pane, () => { hoverAt(hoverEvent); if (!PLAYER) showStatus(hoverEvent.offsetX, hoverEvent.offsetY); }); });
  });
  canvas.addEventListener('pointerleave', here(() => {
    if (!tipFor) $('tip').style.display = 'none';
    canvas.style.cursor = '';
    if (state.frontPath) { state.frontPath = null; draw(); }
    if (!PLAYER) showStatus();
  }));
  if (PLAYER) { canvas.onpointerdown = e => { activate(pane); boxPress(e); }; return; }
  let dragging = null;
  canvas.onpointerdown = e => {
    activate(pane);
    canvas.focus();
    if (boxPress(e) || !state.view) return;
    if (state.measure.on && !e.shiftKey) { dragging = {measure: [e.offsetX, e.offsetY]}; return; }
    if (e.shiftKey) state.boxZoom = [e.offsetX, e.offsetY, e.offsetX, e.offsetY];
    else dragging = [e.offsetX, e.offsetY, state.view.slice()];
    try { canvas.setPointerCapture(e.pointerId); } catch (x) { /* a synthetic pointer */ }
  };
  canvas.onpointermove = here(e => {
    if (state.boxZoom) { state.boxZoom[2] = e.offsetX; state.boxZoom[3] = e.offsetY; draw(); return; }
    if (!dragging || dragging.measure) return;
    const {l, t, r, b} = plotRect(), [px, py, v] = dragging;
    const dx = (e.offsetX - px) / (r - l) * (v[1] - v[0]) * (flipX() ? -1 : 1), dy = (e.offsetY - py) / (b - t) * (v[3] - v[2]);
    state.view = [v[0] - dx, v[1] - dx, v[2] + dy, v[3] + dy];
    stopFollowing(); moved(); scheduleDraw();
  });
  canvas.onpointerup = here(e => {
    if (dragging && dragging.measure) {
      const [x0, y0] = dragging.measure;
      dragging = null;
      if (Math.hypot(e.offsetX - x0, e.offsetY - y0) < 5) measureAt(e.offsetX, e.offsetY);
      return;
    }
    dragging = null;
    if (!state.boxZoom) return;
    const [x0, y0, x1, y1] = state.boxZoom;
    state.boxZoom = null;
    if (Math.abs(x1 - x0) > 4 && Math.abs(y1 - y0) > 4) {
      const [ax, ay] = toData(x0, y0), [bx, by] = toData(x1, y1);
      state.view = [Math.min(ax, bx), Math.max(ax, bx), Math.min(ay, by), Math.max(ay, by)];
      stopFollowing(); equalise();
    }
    draw();
  });
  canvas.ondblclick = here(e => { if (!state.measure.on && !state.boxButtons.some(h => inside(h, e.offsetX, e.offsetY))) fit(); });
  canvas.addEventListener('wheel', here(e => {
    if (!state.view) return;
    e.preventDefault();
    zoom(Math.exp(e.deltaY * 0.0015), state.follow ? null : toData(e.offsetX, e.offsetY));
  }), {passive: false});
}

function setup() {
  activate(addPane(makeState()));
  UNITS.forEach(([name], i) => $('unit').add(new Option(name, i)));
  SPEEDS.forEach(s => { $('speed').add(new Option(speedName(s), s)); $('pSpeed').add(new Option(speedName(s), s)); });
  setupPlayer();
  if (!PLAYER) { setupTabs(); setupSplitter(); setupTreeSplit(); setupLayerSettings(); setupHelp(); }
  if (['appearance', 'details', 'paths'].includes(recall('detailTab'))) detailTab = recall('detailTab');
  for (const id of OPTION_BOXES)
    $(id).onchange = () => { state.prefs[id] = $(id).checked; if (id === 'showTimeMarks' || id === 'showMarkNote') state.marks.key = null; draw(); };
  for (const id of ['logX', 'logY', 'ctTime'])
    $(id).onchange = () => { state.prefs[id] = $(id).checked; plotChanged(); };
  $('equalAspect').onchange = () => { state.prefs.equalAspect = $('equalAspect').checked; equalise(); draw(); };
  $('mode').onchange = () => {
    if ($('mode').value === 'time' && !state.results.some(r => timeColumnOf(r, state.prefs.timeColumn) || timeColumnOf(r, 't'))) {
      message('these results have no t or pt column to plot against'); $('mode').value = 'xy'; return;
    }
    state.prefs.mode = $('mode').value; plotChanged();
  };
  $('unit').onchange = () => {
    //a log axis is in the unit's values: keep the same stretch of the plot in view
    const [ax0, ay0] = axes();
    state.prefs.unit = +$('unit').value;
    const [ax1, ay1] = axes();
    if (state.view) {
      const v = state.view, dx = ax0.log ? Math.log10(ax0.scale / ax1.scale) : 0, dy = ay0.log ? Math.log10(ay0.scale / ay1.scale) : 0;
      state.view = [v[0] + dx, v[1] + dx, v[2] + dy, v[3] + dy];
    }
    invalidatePlot(); state.marks.key = null; draw();
  };
  $('timeColumn').onchange = () => { state.prefs.timeColumn = $('timeColumn').value; state.timeInterval = ''; if (timeMode()) plotChanged(); else { state.marks.key = null; syncControls(); draw(); } };
  $('timeInterval').onchange = () => { state.timeInterval = $('timeInterval').value.trim(); state.marks.key = null; draw(); };
  $('apsisEvery').onchange = () => { state.prefs.apsisEvery = Math.max(1, Math.round(+$('apsisEvery').value) || 1); $('apsisEvery').value = state.prefs.apsisEvery; draw(); };
  $('timeAuto').onclick = () => { state.timeInterval = ''; $('timeInterval').value = ''; state.marks.key = null; draw(); };
  $('speed').onchange = () => { state.prefs.replaySpeed = $('speed').value; };
  $('background').onchange = () => { state.background = $('background').value; showDescription(); showResults(); draw(); };
  $('fit').onclick = fit;
  $('zoomSlider').oninput = () => {
    if (!state.view || !state.fitSpan) return;
    const now = state.fitSpan / (state.view[1] - state.view[0]), want = Math.pow(10, +$('zoomSlider').value);
    zoom(now / want);
  };
  $('rangeApply').onclick = applyRange;
  for (const id of RANGE_INPUTS) $(id).onkeydown = e => { if (e.key === 'Enter') { e.preventDefault(); applyRange(); $(id).blur(); } };
  setupJoystick();
  $('follow').onchange = () => chooseFollow($('follow').value);
  $('measure').onclick = () => { state.measure.on = !state.measure.on; canvas.style.cursor = state.measure.on ? 'crosshair' : ''; showMeasure(); };
  $('measureClear').onclick = () => { state.measure.points = []; showMeasure(); draw(); };
  $('measurePin').onclick = pinRowAt;
  $('measureT').onkeydown = e => { if (e.key === 'Enter') { e.preventDefault(); pinRowAt(); } };
  $('exportPng').onclick = exportPng;
  $('exportSvg').onclick = exportSvg;
  $('exportCsv').onclick = exportCsv;
  $('splitView').onclick = toggleSplit;
  $('copyLink').onclick = () => copyLink(false);
  $('copyEmbed').onclick = () => copyLink(true);
  $('legendsAll').onclick = () => { for (const id of LEGEND_BOXES) state.prefs[id] = true; state.marks.key = null; syncControls(); draw(); };
  $('legendsNone').onclick = () => { for (const id of LEGEND_BOXES) state.prefs[id] = false; state.marks.key = null; syncControls(); draw(); };
  $('showAll').onclick = () => { state.results.forEach(r => { r.visible = true; }); resultsChanged(); };
  $('showNone').onclick = () => { state.results.forEach(r => { r.visible = false; }); resultsChanged(); };
  $('showOnly').onclick = () => { state.results.forEach(r => { r.visible = r === state.selected; }); resultsChanged(); };
  $('closeResult').onclick = closeSelected;
  $('addResult').onclick = openAddDialog;
  $('play').onclick = () => play('together');
  $('playInTurn').onclick = () => play('sequence');
  $('loop').onchange = () => { state.prefs.replayLoop = $('loop').checked; };
  $('pause').onclick = () => { if (state.replay.state === 'playing') state.replay.state = 'paused'; showReplay(); };
  $('restart').onclick = () => { stopReplay(); showReplay(); };
  $('seek').oninput = () => seek($('seek').value / 1000);
  $('openFolder').onclick = () => $('folderInput').click();
  $('folderInput').onchange = () => openFiles([...$('folderInput').files]);
  $('addFolder').onclick = () => $('addInput').click();
  $('addInput').onchange = () => openFiles([...$('addInput').files], true);
  $('reload').onclick = reload;

  //drop a run folder (or its files) on the plot
  const wrap = $('plotWrap');
  wrap.ondragover = e => { e.preventDefault(); $('drop').style.display = 'flex'; };
  wrap.ondragleave = () => { $('drop').style.display = 'none'; };
  wrap.ondrop = async e => {
    e.preventDefault(); $('drop').style.display = 'none';
    openFiles(await droppedFiles(e.dataTransfer), e.shiftKey);
  };
  window.onresize = () => { for (const p of panes) withPane(p, () => { if (PLAYER && !state.keepView) fit(); else { equalise(); draw(); } }); };
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', drawAll);
  if (REDUCED_MOTION.addEventListener) REDUCED_MOTION.addEventListener('change', drawAll);
  document.addEventListener('keydown', e => {
    if (PLAYER || /^(INPUT|SELECT|TEXTAREA)$/.test(document.activeElement.tagName) || e.metaKey || e.ctrlKey || e.altKey) return;
    if (!state.view) return;
    const keys = {'+': () => zoom(1 / ZOOM_STEP), '=': () => zoom(1 / ZOOM_STEP), '-': () => zoom(ZOOM_STEP), '0': fit,
                  ArrowLeft: () => pan(-PAN_STEP, 0), ArrowRight: () => pan(PAN_STEP, 0), ArrowUp: () => pan(0, PAN_STEP), ArrowDown: () => pan(0, -PAN_STEP),
                  Escape: () => { state.measure.points = []; showMeasure(); draw(); }};
    if (keys[e.key]) { e.preventDefault(); keys[e.key](); }
  });

  setupDone = true;
  layoutPanes();
  //what to open: a link's views (state=), or a run (run=). the player waits until it is near the page's view, so a page
  //with several players doesn't load them all at once
  const params = new URLSearchParams(location.search), run = params.get('run'), linked = params.get('state');
  const open = async () => {
    if (linked) {
      try { await openLinked(await decodeState(linked)); }
      catch (e) { message('could not open the link: ' + e.message); syncControls(); draw(); }
    } else if (run) {
      const url = new URL(run, location.href);
      loadRun(urlSource(new URL('.', url)), url.pathname.split('/').pop());
    } else {
      syncControls(); draw();
    }
  };
  if (PLAYER && (run || linked) && window.IntersectionObserver && window.top !== window) {
    syncControls(); draw();
    active.loadingNote.hidden = false; active.loadingNote.textContent = 'waiting to load…'; emptyNote.style.display = 'none';
    const watch = new IntersectionObserver(entries => {
      if (!entries.some(e => e.isIntersecting)) return;
      watch.disconnect(); open();
    }, {rootMargin: '300px'});
    watch.observe(document.body);
  } else open();
}

/* remembered between visits, in this browser only (and not at all where storage is blocked) */
const remember = (key, value) => { try { localStorage.setItem('flowViewer.' + key, value); } catch (e) { /* not kept */ } };
const recall = key => { try { return localStorage.getItem('flowViewer.' + key); } catch (e) { return null; } };

/* each background layer's settings, folded under its checkbox: its colour(s), and sliders for its density, size and
   line width (and a colour map's strength), with a reset. changes draw at once, and are kept in this browser */
const SETTING_SLIDERS = {
  density: {label: 'density', min: 0.25, max: 4, step: 0.05, unit: '\u00d7', tip: {
    u: 'How close together the arrows are', g: 'How close together the arrows are', twist: 'How close together the arcs are',
    cones: 'How close together the cones are', flowLines: 'How many flow lines: more of them closer together',
    contours: 'How many levels of |u| are drawn', scalar: 'How fine the colour map\'s cells are'}},
  size: {label: 'size', min: 0.25, max: 3, step: 0.05, unit: '\u00d7', tip: {
    u: 'How long a full arrow is', g: 'How long a full arrow is', twist: 'How big the arcs are', cones: 'How big the cones are'}},
  width: {label: 'line width', min: 0.5, max: 4, step: 0.1, unit: ' px', tip: {}},
  strength: {label: 'strength', min: 0.2, max: 2, step: 0.05, unit: '\u00d7', tip: {scalar: 'How strong the colours are: above 1, weaker values show more'}},
  speed: {label: 'speed', min: 0.1, max: 4, step: 0.05, unit: '\u00d7', tip: {
    infallArrows: 'How fast the points move: the picture\'s speed, not the real one', infallRings: 'How fast the rings fall: the picture\'s speed, not the real one'}},
};
const COLOUR_NAMES = {colour: 'colour', plus: 'positive', minus: 'negative'};
function setupLayerSettings() {
  try { Object.assign(sharedLayers, JSON.parse(recall('layers') || '{}') || {}); } catch (e) { /* none kept */ }
  const save = () => remember('layers', JSON.stringify(state.layers));
  for (const [name, spec] of Object.entries(LAYERS)) {
    const label = $(spec.box).closest('label'), row = document.createElement('div'), fold = document.createElement('span');
    row.className = 'layerRow';
    label.replaceWith(row);
    fold.className = 'fold shut'; fold.dataset.tip = 'Settings for the ' + spec.name + ': colour, density, size';
    const panel = document.createElement('div');
    panel.className = 'layerSettings'; panel.hidden = true;
    fold.onclick = () => { panel.hidden = !panel.hidden; fold.className = 'fold ' + (panel.hidden ? 'shut' : 'open'); };
    row.append(fold, label);
    row.after(panel);
    const build = () => {
      panel.innerHTML = '';
      const now = layer(name), own = state.layers[name] || (state.layers[name] = {});
      const colours = document.createElement('div');
      colours.className = 'colours';
      for (const key of ['colour', 'plus', 'minus'].filter(k => k in spec.defaults)) {
        const input = Object.assign(document.createElement('input'), {type: 'color', value: now[key]});
        input.oninput = () => { own[key] = input.value; save(); draw(); };
        const wrap = document.createElement('label');
        wrap.dataset.tip = 'The ' + spec.name + (key === 'colour' ? '\'' : '\' ' + COLOUR_NAMES[key] + ' values\'') + ' colour (click to change)';
        wrap.append(input, ' ' + COLOUR_NAMES[key]);
        colours.append(wrap);
      }
      panel.append(colours);
      for (const key of Object.keys(SETTING_SLIDERS).filter(k => k in spec.defaults)) {
        const s = SETTING_SLIDERS[key], line = document.createElement('label'), value = document.createElement('span');
        line.className = 'slider';
        line.dataset.tip = s.tip[name] || (key === 'width' ? 'How thick the ' + spec.name + '\'s lines are' : s.label);
        const input = Object.assign(document.createElement('input'), {type: 'range', min: s.min, max: s.max, step: s.step, value: now[key]});
        const show = () => { value.textContent = (+input.value).toFixed(key === 'width' ? 1 : 2).replace(/\.?0+$/, '') + s.unit; };
        input.oninput = () => { own[key] = +input.value; show(); save(); draw(); };
        show();
        line.append(Object.assign(document.createElement('span'), {textContent: s.label}), input, value);
        panel.append(line);
      }
      const reset = Object.assign(document.createElement('button'), {textContent: 'Reset'});
      reset.dataset.tip = 'Back to the ' + spec.name + '\'s usual colour and sizes';
      reset.onclick = () => { delete state.layers[name]; save(); build(); draw(); };
      panel.append(reset);
    };
    build();
  }
}

/* the split between the results list and the selected result, dragged (kept between visits); a double-click puts it
   back */
function setupTreeSplit() {
  const edge = $('treeSplit'), list = $('results'), section = list.parentElement;
  const set = h => {
    h = Math.max(40, Math.min(Math.round(h), section.clientHeight - 140));
    section.style.setProperty('--tree', h + 'px');
  };
  const kept = +recall('treeHeight');
  if (kept) set(kept);
  let drag = null;
  edge.onpointerdown = e => { drag = {y: e.clientY, h: list.offsetHeight}; try { edge.setPointerCapture(e.pointerId); } catch (x) { /* a synthetic pointer */ } edge.classList.add('dragging'); hideTip(); };
  edge.onpointermove = e => { if (drag) set(drag.h + e.clientY - drag.y); };
  edge.onpointerup = () => { if (!drag) return; drag = null; edge.classList.remove('dragging'); remember('treeHeight', list.offsetHeight); };
  edge.ondblclick = () => { section.style.removeProperty('--tree'); remember('treeHeight', ''); };
}

/* the panel's tabs: Results, View and Background */
function setupTabs() {
  const show = name => {
    for (const b of document.querySelectorAll('#tabs button')) b.setAttribute('aria-selected', String(b.dataset.tab === name));
    for (const p of document.querySelectorAll('aside section[data-panel]')) p.hidden = p.dataset.panel !== name;
    remember('tab', name);
  };
  for (const b of document.querySelectorAll('#tabs button')) b.onclick = () => show(b.dataset.tab);
  show(['results', 'view', 'background'].includes(recall('tab')) ? recall('tab') : 'results');
}

/* the panel's edge, dragged to set its width (kept between visits); a double-click puts it back */
const PANEL_WIDTH = 320;
function setupSplitter() {
  const app = $('app'), edge = $('splitter');
  const set = w => {
    w = Math.max(220, Math.min(Math.round(w), Math.max(260, innerWidth - 360)));
    app.style.setProperty('--panel', w + 'px');
    return w;
  };
  const kept = +recall('panelWidth');
  if (kept) set(kept);
  let drag = null;
  edge.onpointerdown = e => { drag = {x: e.clientX, w: $('app').querySelector('aside').offsetWidth}; try { edge.setPointerCapture(e.pointerId); } catch (x) { /* a synthetic pointer */ } edge.classList.add('dragging'); hideTip(); };
  edge.onpointermove = e => {
    if (!drag) return;
    set(drag.w + drag.x - e.clientX);
    equalise(); draw();
  };
  edge.onpointerup = () => {
    if (!drag) return;
    drag = null; edge.classList.remove('dragging');
    remember('panelWidth', $('app').querySelector('aside').offsetWidth);
  };
  edge.ondblclick = () => { app.style.removeProperty('--panel'); remember('panelWidth', ''); equalise(); draw(); };
}

/* hover help for everything in the header and the panel with a data-tip: shown after a moment, beside the pointer's
   control, and gone when the pointer leaves it */
function setupHelp() {
  let timer = null, over = null;
  const leave = () => { clearTimeout(timer); timer = null; if (over) { over = null; hideTip(); } };
  for (const area of [document.querySelector('header'), document.querySelector('aside'), $('splitter'), $('addDialog')]) {
    area.addEventListener('pointerover', e => {
      const el = e.target.closest('[data-tip]');
      if (!el || el === over || !area.contains(el)) return;
      leave();
      over = el;
      timer = setTimeout(() => { if (over === el && el.dataset.tip) showTip(el); }, 450);
    });
    area.addEventListener('pointerleave', leave);
    area.addEventListener('pointerdown', leave);
  }
  document.querySelector('aside').addEventListener('pointerout', e => {
    if (over && !over.contains(e.relatedTarget)) leave();
  });
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
    const range = clockRange();
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

function openFiles(files, add = false) {
  if (!files.length) return;
  //a chosen folder may hold several runs: take the folder of the first full.json (else of the first csv)
  const first = files.find(f => f.name.endsWith('.full.json')) || files.find(f => f.name.endsWith('.csv'));
  if (!first) { message('no .full.json or .csv files there'); return; }
  const folder = (first.webkitRelativePath || first.relativePath || '').split('/').slice(0, -1).join('/');
  const same = files.filter(f => (f.webkitRelativePath || f.relativePath || '').split('/').slice(0, -1).join('/') === folder);
  loadRun(folderSource(same), null, {add: add && state.results.length > 0});
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
