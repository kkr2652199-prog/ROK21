/* ═══════════════════════════════════════════
   로또 대시보드 JavaScript
   ═══════════════════════════════════════════ */

/* ── 로또 독립 유틸: app.js 의존 최소화 ── */
const _testlottoResolveApiUrl = (typeof resolveApiUrl === 'function')
    ? resolveApiUrl
    : function(path) { return path; };

const _testlottoBrainDisplayNames = {
  stat: '📚 과거학습',
  markov: '🌊 흐름술사',
  review: '📖 복습왕',
};

const _testlottoBrainDescriptions = {
  stat: '자주 나온 번호·끝자리·이월 번호 위주',
  markov: '직전 회차와 함께 나온 번호 위주',
  review: '예전에 틀렸던 패턴을 다시 공부하는 방식',
};

/** REPORT_STYLE.md SSOT — 형이 읽는 과제·전략 한국어 */
const _testlottoSurveyLabelKo = {
  'K-SIGNAL-SELECT-FULL': '신호 선별 전체 검증(1182회)',
  'K-SIGNAL-SELECT-01': '신호 선별 빠른 검증(200회)',
  'K-SIGNAL-REPACK-01': '번호 몰아주기 빠른 검증(200회)',
  'K-SIGNAL-REPACK-FULL': '번호 몰아주기 전체 검증(1182회)',
};

const _testlottoStrategyLabelKo = {
  signal_repack: '신호 몰아주기',
  combined: '통합 선별',
  set_no_asc: '세트번호 오름차순',
  random_repack: '무작위 몰아주기',
  hint_only_repack: '힌트만 몰아주기',
};

function testlottoSurveyLabelKo(id) {
  return _testlottoSurveyLabelKo[id] || id;
}

function testlottoStrategyLabelKo(id) {
  return _testlottoStrategyLabelKo[id] || id;
}

function _tlFriendlyWarrantLabel(label) {
  const map = {
    '실증': '효과 확인됨',
    '기각': '효과 미확인',
    '미정의': '아직 판정 전',
    '전제실증·구현미검증': '일부만 확인됨',
  };
  return map[label] || label;
}

function testlottoGetBrainDisplayName(tag) {
  return _testlottoBrainDisplayNames[tag] || tag;
}

function testlottoGetBrainDescription(tag) {
  return _testlottoBrainDescriptions[tag] || '';
}

const _TL_WARRANT_LABEL_CLASS = {
  '실증': 'tl-wlbl--proved',
  '기각': 'tl-wlbl--rejected',
  '미정의': 'tl-wlbl--undefined',
  '전제실증·구현미검증': 'tl-wlbl--partial',
};

