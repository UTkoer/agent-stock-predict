/* MD report view: delegated tab handling survives dynamic prediction-card rerenders. */
(function () {
  let currentPrediction = null;
  let loadedKey = '';
  function escapeHtml(value) { return String(value).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])); }
  async function loadReport(prediction, report) {
    const key = `${prediction.model}:${prediction.stock_code}:${prediction.predict_date}`; if (loadedKey === key) return;
    report.innerHTML = '<div class="empty">正在加载分析报告...</div>';
    try { const params = new URLSearchParams({ symbol: prediction.stock_code, model: prediction.model, predict_date: prediction.predict_date }); const response = await fetch(`/api/reports?${params}`); if (!response.ok) throw new Error(await response.text()); const data = await response.json(); report.innerHTML = `<div class="markdown-body">${window.marked ? window.marked.parse(data.content) : `<pre>${escapeHtml(data.content)}</pre>`}</div>`; loadedKey = key; }
    catch (error) { report.innerHTML = `<div class="empty">报告加载失败：${escapeHtml(error.message)}</div>`; }
  }
  window.setupReportView = function (prediction) { currentPrediction = prediction; loadedKey = ''; };
  document.addEventListener('click', (event) => { const tab = event.target.closest('.prediction-tab'); if (!tab || !currentPrediction) return; const card = document.querySelector('#predictionCard'); const summary = card.querySelector('[data-prediction-summary]'); const report = card.querySelector('[data-prediction-report]'); card.querySelectorAll('.prediction-tab').forEach((item) => item.classList.toggle('active', item === tab)); const isReport = tab.dataset.view === 'report'; summary.hidden = isReport; report.hidden = !isReport; if (isReport) loadReport(currentPrediction, report); });
}());
