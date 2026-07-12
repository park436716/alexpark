// ---------- Persistence ----------

const STORAGE_KEY = 'trd-data-v1';

function defaultData() {
  return {
    settings: { apiKey: '', model: 'claude-sonnet-5' },
    setups: ['Range Extreme', 'Range Extreme SFP', 'Mean Reversion', 'Mean Reversion SFP'],
    phases: ['Execution', 'Management', 'Closure'],
    mistakeTags: {
      Execution: ['Chased entry', 'Sized too big', 'Ignored invalidation level'],
      Management: ['Moved stop against plan', 'Failed to scale out', 'Overtraded add-ons'],
      Closure: ['Exited too early', 'Held past target', 'No post-trade note']
    },
    weekly: {},
    monthly: {}
  };
}

function loadData() {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) return defaultData();
  try {
    const parsed = JSON.parse(raw);
    const d = defaultData();
    return Object.assign(d, parsed, {
      settings: Object.assign(d.settings, parsed.settings || {}),
      mistakeTags: Object.assign({}, d.mistakeTags, parsed.mistakeTags || {})
    });
  } catch (e) {
    console.error('Failed to parse stored data, resetting.', e);
    return defaultData();
  }
}

let DATA = loadData();

function persist() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(DATA));
}

// ---------- Date / ISO week helpers ----------

function mondayOf(date) {
  const d = new Date(date);
  d.setHours(0, 0, 0, 0);
  const day = (d.getDay() + 6) % 7; // 0 = Monday
  d.setDate(d.getDate() - day);
  return d;
}

function pad2(n) { return String(n).padStart(2, '0'); }

function firstThursday(year) {
  const d = new Date(year, 0, 1);
  while (d.getDay() !== 4) d.setDate(d.getDate() + 1);
  return d;
}

function isoWeekLabel(date) {
  const monday = mondayOf(date);
  const thursday = new Date(monday);
  thursday.setDate(thursday.getDate() + 3);
  const year = thursday.getFullYear();
  const week = 1 + Math.round((thursday - firstThursday(year)) / (7 * 86400000));
  return `${year}-W${pad2(week)}`;
}

function mondayFromWeekLabel(label) {
  const [yearStr, weekStr] = label.split('-W');
  const year = parseInt(yearStr, 10);
  const week = parseInt(weekStr, 10);
  const thursday = new Date(firstThursday(year));
  thursday.setDate(thursday.getDate() + (week - 1) * 7);
  const monday = new Date(thursday);
  monday.setDate(monday.getDate() - 3);
  return monday;
}

function fmtDate(d) {
  return `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}`;
}

function monthLabelFromWeekLabel(label) {
  const monday = mondayFromWeekLabel(label);
  return `${monday.getFullYear()}-${pad2(monday.getMonth() + 1)}`;
}

// ---------- Tab switching ----------

document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById('tab-' + btn.dataset.tab).classList.add('active');
    if (btn.dataset.tab === 'dashboard') renderDashboard();
    if (btn.dataset.tab === 'monthly') renderMonthlyScorecardPreview();
  });
});

// ---------- Weekly tab ----------

function sortedWeekLabels() {
  return Object.keys(DATA.weekly).sort((a, b) => mondayFromWeekLabel(a) - mondayFromWeekLabel(b));
}

function refreshWeeklySelect() {
  const sel = document.getElementById('weekly-select');
  const current = sel.value;
  sel.innerHTML = '<option value="">-- select a saved week --</option>';
  sortedWeekLabels().slice().reverse().forEach(label => {
    const opt = document.createElement('option');
    opt.value = label;
    opt.textContent = label;
    sel.appendChild(opt);
  });
  if (sortedWeekLabels().includes(current)) sel.value = current;
}

