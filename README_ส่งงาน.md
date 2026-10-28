# DSI463 Assignment 4 — ทีม Anupat Suttilert และ Nongnapat Sunontanum

ผู้จัดทำ: Anupat Suttilert (6624650526), Nongnapat Sunontanum (6624650302)
ใช้รหัสหัวหน้าทีม 6624650526 ในชื่อไฟล์ตามเดิม

งานนี้ประกอบด้วย Task 1–5 และ Bonus A–B ครบ ใช้ข้อมูล MSO สังเคราะห์ตาม handout
ไม่มีการอัปโหลดหรือส่งงานไป Teams อัตโนมัติ

## ไฟล์ที่ส่ง

- `A4_6624650526.ipynb`: notebook พร้อม output ทุก code cell
- `A4_6624650526_brief.pdf`: policy brief ภาษาไทย 2 หน้า
- `ext_data/`: ข้อมูลภายนอกต้นฉบับ ข้อมูลสะอาด แหล่งอ้างอิง และสคริปต์ดาวน์โหลด
- `pilot_baseline_ids.json`: รายชื่อ ID สังเคราะห์ของ cohort นำร่อง ใช้ตรวจซ้ำในอนาคต

โฟลเดอร์ `data/` และไฟล์ handout ที่เกี่ยวข้องบรรจุไว้เพื่อรันซ้ำได้ สคริปต์ `load_data.py` จะล้างและโหลดสาม collection ใหม่ตามพฤติกรรมเดิมของ handout ใช้เฉพาะฐานการบ้านที่ไม่มีงานอื่นปน

## อ่านผลอย่างไร

1. เปิด notebook ไล่จาก setup → Task 1 → Task 2 → Task 3 → Task 4 → field log → targeting → Bonus A → Bonus B
2. ฐานหลักมีผู้สูงอายุ 1,461 คน ไม่พบ WFEL9 243 คน (16.63%); ไม่มี PBAC8 ร่วมด้วย 149 คน
3. เปรียบเทียบครัวเรือนใช้ 1,459 คน เพราะกรอง household removed ออก 2 คน จึงได้กลุ่มมีเลขที่ 205/1,378 ต่างจากตัวเลขสำรวจเดิม
4. จังหวัดนำร่องแม่ฮ่องสอน 43 คน ใน 40 ครัวเรือน งบสมมติ 12,900 บาท
5. สูตร age ตามโจทย์ใช้ `$dateDiff` ปีปฏิทิน หากใช้อายุครบวันเกิดจะเหลือฐาน 1,440 คน ช่องว่าง 223 คน มีตาราง sensitivity ใน notebook
6. ไม่พบรหัสสวัสดิการไม่ใช่หลักฐานว่ามีสิทธิหรือไม่ได้รับเงินจริง ต้องตรวจยืนยันก่อนดำเนินการ

## รันซ้ำด้วย Docker ตาม handout

รันจากโฟลเดอร์ที่มี `data/` และ `load_data.py`:

```powershell
docker compose up -d
python -m pip install -r requirements.txt
python load_data.py
```

เปิด notebook ด้วย Jupyter หรือ VS Code แล้ว Restart Kernel and Run All ค่าเริ่มต้นต่อ MongoDB `mongodb://127.0.0.1:27017` database `mso`
ถ้าใช้ Atlas หรือ MongoDB ที่ port อื่น ตั้ง environment variable `MONGO_URI` ก่อนเริ่ม Jupyter หรือแก้ค่า URI ใน setup

ผลลัพธ์ในชุดส่งฉบับล่าสุดรันใหม่กับ MongoDB 7.0 ใน Docker container `dsi463-mongo` บน localhost:27017 ตาม docker-compose.yml ของ handout แล้ว สามารถอ่าน output ที่บันทึกไว้ได้โดยไม่เปิด Docker แต่ต้องเปิด Docker หากต้องการรันใหม่

ตัวอย่างสร้าง notebook พร้อมรันใหม่กับ Docker:

```powershell
$env:MONGO_URI = 'mongodb://127.0.0.1:27017'
$env:OPENBLAS_NUM_THREADS = '1'
python build_assignment.py
```

`build_assignment.py` สร้าง notebook ใหม่ใน `output/` และรันจากต้นจนจบ ใช้ Python kernel ชื่อ `python3`
Notebook สร้าง/refresh เฉพาะ ext_province_elderly, mso_member_v2 และ index ของการบ้าน โดยไม่แก้เนื้อหา collection ต้นฉบับ
Bonus A ลบและสร้างเฉพาะ index `a4_pilot_esr` ของงานนี้เพื่อวัด before/after ซ้ำ

## แหล่งข้อมูลภายนอก

ผู้เผยแพร่: สำนักงานสถิติแห่งชาติ; ข้อมูลต้นทาง: กรมการปกครอง
ประชากรอายุ 60 ปีขึ้นไปจากทะเบียน จำแนกตามเพศและจังหวัด OS_0405_01_0008_01
Catalog: https://gdcatalog.go.th/dataset/gdpublish-605
API: https://catalogapi.nso.go.th/api/index?table=OS_0405_01_0008_01&format=json
เข้าถึง 28 ตุลาคม 2026; ใช้ปี 2024 เทียบกับ snapshot และปี 2025 เป็นบริบทล่าสุดในไฟล์
ไฟล์ metadata มี SHA256 ของต้นฉบับและวิธีเลือกข้อมูล ใช้เฉพาะ 7 จังหวัดที่มีใน MSO

ดาวน์โหลดใหม่ได้ด้วย `python ext_data/prepare_external.py` แต่ไฟล์ต้นฉบับที่ใช้จริงแนบมาแล้ว จึงไม่จำเป็นต้องพึ่งเครือข่ายขณะรัน notebook
อย่าใช้ประชากรจริงหารข้อมูลสังเคราะห์แล้วอ้างความครอบคลุมจริง หรือคูณอัตราสังเคราะห์เพื่อประมาณปัญหาของจังหวัด

## Bonus ที่ทำแล้ว

- A1: `$facet` สามมุมมอง จังหวัด เพศ และช่วงอายุ โดย match ก่อน facet
- A2: explain executionStats ก่อน/หลัง scalar compound index ตาม ESR; ผลคืนเท่ากันทุกครั้ง ไม่อ้างว่าเวลาเร็วขึ้นหากผลจริงไม่สนับสนุน
- B1–B2: ปัญหาโครงสร้างจาก query จริง, sample JSON จากเอกสารที่ migrate จริง, embed/reference, index, validator และต้นทุนรักษาข้อมูล
- B3: migrate ครบ 7,518 เอกสาร และ Q2 เดิมให้ผลเท่ากันทุกกลุ่ม; stages หลัก 7 → 3 โดยไม่ต้อง lookup ตอนอ่าน

## สร้าง PDF ใหม่

แก้ `build_brief.py` แล้วรัน `python build_brief.py` หลังรัน notebook สำเร็จ ต้องมี Google Chrome ตาม path Windows ที่ระบุในสคริปต์
ผลอยู่ `output/` รวม HTML ต้นฉบับและภาพตรวจหน้า สามารถแก้ HTML แล้ว print เป็น PDF ได้เช่นกัน

## ก่อนส่ง

- อ่าน brief ให้เข้าใจเหตุผลเลือกปัญหาและพื้นที่นำร่อง
- ตรวจชื่อ Anupat Suttilert และรหัส 6624650526
- อัปโหลด notebook, PDF และ ext_data หรือ ZIP นี้ตามช่องทางที่อาจารย์กำหนด
- กำหนดส่ง 29 ตุลาคม 2026 เวลา 23:59 ตามโจทย์
