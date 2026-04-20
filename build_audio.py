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

LINES = [
    "สวัสดีครับ วันนี้จะมาสอน วิธีทำคลิปโซเชียลแนวตั้ง ด้วยคล็อดดีไซน์ แบบง่าย สวย เสร็จไว",
    "ขั้นตอนที่หนึ่ง บอกคล็อดว่า อยากได้คลิปแบบไหน พิมพ์ไอเดีย ธีม และความยาว",
    "ขั้นตอนที่สอง เลือกอัตราส่วน เก้าต่อสิบหก ให้เหมาะกับ ติ๊กต๊อก รีล และ ชอร์ต",
    "ขั้นตอนที่สาม ใส่เนื้อหา ข้อความบรรยาย เลือกฟอนต์ สี และภาพประกอบ ตามสไตล์ของคุณ",
    "ขั้นตอนที่สี่ กดส่งออกเป็นไฟล์ เอ็มพีสี่ ขนาด หนึ่งพันแปดสิบ คูณ หนึ่งพันเก้าร้อยยี่สิบ",
    "ถ้าชอบคลิปนี้ อย่าลืมกดไลก์ และ กดติดตาม เจอกันใหม่ คลิปหน้าครับ",
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
    tts.tts(text=text, filename=raw, return_type="file")
    d = duration(raw)
    # Slow fast TTS; aim for 6-9s per line but don't stretch more than 2x
    target = 7.5
    ratio = max(0.5, min(2.0, d / target))
    chain = atempo_chain(ratio)
    run(["ffmpeg", "-y", "-i", raw,
         "-af", f"{chain},highpass=f=80,lowpass=f=7500,loudnorm=I=-16:TP=-1.5:LRA=11",
         fit, "-loglevel", "error"])
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
