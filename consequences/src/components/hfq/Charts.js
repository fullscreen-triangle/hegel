/* ============================================================================
 * Chart primitives.
 *
 * Hand-rolled SVG, drawn from arrays the caller computed. No charting library:
 * the shapes here are a dozen `<rect>`s and a `<path>`, and a dependency that
 * draws them would also bring its own colour model, its own DOM ownership and
 * its own idea of what a theme is -- all three of which this site already has
 * and would then have to fight.
 *
 * Colour follows `currentColor` and the constants in ./theme, which is how
 * every other renderer on this page follows light and dark mode. Nothing here
 * reads a CSS custom property.
 *
 * These take data and geometry only. They do not fetch, memoise, or know what
 * a verdict is; the panels in ./Figures own all of that.
 * ========================================================================== */

import React, { useId, useState } from 'react';

/* ---------------------------------------------------------------- *
 * Scales. Two functions rather than a library: the whole of what is
 * needed from one is a linear map plus a tick list.
 * ---------------------------------------------------------------- */

export const linear = (d0, d1, r0, r1) => (v) =>
  (d1 === d0 ? (r0 + r1) / 2 : r0 + ((v - d0) / (d1 - d0)) * (r1 - r0));

/** `n` round-ish ticks spanning [lo, hi]. */
export function ticks(lo, hi, n = 5) {
  if (!(hi > lo)) return [lo];
  const raw = (hi - lo) / n;
  const mag = 10 ** Math.floor(Math.log10(raw));
  const step = [1, 2, 2.5, 5, 10].map((m) => m * mag)
    .find((s) => s >= raw) || 10 * mag;
  const out = [];
  for (let t = Math.ceil(lo / step) * step; t <= hi + step * 1e-9; t += step) {
    out.push(Math.abs(t) < step * 1e-9 ? 0 : t);
  }
  return out;
}

const fmtTick = (v) => (Number.isInteger(v) ? String(v)
  : Math.abs(v) < 1 ? v.toFixed(2) : v.toFixed(1));

/* ---------------------------------------------------------------- *
 * Frame: axes, gridlines, labels. Every chart below sits in one.
 * ---------------------------------------------------------------- */

// Gutters are tight because a panel is now a quarter of the page rather than
// half of it, and the widest tick label these charts draw is four characters.
const PAD = { l: 34, r: 10, t: 10, b: 32 };

export function Frame({
  width = 340, height = 210, xDomain, yDomain, xLabel, yLabel,
  xTicks, yTicks, yLog = false, pad = PAD, children,
}) {
  const [x0, x1] = xDomain;
  const [y0, y1] = yDomain;
  const iw = width - pad.l - pad.r;
  const ih = height - pad.t - pad.b;

  const lg = (v) => Math.log10(Math.max(v, 1e-9));
  const sx = linear(x0, x1, pad.l, pad.l + iw);
  const sy = yLog
    ? (v) => linear(lg(y0), lg(y1), pad.t + ih, pad.t)(lg(v))
    : linear(y0, y1, pad.t + ih, pad.t);

  const xs = xTicks || ticks(x0, x1, 5);
  const ys = yTicks || (yLog
    ? [1, 10, 100, 1000].filter((v) => v >= y0 && v <= y1)
    : ticks(y0, y1, 4));

  // `width`/`height` are the viewBox coordinate system -- the aspect ratio and
  // the space the labels are laid out in -- not the rendered size. The svg
  // scales to whatever column Quad gives it, which is what lets four panels sit
  // in a row on a wide page and stack on a narrow one without redrawing.
  return (
    <svg viewBox={`0 0 ${width} ${height}`} width="100%"
         style={{ display: 'block' }}
         fontFamily="ui-monospace, monospace">
      {ys.map((t) => (
        <g key={`y${t}`}>
          <line x1={pad.l} x2={pad.l + iw} y1={sy(t)} y2={sy(t)}
                stroke="currentColor" strokeWidth="0.5" opacity="0.12" />
          <text x={pad.l - 5} y={sy(t) + 3} fontSize="9" textAnchor="end"
                fill="currentColor" opacity="0.5">{fmtTick(t)}</text>
        </g>
      ))}
      {xs.map((t) => (
        <text key={`x${t}`} x={sx(t)} y={pad.t + ih + 12} fontSize="9"
              textAnchor="middle" fill="currentColor" opacity="0.5">
          {fmtTick(t)}
        </text>
      ))}
      <line x1={pad.l} x2={pad.l + iw} y1={pad.t + ih} y2={pad.t + ih}
            stroke="currentColor" strokeWidth="0.8" opacity="0.35" />
      <line x1={pad.l} x2={pad.l} y1={pad.t} y2={pad.t + ih}
            stroke="currentColor" strokeWidth="0.8" opacity="0.35" />
      {xLabel && (
        <text x={pad.l + iw / 2} y={height - 4} fontSize="9" textAnchor="middle"
              fill="currentColor" opacity="0.6">{xLabel}</text>
      )}
      {yLabel && (
        <text x={9} y={pad.t + ih / 2} fontSize="9" textAnchor="middle"
              fill="currentColor" opacity="0.6"
              transform={`rotate(-90 9 ${pad.t + ih / 2})`}>{yLabel}</text>
      )}
      {children({ sx, sy, iw, ih, pad })}
    </svg>
  );
}

