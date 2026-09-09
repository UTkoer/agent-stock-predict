const $ = (selector) => document.querySelector(selector);
const state = { symbols: [], models: [], predictions: [], rows: [] };

async function api(path) {
  const response = await fetch(path);
  if (!response.ok) throw new Error(await response.text());
  return response.json();
}

function fillSelect(selector, items) {
  $(selector).innerHTML = items.map((item) => `<option value="${item.value}">${item.text}</option>`).join('');
}

function safeModel(value) {
  return value.replace(/[^A-Za-z0-9._-]+/g, '_').replace(/^\.+|\.+$/g, '') || 'model';
}

async function boot() {
  try {
    $('#health').textContent = '系统在线';
    const [symbols, models, tools, prompt] = await Promise.all([
      api('/api/symbols'), api('/api/models'), api('/api/mcp-tools'), api('/api/prompts')
    ]);
    state.symbols = symbols.symbols;
    state.models = models.models;
    fillSelect('#symbolSelect', state.symbols.map((value) => ({ value, text: value })));
    fillSelect('#modelSelect', [{ value: '', text: '全部模型' }, ...state.models.map((item) => ({ value: safeModel(item.name), text: item.name }))]);
    $('#modelList').innerHTML = state.models.map((item) => `<li><span>${item.name}</span><span class="pill">${item.enabled ? 'ENABLED' : 'OFF'}</span></li>`).join('');
    $('#toolList').innerHTML = tools.tools.map((item) => `<li><span>${item.name}</span><span class="pill">${item.status}</span></li>`).join('');
    $('#promptText').textContent = prompt.default_prompt || '未配置';
    if (state.symbols.length) await load();
  } catch (error) { $('#health').textContent = '连接失败'; $('#predictionCard').innerHTML = `<div class="empty">${error.message}</div>`; }
}

async function load() {
  const symbol = $('#symbolSelect').value;
  const model = $('#modelSelect').value;
  try {
    const [predictions, stock] = await Promise.all([
      api(`/api/predictions?symbol=${encodeURIComponent(symbol)}${model ? `&model=${encodeURIComponent(model)}` : ''}`),
      api(`/api/stocks/${encodeURIComponent(symbol)}`)
    ]);
    state.predictions = predictions.predictions;
    state.rows = stock.data || [];
    fillSelect('#dateSelect', [...new Set(state.predictions.map((item) => item.predict_date))].map((value) => ({ value, text: value })));
    render();
  } catch (error) { $('#predictionCard').innerHTML = `<div class="empty">${error.message}</div>`; }
}

function verificationBadge(value) {
  if (value === null || value === undefined) return '<span class="verification pending">待验证</span>';
  return value
    ? '<span class="verification correct">正确 ✓</span>'
    : '<span class="verification incorrect">错误 ×</span>';
}

function render() {
  const selectedDate = $('#dateSelect').value || state.predictions[0]?.predict_date;
  const prediction = state.predictions.find((item) => item.predict_date === selectedDate) || state.predictions[0];
  if (!prediction) { $('#predictionCard').innerHTML = '<div class="empty">暂无预测结果</div>'; return; }
  $('#coverage').textContent = `${prediction.model} · ${prediction.stock_code}`;
  $('#predictionCard').innerHTML = `<div class="prediction-tabs"><button class="prediction-tab active" type="button" data-view="summary">预测摘要</button><button class="prediction-tab" type="button" data-view="report">MD分析报告</button></div><div class="prediction-view" data-prediction-summary><div class="signal"><div class="direction">${prediction.prediction || '--'}</div><div><div class="confidence">置信度 ${prediction.confidence ?? '--'}</div><div class="meta"><span>预测日 ${prediction.predict_date}</span>${verificationBadge(prediction.correct)}</div></div></div><p class="reasoning">${prediction.reasoning || '暂无分析说明'}</p></div><div class="prediction-view report-view" data-prediction-report hidden><div class="empty">点击“MD分析报告”加载报告</div></div>`;
  if (window.setupReportView) window.setupReportView(prediction);
  $('#stockRows').innerHTML = state.rows.slice(-30).reverse().map((row) => {
    const change = Number(row.pct_chg);
    const className = change > 0 ? 'rise' : change < 0 ? 'fall' : '';
    return `<tr class="${className}"><td>${row.trade_date || '--'}</td><td>${row.open ?? '--'}</td><td>${row.close ?? '--'}</td><td>${row.pct_chg ?? '--'}%</td><td>${row.vol ?? '--'}</td></tr>`;
  }).join('');
}

$('#symbolSelect').addEventListener('change', load);
$('#modelSelect').addEventListener('change', load);
$('#dateSelect').addEventListener('change', render);
$('#refreshBtn').addEventListener('click', load);
boot();
