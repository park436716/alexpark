# Trading Performance Review Dashboard

A dynamic, customizable dashboard for weekly/monthly trading review templates. No build step, no backend — open `index.html` in a browser or serve the folder statically. All data is stored in the browser's `localStorage`.

## Features

- **Weekly review**: "What did I do well / struggle with / how will I improve," plus setup tags (with net R per setup) and mistake tags grouped by trade lifecycle phase (Execution / Management / Closure). Saving by ISO week label overwrites that week's entry cleanly.
- **Monthly review**: best/worst setups, common mistakes, adjustment plan, with an auto-computed net-R-by-setup scorecard pulled from that month's weekly logs.
- **Setups & Tags**: editable setup list and mistake tags per phase — the framework evolves without rebuilding the app.
- **Pattern dashboard**:
  - Active streaks — any tag present in 2+ of the most recent consecutive logged weeks.
  - Punch-card grid — tags x weeks.
  - Setup scorecard — net R per setup per month, best/worst highlighted.
- **AI analysis** — sends every saved weekly/monthly review to the Anthropic Messages API and asks for the 3-5 strongest patterns, especially contradictions between stated improvement plans and later behavior. Requires an Anthropic API key, entered under Settings and stored only in `localStorage`.
- **Export/Import/Reset** under Settings for backing up or clearing your data.

## Running

```
cd trading-review-dashboard
python3 -m http.server 8000
```

Then open `http://localhost:8000`.
