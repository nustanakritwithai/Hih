import { loadJson, escapeHtml } from './utils.js';

async function init() {
  const articles = await loadJson('src/data/articles.json');
  const latest = articles.slice(0, 3);
  const root = document.getElementById('latest-articles');
  root.innerHTML = latest
    .map(
      (a) => `<article class="card"><h3>${escapeHtml(a.title)}</h3><p><strong>${escapeHtml(a.narrator)}</strong></p><p>${escapeHtml(a.summary)}</p><a class="btn btn-secondary" href="ai-news.html">อ่านต่อ</a></article>`
    )
    .join('');
}

init();