/* ---------------------------------------------------------------- *
 * Series: lines with points, hover-readable.
 * ---------------------------------------------------------------- */

/**
 * @param {object[]} series - `{name, color, dashed, points: [{x, y}]}`
 */
export function LineChart({
  series, xDomain, yDomain, xLabel, yLabel, yLog, width, height,
  xTicks, yTicks, hover = true, format = (p) => `${p.x}, ${fmtTick(p.y)}`,
}) {
  const [at, setAt] = useState(null);
  return (
    <div>
      <Frame {...{ width, height, xDomain, yDomain, xLabel, yLabel, yLog, xTicks, yTicks }}>
        {({ sx, sy }) => (
          <>
            {series.map((s) => (
              <g key={s.name}>
                <path
                  d={s.points.map((p, i) =>
                    `${i ? 'L' : 'M'}${sx(p.x)},${sy(p.y)}`).join(' ')}
                  fill="none" stroke={s.color} strokeWidth="1.5"
                  strokeDasharray={s.dashed ? '4 3' : undefined}
                  opacity={s.dashed ? 0.55 : 0.95} />
                {s.points.map((p) => (
                  <circle key={`${p.x}-${p.y}`} cx={sx(p.x)} cy={sy(p.y)}
                    r={at && at.s === s.name && at.p.x === p.x ? 4 : 2.4}
                    fill={s.color} opacity={s.dashed ? 0.6 : 1}
                    onMouseEnter={hover ? () => setAt({ s: s.name, p }) : undefined}
                    onMouseLeave={hover ? () => setAt(null) : undefined}
                    style={{ cursor: hover ? 'pointer' : 'default' }} />
                ))}
              </g>
            ))}
          </>
        )}
      </Frame>
      <div className="flex gap-3 flex-wrap mt-1 text-[10px] font-mono">
        {series.map((s) => (
          <span key={s.name} className="flex items-center gap-1 opacity-70">
            <svg width="14" height="6"><line x1="0" y1="3" x2="14" y2="3"
              stroke={s.color} strokeWidth="2"
              strokeDasharray={s.dashed ? '3 2' : undefined} /></svg>
            {s.name}
          </span>
        ))}
        <span className="opacity-90 ml-auto">
          {at ? `${at.s}: ${format(at.p)}` : ' '}
        </span>
      </div>
    </div>
  );
}

/* ---------------------------------------------------------------- *
 * Heatmap: a categorical grid. Cells carry their own colour because
 * the meaningful ones here are verdicts, not a continuous ramp.
 * ---------------------------------------------------------------- */

/**
 * @param {object} p
 * @param {string[]} p.cols  - column labels, left to right
 * @param {string[]} p.rows  - row labels, BOTTOM to top (matplotlib origin)
 * @param {function} p.cell  - (col, row, ci, ri) => {fill, title, text} | null
 * @param {number} [p.labelWidth] - left gutter. The default suits short row
 *   labels; a grid whose rows are named rather than numbered needs more, and
 *   says so at the call site rather than having every grid pay for it.
 */