function renderWeeklyTagInputs(entry) {
  const setupResults = (entry && entry.setupResults) || [];
  const mistakes = (entry && entry.mistakes) || [];

  const setupsWrap = document.getElementById('weekly-setups-list');
  setupsWrap.innerHTML = '';
  DATA.setups.forEach(setup => {
    const existing = setupResults.find(s => s.setup === setup);
    const row = document.createElement('div');
    row.className = 'chip-row' + (existing ? ' active' : '');
    row.innerHTML = `
      <input type="checkbox" class="setup-check" data-setup="${escapeAttr(setup)}" ${existing ? 'checked' : ''}>
      <label>${escapeHtml(setup)}</label>
      <input type="number" step="0.1" class="setup-r" data-setup="${escapeAttr(setup)}" placeholder="Net R" value="${existing ? existing.r : ''}">
    `;
    const check = row.querySelector('.setup-check');
    check.addEventListener('change', () => row.classList.toggle('active', check.checked));
    setupsWrap.appendChild(row);
  });

  const mistakesWrap = document.getElementById('weekly-mistakes-list');
  mistakesWrap.innerHTML = '';
  DATA.phases.forEach(phase => {
    const title = document.createElement('div');
    title.className = 'mistake-phase-title';
    title.textContent = phase;
    mistakesWrap.appendChild(title);
    const phaseWrap = document.createElement('div');
    phaseWrap.className = 'mistake-phase';
    (DATA.mistakeTags[phase] || []).forEach(tag => {
      const isChecked = mistakes.some(m => m.tag === tag && m.phase === phase);
      const row = document.createElement('div');
      row.className = 'chip-row' + (isChecked ? ' active' : '');
      row.innerHTML = `
        <input type="checkbox" class="mistake-check" data-tag="${escapeAttr(tag)}" data-phase="${escapeAttr(phase)}" ${isChecked ? 'checked' : ''}>
        <label>${escapeHtml(tag)}</label>
      `;
      const check = row.querySelector('.mistake-check');
      check.addEventListener('change', () => row.classList.toggle('active', check.checked));
      phaseWrap.appendChild(row);
    });
    mistakesWrap.appendChild(phaseWrap);
  });
}

function loadWeeklyEntry(label) {
  const entry = DATA.weekly[label];
  document.getElementById('weekly-label').value = label;
  const monday = mondayFromWeekLabel(label);
  const sunday = new Date(monday);
  sunday.setDate(sunday.getDate() + 6);
  document.getElementById('weekly-range').textContent = `${label}  (${fmtDate(monday)} to ${fmtDate(sunday)})`;
  document.getElementById('weekly-well').value = entry ? entry.well : '';
  document.getElementById('weekly-struggle').value = entry ? entry.struggle : '';
  document.getElementById('weekly-improve').value = entry ? entry.improve : '';
  renderWeeklyTagInputs(entry);
  const sel = document.getElementById('weekly-select');
  if (sortedWeekLabels().includes(label)) sel.value = label;
  document.getElementById('weekly-saved-msg').textContent = '';
}

document.getElementById('weekly-new-btn').addEventListener('click', () => {
  const dateVal = document.getElementById('weekly-date').value;
  const selVal = document.getElementById('weekly-select').value;
  if (dateVal) {
    const label = isoWeekLabel(new Date(dateVal + 'T00:00:00'));
    loadWeeklyEntry(label);
  } else if (selVal) {
    loadWeeklyEntry(selVal);
  } else {
    loadWeeklyEntry(isoWeekLabel(new Date()));
  }
});

document.getElementById('weekly-select').addEventListener('change', (e) => {
  if (e.target.value) loadWeeklyEntry(e.target.value);
});

