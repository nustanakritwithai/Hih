import { loadJson, escapeHtml } from './utils.js';

async function init() {
  const articles = await loadJson('src/data/articles.json');
  document.getElementById('news-grid').innerHTML = articles
    .map(
      (a) => `<article class="card"><h3>${escapeHtml(a.title)}</h3><p>ผู้เล่า: <strong>${escapeHtml(a.narrator)}</strong></p><p>${escapeHtml(a.summary)}</p><p><strong>ทำไมสำคัญ:</strong> ${escapeHtml(a.importance)}</p><p><strong>คนทั่วไปควรรู้:</strong> ${escapeHtml(a.whatToKnow)}</p><div class="cta-row"><a class="btn btn-secondary" href="guide.html">ดูคู่มือเพิ่ม</a><a class="btn btn-primary" href="shopee-picks.html">ดูสินค้าเกี่ยวข้อง</a></div></article>`
    )
    .join('');
}

init();