export function Heatmap({
  cols, rows, cell, xLabel, yLabel, size = 20, gap = 1.5,
  colStride = 1, rowStride = 1, onHover, labelWidth,
}) {
  // Same reasoning as PAD above: most grids here label rows with a number -- a
  // budget, an expectation, a position. The one that labels them with predicate
  // names passes `labelWidth` instead of making every grid carry the gutter.
  const L = labelWidth ?? 38;
  const B = 28;
  const w = L + cols.length * (size + gap) + 8;
  const h = 10 + rows.length * (size + gap) + B;
  return (
    // The one chart that keeps a cap. Its cells are squares by construction, and
    // stretching the viewBox past its natural width would only make them
    // rectangles -- the grid says what it says at its own size.
    <svg viewBox={`0 0 ${w} ${h}`} width="100%" style={{ maxWidth: w, display: 'block' }}
         fontFamily="ui-monospace, monospace">
      {rows.map((r, ri) => cols.map((c, ci) => {
        const v = cell(c, r, ci, ri);
        if (!v) return null;
        // Row 0 is the bottom row: matplotlib's origin="lower", kept so the
        // axis reads the same way as the manuscript figure it replaces.
        const y = 10 + (rows.length - 1 - ri) * (size + gap);
        const x = L + ci * (size + gap);
        return (
          <g key={`${ci}-${ri}`}
             onMouseEnter={onHover ? () => onHover(v, c, r) : undefined}
             onMouseLeave={onHover ? () => onHover(null) : undefined}
             style={{ cursor: onHover ? 'pointer' : 'default' }}>
            <rect x={x} y={y} width={size} height={size} rx="2"
                  fill={v.fill} stroke={v.stroke || 'none'}
                  strokeWidth={v.stroke ? 1 : 0} opacity={v.opacity ?? 1}>
              {v.title && <title>{v.title}</title>}
            </rect>
            {v.text && (
              <text x={x + size / 2} y={y + size / 2 + 3} fontSize="8.5"
                    textAnchor="middle" fill={v.textFill || 'currentColor'}
                    opacity="0.85" pointerEvents="none">{v.text}</text>
            )}
          </g>
        );
      }))}
      {rows.map((r, ri) => (ri % rowStride ? null : (
        <text key={`r${ri}`} x={L - 5}
              y={10 + (rows.length - 1 - ri) * (size + gap) + size / 2 + 3}
              fontSize="9" textAnchor="end" fill="currentColor" opacity="0.55">
          {r}
        </text>
      )))}
      {cols.map((c, ci) => (ci % colStride ? null : (
        <text key={`c${ci}`} x={L + ci * (size + gap) + size / 2}
              y={10 + rows.length * (size + gap) + 11}
              fontSize="9" textAnchor="middle" fill="currentColor" opacity="0.55">
          {c}
        </text>
      )))}
      {xLabel && (
        <text x={L + (cols.length * (size + gap)) / 2} y={h - 3} fontSize="9"
              textAnchor="middle" fill="currentColor" opacity="0.6">{xLabel}</text>
      )}
      {yLabel && (
        <text x={9} y={10 + (rows.length * (size + gap)) / 2} fontSize="9"
              textAnchor="middle" fill="currentColor" opacity="0.6"
              transform={`rotate(-90 9 ${10 + (rows.length * (size + gap)) / 2})`}>
          {yLabel}
        </text>
      )}
    </svg>
  );
}

/* ---------------------------------------------------------------- *
 * Bars: grouped or stacked, always labelled with the value. A bar
 * whose height must be read off an axis to be believed is a bar that
 * could have been a table.
 * ---------------------------------------------------------------- */

/**
 * @param {object} p
 * @param {string[]} p.groups - one label per group along x
 * @param {object[]} p.series - `{name, color, values: number[]}`
 */