document.getElementById('weekly-form').addEventListener('submit', (e) => {
  e.preventDefault();
  const label = document.getElementById('weekly-label').value || isoWeekLabel(new Date());
  const monday = mondayFromWeekLabel(label);

  const setupResults = [];
  document.querySelectorAll('#weekly-setups-list .chip-row').forEach(row => {
    const check = row.querySelector('.setup-check');
    if (check.checked) {
      const rInput = row.querySelector('.setup-r');
      const r = parseFloat(rInput.value);
      setupResults.push({ setup: check.dataset.setup, r: isNaN(r) ? 0 : r });
    }
  });

  const mistakes = [];
  document.querySelectorAll('#weekly-mistakes-list .mistake-check').forEach(check => {
    if (check.checked) mistakes.push({ tag: check.dataset.tag, phase: check.dataset.phase });
  });

  DATA.weekly[label] = {
    weekLabel: label,
    startDate: fmtDate(monday),
    well: document.getElementById('weekly-well').value.trim(),
    struggle: document.getElementById('weekly-struggle').value.trim(),
    improve: document.getElementById('weekly-improve').value.trim(),
    setupResults,
    mistakes,
    updatedAt: new Date().toISOString()
  };
  persist();
  refreshWeeklySelect();
  refreshMonthlySelect();
  document.getElementById('weekly-saved-msg').textContent = `Saved ${label}.`;
});

// ---------- Monthly tab ----------

function sortedMonthLabels() {
  return Object.keys(DATA.monthly).sort();
}

function allMonthLabelsFromWeeks() {
  const set = new Set(sortedMonthLabels());
  sortedWeekLabels().forEach(w => set.add(monthLabelFromWeekLabel(w)));
  return Array.from(set).sort();
}

function refreshMonthlySelect() {
  const sel = document.getElementById('monthly-select');
  const current = sel.value;
  sel.innerHTML = '<option value="">-- select a month --</option>';
  allMonthLabelsFromWeeks().slice().reverse().forEach(label => {
    const opt = document.createElement('option');
    opt.value = label;
    opt.textContent = label;
    sel.appendChild(opt);
  });
  if (allMonthLabelsFromWeeks().includes(current)) sel.value = current;
}

function computeSetupNetRByMonth() {
  // { monthLabel: { setupName: netR } }
  const result = {};
  sortedWeekLabels().forEach(label => {
    const entry = DATA.weekly[label];
    const month = monthLabelFromWeekLabel(label);
    if (!result[month]) result[month] = {};
    (entry.setupResults || []).forEach(sr => {
      result[month][sr.setup] = (result[month][sr.setup] || 0) + sr.r;
    });
  });
  return result;
}

function renderMonthlyScorecardPreview() {
  const label = document.getElementById('monthly-label').value;
  const wrap = document.getElementById('monthly-scorecard');
  if (!label) { wrap.innerHTML = ''; return; }
  const byMonth = computeSetupNetRByMonth();
  const scores = byMonth[label] || {};
  const setups = Object.keys(scores);
  if (!setups.length) {
    wrap.innerHTML = '<p class="hint">No weekly setup results logged for this month yet.</p>';
    return;
  }
  setups.sort((a, b) => scores[b] - scores[a]);
  let html = '<p class="hint">Auto-computed from this month\'s weekly logs:</p><table><tr><th>Setup</th><th>Net R</th></tr>';
  setups.forEach((s, i) => {
    const cls = i === 0 ? 'best' : (i === setups.length - 1 && setups.length > 1 ? 'worst' : '');
    html += `<tr><td>${escapeHtml(s)}</td><td class="${cls}">${scores[s].toFixed(2)}</td></tr>`;
  });
  html += '</table>';
  wrap.innerHTML = html;
}

function loadMonthlyEntry(label) {
  const entry = DATA.monthly[label];
  document.getElementById('monthly-label').value = label;
  document.getElementById('monthly-setups').value = entry ? entry.setupsText : '';
  document.getElementById('monthly-mistakes').value = entry ? entry.mistakesText : '';
  document.getElementById('monthly-adjust').value = entry ? entry.adjustText : '';
  const sel = document.getElementById('monthly-select');
  if (allMonthLabelsFromWeeks().includes(label)) sel.value = label;
  document.getElementById('monthly-saved-msg').textContent = '';
  renderMonthlyScorecardPreview();
}

document.getElementById('monthly-new-btn').addEventListener('click', () => {
  const dateVal = document.getElementById('monthly-date').value; // "YYYY-MM"
  const selVal = document.getElementById('monthly-select').value;
  if (dateVal) {
    loadMonthlyEntry(dateVal);
  } else if (selVal) {
    loadMonthlyEntry(selVal);
  } else {
    const now = new Date();
    loadMonthlyEntry(`${now.getFullYear()}-${pad2(now.getMonth() + 1)}`);
  }
});

