import { spawn } from 'child_process';
import path from 'path';

// The notebook executes the SAME interpreter the validation suite runs: this
// route shells to ckg/validation-federated/hfq_serve.py rather than
// reimplementing parse/check/allocate/execute in JavaScript. A second
// implementation could drift, and every verdict shown would then be a claim
// about the reimplementation rather than a reading of the validated one.
//
// Every adapter resolves against a local fixture. No request leaves the
// machine, by construction rather than by configuration.

const HFQ_DIR = path.join(process.cwd(), '..', 'ckg', 'validation-federated');
const TIMEOUT_MS = 15000;
const MAX_SOURCE = 20000;

function runPlan(source) {
  return new Promise((resolve) => {
    const py = process.env.HFQ_PYTHON || 'python';
    let child;
    try {
      child = spawn(py, ['hfq_serve.py'], {
        cwd: HFQ_DIR,
        env: { ...process.env, PYTHONIOENCODING: 'utf-8' },
      });
    } catch (e) {
      return resolve({ ok: false, stage: 'spawn', error: String(e) });
    }

    let out = '', err = '', settled = false;
    const done = (v) => { if (!settled) { settled = true; resolve(v); } };

    const timer = setTimeout(() => {
      child.kill('SIGKILL');
      done({ ok: false, stage: 'timeout',
             error: `execution exceeded ${TIMEOUT_MS} ms and was killed` });
    }, TIMEOUT_MS);

    child.stdout.on('data', (d) => { out += d; });
    child.stderr.on('data', (d) => { err += d; });
    child.on('error', (e) => {
      clearTimeout(timer);
      done({ ok: false, stage: 'spawn',
             error: `cannot start ${py}: ${e.message}` });
    });
    child.on('close', (code) => {
      clearTimeout(timer);
      if (!out.trim()) {
        return done({ ok: false, stage: 'internal',
                      error: err.trim() || `runner exited ${code} with no output` });
      }
      try {
        done(JSON.parse(out));
      } catch {
        done({ ok: false, stage: 'internal',
               error: 'runner emitted unparseable output',
               detail: out.slice(0, 2000) });
      }
    });

    child.stdin.on('error', () => {});
    child.stdin.end(source, 'utf-8');
  });
}

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST');
    return res.status(405).json({ ok: false, stage: 'request',
                                  error: 'use POST' });
  }
  const source = (req.body && req.body.source) || '';
  if (typeof source !== 'string' || !source.trim()) {
    return res.status(400).json({ ok: false, stage: 'request',
                                  error: 'empty plan' });
  }
  if (source.length > MAX_SOURCE) {
    return res.status(413).json({ ok: false, stage: 'request',
                                  error: `plan exceeds ${MAX_SOURCE} characters` });
  }
  const result = await runPlan(source);
  return res.status(200).json(result);
}
