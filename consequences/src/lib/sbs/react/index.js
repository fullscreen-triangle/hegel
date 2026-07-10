/* ============================================================================
 * @sachikonye/sbs/react — presentational components for runSBS output.
 *
 * These render the data returned by runSBS(source). They are props-only and
 * host-agnostic (no app context, neutral styling, d3 via `currentColor`), so
 * any React host can show the same charts hegel shows.
 *
 *   import { runSBS } from '@sachikonye/sbs';
 *   import { MetricsDashboard } from '@sachikonye/sbs/react';
 *
 *   const r = runSBS(source);
 *   <MetricsDashboard metrics={r.metrics} circuit={r.circuit}
 *                     navigation={r.navigation} />
 * ========================================================================== */

export { default as MetricsDashboard } from './MetricsDashboard.jsx';