document.getElementById('monthly-select').addEventListener('change', (e) => {
  if (e.target.value) loadMonthlyEntry(e.target.value);
});

document.getElementById('monthly-form').addEventListener('submit', (e) => {
  e.preventDefault();
  const now = new Date();
  const label = document.getElementById('monthly-label').value || `${now.getFullYear()}-${pad2(now.getMonth() + 1)}`;
  DATA.monthly[label] = {
    monthLabel: label,
    setupsText: document.getElementById('monthly-setups').value.trim(),
    mistakesText: document.getElementById('monthly-mistakes').value.trim(),
    adjustText: document.getElementById('monthly-adjust').value.trim(),
    updatedAt: new Date().toISOString()
  };
  persist();
  refreshMonthlySelect();
  document.getElementById('monthly-saved-msg').textContent = `Saved ${label}.`;
});

// ---------- Framework tab ----------

function renderFramework() {
  const setupsList = document.getElementById('setups-list');
  setupsList.innerHTML = '';
  DATA.setups.forEach((setup, idx) => {
    const li = document.createElement('li');
    li.innerHTML = `<span>${escapeHtml(setup)}</span><button class="remove-btn" data-idx="${idx}">Remove</button>`;
    li.querySelector('.remove-btn').addEventListener('click', () => {
      DATA.setups.splice(idx, 1);
      persist();
      renderFramework();
    });
    setupsList.appendChild(li);
  });

  const phasesWrap = document.getElementById('phases-container');
  phasesWrap.innerHTML = '';
  DATA.phases.forEach(phase => {
    const block = document.createElement('div');
    block.className = 'framework-block';
    block.innerHTML = `<h4 style="margin:0 0 0.5rem;">${escapeHtml(phase)}</h4>
      <ul class="editable-list" data-phase="${escapeAttr(phase)}"></ul>
      <div class="add-row">
        <input type="text" class="new-tag-input" placeholder="New mistake tag">
        <button class="add-tag-btn">Add</button>
      </div>`;
    const ul = block.querySelector('ul');
    (DATA.mistakeTags[phase] || []).forEach((tag, idx) => {
      const li = document.createElement('li');
      li.innerHTML = `<span>${escapeHtml(tag)}</span><button class="remove-btn" data-idx="${idx}">Remove</button>`;
      li.querySelector('.remove-btn').addEventListener('click', () => {
        DATA.mistakeTags[phase].splice(idx, 1);
        persist();
        renderFramework();
      });
      ul.appendChild(li);
    });
    const input = block.querySelector('.new-tag-input');
    block.querySelector('.add-tag-btn').addEventListener('click', () => {
      const val = input.value.trim();
      if (!val) return;
      if (!DATA.mistakeTags[phase]) DATA.mistakeTags[phase] = [];
      DATA.mistakeTags[phase].push(val);
      persist();
      renderFramework();
    });
    phasesWrap.appendChild(block);
  });
}

document.getElementById('add-setup-btn').addEventListener('click', () => {
  const input = document.getElementById('new-setup-input');
  const val = input.value.trim();
  if (!val) return;
  DATA.setups.push(val);
  persist();
  input.value = '';
  renderFramework();
});

// ---------- Dashboard tab ----------

function allTagsForPunchcard() {
  const tags = [];
  DATA.setups.forEach(s => tags.push({ label: s, type: 'setup' }));
  DATA.phases.forEach(phase => {
    (DATA.mistakeTags[phase] || []).forEach(t => tags.push({ label: `${t} (${phase})`, type: 'mistake', raw: t, phase }));
  });
  return tags;
}

function weekHasTag(entry, tagInfo) {
  if (!entry) return false;
  if (tagInfo.type === 'setup') return (entry.setupResults || []).some(sr => sr.setup === tagInfo.label);
  return (entry.mistakes || []).some(m => m.tag === tagInfo.raw && m.phase === tagInfo.phase);
}