export function BarChart({
  groups, series, yLabel, width = 340, height = 200, stacked = false,
  showValues = true, valueFmt = (v) => String(v), yMax,
}) {
  const pad = { l: 32, r: 8, t: 12, b: 38 };
  const iw = width - pad.l - pad.r;
  const ih = height - pad.t - pad.b;
  const top = yMax ?? (stacked
    ? Math.max(...groups.map((_, i) => series.reduce((a, s) => a + s.values[i], 0)))
    : Math.max(...series.flatMap((s) => s.values)));
  const hi = top > 0 ? top * 1.12 : 1;
  const sy = linear(0, hi, pad.t + ih, pad.t);
  const gw = iw / groups.length;
  const bw = stacked ? gw * 0.5 : (gw * 0.72) / series.length;

  return (
    <div>
      <svg viewBox={`0 0 ${width} ${height}`} width="100%"
           style={{ display: 'block' }}
           fontFamily="ui-monospace, monospace">
        {ticks(0, hi, 4).map((t) => (
          <g key={t}>
            <line x1={pad.l} x2={pad.l + iw} y1={sy(t)} y2={sy(t)}
                  stroke="currentColor" strokeWidth="0.5" opacity="0.12" />
            <text x={pad.l - 5} y={sy(t) + 3} fontSize="9" textAnchor="end"
                  fill="currentColor" opacity="0.5">{fmtTick(t)}</text>
          </g>
        ))}
        {groups.map((g, gi) => {
          let acc = 0;
          return (
            <g key={g}>
              {series.map((s, si) => {
                const v = s.values[gi];
                const x = stacked
                  ? pad.l + gi * gw + (gw - bw) / 2
                  : pad.l + gi * gw + gw * 0.14 + si * bw;
                const y = stacked ? sy(acc + v) : sy(v);
                const hgt = Math.max(sy(0) - sy(v), v > 0 ? 1 : 0);
                acc += v;
                return (
                  <g key={s.name}>
                    <rect x={x} y={y} width={bw * 0.92} height={hgt} rx="1.5"
                          fill={s.color} opacity="0.9">
                      <title>{`${g} · ${s.name}: ${valueFmt(v)}`}</title>
                    </rect>
                    {showValues && !stacked && v > 0 && (
                      <text x={x + bw * 0.46} y={y - 3} fontSize="8"
                            textAnchor="middle" fill="currentColor" opacity="0.6">
                        {valueFmt(v)}
                      </text>
                    )}
                  </g>
                );
              })}
              <text x={pad.l + gi * gw + gw / 2} y={pad.t + ih + 12} fontSize="9"
                    textAnchor="middle" fill="currentColor" opacity="0.6">{g}</text>
            </g>
          );
        })}
        <line x1={pad.l} x2={pad.l + iw} y1={sy(0)} y2={sy(0)}
              stroke="currentColor" strokeWidth="0.8" opacity="0.35" />
        {yLabel && (
          <text x={9} y={pad.t + ih / 2} fontSize="9" textAnchor="middle"
                fill="currentColor" opacity="0.6"
                transform={`rotate(-90 9 ${pad.t + ih / 2})`}>{yLabel}</text>
        )}
      </svg>
      {series.length > 1 && (
        <div className="flex gap-3 flex-wrap mt-1 text-[10px] font-mono">
          {series.map((s) => (
            <span key={s.name} className="flex items-center gap-1 opacity-70">
              <span className="inline-block w-2.5 h-2.5 rounded-sm"
                    style={{ background: s.color }} />
              {s.name}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

/* ---------------------------------------------------------------- *
 * Scatter with families: the iso-cardinality plane.
 * ---------------------------------------------------------------- */

export function ScatterChart({
  points, families = [], xDomain, yDomain, xLabel, yLabel,
  width = 340, height = 210,
}) {
  return (
    <Frame {...{ width, height, xDomain, yDomain, xLabel, yLabel }}>
      {({ sx, sy }) => (
        <>
          {points.map((p, i) => (
            <circle key={i} cx={sx(p.x)} cy={sy(p.y)} r="1.6"
                    fill="currentColor" opacity={p.opacity ?? 0.16} />
          ))}
          {families.map((f) => (
            <g key={f.name}>
              <path d={f.points.map((p, i) =>
                      `${i ? 'L' : 'M'}${sx(p.x)},${sy(p.y)}`).join(' ')}
                    fill="none" stroke={f.color} strokeWidth="1.3" opacity="0.8" />
              {f.points.map((p, i) => (
                <circle key={i} cx={sx(p.x)} cy={sy(p.y)} r="3" fill={f.color}>
                  <title>{f.title ? f.title(p) : `${p.x}, ${p.y}`}</title>
                </circle>
              ))}
            </g>
          ))}
        </>
      )}
    </Frame>
  );
}

/* ---------------------------------------------------------------- *
 * Controls.
 * ---------------------------------------------------------------- */

export function Slider({ label, value, min, max, step = 1, onChange, format }) {
  const id = useId();
  return (
    <label htmlFor={id} className="flex items-center gap-2 text-[11px] font-mono">
      <span className="opacity-60 whitespace-nowrap">{label}</span>
      <input id={id} type="range" min={min} max={max} step={step} value={value}
             onChange={(e) => onChange(Number(e.target.value))}
             className="flex-1 min-w-[5rem] max-w-[11rem] accent-primary" />
      <span className="w-10 text-right tabular-nums">
        {format ? format(value) : value}
      </span>
    </label>
  );
}

export function Choice({ label, value, options, onChange }) {
  return (
    <div className="flex items-center gap-1.5 text-[11px] font-mono">
      {label && <span className="opacity-60">{label}</span>}
      {options.map((o) => {
        const v = Array.isArray(o) ? o[0] : o;
        const t = Array.isArray(o) ? o[1] : o;
        return (
          <button key={v} type="button" onClick={() => onChange(v)}
            className={`px-1.5 py-0.5 rounded transition-colors ${
              v === value ? 'bg-primary text-light'
                : 'opacity-55 hover:opacity-100 hover:bg-dark/[0.06] dark:hover:bg-light/[0.09]'
            }`}>
            {t}
          </button>
        );
      })}
    </div>
  );
}

/** A row of controls above a chart, and the chart's own caption of state. */
export function Controls({ children, note }) {
  return (
    <div className="flex flex-wrap items-center gap-x-5 gap-y-1.5 mb-2.5 pb-2
                    border-b border-dark/8 dark:border-light/8">
      {children}
      {note && <span className="text-[10px] font-mono opacity-45 ml-auto">{note}</span>}
    </div>
  );
}

/**
 * The four sub-panels of a figure, lettered as the manuscript figures are.
 *
 * One row where the page is wide enough to give each panel a readable column,
 * falling back through two columns to one as it narrows. The charts themselves
 * scale to whatever column they land in -- their `width` is a viewBox
 * coordinate system, not a rendered size -- so this is a real reflow rather
 * than four fixed-width drawings pushed side by side.
 *
 * Note the direction. This project's tailwind.config.js overrides `screens`
 * with max-width queries, so `lg:` reads "at most 1023px" rather than the
 * stock "at least 1024px". The widest layout is therefore the unprefixed
 * base and each prefix narrows it -- writing this the mobile-first way round
 * silently yields one column on a desktop, which is the bug this replaces.
 */
export function Quad({ children }) {
  return (
    <div className="grid grid-cols-4 lg:grid-cols-2 sm:grid-cols-1 gap-x-5 gap-y-4">
      {children}
    </div>
  );
}

export function Sub({ letter, title, children }) {
  return (
    <div className="min-w-0">
      <h4 className="text-[11px] font-mono mb-1.5 leading-snug min-h-[2.2em]">
        <span className="opacity-40">({letter})</span>{' '}
        <span className="opacity-75">{title}</span>
      </h4>
      {/* Only the heatmap has a fixed natural width now, so this is the escape
          hatch for that one case; everything else scales and never reaches it. */}
      <div className="overflow-x-auto">{children}</div>
    </div>
  );
}

/** A small measured-fact line under a chart: the number, and what it means. */
export function Readout({ children }) {
  return (
    <p className="text-[11px] font-mono mt-1.5 opacity-65 leading-relaxed">
      {children}
    </p>
  );
}
