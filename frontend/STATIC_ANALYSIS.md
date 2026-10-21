# Frontend static analysis

Static-analysis run of `frontend/` (Next.js 15, TypeScript 6, ESLint 9) against `main`
(`e6736f5`, Release v1.2.1). No application code was changed. All failures below already exist on `main`.

Reproduce with `frontend/scripts/static-check.sh` (see the header of the script for options).

## Environment

| Tool | Version |
| --- | --- |
| Node | v20.20.2 |
| npm | 10.8.2 (fallback: npm 11.21.1 via `npx -y npm@11`) |
| Next.js | 15.5.23 |
| TypeScript | 6.0.3 |
| ESLint | 9.39.5 (`eslint-config-next` ^16.3.3) |

Node 20 is below the `>=22` engine range of `blockly`/`kysely`; npm only prints `EBADENGINE` warnings.

## Results

| Step | Command (from `frontend/`) | Exit code | Result |
| --- | --- | --- | --- |
| Clean install | `npm ci` (npm 10.8.2) | 1 | `Missing: @swc/helpers@0.5.23 from lock file` |
| Clean install | `npx -y npm@11 ci` (npm 11.21.1) | 1 | `Missing: sharp@ from lock file` |
| Fallback install | `npx -y npm@11 install --ignore-scripts` | 0 | OK, `package.json`/`package-lock.json` unchanged |
| Type check | `npx tsc --noEmit` | 0 | No errors (no output) |
| Lint | `npm run lint` (`next lint`) | 1 | 244 errors, 44 warnings (`next lint` prints a deprecation notice) |
| Lint | `npx eslint .` | 1 | 288 problems (244 errors, 44 warnings) in 64 of 120 files |
| Lint | `npx eslint src` | 1 | 287 problems (244 errors, 43 warnings) |

## `npm ci` failure: root cause

`npm ci` refuses to install because `package-lock.json` does not match the tree that npm computes from
`package.json` (including `overrides`). Each npm major reports a different missing entry:

- **npm 11: `Missing: sharp@`.** `package.json` overrides `sharp` with `npm:empty-module@1.0.0`.
  `next@15.5.23` lists `sharp ^0.34.3` as an optional dependency, so the expected tree has a
  `node_modules/sharp` (aliased to `empty-module`). The lockfile has no `node_modules/sharp` entry at
  all, so the lock is out of sync with the override. Fix: regenerate the lockfile with `npm install`
  (npm 11) and commit it.
- **npm 10: `Missing: @swc/helpers@0.5.23`.** The lockfile only has `@swc/helpers@0.5.15`, which `next`
  pins exactly. `@swc/core@1.16.1` (pulled in by `next-intl@4.14.1`) declares an optional peer
  `@swc/helpers >=0.5.17`. npm 10 tries to satisfy that peer with a nested `@swc/helpers@0.5.23`,
  which isn't in the lock. npm 11 doesn't hit this check and stops at the `sharp` entry instead.
  (This is inferred from the lockfile contents and the error message.)
- In this run, npm 10 `npm ci` failed with the error above and did not crash. The
  `Cannot read properties of undefined (reading 'edgesOut')` crash seen before comes from npm 10
  `npm install`, so the fallback uses npm 11.

The fallback `npx -y npm@11 install --ignore-scripts` installs from the existing lockfile and leaves
the tracked files unchanged. The script still restores them with `git checkout` if they change.

## TypeScript

`npx tsc --noEmit` exits 0 with no diagnostics (`strict: true`, `skipLibCheck: true`).

## ESLint summary (`npx eslint .`)

`next lint` reports the same 244 errors / 44 warnings. The one extra file `eslint .` covers outside
`src/` is `eslint.config.js` (1 warning, `import/no-anonymous-default-export`).

### By rule

| Rule | Errors | Warnings | Total |
| --- | ---: | ---: | ---: |
| `no-unused-vars` | 130 | 0 | 130 |
| `react-hooks/exhaustive-deps` | 0 | 40 | 40 |
| `no-empty` | 40 | 0 | 40 |
| `react-hooks/set-state-in-effect` | 25 | 0 | 25 |
| `no-undef` | 22 | 0 | 22 |
| `react/display-name` | 10 | 0 | 10 |
| `react-hooks/rules-of-hooks` | 7 | 0 | 7 |
| `react-hooks/refs` | 7 | 0 | 7 |
| `@next/next/no-img-element` | 0 | 2 | 2 |
| `import/no-anonymous-default-export` | 0 | 1 | 1 |
| `no-irregular-whitespace` | 1 | 0 | 1 |
| `no-control-regex` | 1 | 0 | 1 |
| `jsx-a11y/role-supports-aria-props` | 0 | 1 | 1 |
| `react-hooks/immutability` | 1 | 0 | 1 |
| **Total** | **244** | **44** | **288** |

### Top files

| File | Errors | Warnings | Total |
| --- | ---: | ---: | ---: |
| `src/components/map/MapImage.tsx` | 19 | 8 | 27 |
| `src/components/map/IntersectionListPanel.tsx` | 20 | 1 | 21 |
| `src/components/map/IntersectionDraw.tsx` | 18 | 1 | 19 |
| `src/components/map/AreaListPanel.tsx` | 17 | 0 | 17 |
| `src/components/map/MapDraw.tsx` | 17 | 0 | 17 |
| `src/components/map/MapDrawMarker.tsx` | 8 | 3 | 11 |
| `src/components/map/MapLayerPanel.tsx` | 11 | 0 | 11 |
| `src/components/robot/JobCard.tsx` | 9 | 1 | 10 |
| `src/app/[locale]/log/page.tsx` | 9 | 0 | 9 |
| `src/components/map/NodeMarkers.tsx` | 7 | 1 | 8 |
| `src/app/[locale]/admin/access-control/JobTab.tsx` | 6 | 1 | 7 |
| `src/app/[locale]/admin/access-control/NodeTab.tsx` | 6 | 1 | 7 |

`src/components/map/` accounts for 131 of the 288 problems.

### Observations

- Most errors come from the config, not the code. `eslint.config.js` applies `js.configs.recommended`
  to TS files, and its base `no-unused-vars` and `no-undef` rules are not TypeScript-aware. All 130
  `no-unused-vars` hits are in `.ts`/`.tsx` files, many on parameter names inside function *types*
  (e.g. `(index: number) => void`). The 22 `no-undef` hits are `'React' is not defined` (20, from
  type-only `React.*` references) and the DOM type `ScrollBehavior` (2). `tsc` passes, so these are not
  real undefined references. Replacing them with `@typescript-eslint/no-unused-vars` and turning
  `no-undef` off for TS files would remove most of them.
- The remaining errors come from the React Compiler rules in `eslint-config-next` 16
  (`react-hooks/set-state-in-effect`, `refs`, `immutability`), plus 40 empty `catch {}` blocks
  (`no-empty`), 10 missing display names on `forwardRef`/`memo` components, and 7
  `rules-of-hooks` violations. The `rules-of-hooks` violations are worth reviewing as possible
  real bugs.
- `next lint` is deprecated in Next.js 15.5 and will be removed in Next.js 16. The `lint` script
  should move to `eslint .`. Loading `eslint.config.js` also prints `MODULE_TYPELESS_PACKAGE_JSON`
  because `package.json` has no `"type": "module"`.