function computeStreaks() {
  const weeks = sortedWeekLabels();
  const tags = allTagsForPunchcard();
  const streaks = [];
  tags.forEach(tagInfo => {
    let streak = 0;
    for (let i = weeks.length - 1; i >= 0; i--) {
      if (weekHasTag(DATA.weekly[weeks[i]], tagInfo)) streak++;
      else break;
    }
    if (streak >= 2) streaks.push({ label: tagInfo.label, streak, weeks: weeks.slice(weeks.length - streak) });
  });
  streaks.sort((a, b) => b.streak - a.streak);
  return streaks;
}

function renderStreaks() {
  const wrap = document.getElementById('streaks-list');
  const streaks = computeStreaks();
  if (!streaks.length) {
    wrap.innerHTML = '<p class="hint">No active streaks yet. Log at least two consecutive weeks to see alerts.</p>';
    return;
  }
  wrap.innerHTML = streaks.map(s =>
    `<div class="streak-item"><span class="count">${s.streak}&times;</span> ${escapeHtml(s.label)} <span class="hint">(${s.weeks.join(', ')})</span></div>`
  ).join('');
}

function renderPunchcard() {
  const weeks = sortedWeekLabels();
  const wrap = document.getElementById('punchcard-wrap');
  if (!weeks.length) {
    wrap.innerHTML = '<p class="hint">No weekly reviews logged yet.</p>';
    return;
  }
  const tags = allTagsForPunchcard();
  let html = '<table><tr><th>Tag</th>' + weeks.map(w => `<th>${w}</th>`).join('') + '</tr>';
  tags.forEach(tagInfo => {
    html += `<tr><td style="text-align:left;">${escapeHtml(tagInfo.label)}</td>`;
    weeks.forEach(w => {
      const has = weekHasTag(DATA.weekly[w], tagInfo);
      html += `<td class="${has ? 'filled' : ''}">${has ? '●' : ''}</td>`;
    });
    html += '</tr>';
  });
  html += '</table>';
  wrap.innerHTML = html;
}

function renderSetupScorecard() {
  const wrap = document.getElementById('setup-scorecard-wrap');
  const byMonth = computeSetupNetRByMonth();
  const months = Object.keys(byMonth).sort();
  if (!months.length) {
    wrap.innerHTML = '<p class="hint">No setup results logged yet.</p>';
    return;
  }
  let html = '<table><tr><th>Month</th>' + DATA.setups.map(s => `<th>${escapeHtml(s)}</th>`).join('') + '</tr>';
  months.forEach(month => {
    const scores = byMonth[month];
    const values = DATA.setups.map(s => scores[s]).filter(v => v !== undefined);
    const max = values.length ? Math.max(...values) : null;
    const min = values.length ? Math.min(...values) : null;
    html += `<tr><td>${month}</td>`;
    DATA.setups.forEach(s => {
      const v = scores[s];
      if (v === undefined) { html += '<td>&mdash;</td>'; return; }
      let cls = '';
      if (values.length > 1 && v === max) cls = 'best';
      else if (values.length > 1 && v === min) cls = 'worst';
      html += `<td class="${cls}">${v.toFixed(2)}</td>`;
    });
    html += '</tr>';
  });
  html += '</table>';
  wrap.innerHTML = html;
}

function renderDashboard() {
  renderStreaks();
  renderPunchcard();
  renderSetupScorecard();
}

// ---------- AI Analysis ----------

function buildAnalysisPrompt() {
  const weeks = sortedWeekLabels().map(label => {
    const e = DATA.weekly[label];
    return {
      week: label,
      did_well: e.well,
      struggled_with: e.struggle,
      improvement_plan: e.improve,
      setups: e.setupResults,
      mistakes: e.mistakes
    };
  });
  const months = sortedMonthLabels().map(label => {
    const e = DATA.monthly[label];
    return {
      month: label,
      best_worst_setups: e.setupsText,
      common_mistakes: e.mistakesText,
      adjustment_plan: e.adjustText
    };
  });
  return { weeks, months };
}

