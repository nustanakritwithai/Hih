#!/bin/bash
# Regenerate Thai narration with clearer phonetic spelling + audio polish
set -e
cd /home/user/Hih
mkdir -p audio

# Phonetic Thai — English brand names spelled in Thai, spacing added to help espeak
declare -a LINES=(
  "สะ วัด ดี คับ วัน นี้ จะ มา สอน วิ ธี ทำ คลิป โซ เชี่ยล แนว ตั้ง ด้วย คล็อด ดี ไซน์ แบบ ง่าย สะ ดวก เสร็จ ไว"
  "ขั้น ตอน ที่ หนึ่ง บอก คล็อด ว่า อยาก ได้ คลิป แบบ ไหน พิมพ์ ไอ เดีย และ ความ ยาว เช่น คลิป เก้า ต่อ สิบ หก สอน ทำ อา หาร หนึ่ง นา ที"
  "ขั้น ตอน ที่ สอง เลือก อัด ตรา ส่วน เก้า ต่อ สิบ หก เพื่อ ให้ คลิป พอ ดี กับ ติ๊ก ต๊อก รีล และ ชอร์ต"
  "ขั้น ตอน ที่ สาม ใส่ เนื้อ หา ข้อ ความ บัน ยาย เลือก ฟ้อน สี และ ภาพ ประ กอบ ให้ ตรง กับ สะ ไตล์ ของ คุณ"
  "ขั้น ตอน ที่ สี่ กด ส่ง ออก เป็น ไฟล์ เอ็ม พี สี่ ขะ หนาด หนึ่ง พัน แปด สิบ คูณ หนึ่ง พัน เก้า ร้อย ยี่ สิบ แล้ว นำ ไป โพสต์ ได้ ทุก แพลต ฟอร์ม"
  "ถ้า ชอบ คลิป นี้ อย่า ลืม กด ไล้ก์ และ กด ติด ตาม เพื่อ ดู เท็ค นิค เพิ่ม เติม เจอ กัน ใหม่ คลิป หน้า คับ"
)

for i in "${!LINES[@]}"; do
  idx=$((i+1))
  # Slower rate (130), higher pitch (55), louder, more gap
  espeak-ng -v th -s 130 -p 55 -a 200 -g 5 -k 10 "${LINES[$i]}" -w "audio/raw${idx}.wav"
  # Polish: mild low-pass + high-pass for voice band + subtle reverb + normalize
  ffmpeg -y -i "audio/raw${idx}.wav" -af "highpass=f=120,lowpass=f=4800,aecho=0.6:0.5:40:0.15,loudnorm=I=-16:TP=-1.5:LRA=11" "audio/line${idx}.wav" -loglevel error
  dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 audio/line${idx}.wav)
  echo "line${idx}: ${dur}s"
done
