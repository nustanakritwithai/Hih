#!/usr/bin/env python3
"""Render 6 scene PNGs for the 9:16 Thai social clip."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os

W, H = 1080, 1920
OUT = "/home/user/Hih/frames"
os.makedirs(OUT, exist_ok=True)

FONT_REG = "/usr/share/fonts/opentype/tlwg/Loma.otf"
FONT_BOLD = "/usr/share/fonts/opentype/tlwg/Loma-Bold.otf"

BG1 = (11, 11, 23)
BG2 = (26, 15, 46)
ACCENT = (217, 119, 87)
ACCENT2 = (255, 176, 136)
TEXT = (245, 245, 240)
MUTED = (184, 184, 176)


def f(size, bold=False):
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, size)


def gradient_bg():
    img = Image.new("RGB", (W, H), BG1)
    px = img.load()
    for y in range(H):
        t = y / H
        r = int(BG1[0] * (1 - t) + BG2[0] * t)
        g = int(BG1[1] * (1 - t) + BG2[1] * t)
        b = int(BG1[2] * (1 - t) + BG2[2] * t)
        for x in range(W):
            px[x, y] = (r, g, b)
    return img


def add_orbs(img):
    orb = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(orb)
    d.ellipse([W - 400, -200, W + 300, 500], fill=(*ACCENT, 90))
    d.ellipse([-200, H - 500, 500, H + 200], fill=(123, 92, 255, 90))
    orb = orb.filter(ImageFilter.GaussianBlur(120))
    img.paste(orb, (0, 0), orb)
    return img


def draw_centered(draw, text, y, font, fill):
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    draw.text(((W - w) / 2, y), text, font=font, fill=fill)
    return bbox[3] - bbox[1]


def draw_multiline_centered(draw, lines, y, font, fill, line_gap=10):
    total_h = 0
    metrics = []
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        metrics.append((line, bbox[2] - bbox[0], bbox[3] - bbox[1]))
        total_h += bbox[3] - bbox[1] + line_gap
    cy = y
    for line, w, h in metrics:
        draw.text(((W - w) / 2, cy), line, font=font, fill=fill)
        cy += h + line_gap
    return cy - y


def rounded_rect(draw, xy, radius, fill):
    draw.rounded_rectangle(xy, radius=radius, fill=fill)


def draw_tag(draw, text, color=ACCENT2):
    font = f(36, bold=True)
    draw.text((110, 150), text, font=font, fill=color)


def draw_step_pill(draw, text, y):
    font = f(50, bold=True)
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    pad_x, pad_y = 60, 20
    x = (W - tw) / 2 - pad_x
    rx = x + tw + pad_x * 2
    by = y + bbox[3] - bbox[1] + pad_y * 2
    draw.rounded_rectangle([x, y, rx, by], radius=80, fill=ACCENT)
    draw.text((x + pad_x, y + pad_y - 5), text, font=font, fill=(26, 15, 46))
    return by - y


def draw_caption(draw, text_lines):
    x1, x2 = 80, W - 80
    y2 = H - 220
    font = f(38, bold=True)
    line_h = 58
    total_h = len(text_lines) * line_h
    y1 = y2 - total_h - 60
    draw.rounded_rectangle([x1, y1, x2, y2], radius=40, fill=(0, 0, 0, 180))
    cy = y1 + 30
    for line in text_lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        draw.text(((W - tw) / 2, cy), line, font=font, fill=TEXT)
        cy += line_h


def draw_progress(draw, ratio):
    x1, x2 = 80, W - 80
    y1, y2 = H - 100, H - 90
    draw.rounded_rectangle([x1, y1, x2, y2], radius=10, fill=(255, 255, 255, 40))
    fx = x1 + (x2 - x1) * ratio
    draw.rounded_rectangle([x1, y1, fx, y2], radius=10, fill=ACCENT)


def draw_chip(draw, text, cx, cy, on=False):
    font = f(44, bold=True)
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pad_x, pad_y = 40, 18
    x1 = cx - tw / 2 - pad_x
    x2 = cx + tw / 2 + pad_x
    y1 = cy - th / 2 - pad_y
    y2 = cy + th / 2 + pad_y
    if on:
        draw.rounded_rectangle([x1, y1, x2, y2], radius=80, fill=ACCENT)
        fill = (26, 15, 46)
    else:
        draw.rounded_rectangle([x1, y1, x2, y2], radius=80, outline=ACCENT, width=4)
        fill = TEXT
    draw.text((cx - tw / 2, cy - th / 2 - 8), text, font=font, fill=fill)


def scene_base(progress_ratio):
    img = gradient_bg()
    img = add_orbs(img)
    img = img.convert("RGBA")
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    draw_progress(d, progress_ratio)
    return img, overlay, d


def render_scene_1():
    img, ov, d = scene_base(0.08)
    draw_tag(d, "CLAUDE DESIGN · 9:16")
    draw_multiline_centered(
        d,
        ["วิธีทำคลิป", "ด้วย Claude Design"],
        y=520,
        font=f(110, bold=True),
        fill=ACCENT2,
        line_gap=20,
    )
    draw_multiline_centered(
        d,
        ["สร้างคลิปโซเชียล 1 นาที", "ง่าย สวย เสร็จไว"],
        y=950,
        font=f(56),
        fill=MUTED,
        line_gap=16,
    )
    draw_caption(d, ["สวัสดีครับ วันนี้จะมาสอนวิธีทำคลิปโซเชียล", "แนวตั้งด้วย Claude Design แบบเร็วๆ"])
    return Image.alpha_composite(img, ov).convert("RGB")


def render_scene_2():
    img, ov, d = scene_base(0.25)
    draw_tag(d, "STEP 1 / 4")
    draw_step_pill(d, "ขั้นตอนที่ 1", y=380)
    draw_multiline_centered(
        d,
        ["บอก Claude", "ว่าอยากได้คลิปแบบไหน"],
        y=560,
        font=f(88, bold=True),
        fill=TEXT,
        line_gap=16,
    )
    draw_multiline_centered(
        d,
        ["พิมพ์ไอเดีย ธีม และความยาว", "เช่น “คลิป 9:16 สอนทำอาหาร 1 นาที”"],
        y=920,
        font=f(48),
        fill=MUTED,
        line_gap=14,
    )
    draw_caption(d, ["ขั้นแรก บอก Claude ว่าคุณอยากได้คลิป", "เกี่ยวกับอะไร และยาวเท่าไหร่"])
    return Image.alpha_composite(img, ov).convert("RGB")


def render_scene_3():
    img, ov, d = scene_base(0.42)
    draw_tag(d, "STEP 2 / 4")
    draw_step_pill(d, "ขั้นตอนที่ 2", y=380)
    draw_multiline_centered(
        d, ["เลือกอัตราส่วน 9:16"], y=560, font=f(88, bold=True), fill=TEXT
    )
    cy = 850
    draw_chip(d, "16:9", W / 2 - 280, cy, on=False)
    draw_chip(d, "1:1", W / 2, cy, on=False)
    draw_chip(d, "9:16", W / 2 + 280, cy, on=True)
    draw_multiline_centered(
        d,
        ["ให้เหมาะกับ TikTok, Reels, Shorts"],
        y=1050,
        font=f(48),
        fill=MUTED,
    )
    draw_caption(d, ["เลือกอัตราส่วน 9:16 เพื่อให้คลิป", "พอดีกับฟีดโซเชียลบนมือถือ"])
    return Image.alpha_composite(img, ov).convert("RGB")


def render_scene_4():
    img, ov, d = scene_base(0.58)
    draw_tag(d, "STEP 3 / 4")
    draw_step_pill(d, "ขั้นตอนที่ 3", y=320)
    draw_multiline_centered(
        d,
        ["ใส่เนื้อหา", "ข้อความ & ภาพ"],
        y=500,
        font=f(88, bold=True),
        fill=TEXT,
        line_gap=16,
    )
    mx, my, mw, mh = 240, 820, W - 480, 720
    d.rounded_rectangle([mx, my, mx + mw, my + mh], radius=60, fill=(21, 21, 42, 255), outline=ACCENT, width=4)
    bar_y = my + 60
    bars = [("m", 0.85), ("hl", 0.7), ("s", 0.6), ("m", 0.85), ("hl", 0.7), ("s", 0.5)]
    for kind, ratio in bars:
        bw = int((mw - 80) * ratio)
        color = ACCENT2 if kind == "hl" else (255, 255, 255, 40)
        d.rounded_rectangle(
            [mx + 40, bar_y, mx + 40 + bw, bar_y + 40], radius=20, fill=color
        )
        bar_y += 90
    draw_caption(d, ["ใส่ข้อความบรรยาย เลือกฟอนต์ สี", "และภาพประกอบได้ตามสไตล์ของคุณ"])
    return Image.alpha_composite(img, ov).convert("RGB")


def render_scene_5():
    img, ov, d = scene_base(0.75)
    draw_tag(d, "STEP 4 / 4")
    draw_step_pill(d, "ขั้นตอนที่ 4", y=380)
    draw_multiline_centered(
        d, ["ส่งออก & โพสต์"], y=560, font=f(100, bold=True), fill=TEXT
    )
    draw_multiline_centered(
        d,
        ["MP4 · 1080×1920 · 60s"],
        y=800,
        font=f(56, bold=True),
        fill=ACCENT2,
    )
    cy = 1020
    draw_chip(d, "TikTok", W / 2 - 280, cy, on=True)
    draw_chip(d, "Reels", W / 2, cy, on=True)
    draw_chip(d, "Shorts", W / 2 + 280, cy, on=True)
    draw_caption(d, ["สุดท้าย กดส่งออกเป็นไฟล์ MP4", "แล้วนำไปโพสต์ได้ทุกแพลตฟอร์ม"])
    return Image.alpha_composite(img, ov).convert("RGB")


def render_scene_6():
    img, ov, d = scene_base(0.92)
    draw_tag(d, "START NOW")
    draw_multiline_centered(
        d,
        ["ลองทำเลย", "วันนี้!"],
        y=500,
        font=f(130, bold=True),
        fill=ACCENT2,
        line_gap=20,
    )
    draw_multiline_centered(
        d,
        ["Claude Design ช่วยให้คลิปของคุณ", "ดูโปรในไม่กี่นาที"],
        y=1000,
        font=f(52),
        fill=MUTED,
        line_gap=14,
    )
    draw_multiline_centered(
        d,
        ["กดติดตามเพื่อดูเทคนิคเพิ่มเติม ✦"],
        y=1250,
        font=f(56, bold=True),
        fill=ACCENT2,
    )
    draw_caption(d, ["ถ้าชอบคลิปนี้ อย่าลืมกดไลก์และติดตาม", "เจอกันใหม่คลิปหน้าครับ"])
    return Image.alpha_composite(img, ov).convert("RGB")


scenes = [
    render_scene_1,
    render_scene_2,
    render_scene_3,
    render_scene_4,
    render_scene_5,
    render_scene_6,
]

for i, fn in enumerate(scenes, 1):
    out = f"{OUT}/scene{i}.png"
    fn().save(out, "PNG")
    print("wrote", out)
