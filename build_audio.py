#!/usr/bin/env python3
"""Generate Thai narration with PyThaiTTS lunarlist_onnx (neural Tacotron2)."""
import os, subprocess, sys

MODELS = os.path.join(os.path.dirname(__file__), "models")
AUDIO = os.path.join(os.path.dirname(__file__), "audio")
os.makedirs(AUDIO, exist_ok=True)

import huggingface_hub
def _local(repo_id, filename, **kw):
    p = os.path.join(MODELS, filename)
    if not os.path.exists(p):
        raise FileNotFoundError(p)
    return p
huggingface_hub.hf_hub_download = _local
import pythaitts.pretrained.lunarlist_onnx as llo
llo.hf_hub_download = _local

from pythaitts import TTS
import pythaitts.pretrained.lunarlist_onnx as _llo

_ALLOWED = set(_llo.index_list)


def sanitize(text):
    return "".join(c for c in text if c in _ALLOWED)


LINES = [
    "สวัสดีครับ วันนี้เราจะมาเรียนรู้ วิธีสร้างคลิปโซเชียลแนวตั้ง ด้วยคล็อดดีไซน์ อย่างถูกวิธี",
    "ขั้นตอนแรก ระบุสิ่งที่ต้องการ กับคล็อดให้ชัดเจน ทั้งธีม เนื้อหา และความยาวที่ต้องการ",
    "ขั้นตอนที่สอง กำหนดอัตราส่วนภาพ เป็นเก้าต่อสิบหก ซึ่งเหมาะกับการแสดงผล บนแพลตฟอร์มโซเชียล",
    "ขั้นตอนที่สาม ปรับแต่งองค์ประกอบ ทั้งข้อความ ฟอนต์ สี และภาพประกอบ ให้สอดคล้องกับเนื้อหา",
    "ขั้นตอนที่สี่ ส่งออกผลงานเป็นไฟล์วิดีโอ เพื่อใช้เผยแพร่บนแพลตฟอร์มต่างๆ",
    "หากท่านเห็นว่าข้อมูลนี้ มีประโยชน์ ขอเชิญติดตามเพื่อรับเนื้อหา ในลำดับต่อไปครับ",
]


def run(cmd):
    subprocess.run(cmd, check=True, capture_output=True)


def duration(path):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", path],
        capture_output=True, text=True, check=True,
    )
    return float(r.stdout.strip())


def atempo_chain(ratio):
    filters = []
    while ratio > 2.0:
        filters.append("atempo=2.0")
        ratio /= 2.0
    while ratio < 0.5:
        filters.append("atempo=0.5")
        ratio /= 0.5
    filters.append(f"atempo={ratio:.4f}")
    return ",".join(filters)


tts = TTS(pretrained="lunarlist_onnx")

for i, text in enumerate(LINES, 1):
    raw = f"{AUDIO}/raw{i}.wav"
    fit = f"{AUDIO}/fit{i}.wav"
    tts.tts(text=sanitize(text), filename=raw, return_type="file")
    d = duration(raw)
    # Educational tone at natural pace; only speed up if too long, never stretch
    target = 6.0
    raw_ratio = max(1.0, min(2.0, d / target))
    tempo_chain = atempo_chain(raw_ratio)
    # Slightly lower pitch (~3%) for gravitas, warm low-mid, crisp sibilance
    pitch = 0.97
    sr_in = 22050
    sr_up = int(sr_in * pitch)
    af = (
        f"asetrate={sr_up},aresample=44100,atempo={1/pitch:.4f},"
        f"{tempo_chain},"
        "highpass=f=70,lowpass=f=10000,"
        "equalizer=f=250:t=q:w=1:g=1.5,"
        "equalizer=f=500:t=q:w=1:g=-1,"
        "equalizer=f=2800:t=q:w=1.2:g=2.5,"
        "equalizer=f=6500:t=q:w=1.4:g=1.5,"
        "acompressor=threshold=-22dB:ratio=2.5:attack=8:release=180:makeup=2,"
        "loudnorm=I=-16:TP=-1.5:LRA=10"
    )
    run(["ffmpeg", "-y", "-i", raw, "-af", af, fit, "-loglevel", "error"])
    print(f"line{i}: {d:.2f}s -> {duration(fit):.2f}s")

# Combine on 60s timeline: each scene starts at n*10s + 0.3s padding
inputs = []
for i in range(1, 7):
    inputs += ["-i", f"{AUDIO}/fit{i}.wav"]

parts = []
for i in range(6):
    delay = i * 10_000 + 300
    parts.append(f"[{i}:a]adelay={delay}|{delay},apad[a{i}]")
mix_in = "".join(f"[a{i}]" for i in range(6))
parts.append(
    f"{mix_in}amix=inputs=6:normalize=0,volume=1.3,"
    f"atrim=0:60,asetpts=PTS-STARTPTS[aout]"
)
fc = ";".join(parts)

run([
    "ffmpeg", "-y", *inputs,
    "-filter_complex", fc, "-map", "[aout]",
    "-c:a", "pcm_s16le", "-ar", "44100",
    f"{AUDIO}/voice.wav", "-loglevel", "error",
])
print("voice.wav:", duration(f"{AUDIO}/voice.wav"), "s")

# Mux with silent video
run([
    "ffmpeg", "-y", "-i", "clip_silent.mp4", "-i", f"{AUDIO}/voice.wav",
    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
    "-shortest", "-movflags", "+faststart",
    "clip.mp4", "-loglevel", "error",
])
print("clip.mp4:", duration("clip.mp4"), "s")
