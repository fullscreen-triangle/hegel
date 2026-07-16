# Integrating Hegel (SBS) into Buhera OS

This is the exact procedure to make Hegel's Systems Biology Shaders (SBS) DSL
runnable inside Buhera OS, so a user can `dispatch("sbs", "<script>")` in the
Buhera terminal and get back a circuit, metrics, and charts.

The SBS code lives **only** in Hegel. You do **not** copy it into Buhera. You
build it into a single package file (a tarball) and install that file into
Buhera like any npm dependency.

---

## The two locations

| Name | Path |
|------|------|
| **Hegel** (source of truth for SBS) | `C:\Users\kunda\Documents\systems\hegel\consequences` |
| **Buhera OS** (the app that runs SBS) | `C:\Users\kunda\Documents\architecture\buhera\long-grass` |

The SBS package source is `hegel/consequences/src/lib/sbs/`. Edit it there and
nowhere else.

---

## Part A — One-time setup (do this once)

If SBS is already working in Buhera, skip to **Part B** (updating). Do Part A
only on a fresh Buhera checkout, or if the package was never installed.

### A1. Install the package into Buhera

Open a shell (Git Bash or PowerShell) and run these three commands in order.

```bash
# 1. Build the SBS package into a tarball, placing it in Buhera.
cd "C:/Users/kunda/Documents/systems/hegel/consequences/src/lib/sbs"
npm pack --pack-destination "C:/Users/kunda/Documents/architecture/buhera/long-grass"

# 2. Install that tarball into Buhera as a dependency.
cd "C:/Users/kunda/Documents/architecture/buhera/long-grass"
npm install ./sachikonye-sbs-0.1.0.tgz

# 3. Install d3 (used by the SBS chart component).
npm install d3@^7.9.0
```

After this, Buhera's `package.json` contains:

```json
"@sachikonye/sbs": "file:sachikonye-sbs-0.1.0.tgz",
"d3": "^7.9.0"
```

### A2. Confirm Buhera's next.config.js transpiles the package

Open `long-grass/next.config.js`. It must contain this line inside the config
object (it is already there in the current Buhera):

```js
transpilePackages: ["@sachikonye/sbs"],
```

If it is missing, add it. Without it the build fails, because Next.js does not
compile packages in `node_modules` by default and the SBS package is ESM.

### A3. Confirm the module is registered in the terminal

Open `long-grass/src/components/BuheraTerminal.js`. These lines must be present
(they are already there in the current Buhera):

```js
// near the other module imports:
import { sbsModule } from "@/lib/modules/sbs-module";
import { MetricsDashboard } from "@sachikonye/sbs/react";

// inside the mount useEffect, next to the other register() calls:
register(sbsModule);

// inside the Artifact switch, next to the other cases:
case "sbs_result":
  return <ArtifactSBS summary={result.summary} circuit={result.circuit}
    metrics={result.metrics} navigation={result.navigation}
    warnings={result.warnings} />;
```

The `sbs-module.js` adapter and the `ArtifactSBS` renderer are already in
Buhera. If setting up a brand-new Buhera, copy `sbs-module.js` from a working
checkout, or see Part D.

### A4. Build once to verify

```bash
cd "C:/Users/kunda/Documents/architecture/buhera/long-grass"
rm -rf .next
npm run build
```

It should end with `Compiled successfully`. (On Windows you may see a line
`Assertion failed: !(handle->flags...` after it finishes — that is harmless
teardown noise, not a build failure, as long as a `.next/BUILD_ID` file exists.)

### A5. Run it

```bash
npm run dev
```

Open the Buhera terminal in the browser and type:

```
dispatch("sbs", "demo")
```

You should see the glycolysis circuit result with R, V, and charts — not a
"runtime is not installed" message.

---

## Part B — Updating SBS after you change the code

Whenever you edit anything under `hegel/consequences/src/lib/sbs/`, Buhera keeps
running the **old** copy until you rebuild and reinstall the tarball. Do this:

```bash
# 1. Re-pack from Hegel into Buhera (overwrites the old tarball).
cd "C:/Users/kunda/Documents/systems/hegel/consequences/src/lib/sbs"
npm pack --pack-destination "C:/Users/kunda/Documents/architecture/buhera/long-grass"

# 2. Force npm to reinstall from the tarball (the version is unchanged, so
#    npm would otherwise skip it).
cd "C:/Users/kunda/Documents/architecture/buhera/long-grass"
npm install --force ./sachikonye-sbs-0.1.0.tgz

# 3. Clear Next's cache and restart the dev server.
rm -rf .next
npm run dev
```

> **Tip:** if you bump the `version` in
> `hegel/consequences/src/lib/sbs/package.json` (e.g. to `0.1.1`), the tarball
> filename changes to `sachikonye-sbs-0.1.1.tgz`. Then step 2 becomes
> `npm install ./sachikonye-sbs-0.1.1.tgz` (no `--force` needed) and you update
> the filename in `package.json`. Bumping the version is the cleaner habit.

---

## Part C — Things that will bite you (read this)

- **Do NOT use `npm link`.** It creates a machine-global symlink that ordinary
  `npm install` runs silently delete, and it once got hijacked by a stub
  package. The tarball is deliberate and stable; keep using it.

- **You do NOT copy `src/lib/sbs/` into Buhera.** The only SBS file that lives
  in Buhera's own source is the thin adapter
  `long-grass/src/lib/modules/sbs-module.js`. Everything else comes in through
  the installed package.

- **If Buhera shows "runtime is not installed"** or an SBS stub message, the
  real package is not installed. Re-run Part A1, then Part B step 3.

- **Restart `npm run dev` after any reinstall.** The running dev server caches
  the old resolution in memory; clearing `.next` alone is not enough.

- **The tarball is a snapshot.** Editing SBS in Hegel does nothing to Buhera
  until you re-pack and reinstall (Part B). This is expected.

---

## Part D — What is inside the package (reference)

The package `@sachikonye/sbs` exposes two entry points:

- `@sachikonye/sbs` — the runtime. Main function:
  `runSBS(source)` → `{ ok, circuit, metrics, navigation, observations,
  perturbations, warnings, errors, glsl }`. It compiles the `.sbs` script,
  renders the S-entropy observation on WebGL2 (falling back to CPU), and
  extracts metrics. Also exports `checkSBS(source)` and `suggestTherapy(...)`.

- `@sachikonye/sbs/react` — presentational React components. Currently
  `MetricsDashboard`, which draws the S-entropy scatter, flux chart, and
  backward-navigation path from `runSBS` output. Requires `d3`.

Buhera's adapter `sbs-module.js` calls `runSBS(instruction)` and maps the
result to an `ActResult` with `output_delta.kind = "sbs_result"`. The terminal's
`ArtifactSBS` renderer reads that and draws `<MetricsDashboard />`.

---

## Quick reference (the whole thing, once it's set up)

```bash
# after editing SBS in Hegel, run SBS afresh in Buhera:
cd "C:/Users/kunda/Documents/systems/hegel/consequences/src/lib/sbs"
npm pack --pack-destination "C:/Users/kunda/Documents/architecture/buhera/long-grass"
cd "C:/Users/kunda/Documents/architecture/buhera/long-grass"
npm install --force ./sachikonye-sbs-0.1.0.tgz
rm -rf .next && npm run dev
```
