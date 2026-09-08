(() => {
  const key = 'stock-predict-theme';
  const button = document.querySelector('#themeBtn');
  const saved = localStorage.getItem(key);
  if (saved === 'day') document.body.dataset.theme = 'day';
  const update = () => {
    const day = document.body.dataset.theme === 'day';
    button.textContent = day ? '☾' : '☼';
    button.title = day ? '切换夜晚主题' : '切换白天主题';
  };
  button.addEventListener('click', () => {
    const day = document.body.dataset.theme !== 'day';
    document.body.dataset.theme = day ? 'day' : 'night';
    localStorage.setItem(key, day ? 'day' : 'night');
    update();
  });
  update();
})();
