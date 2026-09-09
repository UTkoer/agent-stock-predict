(function () {
  function escapeHtml(value) { return String(value).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])); }
  window.setupReportView = function (prediction) {
    const card = document.querySelector('#predictionCard');
    const tabs = card.querySelectorAll('.prediction-tab');
    const summary = card.querySelector('[data-prediction-summary]');
    const report = card.querySelector('[data-prediction-report]');
    let loaded = false;
    tabs.forEach((tab) => tab.addEventListener('click', async () => {
      tabs.forEach((item) => item.classList.toggle('active', item === tab));
      const isReport = tab.dataset.view === 'report'; summary.hidden = isReport; report.hidden = !isReport;
      if (isReport && !loaded) {
        report.innerHTML = '<div class="empty">正在加载分析报告...</div>';
        try {
          const params = new URLSearchParams({ symbol: prediction.stock_code, model: prediction.model, predict_date: prediction.predict_date });
          const response = await fetch(`/api/reports?${params}`); if (!response.ok) throw new Error(await response.text());
          const data = await response.json(); report.innerHTML = `<div class="markdown-body">${window.marked ? marked.parse(data.content) : `<pre>${escapeHtml(data.content)}</pre>`}</div>`; loaded = true;
        } catch (error) { report.innerHTML = `<div class="empty">报告加载失败：${escapeHtml(error.message)}</div>`; }
      }
    }));
  };
}());
