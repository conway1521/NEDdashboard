// Front end for the static NED dashboard. Replaces the Dash callbacks in src/pages/*.py with Plotly.js.
(function () {
  'use strict';

  const COLORS = { NED: '#d8534f', p: '#4abf73', hsc: '#f0ad4e', e: '#209bcf', red: 'rgba(226,126,123,1)' };
  const PILLAR_COLOR = { PbC: COLORS.p, HSC: COLORS.hsc, EA: COLORS.e };
  const GRAPH_BG = '#fafbfb';
  const FONT = { family: '"Nunito Sans", -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif', color: '#55595c' };

  // Colour scales Plotly Express used in the Dash version (temps_r, emrld, oryel, ice_r)
  const SCALES = {
    NED: ['rgb(207, 89, 126)', 'rgb(232, 132, 113)', 'rgb(238, 180, 121)', 'rgb(233, 226, 156)', 'rgb(156, 203, 134)', 'rgb(57, 177, 133)', 'rgb(0, 147, 146)'],
    p: ['rgb(211, 242, 163)', 'rgb(151, 225, 150)', 'rgb(108, 192, 139)', 'rgb(76, 155, 130)', 'rgb(33, 122, 121)', 'rgb(16, 89, 101)', 'rgb(7, 64, 80)'],
    hsc: ['rgb(236, 218, 154)', 'rgb(239, 196, 126)', 'rgb(243, 173, 106)', 'rgb(247, 148, 93)', 'rgb(249, 123, 87)', 'rgb(246, 99, 86)', 'rgb(238, 77, 90)'],
    e: ['rgb(234, 252, 253)', 'rgb(192, 229, 232)', 'rgb(149, 207, 216)', 'rgb(114, 184, 205)', 'rgb(89, 159, 196)', 'rgb(72, 134, 187)', 'rgb(62, 109, 178)', 'rgb(62, 83, 160)', 'rgb(58, 60, 125)', 'rgb(44, 42, 87)', 'rgb(25, 25, 51)', 'rgb(3, 5, 18)']
  };
  const toScale = colors => colors.map((c, i) => [i / (colors.length - 1), c]);

  const MENU = {
    NED: 'New Economic Development',
    p: 'i. Place-based Conditions',
    hsc: 'i. Human and Social Capital',
    e: 'i. Economic Activity'
  };

  const CONFIG = { responsive: true, displaylogo: false };

  const baseLayout = extra => Object.assign({
    font: FONT,
    paper_bgcolor: '#fff',
    plot_bgcolor: GRAPH_BG,
    margin: { t: 60, l: 60, r: 30, b: 60 },
    hoverlabel: { font: { family: FONT.family } }
  }, extra);

  // ---------------------------------------------------------------- shared: pillar circles (modal + about page)
  const PILLAR_SUBJECTS = [
    ['Environmental Health', 'Food and Physical Health Security', 'Housing', 'Transportation',
     'Access to Banking, Childcare, and Broadband', 'Innovation and Creation Institutions', 'Skill-building'],
    ['Educational Attainment', 'Schooling Outcomes', 'Opportunity Youth', 'Social Networks', 'Social Cohesion'],
    ['Size of Local Economy', 'Standard of Living', 'Productivity', 'Jobs', 'Employment', 'Unemployment',
     'Labor Force Participation', 'Earnings', 'Household Income', 'Poverty', 'Budgetary Assistance',
     'Income Inequality', 'Homeownership', 'Banking', 'Financial Resilience', 'Patents', 'Businesses',
     'Small Business Loans']
  ];

  function drawPillarCircles(el, height) {
    const names = ['Place-based Conditions', 'Human and Social Capital', 'Economic Activity'];
    const colors = [COLORS.p, COLORS.hsc, COLORS.e];
    const traces = names.map((name, i) => ({
      type: 'scatter', mode: 'markers', x: [name], y: [0], name: '',
      customdata: [PILLAR_SUBJECTS[i].join('<br>')],
      hovertemplate: '%{customdata}',
      marker: { size: 60, color: colors[i], line: { width: 1.5, color: 'DarkSlateGrey' } }
    }));
    Plotly.newPlot(el, traces, baseLayout({
      height, showlegend: false, plot_bgcolor: 'white', font: Object.assign({}, FONT, { size: 17 }),
      margin: { t: 20, l: 20, r: 20, b: 50 },
      xaxis: { showgrid: false, fixedrange: true },
      yaxis: { showgrid: false, zeroline: false, showticklabels: false, fixedrange: true }
    }), { displayModeBar: false, responsive: true });
  }

  // ---------------------------------------------------------------- tool page
  async function initTool() {
    const files = ['placedata.csv', 'humansocialdata.csv', 'econdata.csv', 'popweightdata.csv'];
    const [texts, geo] = await Promise.all([
      Promise.all(files.map(f => fetch('data/' + f).then(r => r.text())))
        .then(arr => Object.fromEntries(files.map((f, i) => [f, arr[i]]))),
      fetch('data/counties-geo.json').then(r => r.json())
    ]);
    const model = NEDData.compute(texts);
    const rows = model.counties;

    // Modal pillar circles render once the modal is visible (Plotly needs a sized container)
    const modal = document.getElementById('ned-modal');
    let modalDrawn = false;
    modal.addEventListener('shown.bs.modal', () => {
      const el = document.getElementById('modal-circles');
      if (!modalDrawn) { drawPillarCircles(el, 320); modalDrawn = true; } else Plotly.Plots.resize(el);
    });

    // ---- California view
    const choroSelect = document.getElementById('choro-select');
    const state = { dim: 'NED', view: 'map', order: 'alph' };

    function drawMap(dim) {
      Plotly.react('choro-graph', [{
        type: 'choropleth',
        geojson: geo,
        locations: rows.map(r => r.fips),
        z: rows.map(r => r[dim]),
        hovertext: rows.map(r => r.county),
        hovertemplate: '%{hovertext}: %{z:.1f}<extra></extra>',
        colorscale: toScale(SCALES[dim]),
        colorbar: { title: { text: 'Score' } },
        marker: { line: { color: '#fff', width: 0.5 } }
      }], baseLayout({
        height: 600,
        margin: { t: 10, l: 0, r: 0, b: 10 },
        geo: { scope: 'usa', fitbounds: 'locations', visible: false }
      }), Object.assign({}, CONFIG, { modeBarButtonsToRemove: ['zoom2d', 'pan2d', 'select2d', 'lasso2d'] }));
    }

    function drawBars(dim, order) {
      const sorted = order === 'rank' ? rows.slice().sort((a, b) => a[dim] - b[dim]) : rows;
      const color = COLORS[dim];
      Plotly.react('choro-graph', [{
        type: 'bar',
        x: sorted.map(r => r.county),
        y: sorted.map(r => r[dim]),
        text: sorted.map(r => r.county),
        textposition: 'auto',
        hovertemplate: '%{x}: %{y:.1f}<extra></extra>',
        marker: { color, line: { width: 0.33, color: '#1a1a1a' } },
        selected: { marker: { color } },
        unselected: { marker: { color, opacity: 0.6 } }
      }], baseLayout({
        height: 600,
        clickmode: 'event+select',
        xaxis: { title: { text: 'County' }, showgrid: false, showticklabels: false, fixedrange: true },
        yaxis: { showgrid: false, range: [0, 6.65], fixedrange: true }
      }), CONFIG);
    }

    function updateCA() {
      document.getElementById('choro-title').textContent = MENU[state.dim] + ' Score';
      if (state.view === 'map') drawMap(state.dim); else drawBars(state.dim, state.order);
      document.querySelectorAll('[data-tab-text]').forEach(el => {
        el.hidden = el.dataset.tabText !== state.dim;
      });
    }

    choroSelect.addEventListener('change', () => { state.dim = choroSelect.value; updateCA(); });
    document.querySelectorAll('input[name="mapbar"]').forEach(el =>
      el.addEventListener('change', () => { state.view = el.value; updateCA(); }));
    document.querySelectorAll('input[name="alpharank"]').forEach(el =>
      el.addEventListener('change', () => { state.order = el.value; updateCA(); }));

    // ---- County view
    const countySelect = document.getElementById('county-select');
    rows.forEach(r => countySelect.add(new Option(r.county, r.county)));
    countySelect.value = 'Alameda';

    const maxHsc = Math.max(...rows.map(r => r.hsc));
    const nedAvg = model.averages.NED;

    function drawCountyPillars(row) {
      Plotly.react('county-pillars', [{
        type: 'bar',
        x: ['Place-based Conditions', 'Human and Social Capital', 'Economic Activity'],
        y: [row.p, row.hsc, row.e],
        hovertemplate: '<b>%{x}</b><br><br>Score=%{y}<extra></extra>',
        marker: { color: [COLORS.p, COLORS.hsc, COLORS.e], line: { width: 1, color: '#1a1a1a' } }
      }], baseLayout({
        title: { text: 'i. Pillar Scores', x: 0.5 },
        xaxis: {
          title: { text: 'Pillar' }, fixedrange: true, tickmode: 'array',
          tickvals: ['Place-based Conditions', 'Human and Social Capital', 'Economic Activity'],
          ticktext: ['PbC', 'HSC', 'EA']
        },
        yaxis: { title: { text: 'Score' }, range: [0, maxHsc + 0.1], showgrid: false, fixedrange: true },
        shapes: [{
          type: 'line', xref: 'paper', x0: 0, x1: 1, y0: nedAvg, y1: nedAvg,
          line: { color: COLORS.red, width: 2.5, dash: 'dash' }
        }],
        annotations: [{
          xref: 'paper', x: 1, xanchor: 'right', y: nedAvg, yanchor: 'bottom', showarrow: false,
          text: 'NED Score, CA avg.', font: { color: COLORS.red }, bgcolor: 'rgba(250, 251, 251, 0.35)'
        }]
      }), Object.assign({}, CONFIG, { modeBarButtonsToRemove: ['select2d', 'lasso2d'] }));
    }

    function drawFlower(row) {
      const theta = [0, 40, 80, 120, 160, 200, 240, 280, 320];
      const subjectPillar = ['PbC', 'PbC', 'HSC', 'HSC', 'EA', 'EA', 'EA', 'EA', 'EA'];
      const traces = ['PbC', 'HSC', 'EA'].map(pillar => {
        const idx = subjectPillar.map((p, i) => p === pillar ? i : -1).filter(i => i >= 0);
        const names = idx.map(i => NEDData.LABELS_SUBJECT[model.subjectOrder[i]]);
        return {
          type: 'barpolar', name: pillar, opacity: 0.8, width: 20,
          r: idx.map(i => NEDData.round1(row.subjects[model.subjectOrder[i]])),
          theta: idx.map(i => theta[i]),
          customdata: names,
          hovertemplate: '%{customdata}<br><br>Score=%{r:.1f}<extra></extra>',
          marker: { color: PILLAR_COLOR[pillar], line: { color: 'rgba(26,26,26,1)', width: 1 } }
        };
      });
      traces.push({
        type: 'scatterpolar', mode: 'lines', name: 'NED Score, CA avg.',
        r: new Array(120).fill(nedAvg),
        theta: Array.from({ length: 120 }, (_, i) => i * 3),
        line: { color: COLORS.red, dash: 'dot', width: 2, shape: 'spline', smoothing: 1.3 },
        hoverinfo: 'text', hovertext: 'NED Score CA avg. ' + nedAvg.toFixed(1)
      });
      Plotly.react('county-flower', traces, baseLayout({
        title: { text: 'ii. Subject Scores' },
        showlegend: true,
        legend: { orientation: 'h' },
        polar: {
          bgcolor: GRAPH_BG,
          radialaxis: { range: [0, 8.5], visible: false, showticklabels: false, ticks: '' },
          angularaxis: { showticklabels: false, ticks: '', showgrid: false, showline: false }
        }
      }), Object.assign({}, CONFIG, { modeBarButtonsToRemove: ['zoom2d', 'select2d', 'lasso2d'] }));
    }

    function drawTopics(row) {
      const items = model.topicOrder
        .map(t => ({ topic: t, rank: row.topicRanks[t] }))
        .sort((a, b) => a.rank - b.rank);
      const seen = {};
      items.forEach(it => { seen[it.rank] = (seen[it.rank] || 0); it.y = 0.075 + seen[it.rank] * 0.2; seen[it.rank]++; });
      const maxY = Math.max(...items.map(it => it.y));
      const traces = ['PbC', 'HSC', 'EA'].map(pillar => {
        const sub = items.filter(it => model.topicPillar[it.topic] === pillar);
        return {
          type: 'scatter', mode: 'markers', name: pillar,
          x: sub.map(it => it.rank), y: sub.map(it => it.y),
          hovertext: sub.map(it => NEDData.LABELS_TOPIC[it.topic]),
          hovertemplate: '<b>%{hovertext}</b><br><br>Rank=%{x}<extra></extra>',
          marker: { size: 15, color: PILLAR_COLOR[pillar], line: { width: 1, color: '#1a1a1a' } }
        };
      });
      Plotly.react('county-topics', traces, baseLayout({
        height: 400,
        title: { text: 'iii. Topics Distribution by Score ranking', x: 0.5 },
        legend: { title: { text: 'Pillar' } },
        xaxis: {
          title: { text: 'Rank' }, showgrid: false, range: [59, 0.1], fixedrange: true,
          tickvals: [58, 29, 1], ticktext: ['58', '29', '1']
        },
        yaxis: {
          title: { text: 'Frequency' }, showgrid: false, showticklabels: false, fixedrange: true,
          range: [-0.15, maxY + 0.15], zeroline: true, zerolinecolor: 'black', zerolinewidth: 3
        }
      }), Object.assign({}, CONFIG, { modeBarButtonsToRemove: ['select2d', 'lasso2d'] }));
    }

    function updateCounty() {
      const row = rows.find(r => r.county === countySelect.value);
      drawCountyPillars(row);
      drawFlower(row);
      drawTopics(row);
    }
    countySelect.addEventListener('change', updateCounty);

    document.querySelectorAll('.loading').forEach(el => el.remove());
    updateCA();
    updateCounty();
  }

  // ---------------------------------------------------------------- about page
  async function initAbout() {
    drawPillarCircles(document.getElementById('about-circles'), 315);

    const text = await fetch('data/df_treemap.csv').then(r => r.text());
    const { header, rows } = NEDData.parseCSV(text);
    const col = name => header.indexOf(name);
    const pillarColor = {
      'i. Place-based Conditions': COLORS.p,
      'i. Human and Social Capital': COLORS.hsc,
      'i. Economic Activity': COLORS.e
    };
    const ids = ['NED'], labels = ['NED'], parents = [''], colors = ['lightgrey'];
    const add = (id, label, parent, color) => {
      if (ids.includes(id)) return;
      ids.push(id); labels.push(label); parents.push(parent); colors.push(color);
    };
    rows.forEach(r => {
      const pillar = r[col('pillar')], topic = r[col('topic')], subject = r[col('subject')];
      const c = pillarColor[pillar];
      add('NED/' + pillar, pillar, 'NED', c);
      add('NED/' + pillar + '/' + topic, topic, 'NED/' + pillar, c);
      add('NED/' + pillar + '/' + topic + '/' + subject, subject, 'NED/' + pillar + '/' + topic, c);
    });
    Plotly.newPlot('about-treemap', [{
      type: 'treemap', ids, labels, parents,
      marker: { colors },
      hoverinfo: 'skip'
    }], baseLayout({ margin: { t: 50, l: 25, r: 25, b: 25 }, height: 520 }), { displayModeBar: false, responsive: true });
  }

  document.addEventListener('DOMContentLoaded', () => {
    const page = document.body.dataset.page;
    const run = page === 'tool' ? initTool : page === 'about' ? initAbout : null;
    if (run) run().catch(err => {
      console.error(err);
      document.querySelectorAll('.loading').forEach(el => { el.textContent = 'Could not load the data. Please refresh the page.'; });
    });
  });
})();
