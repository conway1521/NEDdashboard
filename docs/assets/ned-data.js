// NED data pipeline: a direct port of the scoring logic in src/pages/tool.py.
// Raw indicators are min-max normalised across the 58 counties (flipped where lower is better),
// averaged into Topics (x10), Topics into Subjects, Subjects into Pillars, and Pillars into NED.

(function (root) {
  'use strict';

  // ---------------------------------------------------------------- CSV parsing
  function parseCSV(text) {
    const rows = [];
    let row = [], field = '', inQuotes = false;
    for (let i = 0; i < text.length; i++) {
      const c = text[i];
      if (inQuotes) {
        if (c === '"' && text[i + 1] === '"') { field += '"'; i++; }
        else if (c === '"') inQuotes = false;
        else field += c;
      } else if (c === '"') inQuotes = true;
      else if (c === ',') { row.push(field); field = ''; }
      else if (c === '\n' || c === '\r') {
        if (c === '\r' && text[i + 1] === '\n') i++;
        row.push(field); field = '';
        if (row.length > 1 || row[0] !== '') rows.push(row);
        row = [];
      } else field += c;
    }
    if (field !== '' || row.length) { row.push(field); rows.push(row); }
    const header = rows.shift();
    return { header, rows };
  }

  // Returns {columns: [...], data: {col: [values]}}; every column except fips/county is numeric (NaN when blank)
  function toTable(text) {
    const { header, rows } = parseCSV(text);
    const data = {};
    header.forEach((h, j) => {
      const text = h === 'fips' || h === 'county';
      data[h] = rows.map(r => text ? r[j] : (r[j] === '' || r[j] === undefined ? NaN : Number(r[j])));
    });
    return { columns: header, data };
  }

  // ---------------------------------------------------------------- helpers mirroring pandas behaviour
  const isNum = v => typeof v === 'number' && !Number.isNaN(v);

  // pandas mean(skipna=True): NaN only when every value is NaN
  function nanmean(values) {
    let s = 0, n = 0;
    for (const v of values) if (isNum(v)) { s += v; n++; }
    return n ? s / n : NaN;
  }

  // numpy round (half to even) to 1 decimal
  function round1(x) {
    if (!isNum(x)) return x;
    const y = x * 10, f = Math.floor(y), d = y - f;
    let r;
    if (d > 0.5) r = f + 1;
    else if (d < 0.5) r = f;
    else r = f % 2 === 0 ? f : f + 1;
    return r / 10;
  }

  // pandas rank(method='max', ascending=False, na_option='bottom')
  function rankDesc(values) {
    const n = values.length;
    return values.map(v => isNum(v) ? values.filter(w => isNum(w) && w >= v).length : n);
  }

  function colNames(columns, start, end) {
    return columns.slice(columns.indexOf(start), columns.indexOf(end) + 1);
  }

  // ---------------------------------------------------------------- framework definitions
  const LABELS_TOPIC = {
    envhealth: 'Environmental Health',
    foodhealth: 'Food and Physical Health Security',
    housing: 'Housing and Neighborhoods',
    transport: 'Transportation',
    access_bcb: 'Access to Finance Institutions, Childcare, and Broadband',
    innovcreation: 'Density of Innovative Creation Organizations',
    skillbuilding: 'Density of Skill-building Centers',
    educattain: 'Educational Attainment, current adults',
    schooling: 'Schooling Outcomes, current students',
    oppyouth: 'Transitional and Opportunity Youth',
    socialnet: 'Social Networks',
    socialcohesion: 'Social Cohesion',
    size: 'Size of Local Economy',
    stdliving: 'Standard of Living',
    prod: 'Productivity',
    jobs: 'Jobs',
    emp: 'Employment',
    u: 'Unemployment',
    lf: 'Labor Force',
    earn: 'Earnings',
    hhinc: 'Household Income',
    poverty: 'Poverty',
    assistance: 'Budgetary Assistance',
    incineq: 'Income Inequality',
    homeown: 'Homeownership',
    bank: 'Access to Wealth',
    finresil: 'Financial Resilience',
    patents: 'Patents',
    bus: 'Business Establishments',
    smallbusloan: 'Loans to Small Businesses'
  };

  const LABELS_SUBJECT = {
    basic_needs: 'Basic Needs',
    access: 'Access',
    eductalent: 'Education and Talent',
    socialcapital: 'Social Capital',
    growthprosp: 'Growth and Prosperity',
    labormarket: 'Labor Market',
    income: 'Household Income',
    wealth: 'Household Wealth',
    busenv: 'Business Environment'
  };

  // Each layer: topic -> [first column, last column] (inclusive range in the CSV), subject -> topics
  const LAYERS = {
    p: {
      file: 'placedata.csv',
      pillarAbbr: 'PbC',
      topics: {
        envhealth: ['water_violation', 'particulate_matter'],
        foodhealth: ['uninsured', 'food_insec'],
        housing: ['severe_housing', 'crime_rate'],
        transport: ['vehicle_avail', 'commute_long'],
        access_bcb: ['access_finance_insurance', 'access_broadband'],
        innovcreation: ['r1_univ', 'rd_density'],
        skillbuilding: ['cc_density', 'csu']
      },
      subjects: {
        basic_needs: ['envhealth', 'foodhealth', 'housing', 'transport'],
        access: ['access_bcb', 'innovcreation', 'skillbuilding']
      },
      flip: ['water_violation', 'particulate_matter', 'uninsured', 'years_lost', 'limited_healthyfood',
             'food_insec', 'severe_housing', 'rent_costburden', 'housing_afford', 'homelessness',
             'resid_vacancy', 'crime_rate', 'commute_time', 'access_broadband']
    },
    hsc: {
      file: 'humansocialdata.csv',
      pillarAbbr: 'HSC',
      topics: {
        educattain: ['attain_nohs', 'MYS'],
        schooling: ['enrol_preschool', 'juvenile_felony'],
        oppyouth: ['highered_enroll', 'discon_youth'],
        socialnet: ['econ_con', 'clustering'],
        socialcohesion: ['support_ratio', 'civic_orgs']
      },
      subjects: {
        eductalent: ['educattain', 'schooling', 'oppyouth'],
        socialcapital: ['socialnet', 'socialcohesion']
      },
      flip: ['suspensions', 'juvenile_felony', 'discon_youth']
    },
    e: {
      file: 'econdata.csv',
      pillarAbbr: 'EA',
      topics: {
        size: ['rgdp_18', 'rgdp_10yr'],
        stdliving: ['rgdp_capita', 'rgdp_capita'],
        prod: ['prod_jobs', 'prod_worker'],
        jobs: ['jobs', 'jobs_young_prop'],
        emp: ['emp_to_pop', 'jobs_highskill'],
        u: ['u', 'u_youth_gap'],
        lf: ['lfp', 'lfp_youth_gap'],
        earn: ['earn_med', 'earn_med_gender_gap'],
        hhinc: ['hh_inc_med', 'hh_rentburden'],
        poverty: ['poverty_prop', 'poverty_under18'],
        assistance: ['assist_food', 'assist_cash'],
        incineq: ['gini_inc', 'inc_ratio'],
        homeown: ['home_own', 'home_own_edgap'],
        bank: ['hh_underbank', 'hh_unbank'],
        finresil: ['asset_pov_rate', 'l_asset_pov_rate'],
        patents: ['patents_per1000', 'patent_5yr'],
        bus: ['num_establishments', 'num_establishments'],
        smallbusloan: ['loan_smallbus_number', 'loan_avg']
      },
      subjects: {
        growthprosp: ['size', 'stdliving', 'prod'],
        labormarket: ['jobs', 'emp', 'u', 'lf', 'earn'],
        income: ['hhinc', 'poverty', 'assistance', 'incineq'],
        wealth: ['homeown', 'bank', 'finresil'],
        busenv: ['patents', 'bus', 'smallbusloan']
      },
      flip: ['jobs_unstable_prop', 'u', 'u_ed_gap', 'u_youth_gap', 'below_15000', 'below_25000',
             'hh_houseburden', 'hh_rentburden', 'poverty_prop', 'poverty_under18', 'assist_food',
             'assist_income', 'assist_cash', 'gini_inc', 'inc_ratio', 'hh_underbank', 'hh_unbank',
             'asset_pov_rate', 'hh_noNW', 'l_asset_pov_rate']
    }
  };

  // ---------------------------------------------------------------- scoring
  function normalise(table, layer) {
    const out = {};
    for (const col of table.columns) {
      if (col === 'fips' || col === 'county') continue;
      const vals = table.data[col];
      const nums = vals.filter(isNum);
      const min = Math.min(...nums), max = Math.max(...nums);
      const range = (max - min) === 0 ? 1 : (max - min);
      out[col] = vals.map(v => (v - min) / range);
    }
    for (const col of layer.flip) out[col] = out[col].map(v => 1 - v);
    // Matches the original pipeline, which sets commute_long from the flipped commute_alone share
    if (out.commute_alone) out.commute_long = out.commute_alone.map(v => 1 - v);
    return out;
  }

  /**
   * texts: {placedata.csv: '...', humansocialdata.csv: '...', econdata.csv: '...', popweightdata.csv: '...'}
   * Returns one record per county with every score, rank and the population-weighted CA averages.
   */
  function compute(texts) {
    const pop = toTable(texts['popweightdata.csv']).data.pop_perc;
    let counties = null, fips = null;
    const topics = {}, subjects = {}, pillars = {};
    const topicPillar = {}, subjectOrder = [], topicOrder = [];

    for (const [key, layer] of Object.entries(LAYERS)) {
      const table = toTable(texts[layer.file]);
      if (!counties) { counties = table.data.county; fips = table.data.fips; }
      const norm = normalise(table, layer);
      const n = counties.length;

      for (const [topic, [a, b]] of Object.entries(layer.topics)) {
        const cols = colNames(table.columns, a, b);
        topics[topic] = Array.from({ length: n }, (_, i) => nanmean(cols.map(c => norm[c][i])) * 10);
        topicPillar[topic] = layer.pillarAbbr;
        topicOrder.push(topic);
      }
      for (const [subj, tps] of Object.entries(layer.subjects)) {
        subjects[subj] = Array.from({ length: n }, (_, i) => nanmean(tps.map(t => topics[t][i])));
        subjectOrder.push(subj);
      }
      const subjKeys = Object.keys(layer.subjects);
      pillars[key] = Array.from({ length: n }, (_, i) => nanmean(subjKeys.map(s => subjects[s][i])));
    }

    const n = counties.length;
    const ned = Array.from({ length: n }, (_, i) => nanmean(['p', 'hsc', 'e'].map(k => pillars[k][i])));

    const wavg = vals => {
      let s = 0, w = 0;
      vals.forEach((v, i) => { s += v * pop[i]; w += pop[i]; });
      return s / w;
    };

    const ranks = {
      NED: rankDesc(ned), p: rankDesc(pillars.p), hsc: rankDesc(pillars.hsc), e: rankDesc(pillars.e)
    };
    const topicRanks = {};
    for (const t of topicOrder) topicRanks[t] = rankDesc(topics[t]);

    const records = counties.map((county, i) => ({
      county,
      fips: fips[i],
      NED: round1(ned[i]), p: round1(pillars.p[i]), hsc: round1(pillars.hsc[i]), e: round1(pillars.e[i]),
      NED_r: ranks.NED[i], p_r: ranks.p[i], hsc_r: ranks.hsc[i], e_r: ranks.e[i],
      subjects: Object.fromEntries(subjectOrder.map(s => [s, subjects[s][i]])),
      topics: Object.fromEntries(topicOrder.map(t => [t, topics[t][i]])),
      topicRanks: Object.fromEntries(topicOrder.map(t => [t, topicRanks[t][i]]))
    }));

    return {
      counties: records,
      subjectOrder,
      topicOrder,
      topicPillar,
      averages: { NED: wavg(ned), p: wavg(pillars.p), hsc: wavg(pillars.hsc), e: wavg(pillars.e) }
    };
  }

  const NED = { compute, parseCSV, round1, LABELS_TOPIC, LABELS_SUBJECT, LAYERS };
  if (typeof module !== 'undefined' && module.exports) module.exports = NED;
  else root.NEDData = NED;
})(this);
