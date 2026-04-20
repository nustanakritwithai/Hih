# วิธีทำคลิปด้วย Claude Design

คลิปแนวตั้ง 9:16 ความยาว 1 นาที สำหรับโพสต์โซเชียล (TikTok / Reels / Shorts)

## บรรยายภาษาไทย (Voice-over)

**ฉากที่ 1 · 0:00–0:10 · หัวเรื่อง**
> สวัสดีครับ วันนี้จะมาสอนวิธีทำคลิปโซเชียลแนวตั้งด้วย Claude Design แบบง่าย สวย เสร็จไว ภายใน 1 นาที

**ฉากที่ 2 · 0:10–0:20 · ขั้นตอนที่ 1**
> ขั้นแรก บอก Claude ว่าอยากได้คลิปเกี่ยวกับอะไร ธีมแบบไหน และยาวเท่าไหร่ เช่น “คลิป 9:16 สอนทำอาหาร 1 นาที”

**ฉากที่ 3 · 0:20–0:30 · ขั้นตอนที่ 2**
> จากนั้นเลือกอัตราส่วนเป็น 9:16 เพื่อให้คลิปพอดีกับหน้าจอมือถือและฟีดของ TikTok, Reels, Shorts

**ฉากที่ 4 · 0:30–0:40 · ขั้นตอนที่ 3**
> ใส่เนื้อหา ข้อความบรรยาย เลือกฟอนต์ สี และภาพประกอบให้ตรงกับสไตล์ของคุณ

**ฉากที่ 5 · 0:40–0:50 · ขั้นตอนที่ 4**
> สุดท้าย กดส่งออกเป็นไฟล์ MP4 ขนาด 1080 คูณ 1920 แล้วนำไปโพสต์ได้ทุกแพลตฟอร์ม

**ฉากที่ 6 · 0:50–1:00 · Call to action**
> ถ้าชอบคลิปนี้ อย่าลืมกดไลก์และติดตามเพื่อดูเทคนิคเพิ่มเติม เจอกันใหม่คลิปหน้าครับ

## ไฟล์วิดีโอ

- `clip.mp4` — คลิปพร้อมโพสต์ 9:16 / 1080×1920 / 30fps / 60s · **มีเสียงบรรยายไทย (espeak-ng)**
- `clip_silent.mp4` — เวอร์ชันไม่มีเสียง (สำหรับใส่เสียงใหม่)
- `clip.html` — สตอรี่บอร์ดเวอร์ชันเว็บ
- `build_mp4.py` — สคริปต์สร้างภาพแต่ละฉากด้วย Pillow
- `build_audio.sh` — สคริปต์สร้างเสียงบรรยายไทยด้วย espeak-ng

## วิธีสร้าง MP4 ใหม่

```bash
python3 build_mp4.py
ffmpeg -y \
  -loop 1 -t 10.5 -i frames/scene1.png \
  -loop 1 -t 10.5 -i frames/scene2.png \
  -loop 1 -t 10.5 -i frames/scene3.png \
  -loop 1 -t 10.5 -i frames/scene4.png \
  -loop 1 -t 10.5 -i frames/scene5.png \
  -loop 1 -t 11.5 -i frames/scene6.png \
  -filter_complex "[0:v]fps=30,format=yuv420p,fade=t=in:st=0:d=0.5[v0];\
[1:v]fps=30,format=yuv420p[v1];[2:v]fps=30,format=yuv420p[v2];\
[3:v]fps=30,format=yuv420p[v3];[4:v]fps=30,format=yuv420p[v4];\
[5:v]fps=30,format=yuv420p,fade=t=out:st=10:d=1.5[v5];\
[v0][v1]xfade=transition=fade:duration=0.5:offset=10[x1];\
[x1][v2]xfade=transition=fade:duration=0.5:offset=20[x2];\
[x2][v3]xfade=transition=fade:duration=0.5:offset=30[x3];\
[x3][v4]xfade=transition=fade:duration=0.5:offset=40[x4];\
[x4][v5]xfade=transition=fade:duration=0.5:offset=50[out]" \
  -map "[out]" -t 60 -c:v libx264 -preset medium -crf 20 \
  -pix_fmt yuv420p -movflags +faststart clip.mp4
```

## เพิ่มเสียงบรรยาย (ออปชัน)

อัดเสียงตามสคริปต์ด้านบน (หรือใช้ Thai TTS) เป็น `voice.mp3` แล้วรวมเข้าคลิป:

```bash
ffmpeg -i clip.mp4 -i voice.mp3 -c:v copy -c:a aac -shortest clip_with_audio.mp4
```