function _tlEscapeHtml(s) {
  return String(s || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function _tlWarrantLabelClass(label) {
  return _TL_WARRANT_LABEL_CLASS[label] || 'tl-wlbl--undefined';
}

function _tlFormatLearnKeyBar(key, value, cap) {
  const v = Number(value) || 0;
  const c = Number(cap) || 0.5;
  const pct = c > 0 ? Math.min(100, Math.round((v / c) * 100)) : 0;
  return (
    '<div class="tl-wkey">' +
    `<span class="tl-wkey__name">${_tlEscapeHtml(key)}</span>` +
    `<span class="tl-wkey__val">${v.toFixed(2)} / ${c}</span>` +
    `<span class="tl-wkey__bar" aria-hidden="true"><span style="width:${pct}%"></span></span>` +
    '</div>'
  );
}

function renderTestlottoWarrantPanelHtml(data, drawNo) {
  const gates = data.gates || {};
  const frozen = (data.frozen || []).join(' · ');
  const brains = data.brains || [];
  const predict = brains.filter((b) => b.role === 'predict');
  const aux = brains.filter((b) => b.role === 'aux');

  const brainCard = (b) => {
    const lbl = b.warrant_label || '미정의';
    const keys = (b.learn_keys || []).filter((k) => {
      if (b.role === 'predict') return (Number(k.value) || 0) > 0.001;
      return true;
    });
    const keyHtml = keys.length
      ? keys.map((k) => {
          if (k.per_predict_brain) {
            const parts = Object.entries(k.per_predict_brain)
              .map(([t, v]) => `${t}:${Number(v).toFixed(2)}`)
              .join(' · ');
            return (
              '<div class="tl-wkey tl-wkey--aux">' +
              `<span class="tl-wkey__name">${_tlEscapeHtml(k.key)}</span>` +
              `<span class="tl-wkey__val">${_tlEscapeHtml(parts)}</span>` +
              '</div>'
            );
          }
          return _tlFormatLearnKeyBar(k.key, k.value, k.cap);
        }).join('')
      : '<span class="tl-wmuted">지금 쓰는 가중치 없음</span>';
    const lblPlain = _tlFriendlyWarrantLabel(lbl);
    return (
      '<article class="tl-wbrain">' +
      `<header class="tl-wbrain__head">` +
      `<strong>${_tlEscapeHtml(b.name)}</strong>` +
      `<span class="tl-wlbl ${_tlWarrantLabelClass(lbl)}">${_tlEscapeHtml(lblPlain)}</span>` +
      '</header>' +
      `<p class="tl-wbrain__ev">${_tlEscapeHtml(b.warrant_evidence || '')}</p>` +
      `<div class="tl-wbrain__keys">${keyHtml}</div>` +
      '</article>'
    );
  };

  const asOf = gates.learn_as_of != null ? gates.learn_as_of : '—';
  return (
    '<div class="tl-warrant-inner">' +
    '<div class="tl-warrant-head">' +
    '<h3 class="tl-warrant-title">프로그램 설명 · 제한 사항</h3>' +
    `<p class="tl-warrant-note">${_tlEscapeHtml(data.evaluation_axis || '이 화면은 왜 이렇게 동작하는지 보여 주는 참고용입니다.')}</p>` +
    '</div>' +
    '<div class="tl-warrant-gates">' +
    `<span>학습에 쓰는 과거 회차: <strong>${asOf}회까지</strong>${drawNo ? ` (지금 ${drawNo}회 보는 중)` : ''}</span>` +
    `<span>미래 당첨 미리 보기 차단: <strong>${gates.learn_cutoff ? '켜짐' : '꺼짐'}</strong></span>` +
    `<span>같은 조합 중복 정리: <strong>${gates.dedup ? '켜짐' : '꺼짐'}</strong></span>` +
    '</div>' +
    (frozen ? '<p class="tl-warrant-frozen">수정 금지(고정) 기능: ' + _tlEscapeHtml(frozen) + '</p>' : '') +
    '<p class="tl-warrant-disclaimer">※ <b>로또 1등 확률을 높여 주지 않습니다.</b> 성능이 낮다고 표시된 프로그램도 기록·비교를 위해 그대로 둡니다.</p>' +
    '<div class="tl-warrant-section"><h4>번호 예측 3종</h4><div class="tl-warrant-grid">' + predict.map(brainCard).join('') + '</div></div>' +
    '<div class="tl-warrant-section"><h4>보조 알림 4종 (맞춘 개수 채점 안 함)</h4><div class="tl-warrant-grid">' + aux.map(brainCard).join('') + '</div></div>' +
    '</div>'
  );
}

async function fetchTestlottoWarrantDashboard(drawNo) {
  const d = parseInt(drawNo, 10);
  const qs = Number.isFinite(d) && d > 0 ? `?as_of=${d}` : '';
  const r = await fetch(_testlottoResolveApiUrl('/api/testlotto/warrant-dashboard' + qs));
  if (!r.ok) throw new Error(String(r.status));
  return r.json();
}

let _testlottoWarrantByTag = {};
let _testlottoWarrantPolicy = null;
let _testlottoWarrantCacheAsOf = null;

function _testlottoApplyWarrantCache(data, drawNo) {
  _testlottoWarrantByTag = {};
  (data.brains || []).forEach((b) => {
    if (b && b.tag) _testlottoWarrantByTag[b.tag] = b;
  });
  _testlottoWarrantPolicy = data.rejected_brain_policy || null;
  _testlottoWarrantCacheAsOf = drawNo || null;
}

async function ensureTestlottoWarrantLoaded(drawNo) {
  const d = parseInt(drawNo, 10);
  if (_testlottoWarrantPolicy && _testlottoWarrantCacheAsOf === d) {
    return { brains: Object.values(_testlottoWarrantByTag), rejected_brain_policy: _testlottoWarrantPolicy };
  }
  const data = await fetchTestlottoWarrantDashboard(d);
  _testlottoApplyWarrantCache(data, d);
  return data;
}

function testlottoGetWarrantMeta(tag) {
  return _testlottoWarrantByTag[String(tag || '').toLowerCase()] || null;
}

function testlottoWarrantTabBadgeHtml(tag) {
  const meta = testlottoGetWarrantMeta(tag);
  if (!meta) return '';
  const lbl = meta.warrant_label || '미정의';
  const hint = meta.display_hint || {};
  const lblPlain = _tlFriendlyWarrantLabel(lbl);
  const tabHint = hint.tab_hint || lblPlain;
  return (
    `<span class="lotto-warrant-tabline">` +
    `<span class="tl-wlbl ${_tlWarrantLabelClass(lbl)} lotto-warrant-tabline__lbl">${_tlEscapeHtml(lblPlain)}</span>` +
    `<span class="lotto-warrant-tabline__hint">${_tlEscapeHtml(tabHint)}</span>` +
    `</span>`
  );
}

function testlottoBrainPolicyStripHtml(tag) {
  const meta = testlottoGetWarrantMeta(tag);
  if (!meta) return '';
  const hint = meta.display_hint || {};
  const lbl = meta.warrant_label || '미정의';
  const cls = lbl === '기각' ? 'lotto-brain-policy--rejected' : (lbl === '미정의' ? 'lotto-brain-policy--undefined' : 'lotto-brain-policy--proved');
  let extra = '';
  if (hint.warning) {
    extra += `<span class="lotto-brain-policy__warn">⚠ ${_tlEscapeHtml(hint.warning)}</span>`;
  }
  if (hint.contrib_note) {
    extra += `<span class="lotto-brain-policy__note">${_tlEscapeHtml(hint.contrib_note)}</span>`;
  }
  if (meta.kw_alignment) {
    extra += `<span class="lotto-brain-policy__kw">과거 테스트 참고: ${_tlEscapeHtml(meta.kw_alignment)}</span>`;
  }
  return (
    `<div class="lotto-brain-policy ${cls}" role="note">` +
    `<strong>${_tlEscapeHtml(hint.short || _tlFriendlyWarrantLabel(lbl))}</strong>` +
  `<span class="lotto-brain-policy__role">${_tlEscapeHtml(hint.role_line || '')}</span>` +
    extra +
    `<span class="lotto-brain-policy__keep">※ 성능이 낮아도 삭제하지 않습니다 (기록·비교용)</span>` +
    `</div>`
  );
}

async function loadTestlottoWarrantPanel(drawNo) {
  const panel = document.getElementById('testlottoWarrantPanel');
  if (!panel) return;
  const d = parseInt(drawNo, 10);
  try {
    const data = await ensureTestlottoWarrantLoaded(d);
    panel.hidden = false;
    panel.classList.add('tl-warrant-panel');
    panel.innerHTML = renderTestlottoWarrantPanelHtml(data, d);
  } catch (e) {
    panel.hidden = true;
    panel.innerHTML = '';
    console.warn('warrant-dashboard:', e);
  }
}
window.loadTestlottoWarrantPanel = loadTestlottoWarrantPanel;

// ── 탭 전환 ──
function switchTestlottoTab(tabName) {
  document.querySelectorAll('.lotto-tab-content').forEach((el) => { el.style.display = 'none'; });
  document.querySelectorAll('.lotto-sub-tab').forEach((el) => { el.classList.remove('active'); });
  const target = document.getElementById('lotto-tab-' + tabName);
  if (target) target.style.display = 'block';
  const btn = document.querySelector(`[data-lotto-tab="${tabName}"]`);
  if (btn) btn.classList.add('active');

  if (tabName === 'predictions') {
    initTestlottoDrawSearch();
  }
  if (tabName === 'stats') loadStats();
  if (tabName === 'draws') loadDraws();
}

// ── 회차 검색 + 저장 예측(6두뇌 탭) ──
let _testlottoDrawList = [];
let _testlottoDrawDates = {};
let _testlottoPredRowsCache = null;
let _testlottoDetailDrawNo = null;
let _testlottoDetailRows = null;
let _testlottoPredDataSource = 'brain_review';
let _testlottoPredFetchSeq = 0;
let _testlottoCurrentBrainTab = 'all';
let _testlottoSetSubTab = 'pool';
let _testlottoPoolViewMemCache = new Map();
/** 백테 DB 프리로드 — draw_no → summaries[] (로딩 없이 즉시 표시) */
let _testlottoBtByDraw = new Map();
/** draw-index 당첨번호 — 회차별 /draws/{n} fetch 제거 */
let _testlottoActualByDraw = new Map();
let _testlottoBtIndexPromise = null;
let _testlottoBtPreloadDone = false;
/** pool-view 채점용 당첨번호 (회차 전환 시 renderPredictionsByBrain에서 갱신) */
let _testlottoCurrentActualRef = null;
let _testlottoBrainAccordionOpen = { stat: true, markov: false, review: false };

/** 역대 1·2·3등 조건 필터용 brain_tag 집합(null=미로드). */
let _testlottoBrainEliteTagSet = null;

/** 대시보드 brain_power → 태그별 맵(null=미구축). */
let _testlottoBrainPowerByTag = null;

function setLottoBrainPowerCache(brainPower) {
  const map = {};
  (brainPower || []).forEach((b) => {
    const k = String(b.brain || '').toLowerCase();
    if (k) map[k] = b;
  });
  _testlottoBrainPowerByTag = map;
}

async function ensureLottoBrainPowerLoaded() {
  if (_testlottoBrainPowerByTag) return;
  try {
    const res = await fetch(_testlottoResolveApiUrl('/api/testlotto/dashboard-summary'));
    if (!res.ok) return;
    const data = await res.json();
    setLottoBrainPowerCache(data.brain_power);
  } catch (e) {
    console.warn('brain_power cache:', e);
  }
}

/** 카톡 복사용: 해당 뇌 역대 1~5등 적중 한 줄(플레인 텍스트). */
function lottoKakaoBrainRecordLine(tag) {
  const m = _testlottoBrainPowerByTag || {};
  const b = m[String(tag).toLowerCase()] || {};
  const n1 = Number(b.rank1 || 0);
  const n2 = Number(b.rank2 || 0);
  const n3 = Number(b.rank3 || 0);
  const n4 = Number(b.rank4 || 0);
  const n5 = Number(b.rank5 || 0);
  return (
    `  📊 역대 전적: 🥇1등 ${n1}회 🥈2등 ${n2}회 🥉3등 ${n3}회 🎯4등 ${n4}회 ✅5등 ${n5}회\n`
  );
}

/** 역대 1~5등 적중 횟수 나노 한 줄(HTML). */
function lottoBrainTierNanoHtml(tag) {
  const m = _testlottoBrainPowerByTag || {};
  const b = m[String(tag).toLowerCase()];
  if (!b) return '';
  const n1 = Number(b.rank1 || 0);
  const n2 = Number(b.rank2 || 0);
  const n3 = Number(b.rank3 || 0);
  const n4 = Number(b.rank4 || 0);
  const n5 = Number(b.rank5 || 0);
  const txt = [n1, n2, n3, n4, n5].join('·');
  return (
    '<span class="lotto-brain-nano" title="역대 1등·2등·3등·4등·5등(3개 맞춤) 횟수">' +
    txt +
    '</span>'
  );
}

const TESTLOTTO_BRAIN_LIST = [
  { tag: 'stat', name: '과거학습', icon: '📚', color: '#3b82f6' },
  { tag: 'markov', name: '흐름술사', icon: '🌊', color: '#10b981' },
  { tag: 'review', name: '복습왕', icon: '📖', color: '#f59e0b' },
];

function lottoFormatDow(dateStr) {
  if (!dateStr) return '';
  try {
    const d = new Date(dateStr);
    const dows = ['일', '월', '화', '수', '목', '금', '토'];
    return dows[d.getDay()] || '';
  } catch (e) {
    return '';
  }
}

async function loadTestlottoDrawList() {
  try {
    const r = await fetch(_testlottoResolveApiUrl('/api/testlotto/predictions?limit=20000'));
    const data = await r.json();
    const rows = data && data.predictions ? data.predictions : [];
    _testlottoPredRowsCache = rows;
    const set = new Set(rows.map((p) => p.target_draw_no).filter((n) => n != null));

    const dr = await fetch(_testlottoResolveApiUrl('/api/testlotto/draws?limit=10000'));
    const dj = await dr.json();
    const draws = (dj && dj.draws) ? dj.draws : [];
    draws.forEach((d) => {
      if (d && d.draw_no != null && d.draw_no !== '') {
        const n = parseInt(d.draw_no, 10);
        if (Number.isFinite(n) && n > 0) {
          set.add(n);
          _testlottoDrawDates[n] = d.draw_date;
        }
      }
    });
    _testlottoDrawList = Array.from(set).filter((n) => Number.isFinite(n) && n > 0).sort((a, b) => b - a);

    const sel = document.getElementById('testlottoDrawSelect');
    if (sel) {
      sel.innerHTML = _testlottoDrawList.map((no) => {
        const date = _testlottoDrawDates[no] || '?';
        const dow = lottoFormatDow(date);
        return `<option value="${no}">${no}회 (${date} ${dow})</option>`;
      }).join('');
    }
    return true;
  } catch (e) {
    console.error('회차 목록 로드 실패:', e);
    return false;
  }
}

function _testlottoHydrateDrawIndex(data) {
  if (!data || !data.by_draw) return;
  Object.keys(data.by_draw).forEach((k) => {
    const dno = parseInt(k, 10);
    const summaries = data.by_draw[k] || [];
    _testlottoBtByDraw.set(dno, summaries);
    // pool mem cache는 ok pool만 — backtest_only stub 넣으면 pool-index·API ok hit 차단됨
  });
  if (data.actuals) {
    Object.keys(data.actuals).forEach((k) => {
      const a = data.actuals[k];
      const dno = parseInt(k, 10);
      _testlottoActualByDraw.set(dno, {
        target_draw_no: dno,
        actual_1: a.num1,
        actual_2: a.num2,
        actual_3: a.num3,
        actual_4: a.num4,
        actual_5: a.num5,
        actual_6: a.num6,
        actual_bonus: a.bonus,
      });
    });
  }
}

function _testlottoHydratePoolIndex(poolData) {
  if (!poolData || !poolData.by_draw) return;
  Object.keys(poolData.by_draw).forEach((k) => {
    const dno = parseInt(k, 10);
    const pv = poolData.by_draw[k];
    if (pv && pv.ok) {
      _testlottoPoolViewMemCache.set(dno, { ...pv, from_pool_index: true });
    }
  });
}

function preloadTestlottoBacktestIndex() {
  if (_testlottoBtPreloadDone) {
    return Promise.resolve(_testlottoBtByDraw);
  }
  if (_testlottoBtIndexPromise) {
    return _testlottoBtIndexPromise;
  }
  const drawUrl = _testlottoResolveApiUrl('/api/testlotto/backtest/draw-index');
  const poolUrl = _testlottoResolveApiUrl('/api/testlotto/backtest/pool-index');
  _testlottoBtIndexPromise = Promise.all([
    fetch(drawUrl).then((r) => (r.ok ? r.json() : null)),
    fetch(poolUrl).then((r) => (r.ok ? r.json() : null)).catch(() => null),
  ])
    .then(([data, poolData]) => {
      _testlottoHydrateDrawIndex(data);
      _testlottoHydratePoolIndex(poolData);
      _testlottoBtPreloadDone = true;
      const hint = document.querySelector('#testlottoBacktestDetails .testlotto-details-hint');
      if (hint && data && data.n_draws) {
        const poolN = poolData && poolData.n_draws ? poolData.n_draws : 0;
        hint.textContent = poolN
          ? `(${data.n_draws}회 · pool ${poolN} · DB 즉시)`
          : `(${data.n_draws}회 · DB 즉시 적용)`;
      }
      return _testlottoBtByDraw;
    })
    .catch((e) => {
      console.warn('backtest preload:', e);
      _testlottoBtIndexPromise = null;
      return _testlottoBtByDraw;
    });
  return _testlottoBtIndexPromise;
}

function _testlottoGetActualRefSync(drawNo) {
  const d = parseInt(drawNo, 10);
  if (!Number.isFinite(d) || d < 1) return null;
  const cached = _testlottoActualByDraw.get(d);
  if (cached && cached.actual_1 != null) return cached;
  return null;
}

function initTestlottoDrawSearch() {
  const sel = document.getElementById('testlottoDrawSelect');
  if (!sel) return;

  const applyContext = () => {
    if (!_testlottoDrawList.length) return;
    const latest = _testlottoDrawList[0];
    const input = document.getElementById('testlottoPredictDrawNo');
    const cur = input ? parseInt(input.value, 10) : NaN;
    const target = Number.isFinite(cur) && cur > 0 ? cur : latest;
    if (input) input.value = String(target);
    sel.value = String(target);
    // 백테 인덱스 프리로드와 화면 갱신을 병렬 — 로딩 스피너 없이 즉시 적용
    preloadTestlottoBacktestIndex().then(() => {
      testlottoShowDrawContext(target);
    });
    // 목록도 미리 채워 펼칠 때 대기 제거
    const panel = document.getElementById('testlottoBacktestPanel');
    if (panel && !panel.dataset.loaded) {
      loadTestlottoBacktestRuns().then(() => {
        panel.dataset.loaded = '1';
      });
    }
  };

  if (_testlottoDrawList.length > 0) {
    applyContext();
    return;
  }
  loadTestlottoDrawList().then(applyContext);
}

function testlottoSelectDraw(drawNo) {
  const no = parseInt(drawNo, 10);
  if (!no) return;
  const input = document.getElementById('testlottoPredictDrawNo');
  const sel = document.getElementById('testlottoDrawSelect');
  if (input) input.value = String(no);
  if (sel) sel.value = String(no);
  preloadTestlottoBacktestIndex().then(() => {
    testlottoShowDrawContext(no);
  });
}

/** 복습·학습 상세페이지 (새 탭) */
function testlottoOpenDetailPage() {
  const input = document.getElementById('testlottoPredictDrawNo');
  const drawNo = parseInt(input?.value, 10) || _testlottoDetailDrawNo || _testlottoDrawList[0] || 20;
  const q = `draw=${drawNo}&brain=stat&mode=single`;
  // /testlotto-detail 은 서버 재기동 후 사용; static 경로는 항상 동작
  const url = `/static/testlotto-detail.html?${q}`;
  const w = window.open(url, '_blank', 'noopener,noreferrer');
  if (!w) {
    window.location.href = url;
  }
}
window.testlottoOpenDetailPage = testlottoOpenDetailPage;

function testlottoNavDraw(delta) {
  if (!_testlottoDrawList.length) return;
  const input = document.getElementById('testlottoPredictDrawNo');
  const sel = document.getElementById('testlottoDrawSelect');
  const cur = input ? parseInt(input.value, 10) : NaN;
  const base = Number.isFinite(cur) ? cur : _testlottoDrawList[0];
  const idx = _testlottoDrawList.indexOf(base);
  const step = delta > 0 ? -1 : 1; // 최신순: 오른쪽(▶)은 과거로
  const nextIdx = Math.max(0, Math.min(_testlottoDrawList.length - 1, (idx >= 0 ? idx : 0) + step));
  const nextNo = _testlottoDrawList[nextIdx];
  if (input) input.value = String(nextNo);
  if (sel) sel.value = String(nextNo);
  preloadTestlottoBacktestIndex().then(() => {
    testlottoShowDrawContext(nextNo);
  });
}

function _detailResponseToPredictionRows(detail, drawNo) {
  const actual = detail.actual_nums || [];
  const bonus = detail.bonus;
  const rows = [];
  (detail.brains || []).forEach((brain) => {
    (brain.predicted_sets || []).forEach((s) => {
      const nums = s.nums || [];
      if (nums.length < 6) return;
      rows.push({
        target_draw_no: drawNo,
        brain_tag: brain.brain_tag,
        num1: nums[0],
        num2: nums[1],
        num3: nums[2],
        num4: nums[3],
        num5: nums[4],
        num6: nums[5],
        matched_count: s.matched_count != null ? s.matched_count : (brain.matched_count != null ? brain.matched_count : -1),
        bonus_matched: s.bonus_matched != null ? s.bonus_matched : 0,
        confidence: s.confidence,
        reasoning: s.reasoning || brain.narrative || '',
        actual_1: actual[0] != null ? actual[0] : null,
        actual_2: actual[1] != null ? actual[1] : null,
        actual_3: actual[2] != null ? actual[2] : null,
        actual_4: actual[3] != null ? actual[3] : null,
        actual_5: actual[4] != null ? actual[4] : null,
        actual_6: actual[5] != null ? actual[5] : null,
        actual_bonus: bonus != null ? bonus : null,
      });
    });
  });
  return rows;
}

async function _fetchPredictionRowsFromDetail(drawNo) {
  const r = await fetch(_testlottoResolveApiUrl('/api/testlotto/detail/draw/' + drawNo));
  const detail = await r.json();
  if (detail.error || !detail.brains || !detail.brains.length) {
    return { rows: [], source: 'none', detail };
  }
  return { rows: _detailResponseToPredictionRows(detail, drawNo), source: 'brain_review', detail };
}

async function _fetchPredictionRowsLegacy(drawNo) {
  const r = await fetch(_testlottoResolveApiUrl('/api/testlotto/predictions/draw/' + drawNo));
  const data = await r.json();
  const rows = (data && data.predictions) ? data.predictions : [];
  return { rows, source: 'lotto_predictions' };
}

function _testlottoStubRowsForDraw(drawNo, actualRef) {
  const d = parseInt(drawNo, 10);
  const ref = actualRef || _testlottoCurrentActualRef;
  const row = { target_draw_no: d, brain_tag: 'stat', matched_count: -1 };
  if (ref && ref.actual_1 != null) {
    row.actual_1 = ref.actual_1;
    row.actual_2 = ref.actual_2;
    row.actual_3 = ref.actual_3;
    row.actual_4 = ref.actual_4;
    row.actual_5 = ref.actual_5;
    row.actual_6 = ref.actual_6;
    row.actual_bonus = ref.actual_bonus;
  }
  return [row];
}

function _testlottoBuildBacktestPoolView(d, summaries, noteExtra) {
  const list = summaries || _testlottoBtByDraw.get(d) || [];
  if (!list.length) return null;
  return {
    ok: false,
    backtest_only: true,
    target_draw_no: d,
    backtest_summaries: list,
    cache_ms: 0,
    note_extra: noteExtra || '',
  };
}

/** backtest_only — accordion·hero 포함 전체 UI (구 minimal table 경로 대체) */
async function _testlottoRenderBacktestInstant(d, actualRef, summaries, noteExtra) {
  const poolView = _testlottoBuildBacktestPoolView(d, summaries, noteExtra);
  if (!poolView) return;
  _testlottoDetailDrawNo = d;
  _testlottoDetailRows = _testlottoStubRowsForDraw(d, actualRef);
  return renderPredictionsByBrain(d, _testlottoDetailRows, { poolView, skipPoolFetch: true });
}

function _testlottoBacktestCacheNoteHtml(drawNo, poolView) {
  if (!poolView || !poolView.backtest_only) return '';
  const extra = poolView.note_extra ? ` · ${poolView.note_extra}` : '';
  const ms = poolView.cache_ms != null ? ` · ${poolView.cache_ms}ms` : '';
  return (
    `<p class="testlotto-cache-note" role="status">백테스트 DB 저장됨 · 즉시 적용${extra}${ms}</p>` +
    _testlottoRenderBacktestFallbackHtml(drawNo, poolView.backtest_summaries || [])
  );
}

async function _testlottoResolvePoolViewForDraw(d) {
  const mem = _testlottoPoolViewMemCache.get(d);
  if (mem && mem.ok) {
    return mem;
  }
  try {
    const fetched = await _fetchPoolView(d, { cacheOnly: true });
    if (fetched && fetched.ok) {
      return fetched;
    }
    if (fetched && fetched.backtest_only) {
      return fetched;
    }
  } catch (e) {
    console.warn('pool-view cache lookup:', e);
  }
  return _testlottoBuildBacktestPoolView(d);
}

/** 회차 전환 — hero + pool/백테 구조 UI 즉시 · 무거운 WF는 「3뇌 예측」만 */
async function testlottoShowDrawContext(drawNo) {
  const d = parseInt(drawNo, 10);
  const container = document.getElementById('testlottoPredictionResults');
  if (!container || !Number.isFinite(d) || d < 1) {
    return;
  }
  const seq = ++_testlottoPredFetchSeq;
  container.classList.remove('testlotto-results-pending');
  container.removeAttribute('aria-busy');

  const actualRef = _testlottoGetActualRefSync(d) || await _testlottoResolveActualRef(d, null);
  if (seq !== _testlottoPredFetchSeq) {
    return;
  }
  _testlottoCurrentActualRef = actualRef;
  _testlottoDetailDrawNo = d;
  _testlottoDetailRows = _testlottoStubRowsForDraw(d, actualRef);

  const poolView = await _testlottoResolvePoolViewForDraw(d);
  if (seq !== _testlottoPredFetchSeq) {
    return;
  }

  if (poolView && (poolView.ok || poolView.backtest_only)) {
    await renderPredictionsByBrain(d, _testlottoDetailRows, { poolView, skipPoolFetch: true });
    loadTestlottoWarrantPanel(d);
    return;
  }

  const isFuture = !actualRef || actualRef.actual_1 == null;
  const emptyMsg = isFuture
    ? '추첨 전 · 예측하려면 「3뇌 예측」 버튼을 클릭하세요'
    : '예측 버튼을 눌러주세요 · 「3뇌 예측」으로 pool 10+5 세트를 계산합니다';
  await renderTestlottoDrawHero(d, null, actualRef);
  container.innerHTML =
    '<div class="testlotto-predict-empty">' +
    `<p class="testlotto-predict-empty__msg">${emptyMsg}</p>` +
    '<button type="button" class="btn btn-primary testlotto-predict-empty__btn" onclick="testlottoRunPoolPredict()">🎯 3뇌 예측</button>' +
    '</div>';
  loadTestlottoWarrantPanel(d);
}
window.testlottoShowDrawContext = testlottoShowDrawContext;

async function testlottoLoadSavedPrediction(drawNo, options) {
  const d = parseInt(drawNo, 10);
  const fromTab = options && options.fromTab;
  const softLoading = options && options.softLoading;
  const container = document.getElementById('testlottoPredictionResults');
  if (!container || !Number.isFinite(d) || d < 1) {
    return;
  }
  if (fromTab && _testlottoDetailDrawNo === d && Array.isArray(_testlottoDetailRows) && _testlottoDetailRows.length) {
    await renderPredictionsByBrain(d, _testlottoDetailRows);
    return;
  }
  const hasRichUi = !!container.querySelector('.lotto-brain-tabs');
  const useSoftShell = !!(softLoading && hasRichUi);
  const seq = ++_testlottoPredFetchSeq;
  if (useSoftShell) {
    container.classList.add('testlotto-results-pending');
    container.setAttribute('aria-busy', 'true');
    renderTestlottoDrawHero(d, null, _testlottoCurrentActualRef);
  } else {
    container.classList.remove('testlotto-results-pending');
    container.removeAttribute('aria-busy');
    container.innerHTML = testlottoLoadingSkeletonHtml(4);
  }
  try {
    let rows = [];
    let dataSource = 'brain_review';

    const detailResult = await _fetchPredictionRowsFromDetail(d);
    if (detailResult.rows.length) {
      // K-00 SSOT: brain_review(detail) 우선 — lotto_predictions는 detail 없을 때만
      rows = detailResult.rows;
      dataSource = detailResult.source;
    } else if (detailResult.detail && detailResult.detail.error) {
      // 미래 회차(당첨번호 없음): lotto_predictions 폴백
      const legacy = await _fetchPredictionRowsLegacy(d);
      if (legacy.rows.length) {
        rows = legacy.rows;
        dataSource = legacy.source;
      }
    }

    if (seq !== _testlottoPredFetchSeq) {
      return;
    }
    if (!rows.length) {
      // pool-view만으로도 10+5 표시 가능 (미래 회차·저장 없음)
      try {
        const dr = await fetch(_testlottoResolveApiUrl('/api/testlotto/draws/' + d));
        const drawRow = dr.ok ? await dr.json() : null;
        if (drawRow && !drawRow.error) {
          rows = [{
            target_draw_no: d,
            brain_tag: 'stat',
            actual_1: drawRow.num1, actual_2: drawRow.num2, actual_3: drawRow.num3,
            actual_4: drawRow.num4, actual_5: drawRow.num5, actual_6: drawRow.num6,
            actual_bonus: drawRow.bonus,
            matched_count: -1,
          }];
        } else {
          rows = [{ target_draw_no: d, brain_tag: 'stat', matched_count: -1 }];
        }
        _testlottoDetailDrawNo = d;
        _testlottoDetailRows = rows;
        await renderPredictionsByBrain(d, rows);
        loadTestlottoWarrantPanel(d);
        return;
      } catch (_e) {
        /* fall through */
      }
      _testlottoDetailDrawNo = null;
      _testlottoDetailRows = null;
      container.classList.remove('testlotto-results-pending');
      container.removeAttribute('aria-busy');
      await renderTestlottoDrawHero(d, null);
      container.innerHTML = `<p class="testlotto-results-empty">${d}회차 저장된 예측 없음. 「3뇌 예측」 버튼으로 실행하세요.</p>`;
      return;
    }
    _testlottoDetailDrawNo = d;
    _testlottoDetailRows = rows;
    _testlottoPredDataSource = dataSource;
    _testlottoPredRowsCache = (_testlottoPredRowsCache || []).filter((p) => parseInt(p.target_draw_no, 10) !== d);
    _testlottoPredRowsCache = rows.concat(_testlottoPredRowsCache || []);
    await renderPredictionsByBrain(d, rows);
    loadTestlottoWarrantPanel(d);
  } catch (e) {
    if (seq !== _testlottoPredFetchSeq) {
      return;
    }
    container.classList.remove('testlotto-results-pending');
    container.removeAttribute('aria-busy');
    container.innerHTML = `<p style="color: #f88;">로드 실패: ${e.message}</p>`;
  }
}

function testlottoSwitchBrainTab(brainTag) {
  _testlottoCurrentBrainTab = String(brainTag || '').toLowerCase();
  const drawNo = parseInt(document.getElementById('testlottoPredictDrawNo').value, 10);
  if (drawNo && _testlottoDetailRows) {
    const poolView = _testlottoPoolViewMemCache.get(drawNo);
    if (poolView && poolView.ok) {
      renderPredictionsByBrain(drawNo, _testlottoDetailRows, { poolView, skipPoolFetch: true });
    }
  }
}

function testlottoSwitchSetSubTab(kind) {
  _testlottoSetSubTab = kind === 'repack' ? 'repack' : 'pool';
  const drawNo = parseInt(document.getElementById('testlottoPredictDrawNo').value, 10);
  if (!drawNo) return;
  const poolView = _testlottoPoolViewMemCache.get(drawNo) || null;
  const rows = _testlottoDetailRows || _testlottoStubRowsForDraw(drawNo, _testlottoCurrentActualRef);
  renderPredictionsByBrain(drawNo, rows, { poolView, skipPoolFetch: true });
}

function testlottoToggleBrainAccordion(tag, open) {
  const t = String(tag || '').toLowerCase();
  _testlottoBrainAccordionOpen[t] = !!open;
}

function lottoMiniBallBg(num) {
  const n = parseInt(num, 10);
  if (!n) return '#555';
  if (n <= 10) return '#fbc400';
  if (n <= 20) return '#69c8f2';
  if (n <= 30) return '#ff7272';
  if (n <= 40) return '#aaa';
  return '#b0d840';
}

function renderMiniBall(num, isHit, extraClass) {
  const n = parseInt(num, 10);
  const bg = lottoMiniBallBg(n);
  const hitClass = isHit ? 'is-hit' : '';
  const ex = extraClass ? String(extraClass) : '';
  return `<span class="lotto-mini-ball ${hitClass} ${ex}" style="background:${bg};">${n}</span>`;
}

function testlottoTierRank(row) {
  const m = row.matched_count != null ? Number(row.matched_count) : NaN;
  const bonus = row.bonus_matched === 1 || Number(row.bonus_matched) === 1;
  if (!Number.isFinite(m) || m < 0) return 0;
  if (m === 6) return 1;
  if (m === 5 && bonus) return 2;
  if (m === 5) return 3;
  if (m === 4) return 4;
  if (m === 3) return 5;
  return 0;
}

function _testlottoRescoreRow(row, actualRef) {
  const out = { ...row };
  if (!actualRef || actualRef.actual_1 == null) {
    out.matched_count = -1;
    out.bonus_matched = 0;
    return out;
  }
  const rescored = _poolSetToRow(
    {
      nums: [row.num1, row.num2, row.num3, row.num4, row.num5, row.num6],
      brain_tag: row.brain_tag,
      kind: row.reasoning && String(row.reasoning).indexOf('몰아주기') >= 0 ? 'repack' : 'pool',
    },
    parseInt(row.target_draw_no, 10) || parseInt(actualRef.target_draw_no, 10),
    actualRef,
  );
  out.matched_count = rescored.matched_count;
  out.bonus_matched = rescored.bonus_matched;
  out.actual_1 = rescored.actual_1;
  out.actual_2 = rescored.actual_2;
  out.actual_3 = rescored.actual_3;
  out.actual_4 = rescored.actual_4;
  out.actual_5 = rescored.actual_5;
  out.actual_6 = rescored.actual_6;
  out.actual_bonus = rescored.actual_bonus;
  return out;
}

async function _testlottoResolveActualRef(drawNo, rows) {
  const d = parseInt(drawNo, 10);
  if (!Number.isFinite(d) || d < 1) return null;
  const synced = _testlottoGetActualRefSync(d);
  if (synced) return synced;
  const candidate = (rows || []).find(
    (r) => parseInt(r.target_draw_no, 10) === d && r.actual_1 != null && r.actual_6 != null,
  );
  if (candidate) {
    return {
      target_draw_no: d,
      actual_1: candidate.actual_1,
      actual_2: candidate.actual_2,
      actual_3: candidate.actual_3,
      actual_4: candidate.actual_4,
      actual_5: candidate.actual_5,
      actual_6: candidate.actual_6,
      actual_bonus: candidate.actual_bonus,
    };
  }
  try {
    const r = await fetch(_testlottoResolveApiUrl('/api/testlotto/draws/' + d));
    if (r.ok) {
      const drawRow = await r.json();
      if (drawRow && !drawRow.error && drawRow.num1 != null) {
        return {
          target_draw_no: d,
          actual_1: drawRow.num1,
          actual_2: drawRow.num2,
          actual_3: drawRow.num3,
          actual_4: drawRow.num4,
          actual_5: drawRow.num5,
          actual_6: drawRow.num6,
          actual_bonus: drawRow.bonus,
        };
      }
    }
  } catch (e) {
    console.warn('resolve actual ref:', e);
  }
  return null;
}

function _testlottoPoolViewScoreRows(poolView, drawNo, actualRef, kinds) {
  if (!poolView || !poolView.ok || !actualRef || actualRef.actual_1 == null) return [];
  const kindList = kinds || ['pool', 'repack'];
  const out = [];
  kindList.forEach((kind) => {
    const byBrain = kind === 'repack' ? poolView.repack_by_brain : poolView.pool_by_brain;
    if (!byBrain) return;
    Object.keys(byBrain).forEach((tag) => {
      (byBrain[tag] || []).forEach((s) => {
        out.push(_poolSetToRow(
          { ...s, brain_tag: s.brain_tag || tag, kind: kind === 'repack' ? 'repack' : 'pool' },
          drawNo,
          actualRef,
        ));
      });
    });
  });
  return out;
}

function _testlottoHitSummarySourceRows(drawNo, rows, poolView, actualRef) {
  if (poolView && poolView.ok && actualRef) {
    return _testlottoPoolViewScoreRows(poolView, drawNo, actualRef, ['pool', 'repack']);
  }
  if (!actualRef) return [];
  return (rows || []).map((r) => _testlottoRescoreRow(r, actualRef));
}

function _testlottoTierWinsItemsFromRows(scoreRows) {
  return (scoreRows || [])
    .map((r) => ({
      rank: testlottoTierRank(r),
      brain_tag: r.brain_tag,
      nums: [r.num1, r.num2, r.num3, r.num4, r.num5, r.num6],
      matched_count: Number(r.matched_count),
      bonus_matched: r.bonus_matched,
    }))
    .filter((it) => it.rank >= 1 && it.rank <= 5)
    .sort((a, b) => a.rank - b.rank || String(a.brain_tag || '').localeCompare(String(b.brain_tag || '')));
}

function testlottoHitSummaryHtml(rows) {
  const c = { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 };
  (rows || []).forEach((r) => {
    const tr = testlottoTierRank(r);
    if (tr) c[tr] += 1;
  });
  const total = c[1] + c[2] + c[3] + c[4] + c[5];
  if (!total) {
    const pending = (rows || []).some((r) => r.matched_count != null && Number(r.matched_count) < 0);
    if (pending) {
      return '<p class="lotto-hit-summary lotto-hit-summary--pending">아직 추첨 전 — 당첨 번호가 나오면 여기서 맞춘 개수를 보여 줍니다</p>';
    }
    return '<p class="lotto-hit-summary lotto-hit-summary--none">이 회차는 1~5등에 해당하는 예측이 없습니다 · <button type="button" class="lotto-hit-summary__link" onclick="testlottoOpenTierWinsModal()">자세히</button></p>';
  }
  return `<p class="lotto-hit-summary">맞춘 결과: 1등 ${c[1]} · 2등 ${c[2]} · 3등 ${c[3]} · 4등 ${c[4]} · 5등 ${c[5]} · <button type="button" class="lotto-hit-summary__link" onclick="testlottoOpenTierWinsModal()">목록 보기</button></p>`;
}

function _testlottoBuildActualHtml(actuals, bonus) {
  if (!actuals || !actuals.length) {
    return '<div class="testlotto-hero-actual testlotto-hero-actual--pending"><span class="testlotto-hero-actual__label">당첨번호</span><span class="testlotto-hero-actual__pending">아직 추첨 전</span></div>';
  }
  const balls = actuals.map((n) => renderMiniBall(n, false, 'is-actual testlotto-hero-ball')).join('');
  const bonusHtml =
    bonus != null && bonus !== ''
      ? `<span class="testlotto-hero-bonus">+ ${renderMiniBall(bonus, false, 'is-actual is-bonus testlotto-hero-ball')}</span>`
      : '';
  return (
    `<div class="testlotto-hero-actual">` +
    `<span class="testlotto-hero-actual__label">당첨번호</span>` +
    `<span class="testlotto-hero-actual__balls">${balls}</span>` +
    bonusHtml +
    `</div>`
  );
}

async function renderTestlottoDrawHero(drawNo, summaryRows, actualRef) {
  const body = document.getElementById('testlottoDrawHeroBody');
  if (!body) return;
  const d = parseInt(drawNo, 10);
  if (!Number.isFinite(d) || d < 1) return;

  const date = _testlottoDrawDates[d] || '?';
  const dow = lottoFormatDow(date);
  const ref = actualRef || _testlottoCurrentActualRef;
  let actuals = null;
  let bonus = null;

  if (ref && ref.actual_1 != null) {
    actuals = [
      ref.actual_1,
      ref.actual_2,
      ref.actual_3,
      ref.actual_4,
      ref.actual_5,
      ref.actual_6,
    ];
    bonus = ref.actual_bonus;
  } else {
    try {
      const r = await fetch(_testlottoResolveApiUrl(`/api/testlotto/detail/draw/${d}`));
      if (r.ok) {
        const detail = await r.json();
        if (!detail.error) {
          if (Array.isArray(detail.nums) && detail.nums.length) {
            actuals = detail.nums;
          } else if (detail.num1 != null) {
            actuals = [detail.num1, detail.num2, detail.num3, detail.num4, detail.num5, detail.num6];
          } else if (Array.isArray(detail.actual_nums) && detail.actual_nums.length) {
            actuals = detail.actual_nums;
          }
          bonus = detail.bonus;
        }
      }
    } catch (e) {
      console.warn('draw hero detail:', e);
    }
  }

  const hitSummaryHtml = summaryRows && summaryRows.length ? testlottoHitSummaryHtml(summaryRows) : '';
  body.innerHTML =
    `<div class="testlotto-hero-title">` +
    `<span class="testlotto-hero-draw">제 ${d}회</span>` +
    `<span class="testlotto-hero-date">${date !== '?' ? `${date} ${dow}` : '추첨일 미확인'}</span>` +
    `</div>` +
    _testlottoBuildActualHtml(actuals, bonus) +
    (hitSummaryHtml ? `<div class="testlotto-hero-hit">${hitSummaryHtml}</div>` : '');
}

function _poolSetToRow(setObj, drawNo, actualRow) {
  const nums = setObj.nums || [];
  const actuals = actualRow ? [
    actualRow.actual_1, actualRow.actual_2, actualRow.actual_3,
    actualRow.actual_4, actualRow.actual_5, actualRow.actual_6,
  ].filter((x) => x != null).map((n) => parseInt(n, 10)) : [];
  const bonus = actualRow && actualRow.actual_bonus != null ? parseInt(actualRow.actual_bonus, 10) : null;
  let matched = -1;
  let bonusMatched = 0;
  if (actuals.length === 6) {
    const predSet = new Set(nums.map((n) => parseInt(n, 10)));
    matched = actuals.filter((n) => predSet.has(n)).length;
    if (bonus != null && predSet.has(bonus)) bonusMatched = 1;
  }
  return {
    target_draw_no: drawNo,
    brain_tag: setObj.brain_tag,
    num1: nums[0], num2: nums[1], num3: nums[2],
    num4: nums[3], num5: nums[4], num6: nums[5],
    matched_count: matched,
    bonus_matched: bonusMatched,
    confidence: null,
    reasoning: setObj.kind === 'repack' ? '신호 몰아주기' : '10장 pool',
    actual_1: actualRow ? actualRow.actual_1 : null,
    actual_2: actualRow ? actualRow.actual_2 : null,
    actual_3: actualRow ? actualRow.actual_3 : null,
    actual_4: actualRow ? actualRow.actual_4 : null,
    actual_5: actualRow ? actualRow.actual_5 : null,
    actual_6: actualRow ? actualRow.actual_6 : null,
    actual_bonus: actualRow ? actualRow.actual_bonus : null,
  };
}

function renderBrainSetCard(row, idx) {
  const nums = [row.num1, row.num2, row.num3, row.num4, row.num5, row.num6].map((n) => parseInt(n, 10));
  const matched = row.matched_count != null ? Number(row.matched_count) : -1;
  const bonusHit = row.bonus_matched === 1 || Number(row.bonus_matched) === 1;

  let rank = '';
  let rankClass = 'rank-none';
  if (matched === 6) { rank = '🏆 1등!'; rankClass = 'rank-1'; }
  else if (matched === 5 && bonusHit) { rank = '🥈 2등'; rankClass = 'rank-2'; }
  else if (matched === 5) { rank = '🥉 3등'; rankClass = 'rank-3'; }
  else if (matched === 4) { rank = '4등'; rankClass = 'rank-4'; }
  else if (matched === 3) { rank = '5등'; rankClass = 'rank-5'; }
  else if (matched >= 0) { rank = '미당첨'; rankClass = 'rank-none'; }
  else { rank = '추첨 전'; rankClass = 'rank-pending'; }

  const actuals = [row.actual_1, row.actual_2, row.actual_3, row.actual_4, row.actual_5, row.actual_6].filter((x) => x != null);
  const actualSet = new Set(actuals.map((n) => parseInt(n, 10)));

  const ballsHtml = nums.map((n) => renderMiniBall(n, actualSet.has(n))).join('');

  let conf = '-';
  if (row.confidence != null && row.confidence !== '') {
    const v = Number(row.confidence);
    if (Number.isFinite(v)) {
      // DB가 0~1 또는 이미 % (예: 97.9) 둘 다 대응
      conf = (v <= 1 ? (v * 100) : v).toFixed(1) + '%';
    }
  }

  let sourceBadge = '';
  const reasoning = String(row.reasoning || '');
  const srcMatch = reasoning.match(/출처:(SEL4|V3)/);
  if (srcMatch) {
    const src = srcMatch[1];
    const srcClass = src === 'V3' ? 'lotto-set-src-v3' : 'lotto-set-src-sel4';
    const srcLabel = src === 'V3' ? 'v3 방식' : 'SEL4';
    sourceBadge = `<span class="lotto-set-source ${srcClass}">${srcLabel}</span>`;
  }

  return `
    <div class="lotto-set-card ${rankClass}">
      <div class="lotto-set-header">
        <span class="lotto-set-idx">#${idx}</span>
        <span class="lotto-set-rank">${rank}</span>
        ${sourceBadge}
        <span class="lotto-set-conf">신뢰도 ${conf}</span>
      </div>
      <div class="lotto-set-balls">${ballsHtml}</div>
    </div>
  `;
}

async function ensureBrainEliteTagsLoaded() {
  if (_testlottoBrainEliteTagSet !== null) {
    return true;
  }
  try {
    const r = await fetch(_testlottoResolveApiUrl('/api/testlotto/brain/elite-tags'));
    if (!r.ok) {
      throw new Error(String(r.status));
    }
    const data = await r.json();
    _testlottoBrainEliteTagSet = new Set((data.tags || []).map((t) => String(t).toLowerCase()));
    return true;
  } catch (e) {
    console.warn('brain elite-tags:', e);
    return false;
  }
}

async function testlottoOnEliteBrainToggle() {
  _testlottoBrainEliteTagSet = null;
  const d = _testlottoDetailDrawNo;
  if (!d) return;

  const eliteCb = document.getElementById('testlottoEliteBrainToggle');
  const statusEl = document.getElementById('testlottoActionStatus');

  if (eliteCb && eliteCb.checked) {
    const ok = await ensureBrainEliteTagsLoaded();
    if (ok && _testlottoBrainEliteTagSet && _testlottoBrainEliteTagSet.size === 0) {
      eliteCb.checked = false;
      if (statusEl) {
        statusEl.textContent = '고적중 조건 해당 뇌 없음 — 전체 표시 유지';
        setTimeout(() => {
          if (statusEl.textContent.includes('고적중 조건')) statusEl.textContent = '';
        }, 4000);
      }
      await testlottoShowDrawContext(d);
      return;
    }
  }

  await testlottoShowDrawContext(d);
}
window.testlottoOnEliteBrainToggle = testlottoOnEliteBrainToggle;

/** B-04: pool-view fetch 중 스켈레톤 — firstCompute=true 일 때만 장시간 안내 */
function testlottoLoadingSkeletonHtml(cardCount = 6, firstCompute = false) {
  const msg = firstCompute
    ? '처음 pool 계산 중… (최초 1회만 수십 초 걸릴 수 있습니다)'
    : '불러오는 중…';
  const cards = Array.from({ length: cardCount }, () =>
    '<div class="testlotto-skeleton-card" aria-hidden="true">' +
    '<div class="testlotto-skeleton-line testlotto-skeleton-line--short"></div>' +
    '<div class="testlotto-skeleton-balls"></div></div>'
  ).join('');
  return (
    '<div class="testlotto-loading-inner">' +
    '<div class="testlotto-loading-spinner" role="presentation"></div>' +
    `<p class="testlotto-loading-msg" role="status">${msg}</p>` +
    `<div class="testlotto-skeleton-grid">${cards}</div></div>`
  );
}

function testlottoShowResultsLoading(container, firstCompute = false) {
  if (!container) return;
  container.setAttribute('aria-busy', 'true');
  container.classList.add('testlotto-results-pending');
  const cardsEl = container.querySelector('#hyodoBrainCards, #testlottoBrainAccordions, .testlotto-brain-accordions');
  if (cardsEl) {
    cardsEl.innerHTML = testlottoLoadingSkeletonHtml(6, firstCompute);
    return;
  }
  if (!container.querySelector('.testlotto-loading-inner')) {
    container.innerHTML = testlottoLoadingSkeletonHtml(4, firstCompute);
  }
}

function testlottoClearResultsLoading(container) {
  if (!container) return;
  container.classList.remove('testlotto-results-pending');
  container.removeAttribute('aria-busy');
}

function _testlottoBrainTierSummaryText(tag) {
  const m = _testlottoBrainPowerByTag || {};
  const b = m[String(tag).toLowerCase()] || {};
  return [b.rank1 || 0, b.rank2 || 0, b.rank3 || 0, b.rank4 || 0, b.rank5 || 0].join('·');
}

function _testlottoPoolHasKind(poolView, kind) {
  if (!poolView || !poolView.ok) return false;
  const src = kind === 'repack' ? poolView.repack_by_brain : poolView.pool_by_brain;
  if (!src || typeof src !== 'object') return false;
  return Object.values(src).some((arr) => Array.isArray(arr) && arr.length > 0);
}

function _testlottoRenderSetSubTabsHtml(activeKind, poolView) {
  const hasPool = _testlottoPoolHasKind(poolView, 'pool');
  const hasRepack = _testlottoPoolHasKind(poolView, 'repack');
  if (!hasPool && !hasRepack) return '';
  if (hasPool && !hasRepack) {
    return '<p class="testlotto-set-kind-label" role="note">10장 pool</p>';
  }
  if (!hasPool && hasRepack) {
    return '<p class="testlotto-set-kind-label" role="note">몰아주기 5장</p>';
  }
  const poolActive = activeKind !== 'repack' ? 'active' : '';
  const repackActive = activeKind === 'repack' ? 'active' : '';
  return (
    '<div class="testlotto-set-subtabs" role="tablist" aria-label="세트 종류">' +
    `<button type="button" class="testlotto-set-subtab ${poolActive}" role="tab" aria-selected="${activeKind !== 'repack'}" onclick="testlottoSwitchSetSubTab('pool')">10장 pool</button>` +
    `<button type="button" class="testlotto-set-subtab ${repackActive}" role="tab" aria-selected="${activeKind === 'repack'}" onclick="testlottoSwitchSetSubTab('repack')">몰아주기 5장</button>` +
    '</div>'
  );
}

function _testlottoRenderBrainCardsHtml(tag, poolView, drawNo, actualRef, subTab) {
  if (!poolView || !poolView.ok || !poolView.pool_by_brain) {
    if (poolView && poolView.backtest_only) {
      return (
        '<div class="testlotto-predict-empty testlotto-predict-empty--inline">' +
        '<p class="testlotto-predict-empty__msg">pool 10+5 상세는 「3뇌 예측」으로 계산합니다</p>' +
        '<button type="button" class="btn btn-primary testlotto-predict-empty__btn" onclick="testlottoRunPoolPredict()">🎯 3뇌 예측</button>' +
        '</div>'
      );
    }
    if (poolView && poolView.backtest_summaries && poolView.backtest_summaries.length) {
      return _testlottoRenderBacktestFallbackHtml(drawNo, poolView.backtest_summaries);
    }
    return '<p style="color:#888;padding:8px;">pool 데이터 없음</p>';
  }
  const kind = subTab === 'repack' ? 'repack' : 'pool';
  const src = kind === 'repack'
    ? (poolView.repack_by_brain[tag] || [])
    : (poolView.pool_by_brain[tag] || []);
  const rows = src.map((s) => _poolSetToRow(s, drawNo, actualRef));
  if (!rows.length) {
    return kind === 'repack'
      ? '<p style="color:#888;padding:8px;">몰아주기 세트 없음</p>'
      : '<p style="color:#888;padding:8px;">pool 없음</p>';
  }
  return rows.map((r, i) => renderBrainSetCard(r, i + 1)).join('');
}

function _testlottoRenderAllBrainsAccordion(poolView, drawNo, actualRef, brainListForTabs, subTab) {
  return brainListForTabs.map((b) => {
    const open = !!_testlottoBrainAccordionOpen[b.tag];
    const tierTxt = _testlottoBrainTierSummaryText(b.tag);
    const cards = _testlottoRenderBrainCardsHtml(b.tag, poolView, drawNo, actualRef, subTab);
    const subTabsHtml = _testlottoRenderSetSubTabsHtml(subTab, poolView);
    const poolCnt = poolView && poolView.pool_by_brain && poolView.pool_by_brain[b.tag]
      ? poolView.pool_by_brain[b.tag].length : 0;
    return (
      `<details class="testlotto-brain-accordion" data-brain="${b.tag}" ${open ? 'open' : ''} ontoggle="testlottoToggleBrainAccordion('${b.tag}', this.open)">` +
      '<summary class="testlotto-brain-accordion__head">' +
      `<span class="testlotto-brain-accordion__chevron" aria-hidden="true"></span>` +
      `<span class="testlotto-brain-accordion__icon">${b.icon}</span>` +
      `<span class="testlotto-brain-accordion__name">${b.name}</span>` +
      (poolCnt ? `<span class="testlotto-brain-accordion__cnt">${poolCnt}장</span>` : '') +
      `<span class="testlotto-brain-accordion__tier" title="역대 1~5등 횟수">${tierTxt}</span>` +
      '</summary>' +
      `<div class="testlotto-brain-accordion__body">` +
      subTabsHtml +
      `<div class="lotto-brain-cards testlotto-brain-accordion__cards">${cards}</div>` +
      '</div></details>'
    );
  }).join('');
}

async function _fetchPoolView(drawNo, options) {
  const opts = options || {};
  const forceRefresh = !!opts.forceRefresh;
  const compute = !!opts.compute;
  const cacheOnly = !!opts.cacheOnly || (!compute && !forceRefresh);

  if (!forceRefresh) {
    const mem = _testlottoPoolViewMemCache.get(drawNo);
    if (mem && mem.ok) {
      return { ...mem, from_mem: true };
    }
  }

  let url = _testlottoResolveApiUrl('/api/testlotto/predict/pool-view/' + drawNo);
  const params = [];
  if (forceRefresh) {
    params.push('refresh=1');
  } else if (compute) {
    params.push('compute=1');
  }
  if (params.length) {
    url += '?' + params.join('&');
  }

  const pr = await fetch(url);
  if (!pr.ok) {
    throw new Error(String(pr.status));
  }
  const data = await pr.json();
  if (data && data.ok) {
    _testlottoPoolViewMemCache.set(drawNo, data);
  } else if (cacheOnly && data && data.cache_miss && !data.backtest_only) {
    return data;
  }
  return data;
}

function _testlottoRenderBacktestFallbackHtml(drawNo, summaries) {
  if (!summaries || !summaries.length) {
    return '<p style="color:#888;padding:8px;">pool 데이터 없음</p>';
  }
  let html =
    `<p class="testlotto-backtest-fallback-note">${drawNo}회차 · 백테스트 DB 저장됨 · 즉시 표시 (pool 상세는 예측 버튼)</p>` +
    '<table class="testlotto-backtest-table testlotto-backtest-table--draws"><thead><tr>' +
    '<th>전략</th><th>최고 적중</th><th>등수</th></tr></thead><tbody>';
  summaries.forEach((s) => {
    html += '<tr>';
    html += '<td>' + _tlEscapeHtml(s.strategy_label_ko || testlottoStrategyLabelKo(s.strategy_id)) + '</td>';
    html += '<td>' + (s.best_hits != null ? s.best_hits + '개' : '—') + '</td>';
    html += '<td>' + _tlEscapeHtml(s.best_tier_label || '—') + '</td>';
    html += '</tr>';
  });
  html += '</tbody></table>';
  return html;
}

async function renderPredictionsByBrain(drawNo, rows, options) {
  const container = document.getElementById('testlottoPredictionResults');
  if (!container) return;

  const opts = options || {};
  const skipPoolFetch = !!opts.skipPoolFetch;
  const shouldCompute = !!opts.compute;

  // skipPoolFetch여도 mem cache는 사용 (서브탭·뇌 전환 시 poolView 유실 방지)
  let poolView = opts.poolView || _testlottoPoolViewMemCache.get(drawNo) || null;
  if (!poolView && shouldCompute) {
    testlottoShowResultsLoading(container, true);
    try {
      poolView = await _fetchPoolView(drawNo, { compute: true });
      if (poolView && !poolView.ok) {
        poolView = null;
      }
    } catch (e) {
      console.warn('pool-view compute:', e);
    }
  }

  await ensureLottoBrainPowerLoaded();
  try {
    await ensureTestlottoWarrantLoaded(drawNo);
  } catch (e) {
    console.warn('warrant cache:', e);
  }

  const actualRef = await _testlottoResolveActualRef(drawNo, rows);
  _testlottoCurrentActualRef = actualRef;
  const summaryRows = _testlottoHitSummarySourceRows(drawNo, rows, poolView, actualRef);
  await renderTestlottoDrawHero(drawNo, summaryRows, actualRef);
  const byBrain = {};
  rows.forEach((r) => {
    const tag = String(r.brain_tag || 'legacy').toLowerCase();
    if (!byBrain[tag]) byBrain[tag] = [];
    byBrain[tag].push(r);
  });

  const eliteCb = document.getElementById('testlottoEliteBrainToggle');
  let eliteOn = !!(eliteCb && eliteCb.checked);

  let brainListForTabs = TESTLOTTO_BRAIN_LIST;
  if (eliteOn) {
    const ok = await ensureBrainEliteTagsLoaded();
    if (ok) {
      brainListForTabs = TESTLOTTO_BRAIN_LIST.filter((b) => _testlottoBrainEliteTagSet.has(b.tag));
    }
  }

  if (eliteOn && brainListForTabs.length === 0) {
    if (eliteCb) eliteCb.checked = false;
    const statusEl = document.getElementById('testlottoActionStatus');
    if (statusEl) {
      statusEl.textContent = '고적중 조건 해당 뇌 없음 — 전체 표시';
      setTimeout(() => {
        if (statusEl.textContent.includes('고적중 조건')) statusEl.textContent = '';
      }, 4000);
    }
    brainListForTabs = TESTLOTTO_BRAIN_LIST;
    eliteOn = false;
  }

  if (!_testlottoCurrentBrainTab || _testlottoCurrentBrainTab === 'legacy') {
    _testlottoCurrentBrainTab = 'all';
  }
  const allowedTags = new Set(brainListForTabs.map((b) => b.tag));
  if (_testlottoCurrentBrainTab !== 'all' && eliteOn && allowedTags.size && !allowedTags.has(_testlottoCurrentBrainTab)) {
    _testlottoCurrentBrainTab = brainListForTabs[0].tag;
  }
  if (_testlottoCurrentBrainTab !== 'all' && !byBrain[_testlottoCurrentBrainTab] && !(poolView && poolView.pool_by_brain)) {
    const firstTag = Object.keys(byBrain)[0];
    _testlottoCurrentBrainTab = firstTag || 'all';
  }

  let bodyHtml = '';
  const subTab = _testlottoSetSubTab;
  const useAccordion = _testlottoCurrentBrainTab === 'all';

  if (useAccordion) {
    bodyHtml =
      `<div class="testlotto-brain-accordions" id="testlottoBrainAccordions">` +
      _testlottoRenderAllBrainsAccordion(poolView, drawNo, actualRef, brainListForTabs, subTab) +
      '</div>';
    if (poolView && poolView.no_peek) {
      bodyHtml += '<p class="testlotto-no-peek-note">※ 미래 회차 미열람(walk-forward) · coordinator 미배선 · 표시 전용</p>';
    }
  } else {
    const tag = _testlottoCurrentBrainTab;
    const tabsHtml = brainListForTabs.map((b) => {
      const poolCnt = poolView && poolView.pool_by_brain && poolView.pool_by_brain[b.tag]
        ? poolView.pool_by_brain[b.tag].length : (byBrain[b.tag] || []).length;
      const active = b.tag === tag ? 'active' : '';
      const disabled = poolCnt === 0 ? 'disabled' : '';
      return (
        `<button class="lotto-brain-tab ${active} ${disabled}"` +
        ` data-brain="${b.tag}" style="--brain-color: ${b.color};"` +
        ` onclick="testlottoSwitchBrainTab('${b.tag}')" ${disabled ? 'disabled' : ''}>` +
        `<span class="lotto-brain-tab-head">` +
        `<span class="lotto-brain-icon">${b.icon}</span>` +
        `<span class="lotto-brain-name">${b.name}</span>` +
        `<span class="lotto-brain-cnt">${poolCnt || 0}</span>` +
        '</span></button>'
      );
    }).join('');
    const allTabHtml =
      `<button class="lotto-brain-tab lotto-brain-tab--all" data-brain="all"` +
      ` onclick="testlottoSwitchBrainTab('all')">` +
      '<span class="lotto-brain-tab-head">' +
      '<span class="lotto-brain-icon">📋</span>' +
      '<span class="lotto-brain-name">전체 보기</span>' +
      '</span></button>';

    let cardsHtml = '';
    if (poolView && poolView.ok && poolView.pool_by_brain) {
      cardsHtml = _testlottoRenderBrainCardsHtml(tag, poolView, drawNo, actualRef, subTab);
      if (poolView.no_peek) {
        cardsHtml += '<p class="testlotto-no-peek-note">※ 미래 회차 미열람(walk-forward) · coordinator 미배선 · 표시 전용</p>';
      }
    } else {
      const selectedRows = byBrain[tag] || [];
      cardsHtml = selectedRows.length
        ? selectedRows.map((r, i) => renderBrainSetCard(r, i + 1)).join('')
        : '<p style="color:#888; padding: 16px;">이 프로그램은 이 회차 예측 기록이 없습니다.</p>';
    }
    bodyHtml =
      `<div class="lotto-brain-tabs">${tabsHtml}${allTabHtml}</div>` +
      _testlottoRenderSetSubTabsHtml(subTab, poolView) +
      `<div class="lotto-brain-cards" id="hyodoBrainCards">${cardsHtml}</div>`;
  }

  const cacheNote = poolView && poolView.ok && (poolView.cached || poolView.from_mem || poolView.from_pool_index)
    ? `<p class="testlotto-cache-note" role="status">DB 캐시 · 저장됨${poolView.computed_at ? ` · ${poolView.computed_at}` : ''}${poolView.cache_ms != null ? ` · ${poolView.cache_ms}ms` : ''}</p>`
    : (poolView && poolView.ok && poolView.compute_ms
      ? `<p class="testlotto-cache-note testlotto-cache-note--fresh">처음 계산 완료 · ${poolView.compute_ms}ms · DB 저장됨</p>`
      : (poolView && poolView.backtest_only
        ? _testlottoBacktestCacheNoteHtml(drawNo, poolView)
        : ''));

  container.innerHTML = `${cacheNote}${bodyHtml}`;
  testlottoClearResultsLoading(container);
}

/** 세트 순번(#1~#5) → 카톡용 이모지 */
const _testlottoKakaoSetEmoji = ['', '🥇', '🥈', '🥉', '4️⃣', '5️⃣'];

function lottoClipboardWriteText(text) {
  if (navigator.clipboard && window.isSecureContext) {
    return navigator.clipboard.writeText(text);
  }
  return new Promise((resolve, reject) => {
    const ta = document.createElement('textarea');
    ta.value = text;
    ta.setAttribute('readonly', '');
    ta.style.position = 'fixed';
    ta.style.left = '-9999px';
    document.body.appendChild(ta);
    ta.select();
    try {
      if (document.execCommand('copy')) {
        resolve();
      } else {
        reject(new Error('execCommand copy failed'));
      }
    } catch (e) {
      reject(e);
    } finally {
      document.body.removeChild(ta);
    }
  });
}

/**
 * 1군 두뇌예측: 현재 불러온 예측(_testlottoDetailRows)을 카카오톡용 텍스트로 복사.
 * 고적중 필터·뇌 탭 목록과 동일한 뇌 순서(TESTLOTTO_BRAIN_LIST)로 전 뇌 출력(화면은 한 탭만 보여도 전 뇌 포함).
 */
async function testlottoCopyKakaoText() {
  const rows = _testlottoDetailRows;
  const drawNo = _testlottoDetailDrawNo;
  if (!rows || !rows.length || !drawNo) {
    alert('먼저 회차를 선택한 뒤 「3뇌 예측」을 눌러 예측을 불러오세요.');
    return;
  }

  let brainListForTabs = TESTLOTTO_BRAIN_LIST;
  const eliteCb = document.getElementById('testlottoEliteBrainToggle');
  const eliteOn = !!(eliteCb && eliteCb.checked);
  if (eliteOn) {
    const ok = await ensureBrainEliteTagsLoaded();
    if (ok && _testlottoBrainEliteTagSet) {
      brainListForTabs = TESTLOTTO_BRAIN_LIST.filter((b) => _testlottoBrainEliteTagSet.has(b.tag));
    }
    if (brainListForTabs.length === 0) {
      alert('고적중 뇌만 필터가 켜져 있으나 표시할 뇌가 없습니다.');
      return;
    }
  }

  const byBrain = {};
  rows.forEach((r) => {
    const tag = String(r.brain_tag || 'legacy').toLowerCase();
    if (!byBrain[tag]) byBrain[tag] = [];
    byBrain[tag].push(r);
  });

  await ensureLottoBrainPowerLoaded();

  const first = rows[0] || {};
  const hasActual = first.actual_1 != null;
  const statusLabel = hasActual ? '추첨 후' : '추첨 전';

  let body = '';
  brainListForTabs.forEach((b) => {
    const list = byBrain[b.tag];
    if (!list || !list.length) {
      return;
    }
    body += '\n';
    body += testlottoGetBrainDisplayName(b.tag);
    body += '\n';
    list.forEach((row, i) => {
      const idx = i + 1;
      const emoji = _testlottoKakaoSetEmoji[idx] || '📌';
      const nums = [row.num1, row.num2, row.num3, row.num4, row.num5, row.num6].map((n) => {
        const v = parseInt(n, 10);
        return Number.isFinite(v) ? String(v).padStart(2, '0') : '00';
      });
      body += `  ${emoji} #${idx}  ${nums.join(' - ')}\n`;
    });
    body += lottoKakaoBrainRecordLine(b.tag);
  });

  if (!body.trim()) {
    alert('복사할 예측 행이 없습니다.');
    return;
  }

  const text = ''
    + '🎱 ROK21 AI 예측\n'
    + '━━━━━━━━━━━━━━━━━━\n'
    + `📌 ${drawNo}회 (${statusLabel})\n`
    + '━━━━━━━━━━━━━━━━━━\n'
    + body
    + '\n━━━━━━━━━━━━━━━━━━\n'
    + '🧠 1군 6뇌 AI 예측 시스템\n'
    + '━━━━━━━━━━━━━━━━━━';

  try {
    await lottoClipboardWriteText(text);
    alert('📋 카톡용 텍스트가 복사되었습니다!');
  } catch (e) {
    console.warn('testlottoCopyKakaoText', e);
    alert('복사에 실패했습니다. 브라우저 권한·HTTPS를 확인하세요.');
  }
}

/** 1~5등 적중 요약 모달 — 읽기 전용 API 연동 */
let _testlottoTierWinsEscHandler = null;

function lottoCloseTierWinsModal() {
  const modal = document.getElementById('lottoTierWinsModal');
  if (modal) {
    modal.hidden = true;
    modal.setAttribute('aria-hidden', 'true');
  }
  if (_testlottoTierWinsEscHandler) {
    document.removeEventListener('keydown', _testlottoTierWinsEscHandler);
    _testlottoTierWinsEscHandler = null;
  }
}

function lottoTierWinsRankTitleClass(rank) {
  if (rank === 1) return 'lotto-tier-wins-rank-title lotto-tier-wins-rank-title--r1';
  if (rank === 2) return 'lotto-tier-wins-rank-title lotto-tier-wins-rank-title--r2';
  if (rank === 3) return 'lotto-tier-wins-rank-title lotto-tier-wins-rank-title--r3';
  if (rank === 4) return 'lotto-tier-wins-rank-title lotto-tier-wins-rank-title--r4';
  if (rank === 5) return 'lotto-tier-wins-rank-title lotto-tier-wins-rank-title--r5';
  return 'lotto-tier-wins-rank-title';
}

function lottoRenderTierWinsModalContent(data) {
  const body = document.getElementById('lottoTierWinsModalBody');
  const title = document.getElementById('lottoTierWinsModalTitle');
  if (!body || !title) return;
  const drawNo = data.draw_no;
  const dateHint = data.draw_date ? ` · ${data.draw_date}` : '';
  title.textContent = `${drawNo}회차 · 1~5등 적중 세트${dateHint}`;

  let actualLine = '';
  if (data.actual_numbers && data.actual_numbers.length === 6) {
    const balls = data.actual_numbers.map((n) => renderMiniBall(n, false)).join('');
    const bonusHtml = data.bonus != null
      ? `<span class="lotto-tier-wins-bonus-wrap">+ 보너스 ${renderMiniBall(data.bonus, false, 'is-bonus')}</span>`
      : '';
    actualLine = `
      <div class="lotto-tier-wins-actual">
        <span class="lotto-tier-wins-actual-label">실제 당첨번호</span>
        <span class="lotto-tier-wins-balls">${balls}</span>
        ${bonusHtml}
      </div>`;
  }

  const items = data.items || [];
  if (!items.length) {
    body.innerHTML = actualLine
      + '<p class="lotto-tier-wins-empty">이 회차에 저장된 1~5등 적중 예측이 없습니다. 미추첨·미채점이거나 해당 회차 예측이 없을 수 있습니다.</p>';
    return;
  }

  const byRank = { 1: [], 2: [], 3: [], 4: [], 5: [] };
  items.forEach((it) => {
    const rk = it.rank;
    if (byRank[rk]) byRank[rk].push(it);
  });

  const rankTitles = { 1: '1등', 2: '2등', 3: '3등', 4: '4등', 5: '5등' };
  const actualSet = new Set((data.actual_numbers || []).map((n) => parseInt(n, 10)));
  let html = actualLine + '<div class="lotto-tier-wins-sections">';
  for (let r = 1; r <= 5; r++) {
    const list = byRank[r];
    if (!list.length) continue;
    html += `<section class="lotto-tier-wins-rank"><h3 class="${lottoTierWinsRankTitleClass(r)}">${rankTitles[r]}</h3><ul class="lotto-tier-wins-list">`;
    list.forEach((it) => {
      const nums = (it.nums || []).map((n) => renderMiniBall(n, actualSet.has(parseInt(n, 10)))).join('');
      const tag = String(it.brain_tag || '').toLowerCase();
      const brain = testlottoGetBrainDisplayName(tag);
      html += `<li class="lotto-tier-wins-item"><span class="lotto-tier-wins-brain">${brain}</span><span class="lotto-tier-wins-balls-row">${nums}</span></li>`;
    });
    html += '</ul></section>';
  }
  html += '</div>';
  body.innerHTML = html;
}

async function lottoRefreshTierWinsModalContent() {
  const input = document.getElementById('testlottoPredictDrawNo');
  const d = input ? parseInt(input.value, 10) : NaN;
  const body = document.getElementById('lottoTierWinsModalBody');
  const title = document.getElementById('lottoTierWinsModalTitle');
  const jump = document.getElementById('lottoTierWinsJumpInput');
  if (!body) return;
  if (!Number.isFinite(d) || d < 1) {
    body.innerHTML = '<p class="lotto-tier-wins-empty">회차가 올바르지 않습니다.</p>';
    return;
  }
  if (jump) jump.value = String(d);
  body.innerHTML = '<p class="lotto-tier-wins-loading">불러오는 중…</p>';
  if (title) title.textContent = `${d}회차 · 불러오는 중…`;
  try {
    let data = null;
    const poolView = _testlottoPoolViewMemCache.get(d);
    const actualRef = _testlottoCurrentActualRef || await _testlottoResolveActualRef(d, _testlottoDetailRows);
    if (poolView && poolView.ok && actualRef && actualRef.actual_1 != null) {
      const scoreRows = _testlottoPoolViewScoreRows(poolView, d, actualRef, ['pool', 'repack']);
      data = {
        draw_no: d,
        draw_date: _testlottoDrawDates[d] || null,
        actual_numbers: [
          actualRef.actual_1, actualRef.actual_2, actualRef.actual_3,
          actualRef.actual_4, actualRef.actual_5, actualRef.actual_6,
        ].map((n) => parseInt(n, 10)),
        bonus: actualRef.actual_bonus != null ? parseInt(actualRef.actual_bonus, 10) : null,
        items: _testlottoTierWinsItemsFromRows(scoreRows),
      };
    } else {
      const r = await fetch(_testlottoResolveApiUrl(`/api/testlotto/predictions/draw/${d}/tier-wins`));
      if (!r.ok) throw new Error(String(r.status));
      data = await r.json();
    }
    lottoRenderTierWinsModalContent(data);
    const dn = data && data.draw_no != null ? parseInt(data.draw_no, 10) : d;
    if (jump && Number.isFinite(dn)) jump.value = String(dn);
  } catch (e) {
    console.warn('tier-wins:', e);
    body.innerHTML = `<p class="lotto-tier-wins-error">불러오기 실패: ${String(e.message)}</p>`;
    if (title) title.textContent = `${d}회차`;
  }
}

async function testlottoOpenTierWinsModal() {
  const input = document.getElementById('testlottoPredictDrawNo');
  const jump = document.getElementById('lottoTierWinsJumpInput');
  const d = input ? parseInt(input.value, 10) : NaN;
  if (!Number.isFinite(d) || d < 1) {
    alert('회차를 입력하거나 목록에서 선택하세요.');
    return;
  }
  const modal = document.getElementById('lottoTierWinsModal');
  if (!modal) {
    alert('1~5등 적중 모달을 찾을 수 없습니다. 페이지를 새로고침(Ctrl+F5)하세요.');
    return;
  }
  if (_testlottoTierWinsEscHandler) {
    document.removeEventListener('keydown', _testlottoTierWinsEscHandler);
    _testlottoTierWinsEscHandler = null;
  }
  if (jump) jump.value = String(d);
  modal.hidden = false;
  modal.setAttribute('aria-hidden', 'false');
  await lottoRefreshTierWinsModalContent();
  _testlottoTierWinsEscHandler = (e) => {
    if (e.key === 'Escape') lottoCloseTierWinsModal();
  };
  document.addEventListener('keydown', _testlottoTierWinsEscHandler);
}

async function lottoTierWinsModalNav(delta) {
  if (!_testlottoDrawList.length) {
    await lottoRefreshTierWinsModalContent();
    return;
  }
  const input = document.getElementById('testlottoPredictDrawNo');
  const sel = document.getElementById('testlottoDrawSelect');
  const cur = input ? parseInt(input.value, 10) : NaN;
  const base = Number.isFinite(cur) ? cur : _testlottoDrawList[0];
  const idx = _testlottoDrawList.indexOf(base);
  const step = delta > 0 ? -1 : 1;
  const nextIdx = Math.max(0, Math.min(_testlottoDrawList.length - 1, (idx >= 0 ? idx : 0) + step));
  const nextNo = _testlottoDrawList[nextIdx];
  if (input) input.value = String(nextNo);
  if (sel) sel.value = String(nextNo);
  await testlottoShowDrawContext(nextNo);
  await lottoRefreshTierWinsModalContent();
}

async function lottoTierWinsModalGoDraw() {
  const jump = document.getElementById('lottoTierWinsJumpInput');
  const d = jump ? parseInt(jump.value, 10) : NaN;
  if (!Number.isFinite(d) || d < 1) {
    alert('올바른 회차 번호를 입력하세요.');
    return;
  }
  const input = document.getElementById('testlottoPredictDrawNo');
  const sel = document.getElementById('testlottoDrawSelect');
  if (input) input.value = String(d);
  if (sel) {
    const opt = sel.querySelector(`option[value="${d}"]`);
    if (opt) sel.value = String(d);
  }
  await testlottoShowDrawContext(d);
  await lottoRefreshTierWinsModalContent();
}

/** ISO(YYYY-MM-DD) → 2026년4월25일 (엔진 `draw_date_for_draw_no`와 동일) */
function formatLottoDateKr(isoDate) {
  if (!isoDate || typeof isoDate !== 'string') {
    return '';
  }
  const p = isoDate.split('T')[0].split('-');
  if (p.length !== 3) {
    return isoDate;
  }
  const y = parseInt(p[0], 10);
  const m = parseInt(p[1], 10);
  const d = parseInt(p[2], 10);
  if (Number.isNaN(y) || Number.isNaN(m) || Number.isNaN(d)) {
    return isoDate;
  }
  return `${y}년${m}월${d}일`;
}

function lottoSetActionStatusText(el, text, color) {
  if (!el) {
    return;
  }
  el.className = 'lotto-action-status';
  el.textContent = text;
  el.style.color = color || '';
}

function lottoSetActionStatusNoNew(el, isoDate) {
  if (!el) {
    return;
  }
  const line2 = formatLottoDateKr(isoDate) || '다음 추첨일(추정)을 알 수 없습니다';
  el.className = 'lotto-action-status lotto-action-status--no-new';
  el.removeAttribute('style');
  el.innerHTML = '<div class="lotto-action-status__title">신규 회차 없음</div>'
    + '<div class="lotto-action-status__date">' + line2 + '</div>';
}

// ── 데이터 수집 ──
async function lottoFetchAll() {
  const status = lottoGetActiveStatusEl();
  const btn = document.getElementById('btnFetchAll');
  btn.disabled = true;
  lottoSetActionStatusText(status, '힌트 불러오는 중…', '#f0c040');
  try {
    try {
      const hintRes = await fetch(_testlottoResolveApiUrl('/api/testlotto/collection-hint'));
      const hint = await hintRes.json();
      if (hint && hint.max_draw_no > 0) {
        // 이미 과거 데이터가 있다면 "전체 수집"은 실수 방지용으로 잠금 처리.
        // (사용자는 과거 기록을 보유한 상태라고 가정)
        lottoSetActionStatusText(
          status,
          '이미 로또 데이터가 있습니다(최대 ' + hint.max_draw_no + '회). "전체 데이터 수집"은 잠금 처리되었습니다. 필요 시 관리자에게 문의하세요.',
          '#f0c040',
        );
        alert('이미 과거 로또 데이터가 있어서 "전체 데이터 수집"은 잠금 처리되었습니다.');
        btn.disabled = false;
        return;
      } else {
        lottoSetActionStatusText(status, 'DB가 비어 있습니다. 전체 수집 요청 중…', '#f0c040');
      }
    } catch (hintErr) {
      lottoSetActionStatusText(status, '전체 수집 요청 중… (힌트 생략)', '#f0c040');
    }
    const res = await fetch(_testlottoResolveApiUrl('/api/testlotto/fetch-all'), { method: 'POST' });
    const data = await res.json();
    lottoSetActionStatusText(
      status,
      (data && data.message) ? data.message : '수집 시작됨. 완료 요약을 불러옵니다…',
      '#4ade80',
    );

    var attempts = 0;
    var poll = setInterval(async function() {
      attempts += 1;
      try {
        const lr = await fetch(_testlottoResolveApiUrl('/api/testlotto/last-fetch-all'));
        const j = await lr.json();
        var r = j && j.result;
        if (r && r.user_message) {
          if (r.status === 'running') {
            if (attempts >= 200) {
              clearInterval(poll);
              lottoSetActionStatusText(status, '응답이 지연되고 있습니다. 잠시 후 당첨 이력 탭을 확인하세요.', '#f0c040');
              btn.disabled = false;
              loadDraws();
            }
            return;
          }
          clearInterval(poll);
          lottoSetActionStatusText(
            status,
            r.user_message,
            (r.ok === false) ? '#f87171' : (r.tail_unavailable > 0 && (r.fetched || 0) === 0) ? '#f0c040' : '#4ade80',
          );
          loadDraws();
          loadBrainStatus();
          btn.disabled = false;
          return;
        }
        if (attempts >= 200) {
          clearInterval(poll);
          lottoSetActionStatusText(status, '완료 요약을 가져오지 못했습니다. 당첨 이력 탭을 확인하세요.', '#f0c040');
          loadDraws();
          loadBrainStatus();
          btn.disabled = false;
        }
      } catch (err) {
        clearInterval(poll);
        lottoSetActionStatusText(status, '상태 조회 실패: ' + err.message, '#f87171');
        btn.disabled = false;
      }
    }, 500);
  } catch (e) {
    lottoSetActionStatusText(status, '수집 실패: ' + e.message, '#f87171');
    btn.disabled = false;
  }
}

async function lottoFetchLatest() {
  const status = lottoGetActiveStatusEl();
  try {
    const res = await fetch(_testlottoResolveApiUrl('/api/testlotto/fetch-latest'), { method: 'POST' });
    const data = await res.json();
    if (data.draw) {
      lottoSetActionStatusText(status, `${data.draw.draw_no}회차 수집 완료!`, '#4ade80');
      loadDraws();
    } else {
      const iso = data && data.next_draw_date;
      if (iso) {
        lottoSetActionStatusNoNew(status, iso);
      } else {
        try {
          const hRes = await fetch(_testlottoResolveApiUrl('/api/testlotto/collection-hint'));
          const hint = await hRes.json();
          if (hint && hint.next_draw_date) {
            lottoSetActionStatusNoNew(status, hint.next_draw_date);
          } else {
            lottoSetActionStatusText(status, '신규 회차 없음', 'var(--text-secondary)');
          }
        } catch (hintEx) {
          lottoSetActionStatusText(status, '신규 회차 없음', 'var(--text-secondary)');
        }
      }
    }
  } catch (e) {
    lottoSetActionStatusText(status, '수집 실패: ' + e.message, '#f87171');
  }
}

// PIN: single 3뇌 predict button — no 두뇌 duplicate (index.html SSOT · testlottoRunPoolPredict only)
function initTestlottoActionsBarPin() {
  const bar = document.querySelector('#view-testlotto .testlotto-actions-bar');
  if (!bar) return;
  bar.querySelectorAll('button[onclick*="testlottoPredict"]').forEach((btn) => btn.remove());
}
window.initTestlottoActionsBarPin = initTestlottoActionsBarPin;

// ── pool-view 예측 (클릭 시에만 계산 · 비백테스트 회차) ──
async function testlottoRunPoolPredict() {
  const input = document.getElementById('testlottoPredictDrawNo');
  const drawNo = parseInt(input?.value, 10);
  if (!drawNo || drawNo < 1) {
    alert('회차 번호를 선택하세요.');
    return;
  }
  const status = document.getElementById('testlottoActionStatus');
  const container = document.getElementById('testlottoPredictionResults');
  lottoSetActionStatusText(status, '3뇌 pool 계산 중… (최초 1회만 수십 초)', '#f0c040');
  testlottoShowResultsLoading(container, true);

  try {
    const poolView = await _fetchPoolView(drawNo, { compute: true });
    if (!poolView || !poolView.ok) {
      lottoSetActionStatusText(status, (poolView && poolView.message) || 'pool 계산 실패', '#f87171');
      await testlottoShowDrawContext(drawNo);
      return;
    }
    const actualRef = await _testlottoResolveActualRef(drawNo, null);
    _testlottoCurrentActualRef = actualRef;
    _testlottoDetailDrawNo = drawNo;
    _testlottoDetailRows = _testlottoStubRowsForDraw(drawNo, actualRef);
    lottoSetActionStatusText(status, `${drawNo}회차 3뇌 예측 완료 · DB 저장됨`, '#4ade80');
    await renderPredictionsByBrain(drawNo, _testlottoDetailRows, { poolView, skipPoolFetch: true });
    loadTestlottoWarrantPanel(drawNo);
  } catch (e) {
    lottoSetActionStatusText(status, '예측 실패: ' + e.message, '#f87171');
    await testlottoShowDrawContext(drawNo);
  }
}
window.testlottoRunPoolPredict = testlottoRunPoolPredict;

// ── 레거시 두뇌 예측 (coordinator POST) — PIN: 사용 금지 · 3뇌 pool만 ──
async function testlottoPredict() {
  console.warn('testlottoPredict() deprecated — use testlottoRunPoolPredict()');
  return testlottoRunPoolPredict();
}

/** 예측 세트 1개 카드 (Top5 / 최다 적중 공용) */
function renderLottoPredCard(pred, rankLabel, data, options) {
  const opts = options || {};
  const nums = pred.nums || [pred.num1, pred.num2, pred.num3, pred.num4, pred.num5, pred.num6];
  const matched = pred.matched_count >= 0 ? pred.matched_count : null;
  const tag = String(pred.brain_tag || '').toLowerCase();
  const dn = tag ? testlottoGetBrainDisplayName(tag) : '';
  const dd = tag ? testlottoGetBrainDescription(tag) : '';
  const method = pred.method || '알수없음';
  const brainText = dn ? (dn + (dd ? ' (' + dd + ')' : '')) : method;
  const confidence = pred.confidence || 0;
  const matchColor = matched === null ? '#666' :
    matched >= 5 ? '#ffd700' :
      matched >= 4 ? '#ff6b6b' :
        matched >= 3 ? '#4ade80' : '#666';
  const leftBar = opts.emphasize ? '#2ed573' : matchColor;
  let h = '';
  h += '<div style="background: #1e1e3a; border-left: 4px solid ' + leftBar + '; border-radius: 8px; padding: 14px; margin-bottom: 10px;">';
  h += '<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">';
  h += '<span style="color: #8b9cf7; font-weight: bold;">' + rankLabel + ' ' + brainText + '</span>';
  h += '<span style="color: #aaa; font-size: 12px;">신뢰도: ' + confidence + '%</span>';
  h += '</div>';
  h += '<div style="margin-bottom: 6px;">';
  nums.forEach((n) => {
    const isM = data.actual_numbers && data.actual_numbers.indexOf(n) >= 0;
    h += renderBall(n, isM, isM ? { role: 'hit' } : undefined);
  });
  h += '</div>';
  if (matched !== null && matched >= 0) {
    let rankText = '';
    if (matched === 6) { rankText = '🏆 1등!!! (6개 전체 적중)'; } else if (matched === 5 && pred.bonus_matched) { rankText = '🥈 2등! (5개 + 보너스)'; } else if (matched === 5) { rankText = '🥉 3등! (5개 적중)'; } else if (matched === 4) { rankText = '🎯 4등 (4개 적중)'; } else if (matched === 3) { rankText = '✅ 5등 (3개 적중)'; } else { rankText = matched + '개 적중 (등수 외)'; }
    h += '<div style="font-size: 13px; color: ' + matchColor + '; font-weight: bold;">' + rankText + '</div>';
  }
  if (pred.reasoning) {
    h += '<div style="font-size: 12px; color: #888; margin-top: 4px;">' + pred.reasoning + '</div>';
  }
  h += '</div>';
  return h;
}

function renderPredictions(data) {
  const container = document.getElementById('testlottoPredictionResults');
  let html = `<h3 style="color: #e0e0ff;">${data.target_draw_no}회차 예측 결과</h3>`;

  if (data.status && data.status.includes('기존')) {
    html += `<p style="color: #f0c040; font-size: 13px;">ℹ️ ${data.status}</p>`;
  }

  if (data.actual_numbers) {
    const sorted = [...data.actual_numbers].sort((a, b) => a - b);
    html += `<div style="background: #2d1b69; padding: 12px; border-radius: 8px; margin-bottom: 16px;">`;
    html += `<span style="color: #ffd700; font-weight: bold;">실제 당첨번호: </span>`;
    sorted.forEach((n) => {
      html += renderBall(n, true, { role: 'winning' });
    });
    if (data.actual_bonus != null && data.actual_bonus !== undefined) {
      html += `<span style="color: #888; margin: 0 6px;">+</span>`;
      html += '<span style="color: #ffd700; font-size: 12px; margin-right: 4px;">보너스</span>';
      html += renderBall(data.actual_bonus, true, { role: 'winning' });
    }
    html += `</div>`;
  }

  const totalN = data.total_sets || (data.predictions && data.predictions.length) || 0;
  // 당첨이 있을 때: Top5는 '신뢰도' 기준이라, 적중 개수가 가장 많은 세트(예: 5등)가 6~15위에 있으면 여기 안 나옴(명예의 전당과 달리 보이는 이유)
  if (data.actual_numbers && data.all_predictions && data.all_predictions.length) {
    const aps = data.all_predictions;
    const counts = aps.map((p) => (p.matched_count != null && p.matched_count >= 0 ? p.matched_count : 0));
    const maxM = Math.max(0, ...counts);
    if (maxM > 0) {
      const bestPreds = aps.filter((p) => p.matched_count != null && p.matched_count === maxM);
      if (bestPreds.length) {
        html += `<p style="color: #a8e6cf; font-size: 13px; margin: 0 0 8px 0;">🎯 이 회차 <b>최다 적중</b> (총 15세트 기준) — <span style="color: #9a9ab0; font-weight: normal;">적중 ${maxM}개(동률이면 여러 줄). <b>신뢰도 1~5위 밖</b>일 수 있음</span></p>`;
        bestPreds.forEach((pred, i) => {
          const rlab = bestPreds.length > 1 ? '최다' + (i + 1) : '최다';
          html += renderLottoPredCard(pred, rlab, data, { emphasize: true });
        });
        html += '<hr style="border: 0; border-top: 1px solid #333; margin: 12px 0;" />';
      }
    }
  }
  html += `<p style="color: #aaa; font-size: 13px;">🏅 <b>신뢰도</b> 상위 5세트 (총 ${totalN}세트 중) — 3개 이상 맞힌 세트는 <b>최다 적중</b> 블록에 있을 수 있고, 여기(#1~#5)엔 없을 수 있음</p>`;

  const top5 = data.top5 || (data.predictions && data.predictions.slice(0, 5)) || [];
  top5.forEach((pred, i) => {
    html += renderLottoPredCard(pred, '#' + (i + 1), data, {});
  });

  container.innerHTML = html;
}

/**
 * @param {number} num
 * @param {boolean} highlighted
 * @param {{ role?: 'hit' | 'winning' }} [opt] — hit: 예측↔당첨 일치(최강), winning: 당첨 요약 행
 */
function renderBall(num, highlighted, opt) {
  const role = (opt && opt.role) || null;
  const colors = {
    1: '#fbc400', 11: '#69c8f2', 21: '#ff7272',
    31: '#aaa', 41: '#b0d840',
  };
  let bg = '#555';
  const keys = Object.keys(colors).map((k) => parseInt(k, 10)).sort((a, b) => b - a);
  for (const start of keys) {
    if (num >= start) {
      bg = colors[start];
      break;
    }
  }
  const base =
    'display: inline-flex; align-items: center; justify-content: center; ' +
    'border-radius: 50%; color: #000; font-weight: bold; margin: 3px; ' +
    'vertical-align: middle; box-sizing: border-box;';

  // 예측 번호가 실제 당첨과 겹칠 때(가독성 최우선)
  if (role === 'hit' && highlighted) {
    var redHit = opt && opt.red_hit_border;
    var hitBorder = redHit
      ? 'border: 3px solid #e53935; box-shadow: 0 0 0 1px rgba(229,57,53,0.5), 0 0 12px rgba(229,57,53,0.45); '
      : 'border: 3px solid #fff; ' +
        'box-shadow: 0 0 0 2px #f5c400, 0 0 0 5px rgba(46,213,115,0.55), 0 0 22px 4px rgba(255,220,100,0.9); ';
    return (
      '<span style="' + base + ' ' +
      'width: 42px; height: 42px; font-size: 16px; background: ' + bg + '; ' +
      hitBorder +
      'transform: scale(1.1); z-index: 1; position: relative;' +
      '" title="당첨번호와 일치">' +
      num +
      '</span>'
    );
  }

  // «실제 당첨번호» 요약 행(전체 6+보너스) — 눈에 띄게, 적중 강조보다는 덜
  if (role === 'winning' || (highlighted && !role)) {
    return (
      '<span style="' + base + ' ' +
      'width: 38px; height: 38px; font-size: 15px; background: ' + bg + '; ' +
      'border: 2px solid rgba(255, 215, 0, 0.95); ' +
      'box-shadow: 0 0 14px rgba(255, 200, 80, 0.55), inset 0 0 8px rgba(255,255,255,0.15);' +
      '">' +
      num +
      '</span>'
    );
  }

  return (
    '<span style="' + base + ' ' +
    'width: 36px; height: 36px; font-size: 14px; background: ' + bg + '; ' +
    'border: 2px solid transparent;">' +
    num +
    '</span>'
  );
}

// ── 두뇌 상태 ──
async function loadBrainStatus() {
  try {
    var res = await fetch(_testlottoResolveApiUrl('/api/testlotto/brain/status'));
    var data = await res.json();

    document.getElementById('brainGrade').textContent = data.grade_emoji || '🧠';
    document.getElementById('brainGradeText').textContent = '두뇌 등급: ' + (data.grade || '일반');

    // 기본 통계
    var statsHtml = '총 예측: ' + (data.total_predictions || 0) + '건 | 최고 기록: ';
    if (data.best_record) {
      var mc = data.best_record.matched_count;
      var bm = data.best_record.bonus_matched;
      var bestRank = '';
      if (mc === 6) bestRank = '🏆 1등';
      else if (mc === 5 && bm) bestRank = '🥈 2등';
      else if (mc === 5) bestRank = '🥉 3등';
      else if (mc === 4) bestRank = '🎯 4등';
      else if (mc === 3) bestRank = '✅ 5등';
      else bestRank = mc + '개 적중';
      statsHtml += bestRank + ' (' + data.best_record.target_draw_no + '회차, ' + data.best_record.method + ')';
    } else {
      statsHtml += '없음';
    }
    document.getElementById('brainStats').innerHTML = statsHtml;

    // 3종 두뇌별 성적 비교 카드
    var profileDiv = document.getElementById('brainProfiles');
    if (profileDiv && data.brain_profiles && data.brain_profiles.length > 0) {
      var pHtml = '';
      data.brain_profiles.forEach(function(bp) {
        var icon = '🧠';
        if (bp.method === '통계두뇌') icon = '📊';
        else if (bp.method === 'LLM두뇌') icon = '🤖';
        else if (bp.method === '하이브리드두뇌') icon = '⚡';

        var barWidth = Math.min(Math.round((bp.avg_match || 0) / 3 * 100), 100);
        var barColor = bp.best_match >= 3 ? '#4ade80' : bp.best_match >= 2 ? '#f0c040' : '#666';

        pHtml += '<div style="background: #1e1e3a; border-radius: 8px; padding: 12px; flex: 1; min-width: 200px;">';
        pHtml += '<div style="font-size: 18px; margin-bottom: 6px;">' + icon + ' <span style="color: #e0e0ff; font-weight: bold;">' + bp.method + '</span></div>';
        pHtml += '<div style="color: #aaa; font-size: 13px;">예측: ' + (bp.total_predictions || 0) + '건</div>';
        pHtml += '<div style="color: #aaa; font-size: 13px;">평균 적중: ' + (bp.avg_match || 0).toFixed(2) + '개</div>';
        pHtml += '<div style="color: #aaa; font-size: 13px;">최고 적중: ' + (bp.best_match || 0) + '개</div>';
        pHtml += '<div style="background: #333; border-radius: 4px; height: 8px; margin-top: 6px;">';
        pHtml += '<div style="background: ' + barColor + '; width: ' + barWidth + '%; height: 100%; border-radius: 4px;"></div>';
        pHtml += '</div>';
        pHtml += '</div>';
      });
      profileDiv.innerHTML = pHtml;
    }

  } catch (e) {
    console.warn('두뇌 상태 로드 실패:', e);
  }
}

// ── 명예의 전당 ──
// === 명예의전당 전역 변수 ===
var _fameAllData = [];
var _fameCurrentRank = 'all';
var _fameShowCount = {};  // 두뇌별 표시 건수

async function loadHallOfFame() {
  try {
    const res = await fetch(_testlottoResolveApiUrl('/api/testlotto/brain/hall-of-fame'));
    const data = await res.json();
    _fameAllData = data.hall_of_fame || [];
    _fameCurrentRank = '1';
    _fameShowCount = {};
    renderHallOfFame();
  } catch (e) {
    console.warn('명예의 전당 로드 실패:', e);
  }
}

function getFameRank(mc, bm) {
  if (mc === 6) return '1';
  if (mc === 5 && bm) return '2';
  if (mc === 5) return '3';
  if (mc === 4) return '4';
  if (mc === 3) return '5';
  return '0';
}

function getFameRankText(rank) {
  var map = { '1': '🏆 1등!!!', '2': '🥈 2등!', '3': '🥉 3등!', '4': '🎯 4등', '5': '✅ 5등' };
  return map[rank] || '';
}

function getFameRankColor(rank) {
  var map = { '1': '#ffd700', '2': '#c0c0c0', '3': '#ff6b6b', '4': '#ff6b6b', '5': '#4ade80' };
  return map[rank] || '#888';
}

function renderHallOfFame() {
  var container = document.getElementById('hallOfFame');
  if (!_fameAllData.length) {
    container.innerHTML = '<p class="fame-empty">🏆 3개 이상 적중한 예측이 없습니다.</p>';
    return;
  }

  // 필터링
  var filtered = _fameAllData;
  if (_fameCurrentRank !== 'all') {
    filtered = _fameAllData.filter(function(r) {
      return getFameRank(r.matched_count, r.bonus_matched) === _fameCurrentRank;
    });
  }

  // 등수별 건수 계산 (필터바 표시용)
  var rankCounts = { '1': 0, '2': 0, '3': 0, '4': 0, '5': 0 };
  _fameAllData.forEach(function(r) {
    var rk = getFameRank(r.matched_count, r.bonus_matched);
    if (rankCounts[rk] !== undefined) rankCounts[rk]++;
  });
  var totalCount = _fameAllData.length;

  // 필터 바
  var html = '<div class="fame-filter-bar">';
  var ranks = [
    { key: 'all', label: '전체 (' + totalCount + ')' },
    { key: '1', label: '1등 (' + rankCounts['1'] + ')' },
    { key: '2', label: '2등 (' + rankCounts['2'] + ')' },
    { key: '3', label: '3등 (' + rankCounts['3'] + ')' },
    { key: '4', label: '4등 (' + rankCounts['4'] + ')' },
    { key: '5', label: '5등 (' + rankCounts['5'] + ')' }
  ];
  ranks.forEach(function(rk) {
    var active = _fameCurrentRank === rk.key ? ' active' : '';
    html += '<button class="fame-filter-btn' + active + '" onclick="fameFilterRank(\'' + rk.key + '\')">' + rk.label + '</button>';
  });
  html += '</div>';

  // 6컬럼 그리드
  var brains = ['stat', 'markov', 'llm', 'lstm', 'fusion', 'hyena'];
  html += '<div class="fame-grid">';

  brains.forEach(function(brain) {
    var brainData = filtered.filter(function(r) {
      return (r.brain_tag || '').toLowerCase() === brain;
    });
    // 최신순 정렬
    brainData.sort(function(a, b) { return (b.target_draw_no || 0) - (a.target_draw_no || 0); });

    var showKey = brain + '_' + _fameCurrentRank;
    if (!_fameShowCount[showKey]) _fameShowCount[showKey] = 20;
    var limit = _fameShowCount[showKey];
    var showing = brainData.slice(0, limit);

    html += '<div class="fame-column">';
    // 헤더
    html += '<div class="fame-col-header">';
    html += '<div class="brain-name">' + testlottoGetBrainDisplayName(brain) + '</div>';
    html += '<div class="brain-desc">' + testlottoGetBrainDescription(brain) + '</div>';
    html += '<div class="fame-count">' + brainData.length + '건</div>';
    html += '</div>';

    if (showing.length === 0) {
      html += '<div class="fame-empty">(없음)</div>';
    }

    showing.forEach(function(record) {
      var rank = getFameRank(record.matched_count, record.bonus_matched);
      var rankClass = 'fame-card rank-' + rank;
      var rankColor = getFameRankColor(rank);

      var predNums = [record.num1, record.num2, record.num3, record.num4, record.num5, record.num6];
      var actNums = [record.actual_1, record.actual_2, record.actual_3, record.actual_4, record.actual_5, record.actual_6].filter(function(n) { return n != null; });
      var actBonus = record.actual_bonus || null;
      var actSet = {};
      actNums.forEach(function(n) { actSet[n] = true; });
      var drawDate = record.draw_date ? ' (' + record.draw_date + ')' : '';

      html += '<div class="' + rankClass + '">';
      // 헤더
      html += '<div class="card-header">';
      html += '<span class="draw-info">' + record.target_draw_no + '회' + drawDate + '</span>';
      html += '<span class="rank-badge" style="color:' + rankColor + '">' + getFameRankText(rank) + '</span>';
      html += '</div>';
      // 예측 번호
      html += '<div class="nums-row"><span class="label">예측: </span>';
      predNums.forEach(function(n) {
        var isMatch = actSet[n] === true;
        html += renderBall(n, isMatch, isMatch ? { role: 'hit' } : undefined);
      });
      html += '</div>';
      // 당첨 번호
      if (actNums.length > 0) {
        html += '<div class="nums-row"><span class="label">당첨: </span>';
        actNums.forEach(function(n) {
          html += renderBall(n, true, { role: 'winning' });
        });
        if (actBonus) {
          html += '<span style="color:#aaa;margin:0 2px">+</span>';
          html += renderBall(actBonus, true, { role: 'winning' });
        }
        html += '</div>';
      }
      // 푸터
      html += '<div class="card-footer">';
      html += '<span>신뢰도 ' + (record.confidence || 0).toFixed(1) + '%</span>';
      html += '</div>';
      html += '</div>';
    });

    // 더보기 버튼
    if (brainData.length > limit) {
      var remaining = brainData.length - limit;
      html += '<button class="fame-more-btn" onclick="fameShowMore(\'' + brain + '\')">+ 더보기 (' + remaining + '건 남음)</button>';
    }

    html += '</div>';
  });

  html += '</div>';
  container.innerHTML = html;
}

function fameFilterRank(rank) {
  _fameCurrentRank = rank;
  _fameShowCount = {};
  renderHallOfFame();
}

function fameShowMore(brain) {
  var showKey = brain + '_' + _fameCurrentRank;
  _fameShowCount[showKey] = (_fameShowCount[showKey] || 20) + 20;
  renderHallOfFame();
}

// ── 통계 분석 ──
async function loadStats() {
  try {
    const res = await fetch(_testlottoResolveApiUrl('/api/testlotto/stats/comprehensive'));
    const data = await res.json();

    if (data.error) {
      document.getElementById('freqChart').innerHTML = `<p style="color: #f87171;">${data.error}</p>`;
      return;
    }

    renderFreqChart(data.frequency);
    renderOddEvenChart(data.odd_even);
    renderRangeChart(data.range_distribution);
    renderSumChart(data.sum_range);
    renderPairChart(data.pair_frequency);
  } catch (e) {
    console.warn('통계 로드 실패:', e);
  }
}

function renderFreqChart(freq) {
  const container = document.getElementById('freqChart');
  if (!freq) { container.innerHTML = '데이터 없음'; return; }

  const values = Object.values(freq).map((v) => v.count || 0);
  const maxCount = values.length > 0 ? Math.max.apply(null, values) : 1;

  let html = '<div style="display: flex; flex-wrap: wrap; gap: 4px;">';
  for (let n = 1; n <= 45; n += 1) {
    const info = freq[n] || freq[String(n)] || { count: 0 };
    const count = info.count || 0;
    const intensity = Math.round((count / Math.max(maxCount, 1)) * 255);
    const bg = `rgb(${intensity}, ${Math.round(intensity * 0.6)}, ${255 - intensity})`;
    html += `<div style="width: 48px; text-align: center; padding: 4px; border-radius: 6px; background: ${bg}; color: #fff; font-size: 11px;"
                  title="${n}번: ${count}회 출현">
              <div style="font-weight: bold;">${n}</div>
              <div>${count}</div>
            </div>`;
  }
  html += '</div>';
  container.innerHTML = html;
}

function renderOddEvenChart(data) {
  const container = document.getElementById('oddEvenChart');
  if (!data) { container.innerHTML = '데이터 없음'; return; }

  let html = '';
  const entries = Object.entries(data).sort((a, b) => b[1] - a[1]);
  const max = entries.length > 0 ? entries[0][1] : 1;
  entries.forEach(([pattern, count]) => {
    const width = Math.round((count / max) * 100);
    html += `<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
              <span style="min-width: 70px; color: #aaa; font-size: 13px;">${pattern}</span>
              <div style="flex: 1; background: #333; border-radius: 4px; height: 20px;">
                <div style="width: ${width}%; background: #8b9cf7; border-radius: 4px; height: 100%;"></div>
              </div>
              <span style="color: #ccc; font-size: 12px; min-width: 40px;">${count}회</span>
            </div>`;
  });
  container.innerHTML = html;
}

function renderRangeChart(data) {
  const container = document.getElementById('rangeChart');
  if (!data) { container.innerHTML = '데이터 없음'; return; }

  let html = '';
  const vals = Object.values(data);
  const max = vals.length > 0 ? Math.max.apply(null, vals) : 1;
  Object.entries(data).forEach(([range, count]) => {
    const width = Math.round((count / max) * 100);
    html += `<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
              <span style="min-width: 50px; color: #aaa; font-size: 13px;">${range}</span>
              <div style="flex: 1; background: #333; border-radius: 4px; height: 20px;">
                <div style="width: ${width}%; background: #4ade80; border-radius: 4px; height: 100%;"></div>
              </div>
              <span style="color: #ccc; font-size: 12px; min-width: 50px;">${count}회</span>
            </div>`;
  });
  container.innerHTML = html;
}

function renderSumChart(data) {
  const container = document.getElementById('sumChart');
  if (!data) { container.innerHTML = '데이터 없음'; return; }

  const html = `<p style="color: #ccc; font-size: 14px;">
    평균 합계: <b style="color: #ffd700;">${data.average}</b> |
    최소: ${data.min} | 최대: ${data.max}
  </p>`;
  container.innerHTML = html;
}

function renderPairChart(pairs) {
  const container = document.getElementById('pairChart');
  if (!pairs || pairs.length === 0) { container.innerHTML = '데이터 없음'; return; }

  let html = '<div style="display: flex; flex-wrap: wrap; gap: 6px;">';
  pairs.slice(0, 30).forEach((p) => {
    html += `<span style="background: #2a2a4e; padding: 4px 10px; border-radius: 12px; color: #ccc; font-size: 12px;">
              ${p.pair[0]}-${p.pair[1]} (${p.count}회)
            </span>`;
  });
  html += '</div>';
  container.innerHTML = html;
}

// ── 당첨 이력 ──
async function loadDraws() {
  try {
    const res = await fetch(_testlottoResolveApiUrl('/api/testlotto/draws?limit=50'));
    const data = await res.json();
    const container = document.getElementById('drawsList');

    if (!data.draws || data.draws.length === 0) {
      container.innerHTML = '<p style="color: #888;">데이터가 없습니다. "전체 데이터 수집"을 먼저 실행하세요.</p>';
      return;
    }

    let html = `<p style="color: #aaa; margin-bottom: 12px;">총 ${data.total}회차 저장됨 (최근 50개 표시)</p>`;
    html += '<div style="max-height: 500px; overflow-y: auto;">';

    data.draws.forEach((d) => {
      html += `<div style="display: flex; align-items: center; gap: 12px; padding: 8px; border-bottom: 1px solid #333;">`;
      html += `<span style="color: #8b9cf7; font-weight: bold; min-width: 70px;">${d.draw_no}회</span>`;
      html += `<span style="color: #888; min-width: 90px; font-size: 12px;">${d.draw_date}</span>`;
      [d.num1, d.num2, d.num3, d.num4, d.num5, d.num6].forEach((n) => {
        html += renderBall(n, false);
      });
      html += `<span style="color: #888; font-size: 11px;">+</span>`;
      html += renderBall(d.bonus, false);
      if (d.first_prize) {
        html += `<span style="color: #aaa; font-size: 11px; margin-left: 8px;">1등: ${(d.first_prize / 100000000).toFixed(1)}억</span>`;
      }
      html += `</div>`;
    });

    html += '</div>';
    container.innerHTML = html;
  } catch (e) {
    console.warn('당첨 이력 로드 실패:', e);
  }
}

// ── K-SIGNAL 백테스트 기록 (DB) ──
async function loadTestlottoBacktestRuns() {
  const panel = document.getElementById('testlottoBacktestPanel');
  if (!panel) return;
  // 이미 그려진 표가 있으면 스피너 없이 유지
  if (!panel.querySelector('.testlotto-backtest-table')) {
    panel.innerHTML = '<p class="testlotto-hero-placeholder">백테스트 DB에서 읽는 중…</p>';
  }
  try {
    const r = await fetch(_testlottoResolveApiUrl('/api/testlotto/backtest/runs?limit=20'));
    const data = await r.json();
    renderTestlottoBacktestList(data.runs || []);
    panel.dataset.loaded = '1';
  } catch (e) {
    panel.innerHTML = '<p style="color:#f88;">백테스트 로드 실패: ' + _tlEscapeHtml(e.message) + '</p>';
  }
}

function renderTestlottoBacktestList(runs) {
  const panel = document.getElementById('testlottoBacktestPanel');
  if (!panel) return;
  if (!runs.length) {
    panel.innerHTML = '<p class="testlotto-hero-placeholder">아직 DB에 백테스트 기록이 없습니다. <code>tools/import_k_signal_backtest.py</code> 실행 후 새로고침하세요.</p>';
    return;
  }
  let html = '<table class="testlotto-backtest-table"><thead><tr>';
  html += '<th>과제</th><th>전략</th><th>3개 이상 적중률</th><th>평균 적중</th><th>회차</th><th>판정</th><th></th>';
  html += '</tr></thead><tbody>';
  runs.forEach((run) => {
    const ge3 = run.ge3_rate != null ? (run.ge3_rate * 100).toFixed(1) + '%' : '—';
    const mean = run.mean_hits != null ? Number(run.mean_hits).toFixed(2) : '—';
    const dr = run.draw_range || [];
    html += '<tr>';
    html += '<td><strong>' + _tlEscapeHtml(run.survey_label_ko || testlottoSurveyLabelKo(run.survey_id)) + '</strong></td>';
    html += '<td>' + _tlEscapeHtml(run.strategy_label_ko || testlottoStrategyLabelKo(run.strategy_id)) + '</td>';
    html += '<td>' + ge3 + '</td><td>' + mean + '</td>';
    html += '<td>' + _tlEscapeHtml(String(dr[0] || '') + '~' + String(dr[1] || '')) + ' (' + (run.n_draws || '') + '회)</td>';
    html += '<td>' + _tlEscapeHtml(run.verdict || run.gate_mode_ko || '') + '</td>';
    html += '<td><button type="button" class="btn btn-secondary btn-sm" onclick="testlottoShowBacktestDetail(' + run.run_id + ')">회차별</button></td>';
    html += '</tr>';
  });
  html += '</tbody></table>';
  html += '<div id="testlottoBacktestDetail" class="testlotto-backtest-detail" hidden></div>';
  panel.innerHTML = html;
}

async function testlottoShowBacktestDetail(runId) {
  const box = document.getElementById('testlottoBacktestDetail');
  if (!box) return;
  box.hidden = false;
  box.innerHTML = '<p>회차별 결과 불러오는 중…</p>';
  try {
    const r = await fetch(_testlottoResolveApiUrl('/api/testlotto/backtest/runs/' + runId + '?draw_limit=200'));
    const data = await r.json();
    if (data.error) {
      box.innerHTML = '<p style="color:#f88;">' + _tlEscapeHtml(data.error) + '</p>';
      return;
    }
    let html = '<h4>' + _tlEscapeHtml(data.survey_label_ko) + ' · ' + _tlEscapeHtml(data.strategy_label_ko) + '</h4>';
    html += '<p class="testlotto-no-peek-note">seed=' + data.seed + ' · walk-forward only · 미래 회차 미열람</p>';
    html += '<table class="testlotto-backtest-table testlotto-backtest-table--draws"><thead><tr>';
    html += '<th>회차</th><th>최고 적중</th><th>등수</th></tr></thead><tbody>';
    (data.draws || []).forEach((d) => {
      html += '<tr><td>' + d.draw_no + '회</td><td>' + d.best_hits + '개</td><td>' + _tlEscapeHtml(d.best_tier_label || '') + '</td></tr>';
    });
    html += '</tbody></table>';
    box.innerHTML = html;
    box.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  } catch (e) {
    box.innerHTML = '<p style="color:#f88;">' + _tlEscapeHtml(e.message) + '</p>';
  }
}

// ── 초기화 ──
document.addEventListener('DOMContentLoaded', () => {
  preloadTestlottoBacktestIndex();
  initTestlottoActionsBarPin();
  const btDetails = document.getElementById('testlottoBacktestDetails');
  if (btDetails) {
    btDetails.addEventListener('toggle', () => {
      if (btDetails.open) loadTestlottoBacktestRuns();
    });
  }
  const lottoTab = document.querySelector('[data-tab="lotto"]');
  if (lottoTab) {
    lottoTab.addEventListener('click', () => {
      setTimeout(() => {
        loadBrainStatus();
        loadHallOfFame();
        initTestlottoDrawSearch();
      }, 300);
    });
  }
});

// ============================================
// === 사이드바 + 대시보드 (1단계) ===
// ============================================

// === 사이드바 페이지 전환 ===
function switchLottoPage(pageName) {
  const root = document.getElementById('tab-lotto');
  if (!root) return;
  root.querySelectorAll('.lotto-page').forEach((p) => p.classList.remove('active'));
  root.querySelectorAll('.lotto-sidebar-item').forEach((b) => b.classList.remove('active'));

  const page = document.getElementById('lotto-page-' + pageName);
  if (page) page.classList.add('active');

  root.querySelectorAll('.lotto-sidebar-item').forEach((b) => {
    if (b.getAttribute('onclick') === "switchLottoPage('" + pageName + "')") {
      b.classList.add('active');
    }
  });

  // 페이지별 데이터 로드
  if (pageName === 'dashboard') loadDashboard();
  if (pageName === 'predict') initTestlottoDrawSearch();
  if (pageName === 'fame') loadHallOfFame();
  if (pageName === 'stats') loadStats();
  if (pageName === 'draws') loadDraws();
  if (pageName === 'brains') loadBrainStatus();
  if (pageName === 'special') loadSpecialForce();
}

// === 등수 드롭다운 토글 ===
function toggleRankDropdown(rankId) {
  const list = document.getElementById(rankId + 'List');
  if (list) {
    list.style.display = list.style.display === 'none' ? 'block' : 'none';
  }
}

// === 대시보드 데이터 로드 ===
async function loadDashboard() {
  try {
    const res = await fetch('/api/testlotto/dashboard-summary');
    const data = await res.json();
    setLottoBrainPowerCache(data.brain_power);
    renderCountdown(data.next_draw_no, data.next_draw_date, data.next_draw_weekday);
    renderRankings(data.rankings);
    renderPowerMeter(data.brain_power);
    renderProgress(data.learning_range, data.total_predictions);
    renderScores(data.scores);
  } catch (e) {
    console.error('Dashboard load failed:', e);
  }
}

// === 카운트다운 타이머 ===
let _testlottoCountdownInterval = null;

function renderCountdown(drawNo, dateStr, weekday) {
  const nextEl = document.getElementById('lottoNextDraw');
  if (nextEl) {
    nextEl.textContent = '🔔 다음 추첨: ' + drawNo + '회 (' + dateStr + ' ' + weekday + ')';
  }

  if (_testlottoCountdownInterval) clearInterval(_testlottoCountdownInterval);
  const target = new Date(dateStr + 'T20:45:00+09:00');

  function updateTimer() {
    const el = document.getElementById('lottoCountdownTimer');
    if (!el) return;
    const now = new Date();
    const diff = target - now;
    if (diff <= 0) {
      el.textContent = '🎉 추첨 완료!';
      clearInterval(_testlottoCountdownInterval);
      return;
    }
    const d = Math.floor(diff / 86400000);
    const h = Math.floor((diff % 86400000) / 3600000);
    const m = Math.floor((diff % 3600000) / 60000);
    const s = Math.floor((diff % 60000) / 1000);
    el.textContent =
      '⏰ 추첨까지 D-' + d + ' ' +
      String(h).padStart(2, '0') + ':' +
      String(m).padStart(2, '0') + ':' +
      String(s).padStart(2, '0');
  }

  updateTimer();
  _testlottoCountdownInterval = setInterval(updateTimer, 1000);
}

// === 등수별 랭킹 ===
function renderRankings(rankings) {
  if (!rankings) return;
  window._testlottoDashboardRankings = rankings;
  if (!window._testlottoRankState) {
    window._testlottoRankState = { rank1: { limit: 20 }, rank2: { limit: 20 }, rank3: { limit: 20 } };
  }
  ['rank1', 'rank2', 'rank3'].forEach((key) => {
    const list = rankings[key] || [];
    const countEl = document.getElementById(key + 'Count');
    const listEl = document.getElementById(key + 'List');
    if (countEl) countEl.textContent = String(list.length);
    if (listEl) {
      if (list.length === 0) {
        listEl.innerHTML = '<div style="padding:8px;color:#666">아직 없음</div>';
      } else {
        const state = window._testlottoRankState[key] || { limit: 20 };
        const limit = Math.max(20, Number(state.limit || 20));
        const shown = list.slice(0, limit);
        let html = '';
        html += shown.map((item) => {
          const t = String(item.brain || '').toLowerCase();
          const brain = testlottoGetBrainDisplayName(t);
          return '<div style="padding:4px 0;border-bottom:1px solid #0f3460">' +
            '<strong>' + item.draw_no + '회</strong> ' + brain + ' — ' +
            (item.numbers ? item.numbers.join(', ') : '') +
          '</div>';
        }).join('');
        if (list.length > limit) {
          html += '<div style="padding:10px 0;display:flex;justify-content:center">';
          html += '<button class="btn btn-primary" style="padding:8px 12px;font-size:12px" onclick="lottoRankShowMore(\'' + key + '\')">더보기 (+20)</button>';
          html += '</div>';
        } else {
          html += '<div style="padding:8px 0;color:#666;text-align:center;font-size:12px">끝</div>';
        }
        listEl.innerHTML = html;
      }
    }
  });
}

function lottoRankShowMore(key) {
  if (!window._testlottoRankState) window._testlottoRankState = {};
  const state = window._testlottoRankState[key] || { limit: 20 };
  state.limit = Number(state.limit || 20) + 20;
  window._testlottoRankState[key] = state;
  if (window._testlottoDashboardRankings) {
    renderRankings(window._testlottoDashboardRankings);
    const el = document.getElementById(key + 'List');
    if (el) el.style.display = 'block';
  }
}

function lottoRankShowAll(key) {
  if (!window._testlottoRankState) window._testlottoRankState = {};
  const state = window._testlottoRankState[key] || { limit: 20 };
  state.limit = 1000000;
  window._testlottoRankState[key] = state;
  if (window._testlottoDashboardRankings) {
    renderRankings(window._testlottoDashboardRankings);
    const el = document.getElementById(key + 'List');
    if (el) el.style.display = 'block';
  }
}

// === 두뇌 파워 미터 ===
function renderPowerMeter(brainPower) {
  const el = document.getElementById('powerMeterContent');
  if (!el || !brainPower) return;
  const maxScore = Math.max(...brainPower.map((b) => b.rank1 * 100 + b.rank2 * 50 + b.rank3 * 10), 1);
  el.innerHTML = brainPower.map((b) => {
    const t = String(b.brain || '').toLowerCase();
    const brain = testlottoGetBrainDisplayName(t);
    const desc = testlottoGetBrainDescription(t);
    const score = b.rank1 * 100 + b.rank2 * 50 + b.rank3 * 10;
    const pct = Math.round(score / maxScore * 100);
    const medal = pct >= 80 ? '🥇' : pct >= 50 ? '🥈' : pct >= 30 ? '🥉' : '  ';
    return '<div style="margin-bottom:12px">' +
      '<div style="display:flex;justify-content:space-between;margin-bottom:4px">' +
        '<span style="color:#fff">' + medal + ' ' + brain + (desc ? ' <span style="color:#9a9ab0;font-size:12px">(' + desc + ')</span>' : '') + '</span>' +
        '<span style="color:#ffd700">' + b.label + '</span>' +
      '</div>' +
      '<div style="color:#a0a0b0;font-size:13px;margin-bottom:4px">' +
        '1등 ' + b.rank1 + '회 · 2등 ' + b.rank2 + '회 · 3등 ' + b.rank3 + '회 · 4등 ' +
        Number(b.rank4 || 0) +
        '회 · 5등 ' +
        Number(b.rank5 || 0) +
        '회' +
      '</div>' +
      '<div style="background:#0a0a1a;border-radius:4px;height:8px;overflow:hidden">' +
        '<div style="background:linear-gradient(90deg,#e94560,#ffd700);width:' + pct + '%;height:100%;border-radius:4px"></div>' +
      '</div>' +
    '</div>';
  }).join('');
}

// === AI 학습 현황 ===
function renderProgress(range, totalPreds) {
  const el = document.getElementById('progressContent');
  if (!el || !range) return;
  const learned = (range.end - range.start + 1);
  const total = range.total_draws;
  const pct = Math.round(learned / Math.max(total, 1) * 100);
  el.innerHTML =
    '<div style="display:flex;justify-content:space-between;color:#fff;margin-bottom:8px">' +
      '<span>학습 범위: ' + range.start + ' ~ ' + range.end + '회차</span>' +
      '<span>' + pct + '% (' + learned + '/' + total + ')</span>' +
    '</div>' +
    '<div style="background:#0a0a1a;border-radius:4px;height:12px;overflow:hidden;margin-bottom:8px">' +
      '<div style="background:linear-gradient(90deg,#00b894,#0984e3);width:' + pct + '%;height:100%;border-radius:4px"></div>' +
    '</div>' +
    '<div style="color:#a0a0b0;font-size:13px">총 예측 세트: ' + Number(totalPreds || 0).toLocaleString() + '건</div>';
}

// === 등수별 적중 점수 ===
function renderScores(scores) {
  const el = document.getElementById('scoresContent');
  if (!el || !scores) return;
  const rows = [
    { label: '🥇 1등', pct: scores.rank1_pct, cnt: scores.rank1_cnt, color: '#ffd700' },
    { label: '🥈 2등', pct: scores.rank2_pct, cnt: scores.rank2_cnt, color: '#c0c0c0' },
    { label: '🥉 3등', pct: scores.rank3_pct, cnt: scores.rank3_cnt, color: '#cd7f32' },
    { label: '4등', pct: scores.rank4_pct, cnt: scores.rank4_cnt, color: '#74b9ff' },
    { label: '5등', pct: scores.rank5_pct, cnt: scores.rank5_cnt, color: '#a0a0b0' },
  ];
  el.innerHTML = rows.map((r) =>
    '<div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid #0f3460">' +
      '<span style="color:' + r.color + '">' + r.label + '</span>' +
      '<span style="color:#fff">' + Number(r.pct || 0).toFixed(3) + '% (' + Number(r.cnt || 0) + '건)</span>' +
    '</div>'
  ).join('') +
  '<div style="display:flex;justify-content:space-between;padding:8px 0;margin-top:4px">' +
    '<span style="color:#e94560;font-weight:bold">🎯 총 당첨 점수</span>' +
    '<span style="color:#e94560;font-weight:bold">' + Number(scores.total_hit_pct || 0).toFixed(2) + '%</span>' +
  '</div>';
}

// === 로또 탭 진입 시 대시보드 자동 로드 ===
(function() {
  const lottoTab = document.getElementById('tab-lotto');
  if (!lottoTab || typeof MutationObserver === 'undefined') return;
  const observer = new MutationObserver(function(mutations) {
    mutations.forEach(function(m) {
      if (m.target && m.target.id === 'tab-lotto' && m.target.classList.contains('active')) {
        loadDashboard();
      }
    });
  });
  observer.observe(lottoTab, { attributes: true, attributeFilter: ['class'] });
})();

function lottoGetActiveStatusEl() {
  const activePage = document.querySelector('.lotto-page.active');
  if (!activePage) return document.getElementById('testlottoActionStatus');
  if (activePage.id === 'lotto-page-collect') {
    return document.getElementById('lottoCollectStatus') || document.getElementById('testlottoActionStatus');
  }
  return document.getElementById('testlottoActionStatus');
}

// === 특수부대 페이지 ===
var _specialMissListLimit = 20;

/** 성적표: 5등 접기/더보기 상태 (loadSpecialForce 호출 시 초기화) */
var _specialFifthExpanded = false;
var _specialFifthLimit = 20;
/** @type {Array<Record<string, unknown>>|null} */
var _specialScorecardPredsCache = null;

async function loadSpecialForce() {
  try {
    _specialFifthExpanded = false;
    _specialFifthLimit = 20;
    _specialScorecardPredsCache = null;

    const predRes = await fetch(_testlottoResolveApiUrl('/api/testlotto/predictions?limit=50000'));
    const predData = await predRes.json();
    const preds = predData.predictions || predData || [];

    const drawBest = {};
    const baseTags = ['stat', 'markov', 'llm', 'lstm', 'fusion', 'hyena'];
    preds.forEach(function(p) {
      if (baseTags.indexOf(p.brain_tag) === -1) return;
      if (p.matched_count < 0) return;
      var dno = p.target_draw_no;
      if (!drawBest[dno] || p.matched_count > drawBest[dno]) {
        drawBest[dno] = p.matched_count;
      }
    });
    var missDrawNos = [];
    Object.keys(drawBest).forEach(function(dno) {
      if (drawBest[dno] <= 2) missDrawNos.push(parseInt(dno, 10));
    });
    missDrawNos.sort(function(a, b) { return b - a; });
    var totalDraws = Object.keys(drawBest).length;

    var summaryEl = document.getElementById('specialSummary');
    if (!summaryEl) return;
    var pctStr = totalDraws > 0 ? ((missDrawNos.length / totalDraws) * 100).toFixed(1) : '0.0';
    summaryEl.innerHTML =
      '총 미당첨 회차: <strong>' + missDrawNos.length + '회</strong> / ' + totalDraws +
      '회 (' + pctStr + '%) — 기존 6두뇌 30세트 전부 2개 이하 적중';

    var missPreds = preds.filter(function(p) { return p.brain_tag === 'miss_analysis'; });
    var snakePreds = preds.filter(function(p) { return p.brain_tag === 'snake'; });

    renderSpecialBrainStats('specialMissStats', missPreds);
    renderSpecialBrainStats('specialSnakeStats', snakePreds);

    renderSpecialBrainPreds('specialMissPreds', missPreds);
    renderSpecialBrainPreds('specialSnakePreds', snakePreds);

    renderSpecialMissList(missDrawNos, preds);

    renderSpecialScorecard(preds);
  } catch (e) {
    console.warn('특수부대 로드 실패:', e);
  }
}

/**
 * 특수부대 백테스트 성적표 (이미 fetch한 predictions만 사용)
 * @param {Array<Record<string, unknown>>} allPreds
 */
function renderSpecialScorecard(allPreds) {
  var page = document.getElementById('lotto-page-special');
  if (!page) return;

  var missPreds = allPreds.filter(function(p) { return p.brain_tag === 'miss_analysis'; });
  var snakePreds = allPreds.filter(function(p) { return p.brain_tag === 'snake'; });
  _specialScorecardPredsCache = allPreds;

  var wrap = document.getElementById('specialScorecard');
  if (!wrap) {
    wrap = document.createElement('div');
    wrap.id = 'specialScorecard';
    var summaryEl = document.getElementById('specialSummary');
    if (summaryEl && summaryEl.parentNode) {
      summaryEl.parentNode.insertBefore(wrap, summaryEl.nextSibling);
    } else {
      page.appendChild(wrap);
    }
  }

  function countScored(arr) {
    var n = 0;
    arr.forEach(function(p) {
      if (p.matched_count >= 0) n++;
    });
    return n;
  }

  function tagStats(arr) {
    var scored = arr.filter(function(p) { return p.matched_count >= 0; });
    var r4 = 0;
    var r5 = 0;
    var sum = 0;
    scored.forEach(function(p) {
      if (p.matched_count === 4) r4++;
      if (p.matched_count === 3) r5++;
      sum += Number(p.matched_count || 0);
    });
    var avg = scored.length ? (sum / scored.length).toFixed(2) : '0.00';
    return { r4: r4, r5: r5, avg: avg, scored: scored.length };
  }

  var drawRounds = new Set();
  missPreds.forEach(function(p) {
    drawRounds.add(p.target_draw_no);
  });

  var scoredTotal = countScored(missPreds) + countScored(snakePreds);
  var sm = tagStats(missPreds);
  var ss = tagStats(snakePreds);

  var boxStyle =
    'background: linear-gradient(135deg, #1a1a2e, #16213e); border: 1px solid #333; border-radius: 10px; ' +
    'padding: 16px; margin-bottom: 16px; color: #e0e0ff; font-size: 0.92em;';
  var hStyle = 'color: #ffd700; margin: 0 0 10px 0; font-size: 1.05em;';
  var grid2 =
    'display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 10px;';
  if (window.innerWidth && window.innerWidth < 520) {
    grid2 = 'display: grid; grid-template-columns: 1fr; gap: 12px; margin-top: 10px;';
  }

  var html = '';
  html += '<div style="' + boxStyle + '">';
  html += '<h4 style="' + hStyle + '">📊 백테스트 성적표</h4>';
  html += '<div style="color:#ccc;line-height:1.5;">';
  html += '총 <strong>' + drawRounds.size + '</strong>회차 테스트 | 채점완료 <strong>' + scoredTotal + '</strong>건';
  html += '</div>';
  html += '<div style="' + grid2 + '">';
  html += '<div style="border:1px solid #444;border-radius:8px;padding:10px;background:#0d1117;">';
  html += '<div style="font-weight:bold;color:#e0e0ff;margin-bottom:6px;">' + testlottoGetBrainDisplayName('miss_analysis') + '</div>';
  html += '<div style="color:#aaa;font-size:0.85em;">4등: ' + sm.r4 + '건</div>';
  html += '<div style="color:#aaa;font-size:0.85em;">5등: ' + sm.r5 + '건</div>';
  html += '<div style="color:#ffd700;margin-top:6px;">평균적중: ' + sm.avg + '</div>';
  html += '</div>';
  html += '<div style="border:1px solid #444;border-radius:8px;padding:10px;background:#0d1117;">';
  html += '<div style="font-weight:bold;color:#e0e0ff;margin-bottom:6px;">' + testlottoGetBrainDisplayName('snake') + '</div>';
  html += '<div style="color:#aaa;font-size:0.85em;">4등: ' + ss.r4 + '건</div>';
  html += '<div style="color:#aaa;font-size:0.85em;">5등: ' + ss.r5 + '건</div>';
  html += '<div style="color:#ffd700;margin-top:6px;">평균적중: ' + ss.avg + '</div>';
  html += '</div>';
  html += '</div>';
  html += '</div>';

  html += '<div style="' + boxStyle + '">';
  html += '<h4 style="' + hStyle + '">🏅 4등 이상 상세</h4>';
  var high = allPreds.filter(function(p) {
    var t = p.brain_tag;
    return (t === 'miss_analysis' || t === 'snake') && p.matched_count >= 4;
  }).sort(function(a, b) {
    var da = (b.target_draw_no || 0) - (a.target_draw_no || 0);
    if (da !== 0) return da;
    return (b.matched_count || 0) - (a.matched_count || 0);
  });
  if (!high.length) {
    html += '<div style="color:#666;font-size:0.85em;">4등 이상 적중 내역이 없습니다.</div>';
  } else {
    high.forEach(function(p) {
      html += _specialRenderHitDetailRow(p);
    });
  }
  html += '</div>';

  html += '<div style="' + boxStyle + '">';
  html += '<h4 style="' + hStyle + '">✅ 5등 내역</h4>';
  html += '<button type="button" class="special-more-btn" id="specialFifthToggleBtn" onclick="specialToggleFifth()">5등 보기 ▼</button>';
  html += '<div id="specialFifthBody" style="margin-top:10px;"></div>';
  html += '</div>';

  html += '<div style="' + boxStyle + '">';
  html += '<h4 style="' + hStyle + '">📈 구간별 성장 추이</h4>';
  html += _specialRenderRangeBars(missPreds, 'miss_analysis');
  html += '<div style="height:10px"></div>';
  html += _specialRenderRangeBars(snakePreds, 'snake');
  html += '</div>';

  wrap.innerHTML = html;
  renderSpecialFifthBody();
}

function _specialRangeGroup(dno) {
  var d = Number(dno) || 0;
  if (d < 100) return '001-099';
  if (d < 300) return '100-299';
  if (d < 500) return '300-499';
  if (d < 700) return '500-699';
  if (d < 900) return '700-899';
  return '900+';
}

function _specialRangeOrder() {
  return ['001-099', '100-299', '300-499', '500-699', '700-899', '900+'];
}

function _specialRenderRangeBars(arr, tag) {
  var scored = arr.filter(function(p) {
    return p.brain_tag === tag && p.matched_count >= 0;
  });
  var groups = {};
  _specialRangeOrder().forEach(function(g) { groups[g] = { sum: 0, cnt: 0 }; });
  scored.forEach(function(p) {
    var g = _specialRangeGroup(p.target_draw_no);
    groups[g].sum += Number(p.matched_count || 0);
    groups[g].cnt += 1;
  });
  var avgs = {};
  var maxAvg = 0.001;
  _specialRangeOrder().forEach(function(g) {
    var c = groups[g].cnt;
    var a = c ? groups[g].sum / c : 0;
    avgs[g] = a;
    if (a > maxAvg) maxAvg = a;
  });

  var title = testlottoGetBrainDisplayName(tag);
  var out = '<div style="color:#e0e0ff;font-weight:bold;margin-bottom:8px;">' + title + '</div>';
  _specialRangeOrder().forEach(function(g) {
    var a = avgs[g] || 0;
    var bars = Math.max(0, Math.min(10, Math.round((a / maxAvg) * 10)));
    var filled = '';
    var ei;
    for (ei = 0; ei < bars; ei++) filled += '█';
    var empty = '';
    for (ei = 0; ei < 10 - bars; ei++) empty += '░';
    out += '<div style="display:flex;align-items:center;gap:8px;margin:4px 0;font-family:monospace;font-size:0.85em;">';
    out += '<span style="min-width:72px;color:#888;">' + g + '</span>';
    out += '<span style="color:#8b9cf7;">' + filled + empty + '</span>';
    out += '<span style="color:#ccc;">' + a.toFixed(2) + '</span>';
    out += '</div>';
  });
  return out;
}

function _specialDrawDateLabel(p) {
  var d = p && p.draw_date;
  if (d) return String(d);
  return '—';
}

function _specialRankLabel(mc, bm) {
  if (mc === 6) return '1등';
  if (mc === 5 && bm) return '2등';
  if (mc === 5) return '3등';
  if (mc === 4) return '4등';
  if (mc === 3) return '5등';
  return (mc != null ? mc : '?') + '개 적중';
}

function _specialRenderHitDetailRow(p) {
  var tag = String(p.brain_tag || '');
  var dno = p.target_draw_no;
  var dateStr = _specialDrawDateLabel(p);
  var predNums = [p.num1, p.num2, p.num3, p.num4, p.num5, p.num6];
  var act = [p.actual_1, p.actual_2, p.actual_3, p.actual_4, p.actual_5, p.actual_6].filter(function(n) {
    return n != null;
  });
  var bonus = p.actual_bonus;
  var actSet = {};
  act.forEach(function(n) { actSet[n] = true; });

  var row =
    'border:1px solid #333;border-radius:8px;padding:10px;margin-bottom:10px;background:#0d1117;';
  var html = '<div style="' + row + '">';
  html += '<div style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:6px;margin-bottom:6px;">';
  html += '<span style="color:#e0e0ff;font-weight:bold;">' + dno + '회 <span style="color:#888;font-weight:normal;">· ' + dateStr + '</span></span>';
  html += '<span style="color:#8b9cf7;">' + testlottoGetBrainDisplayName(tag) + '</span>';
  html += '</div>';
  html += '<div style="color:#888;font-size:0.78em;margin-bottom:4px;">' + _specialRankLabel(p.matched_count, p.bonus_matched) + ' · 신뢰도 ' + (Number(p.confidence || 0).toFixed(1)) + '%</div>';
  html += '<div style="margin-bottom:4px;"><span style="color:#888;font-size:0.8em;">예측</span> ';
  predNums.forEach(function(n) {
    var hit = actSet[n] === true;
    html += renderBall(Number(n), hit, hit ? { role: 'hit', red_hit_border: true } : undefined);
  });
  html += '</div>';
  html += '<div><span style="color:#888;font-size:0.8em;">당첨</span> ';
  if (act.length >= 6) {
    act.forEach(function(n) {
      html += renderBall(Number(n), true, { role: 'winning' });
    });
    if (bonus != null) {
      html += '<span style="color:#aaa;margin:0 4px">+</span>';
      html += renderBall(Number(bonus), true, { role: 'winning' });
    }
  } else {
    html += '<span style="color:#666;font-size:0.85em;">미정(당첨 미수집)</span>';
  }
  html += '</div>';
  html += '</div>';
  return html;
}

function renderSpecialFifthBody() {
  var body = document.getElementById('specialFifthBody');
  var btn = document.getElementById('specialFifthToggleBtn');
  if (!body) return;
  var preds = _specialScorecardPredsCache || [];
  var fifth = preds.filter(function(p) {
    var t = p.brain_tag;
    return (t === 'miss_analysis' || t === 'snake') && p.matched_count === 3;
  }).sort(function(a, b) {
    return (b.target_draw_no || 0) - (a.target_draw_no || 0);
  });
  if (btn) {
    btn.textContent = _specialFifthExpanded
      ? ('5등 ' + fifth.length + '건 접기 ▲')
      : ('5등 ' + fifth.length + '건 보기 ▼');
  }
  if (!_specialFifthExpanded) {
    body.innerHTML = '';
    return;
  }
  var slice = fifth.slice(0, _specialFifthLimit);
  var h = '';
  slice.forEach(function(p) {
    h += _specialRenderHitDetailRow(p);
  });
  if (fifth.length > _specialFifthLimit) {
    var rem = fifth.length - _specialFifthLimit;
    h += '<button type="button" class="special-more-btn" onclick="specialFifthMore()">+ 더보기 (' + rem + '건 남음)</button>';
  }
  body.innerHTML = h;
}

function specialToggleFifth() {
  _specialFifthExpanded = !_specialFifthExpanded;
  if (!_specialFifthExpanded) {
    _specialFifthLimit = 20;
  }
  renderSpecialFifthBody();
}

function specialFifthMore() {
  _specialFifthLimit += 20;
  renderSpecialFifthBody();
}

function renderSpecialBrainStats(elId, preds) {
  var el = document.getElementById(elId);
  if (!el) return;
  if (!preds.length) {
    el.innerHTML = '아직 예측 데이터가 없습니다. 두뇌예측 페이지에서 예측을 실행하세요.';
    return;
  }
  var r1 = 0; var r2 = 0; var r3 = 0; var r4 = 0; var r5 = 0; var total = 0;
  preds.forEach(function(p) {
    if (p.matched_count < 0) return;
    total++;
    if (p.matched_count === 6) r1++;
    else if (p.matched_count === 5 && p.bonus_matched) r2++;
    else if (p.matched_count === 5) r3++;
    else if (p.matched_count === 4) r4++;
    else if (p.matched_count === 3) r5++;
  });
  var html = '총 예측: ' + preds.length + '세트<br>';
  html += '🏆1등: ' + r1 + ' | 🥈2등: ' + r2 + ' | 🥉3등: ' + r3 + ' | 🎯4등: ' + r4 + ' | ✅5등: ' + r5;
  if (total > 0) {
    var hitRate = (((r1 + r2 + r3 + r4 + r5) / total) * 100).toFixed(1);
    html += '<br>5등 이상 적중률: ' + hitRate + '%';
  }
  el.innerHTML = html;
}

function renderSpecialBrainPreds(elId, preds) {
  var el = document.getElementById(elId);
  if (!el) return;
  if (!preds.length) {
    el.innerHTML = '<div style="color:#555;font-size:0.85em;">예측 없음</div>';
    return;
  }
  var sorted = preds.slice().sort(function(a, b) { return (b.target_draw_no || 0) - (a.target_draw_no || 0); });
  var latestDraw = sorted[0].target_draw_no;
  var latest = sorted.filter(function(p) { return p.target_draw_no === latestDraw; });

  var html = '<div style="color:#888;font-size:0.75em;margin-bottom:6px;">' + latestDraw + '회차 예측</div>';
  latest.forEach(function(p, i) {
    html += '<div class="special-pred-card">';
    html += '<div class="special-pred-header">';
    html += '<span>#' + (i + 1) + '</span>';
    html += '<span>신뢰도 ' + (p.confidence || 0).toFixed(1) + '%</span>';
    html += '</div>';
    html += '<div class="special-pred-nums">';
    var nums = [p.num1, p.num2, p.num3, p.num4, p.num5, p.num6];
    nums.forEach(function(n) {
      html += renderBall(n, false);
    });
    html += '</div>';
    html += '</div>';
  });
  el.innerHTML = html;
}

function renderSpecialMissList(missDrawNos, allPreds) {
  var el = document.getElementById('specialMissList');
  if (!el) return;
  if (!missDrawNos.length) {
    el.innerHTML = '<div style="color:#555;">미당첨 회차가 없습니다.</div>';
    return;
  }
  var showing = missDrawNos.slice(0, _specialMissListLimit);

  var html = '<table class="special-miss-table">';
  html += '<thead><tr><th>회차</th><th>최고 적중</th><th>미당첨분석</th><th>뱀</th></tr></thead>';
  html += '<tbody>';

  showing.forEach(function(dno) {
    var basePreds = allPreds.filter(function(p) {
      return p.target_draw_no === dno &&
        ['stat', 'markov', 'llm', 'lstm', 'fusion', 'hyena'].indexOf(p.brain_tag) >= 0 &&
        p.matched_count >= 0;
    });
    var bestMatch = 0;
    basePreds.forEach(function(p) { if (p.matched_count > bestMatch) bestMatch = p.matched_count; });

    var missBest = '-';
    var missP = allPreds.filter(function(p) {
      return p.target_draw_no === dno && p.brain_tag === 'miss_analysis' && p.matched_count >= 0;
    });
    if (missP.length) {
      var mb = 0;
      missP.forEach(function(p) { if (p.matched_count > mb) mb = p.matched_count; });
      missBest = mb + '개';
    }

    var snakeBest = '-';
    var snakeP = allPreds.filter(function(p) {
      return p.target_draw_no === dno && p.brain_tag === 'snake' && p.matched_count >= 0;
    });
    if (snakeP.length) {
      var sb = 0;
      snakeP.forEach(function(p) { if (p.matched_count > sb) sb = p.matched_count; });
      snakeBest = sb + '개';
    }

    html += '<tr>';
    html += '<td>' + dno + '회</td>';
    html += '<td>' + bestMatch + '개</td>';
    html += '<td>' + missBest + '</td>';
    html += '<td>' + snakeBest + '</td>';
    html += '</tr>';
  });

  html += '</tbody></table>';

  if (missDrawNos.length > _specialMissListLimit) {
    var remaining = missDrawNos.length - _specialMissListLimit;
    html += '<button class="special-more-btn" onclick="specialShowMoreMiss()">+ 더보기 (' + remaining + '건 남음)</button>';
  }

  el.innerHTML = html;
}

function specialShowMoreMiss() {
  _specialMissListLimit += 20;
  loadSpecialForce();
}