document.getElementById('analyze-btn').addEventListener('click', async () => {
  const statusEl = document.getElementById('analysis-status');
  const resultEl = document.getElementById('analysis-result');
  resultEl.classList.remove('show');
  resultEl.textContent = '';

  if (!DATA.settings.apiKey) {
    statusEl.textContent = 'Add your Anthropic API key in Settings first.';
    return;
  }
  const data = buildAnalysisPrompt();
  if (!data.weeks.length && !data.months.length) {
    statusEl.textContent = 'No reviews logged yet — add at least one weekly review first.';
    return;
  }

  statusEl.textContent = 'Analyzing...';

  const systemPrompt = `You are a trading performance coach. You will be given a trader's saved weekly and monthly self-reviews as JSON, including free-text reflections and tagged setups/mistakes. Identify the 3-5 strongest patterns in this data. Prioritize contradictions between what the trader said they would do (improvement_plan / adjustment_plan) and what they actually did in later weeks (struggled_with / mistakes / setups). Be specific and quote or paraphrase the trader's own words when pointing out a contradiction. Keep the answer concise and structured as a numbered list.`;

  try {
    const resp = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'content-type': 'application/json',
        'x-api-key': DATA.settings.apiKey,
        'anthropic-version': '2023-06-01',
        'anthropic-dangerous-direct-browser-access': 'true'
      },
      body: JSON.stringify({
        model: DATA.settings.model || 'claude-sonnet-5',
        max_tokens: 1500,
        system: systemPrompt,
        messages: [
          { role: 'user', content: JSON.stringify(data, null, 2) }
        ]
      })
    });

    if (!resp.ok) {
      const errText = await resp.text();
      throw new Error(`API error ${resp.status}: ${errText}`);
    }
    const json = await resp.json();
    const text = (json.content || []).map(block => block.text || '').join('\n').trim();
    statusEl.textContent = '';
    resultEl.textContent = text || '(empty response)';
    resultEl.classList.add('show');
  } catch (err) {
    statusEl.textContent = `Failed: ${err.message}`;
  }
});

// ---------- Settings ----------

function loadSettingsUI() {
  document.getElementById('api-key-input').value = DATA.settings.apiKey || '';
  document.getElementById('model-select').value = DATA.settings.model || 'claude-sonnet-5';
}

document.getElementById('save-settings-btn').addEventListener('click', () => {
  DATA.settings.apiKey = document.getElementById('api-key-input').value.trim();
  DATA.settings.model = document.getElementById('model-select').value;
  persist();
  document.getElementById('settings-saved-msg').textContent = 'Saved.';
  setTimeout(() => { document.getElementById('settings-saved-msg').textContent = ''; }, 2000);
});

document.getElementById('export-btn').addEventListener('click', () => {
  const blob = new Blob([JSON.stringify(DATA, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `trading-review-export-${fmtDate(new Date())}.json`;
  a.click();
  URL.revokeObjectURL(url);
});

document.getElementById('import-btn').addEventListener('click', () => {
  document.getElementById('import-file').click();
});

document.getElementById('import-file').addEventListener('change', (e) => {
  const file = e.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = () => {
    try {
      const parsed = JSON.parse(reader.result);
      DATA = Object.assign(defaultData(), parsed);
      persist();
      initAll();
    } catch (err) {
      alert('Invalid JSON file: ' + err.message);
    }
  };
  reader.readAsText(file);
  e.target.value = '';
});

document.getElementById('reset-btn').addEventListener('click', () => {
  if (!confirm('This will permanently delete all saved reviews, tags, and settings. Continue?')) return;
  localStorage.removeItem(STORAGE_KEY);
  DATA = defaultData();
  initAll();
});

// ---------- Utilities ----------

function escapeHtml(str) {
  return String(str).replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));
}

function escapeAttr(str) { return escapeHtml(str); }

// ---------- Init ----------

function initAll() {
  refreshWeeklySelect();
  refreshMonthlySelect();
  renderFramework();
  loadSettingsUI();
  loadWeeklyEntry(isoWeekLabel(new Date()));
  renderDashboard();
}

initAll();
