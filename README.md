# Nut AI Smart Glasses (MVP)

เว็บศูนย์กลางแบรนด์ **Nut AI Smart Glasses** แบบ Static Website (HTML + CSS + JS + JSON)

## โครงสร้างหน้า
- `index.html` — Home
- `nut-family.html` — ครอบครัวถั่ว
- `ai-news.html` — ข่าว AI
- `guide.html` — คู่มือแว่น AI / Smart Glasses / AR Glasses
- `shopee-picks.html` — ชี้เป้า Shopee
- `quiz.html` — แบบทดสอบช่วยเลือกแว่น

## Run local
```bash
python -m http.server 8080
```

แล้วเปิด `http://localhost:8080`

---

## Deploy บน GitHub Pages (แนะนำ)
โปรเจกต์นี้ตั้งค่าไว้พร้อม deploy ด้วย GitHub Actions แล้วที่:
- `.github/workflows/deploy-pages.yml`
- `.nojekyll`

### วิธีเร็วสุด (แนะนำ)
1. ตั้ง remote `origin` ให้ชี้ไป GitHub repo ของคุณ
2. รัน:
   ```bash
   bash scripts/deploy_github_pages.sh
   ```
3. ไปที่ **Settings → Pages → Source: GitHub Actions**
4. รอ workflow `Deploy to GitHub Pages` ทำงานเสร็จ

สคริปต์จะพิมพ์ลิงก์รูปแบบนี้ให้อัตโนมัติ:
- `https://<username>.github.io/<repository>/`

### วิธี manual
1. Push โค้ดขึ้น GitHub repository
2. ไปที่ **Settings → Pages**
3. ที่หัวข้อ **Build and deployment** เลือก **Source: GitHub Actions**
4. Push commit ใหม่เข้า `main` (หรือ `master`) เพื่อ trigger deploy
5. รอ workflow `Deploy to GitHub Pages` ทำงานเสร็จ

### URL หลัง deploy
- User/Org site: `https://<username>.github.io/`
- Project site: `https://<username>.github.io/<repository>/`

> ลิงก์ในเว็บนี้เป็น relative path ทั้งหมด จึงใช้งานได้ทั้ง root domain และ project subpath ของ GitHub Pages

---

## ตัวเลือก deploy อื่น
### Netlify
ใช้ `netlify.toml` (publish จาก root)

### Vercel
ใช้ `vercel.json` (static config)

## หมายเหตุ
- เว็บไซต์นี้มีข้อความ affiliate disclaimer ในหน้า Home และ Shopee Picks
- ข้อมูลตัวละคร/บทความ/สินค้าอยู่ใน `src/data/*.json` แก้ไขต่อได้ทันที
