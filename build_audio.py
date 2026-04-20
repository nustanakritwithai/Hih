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
    "เฮ อยากทำคลิปโซเชียลสวยๆ ใน หนึ่ง นาทีมั้ย วันนี้คล็อดดีไซน์ มาช่วยแล้ว",
    "ขั้นตอนแรก แค่บอกคล็อด ว่าอยากได้คลิปแบบไหน พิมพ์ธีมแล้วรอเลย",
    "สอง เลือกแนวตั้ง เก้าต่อสิบหก เหมาะกับ ติ๊กต๊อก รีล และ ชอร์ต เป๊ะมาก",
    "สาม ใส่ข้อความบรรยาย ฟอนต์ สี ภาพประกอบ สวย ปังในไม่กี่คลิก",
    "สี่ กดส่งออก เป็นไฟล์วิดีโอ แล้วโพสต์ได้เลย ทุกแพลตฟอร์ม",
    "ถ้าชอบ อย่าลืมกดไลก์ กดติดตาม แล้วเจอกัน คลิปหน้าเลยนะ",
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
    # Energetic voice: pitch up ~8%, slightly faster, punchy compression
    target = 6.5
    raw_ratio = max(0.5, min(2.0, d / target))
    rate_ratio = raw_ratio
    tempo_chain = atempo_chain(rate_ratio)
    # Natural pitch (no shift)
    pitch = 1.00
    sr_in = 22050
    sr_up = int(sr_in * pitch)
    af = (
        f"asetrate={sr_up},aresample=44100,atempo={1/pitch:.4f},"
        f"{tempo_chain},"
        "highpass=f=90,"
        "equalizer=f=180:t=q:w=1:g=-2,"
        "equalizer=f=3000:t=q:w=1:g=4,"
        "equalizer=f=6000:t=q:w=1:g=3,"
        "acompressor=threshold=-18dB:ratio=4:attack=5:release=80:makeup=3,"
        "aecho=0.6:0.4:30:0.08,"
        "loudnorm=I=-14:TP=-1:LRA=9"
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
