/* 预测总览：按模型聚合准确率，支持按标的贡献图与按日期列表。 */
(function () {
  const state = { predictions: [], model: '' };
  const $ = (selector) => document.querySelector(selector);
  const esc = (value) => String(value).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  async function load() {
    try {
      const response = await fetch('/api/predictions'); if (!response.ok) throw new Error(await response.text());
      state.predictions = (await response.json()).predictions || [];
      const models = [...new Set(state.predictions.map((item) => item.model))]; state.model = models[0] || '';
      $('#overviewModelSelect').innerHTML = models.map((model) => `<option value="${esc(model)}">${esc(model)}</option>`).join(''); render();
    } catch (error) { $('#overviewChart').innerHTML = `<div class="empty">加载失败：${esc(error.message)}</div>`; }
  }
  function render() {
    const rows = state.predictions.filter((item) => !state.model || item.model === state.model); const checked = rows.filter((item) => item.correct !== null && item.correct !== undefined); const wins = checked.filter((item) => item.correct).length;
    $('#overviewStats').innerHTML = `<div class="stat-item"><span>总预测</span><strong>${rows.length}</strong></div><div class="stat-item"><span>已验证</span><strong>${checked.length}</strong></div><div class="stat-item"><span>正确率</span><strong>${checked.length ? Math.round(wins / checked.length * 100) : 0}%</strong></div><div class="stat-item"><span>待验证</span><strong>${rows.length - checked.length}</strong></div>`;
    const bySymbol = $('#overviewDimension').value === 'symbol'; const groups = {}; rows.forEach((item) => { const key = bySymbol ? item.stock_code : item.predict_date; (groups[key] ||= []).push(item); });
    if (bySymbol) { const dates = [...new Set(rows.map((item) => item.predict_date))].sort(); $('#overviewChart').innerHTML = `<div class="contribution"><div class="contribution-head"><span>标的</span>${dates.map((date) => `<span>${date.slice(4)}</span>`).join('')}</div>${Object.keys(groups).sort().map((symbol) => `<div class="contribution-row"><span>${esc(symbol)}</span>${dates.map((date) => { const item = groups[symbol].find((entry) => entry.predict_date === date); return `<span class="result-cell ${item ? (item.correct === true ? 'is-correct' : item.correct === false ? 'is-wrong' : 'is-pending') : 'is-empty'}">${item ? (item.correct === true ? '✓' : item.correct === false ? '×' : '·') : ''}</span>`; }).join('')}</div>`).join('')}</div>`; }
    else { const dates = Object.keys(groups).sort().reverse(); $('#overviewChart').innerHTML = `<div class="date-list">${dates.map((date) => `<div class="date-row"><strong>${date}</strong><span>${groups[date].map((item) => `<span class="date-result ${item.correct === true ? 'is-correct' : item.correct === false ? 'is-wrong' : 'is-pending'}">${esc(item.stock_code)} ${item.correct === true ? '✓' : item.correct === false ? '×' : '·'}</span>`).join('')}</span></div>`).join('')}</div>`; }
    const leaderboard = [...new Set(state.predictions.map((item) => item.model))].map((model) => { const data = state.predictions.filter((item) => item.model === model && item.correct !== null && item.correct !== undefined); const count = data.filter((item) => item.correct).length; return { model, count, total: data.length, rate: data.length ? count / data.length : 0 }; }).sort((a, b) => b.rate - a.rate || b.count - a.count); $('#leaderboard').innerHTML = leaderboard.map((item, index) => `<div class="leader-row"><strong>#${index + 1} ${esc(item.model)}</strong><span>${Math.round(item.rate * 100)}% (${item.count}/${item.total})</span></div>`).join('') || '<div class="empty">暂无数据</div>';
  }
  $('#overviewModelSelect').addEventListener('change', (event) => { state.model = event.target.value; render(); }); $('#overviewDimension').addEventListener('change', render);
  document.querySelectorAll('.view-switch').forEach((button) => button.addEventListener('click', () => { document.querySelectorAll('.view-switch').forEach((item) => item.classList.toggle('active', item === button)); const overview = button.dataset.viewTarget === 'overview'; $('#overviewView').hidden = !overview; $('#detailView').hidden = overview; }));
  load();
}());
