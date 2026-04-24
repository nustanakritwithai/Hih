const questions = [
  { key: 'use', label: '1) คุณอยากใช้แว่นทำอะไรเป็นหลัก?', options: ['ถ่ายคลิป / ทำคอนเทนต์', 'ฟังเพลง / โทร', 'ดูหนัง / เล่นเกม', 'ใช้ AI ช่วยถามตอบ', 'อยากลองของถูกก่อน'] },
  { key: 'budget', label: '2) งบประมาณของคุณประมาณเท่าไหร่?', options: ['ไม่เกิน 1,000 บาท', '1,000–5,000 บาท', '5,000–10,000 บาท', '10,000 บาทขึ้นไป'] },
  { key: 'device', label: '3) คุณใช้กับอุปกรณ์อะไรเป็นหลัก?', options: ['iPhone', 'Android', 'PC / Notebook', 'เครื่องเกม', 'ใช้งานทั่วไป'] },
  { key: 'camera', label: '4) คุณต้องการกล้องในแว่นไหม?', options: ['ต้องการ', 'ไม่ต้องการ', 'ไม่แน่ใจ'] },
  { key: 'priority', label: '5) คุณเน้นอะไรมากที่สุด?', options: ['ราคาถูก', 'คุณภาพดี', 'ดีไซน์ใส่ง่าย', 'ฟีเจอร์ล้ำ', 'ใช้ง่ายไม่ยุ่งยาก'] }
];

function scoreType(ans) {
  const score = { Bluetooth: 0, Camera: 0, AI: 0, AR: 0 };
  if (ans.use.includes('ถ่ายคลิป')) score.Camera += 3;
  if (ans.use.includes('ฟังเพลง')) score.Bluetooth += 3;
  if (ans.use.includes('ดูหนัง')) score.AR += 3;
  if (ans.use.includes('AI')) score.AI += 3;
  if (ans.use.includes('ของถูก')) score.Bluetooth += 2;

  if (ans.budget.includes('ไม่เกิน')) score.Bluetooth += 2;
  if (ans.budget.includes('1,000–5,000')) score.Camera += 1;
  if (ans.budget.includes('5,000–10,000')) score.AR += 2;
  if (ans.budget.includes('10,000')) score.AI += 2;

  if (ans.camera === 'ต้องการ') score.Camera += 2;
  if (ans.priority === 'ฟีเจอร์ล้ำ') score.AI += 2;
  if (ans.priority === 'คุณภาพดี') score.AR += 1;

  return Object.entries(score).sort((a, b) => b[1] - a[1])[0][0];
}

function explain(type) {
  const map = {
    Bluetooth: 'คุณเหมาะกับ Bluetooth Glasses — เริ่มง่าย งบประหยัด เหมาะกับฟังเพลง/โทรและคนที่อยากลองก่อน',
    Camera: 'คุณเหมาะกับ Camera Glasses / POV Glasses — เหมาะกับคนทำคอนเทนต์ที่อยากถ่ายคลิปแบบไม่ต้องถือกล้อง',
    AI: 'คุณเหมาะกับ AI Glasses — เหมาะกับคนที่อยากได้ผู้ช่วย AI, ถามตอบไว, ใช้ทำงานจริงจัง',
    AR: 'คุณเหมาะกับ AR Glasses — เหมาะกับการดูหนัง เล่นเกม หรือทำงานบนจอเสมือนขนาดใหญ่'
  };
  return map[type];
}

const form = document.getElementById('quiz-form');
questions.forEach((q) => {
  const section = document.createElement('section');
  section.className = 'question';
  section.innerHTML = `<h3>${q.label}</h3>` + q.options.map((opt, idx) => `<label><input required type="radio" name="${q.key}" value="${opt}" ${idx === 0 ? '' : ''}/> ${opt}</label>`).join('');
  form.appendChild(section);
});

document.getElementById('submit-quiz').addEventListener('click', () => {
  const data = new FormData(form);
  const answers = Object.fromEntries(data.entries());
  if (Object.keys(answers).length !== questions.length) return alert('กรุณาตอบให้ครบทั้ง 5 ข้อก่อนนะครับ');
  const type = scoreType(answers);
  const result = document.getElementById('quiz-result');
  result.hidden = false;
  result.innerHTML = `<h2>${explain(type)}</h2><p>คำแนะนำจากครอบครัวถั่ว: ลองเทียบตัวเลือกในหมวดที่ตรงกับคุณ แล้วอ่านรีวิวก่อนซื้อทุกครั้ง</p><a class="btn btn-primary" href="shopee-picks.html">ดูตัวเลือกใน Shopee</a>`;
});
