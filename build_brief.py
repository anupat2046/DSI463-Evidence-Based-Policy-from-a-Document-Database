"""Generate a two-page Thai policy brief from verified notebook results."""
from pathlib import Path
from html import escape
import json
import base64
from playwright.sync_api import sync_playwright
import fitz

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'output'
r = json.loads((OUT/'verified_results.json').read_text(encoding='utf-8'))
assert r['pilot_people'] == 43 and r['gap'] == 243
query = '''from datetime import datetime
target = {
  "province_code": "58", "vital_status": 1,
  "status": {"$ne": "removed"},
  "birthdate": {"$lt": datetime(1965, 1, 1)},
  "$expr": {"$gte": [{"$dateDiff": {
    "startDate": "$birthdate",
    "endDate": datetime(2024, 6, 30),
    "unit": "year"}}, 60]},
  "welf_eldery.code": {"$ne": "WFEL9"}
}
db.mso_member.find(target)'''

font_dir = ROOT/'assets/fonts'
font_rules = '\n'.join(
    "@font-face { font-family:'TH Sarabun New'; font-style:normal; font-weight:" + weight + "; src:url(data:font/ttf;base64," + base64.b64encode((font_dir/name).read_bytes()).decode('ascii') + ") format('truetype'); }"
    for name,weight in [('THSarabunNew.ttf','400'),('THSarabunNewBold.ttf','700')]
)
html = '''<!doctype html><html lang="th"><meta charset="utf-8">
<title>DSI463 | Anupat Suttilert 6624650526 | Nongnapat Sunontanum 6624650302</title>
<style>
@page { size:A4; margin:0; }
* { box-sizing:border-box; }
body { margin:0; color:#000; font-family:'TH Sarabun New',sans-serif; font-size:15.5pt; line-height:1.12; }
.page { width:210mm; height:297mm; padding:14mm 16mm 16mm; position:relative; break-after:page; overflow:hidden; }
.page:last-child { break-after:auto; }
.eyebrow { font-size:12.5pt; letter-spacing:.8px; font-weight:bold; color:#000; }
h1 { font-size:24pt; line-height:1.15; margin:4mm 0 2mm; }
.subtitle { font-size:16pt; color:#000; margin:0 0 3mm; }
.author { font-size:13pt; color:#000; border-bottom:1px solid #000; padding-bottom:3mm; }
h2 { margin:5mm 0 2mm; font-size:18pt; color:#000; }
p { margin:0 0 2.5mm; overflow-wrap:anywhere; }
.banner { padding:2mm 0; margin:3mm 0; }
.metrics { display:flex; gap:3mm; margin:3mm 0; }
.metric { flex:1; padding:2mm; border-top:1px solid #000; }
.number { font-size:24pt; font-weight:bold; line-height:1.1; color:#000; }
.caption { font-size:12.5pt; line-height:1.15; margin-top:2mm; }
table { border-collapse:collapse; width:100%; font-size:14pt; margin:2mm 0; }
td,th { text-align:left; border-bottom:1px solid #000; padding:2mm 2mm; vertical-align:top; }
th { font-weight:bold; }
.small { font-size:12.5pt; line-height:1.15; color:#000; }
pre { border:1px solid #000; padding:3mm; font:12.5pt/1.05 'TH Sarabun New',sans-serif; margin:2mm 0 3mm; white-space:pre-wrap; }
code { font-family:inherit; }
.footer { position:absolute; bottom:9mm; left:16mm; right:16mm; border-top:1px solid #000; padding-top:2mm; display:flex; justify-content:space-between; font-size:12pt; color:#000; }
a { color:#000; text-decoration:none; overflow-wrap:anywhere; }
.source { font-size:11.5pt; line-height:1.1; }
.page:nth-of-type(2) { font-size:14.5pt; }
.page:nth-of-type(2) h2 { font-size:17pt; margin:1.5mm 0 1.5mm; }
.page:nth-of-type(2) p { margin-bottom:2mm; }
.page:nth-of-type(2) .small { font-size:12pt; line-height:1.05; }
.page:nth-of-type(2) pre { padding:2mm 3mm; font-size:12.5pt; line-height:1; }
.page:nth-of-type(2) table { font-size:13.5pt; }
.page:nth-of-type(2) td, .page:nth-of-type(2) th { padding:1.5mm 2mm; }
</style>
<body><section class="page">
<div class="eyebrow">DSI463 · ASSIGNMENT 4 · POLICY BRIEF</div>
<h1>ข้อเสนอนโยบายตรวจสอบและเชื่อมต่อสิทธิ<br>เบี้ยยังชีพผู้สูงอายุ จังหวัดแม่ฮ่องสอน</h1>
<p class="subtitle">เสนอต่อสำนักงานพัฒนาสังคมและความมั่นคงของมนุษย์จังหวัดแม่ฮ่องสอน</p>
<div class="author">Anupat Suttilert · 6624650526<br>Nongnapat Sunontanum · 6624650302 &nbsp;|&nbsp; 29 ตุลาคม 2026</div>
<div class="banner"><b>สาระสำคัญ:</b> ตรวจสอบรายชื่อ 43 คนใน 40 ครัวเรือน ประสานการเข้าถึงสิทธิ และติดตามผลภายใน 6 เดือน โดยใช้งบดำเนินการนำร่อง 12,900 บาทตามสมมติฐานที่ระบุ</div>

<h2>01 &nbsp; นโยบาย: ตรวจสอบ–ส่งต่อ–ติดตาม</h2>
<p>ให้สำนักงาน พมจ.แม่ฮ่องสอนร่วมกับองค์กรปกครองส่วนท้องถิ่นและ อพม. ตรวจสอบผู้สูงอายุที่ยังมีชีวิต ไม่ถูกลบออกจากระบบ และไม่พบบันทึก WFEL9 โดยเริ่มจากรายชื่อใน query หน้า 2 จัดลำดับเยี่ยมบ้านก่อนสำหรับผู้ไม่มีเลขที่บ้านหรืออยู่คนเดียว</p>
<p>ยืนยันข้อมูลการรับเงินและเงื่อนไขสิทธิกับหน่วยงานรับผิดชอบ จากนั้นช่วยลงทะเบียนหรือส่งต่อตามแนวทาง <b>TR47 เบี้ยยังชีพผู้สูงอายุ</b> สำหรับผู้เข้าเงื่อนไข ส่วนผู้ไม่เข้าเงื่อนไขให้ประสานบริการช่วยเหลือที่เหมาะสมและบันทึกผลตรวจสอบ</p>

<h2>02 &nbsp; หลักฐานที่ใช้ตัดสินใจ</h2>
<div class="metrics">
<div class="metric"><div class="number">243 คน</div><div class="caption">ไม่พบบันทึก WFEL9<br>จากผู้สูงอายุ 1,461 คน (<b>16.63%</b>)<br><span class="small">ผลวิเคราะห์ MSO · Q1</span></div></div>
<div class="metric"><div class="number">31.85%</div><div class="caption">แม่ฮ่องสอนไม่พบบันทึก WFEL9<br>43 จาก 135 คน สูงสุดใน 7 จังหวัด<br><span class="small">ผลวิเคราะห์ MSO · Q1/Q6</span></div></div>
<div class="metric"><div class="number">40,031</div><div class="caption">ผู้สูงอายุจากทะเบียนจริง<br>แม่ฮ่องสอน ปี 2024<br><span class="small">NSO/DOPA · Q6</span></div></div>
</div>
<p>ผู้ไม่มีเลขที่บ้านไม่พบบันทึก WFEL9 จำนวน 37/81 คน (45.68%) เทียบกับผู้มีเลขที่ 205/1,378 คน (14.88%) และ 149/243 คนไม่มี PBAC8 บันทึกไว้ด้วย ส่วน 94 คนที่มี PBAC8 มี 35 คนยังไม่มีแผน (37.23%) จึงต้องดำเนินการทั้งค้นหาเคสและเปิดแผนช่วยเหลือ</p>
<p class="small">นิยามกลุ่มเป้าหมาย: สมาชิกมีชีวิต อายุ 60 ปีขึ้นไปตามวันอ้างอิง 30 มิถุนายน 2024 และไม่มีรหัส WFEL9 ใน welf_eldery; ตารางเปรียบเทียบที่อยู่อาศัยใช้ฐาน 1,459 คน หลังตัดผู้เชื่อมกับครัวเรือนที่ถูกลบออก 2 คน</p>

<h2>03 &nbsp; ขอบเขตและต้นทุนดำเนินการ</h2>
<p>ข้อมูล NSO/DOPA ปี 2025 ระบุผู้สูงอายุแม่ฮ่องสอน 41,623 คน เพิ่ม 1,592 คน (+3.98%) จากปี 2024 หากตรวจทุกรายโดยใช้เวลา 1 ชั่วโมงและค่าเดินทาง/ติดต่อ 300 บาทต่อคน จะใช้ <b>41,623 ชั่วโมง และ 12,486,900 บาท</b> จึงกำหนดข้อเสนอเป็นโครงการนำร่องตามรายชื่อ 43 คน ก่อนวางแผนขยายจากทะเบียนจริง</p>
<p>การนำร่อง 43 คน ใน 40 ครัวเรือน ใช้ <b>43 ชั่วโมง และ 12,900 บาท</b> ภายใต้สมมติฐานเดียวกัน ตัวเลขนี้เป็นงบตรวจสอบและประสานงาน ไม่รวมงบจ่ายเบี้ยหรือค่าใช้จ่ายบริหารเพิ่มเติม การตรวจครบทะเบียนเป็นสถานการณ์เทียบขนาดงาน ไม่ใช่จำนวนผู้ตกหล่น</p>

<div class="footer"><span>DSI463 · ข้อเสนอนโยบาย</span><span>1 / 2</span></div>
</section>

<section class="page">
<div class="eyebrow">IMPLEMENTATION · TARGETING & EVALUATION</div>
<h2 style="margin-top:3mm">04 &nbsp; คัดรายชื่อด้วย MongoDB query เดียว</h2>
<p>ใช้กับ <code>mso_member</code> เพื่อสร้างคิวตรวจสอบในจังหวัด 58 ทั้งสองอำเภอ; เจ้าหน้าที่ตรวจเอกสารและสิทธิก่อนดำเนินการ ส่วนการจัดลำดับเยี่ยมบ้านใช้ผล household join ใน Q2</p>
<pre>''' + escape(query) + '''</pre>
<p class="small">เกณฑ์อายุในผลวิเคราะห์ใช้การนับขอบเขตปี ณ 30 มิถุนายน 2024 ตามสูตรโจทย์ สำหรับการปฏิบัติงานให้ตรวจอายุครบวันเกิดและปรับวันอ้างอิงเป็นวันที่ตรวจสอบสิทธิ</p>

<h2>05 &nbsp; วัดผลใน 60 วันและอีก 6 เดือน</h2>
<table><tr><th style="width:30%">เป้าหมายที่เสนอ</th><th>วิธีตรวจสอบ</th></tr>
<tr><td>ยืนยันข้อมูล ≥90%<br>ภายใน 60 วัน</td><td>เก็บผลตรวจสิทธิ เหตุไม่ผ่าน วันที่ยืนยัน และหน่วยงานรับผิดชอบเพิ่ม แยก “ไม่รับ” จาก “ไม่บันทึก”</td></tr>
<tr><td>ลดช่องว่าง ≥50%<br>ในกลุ่มยืนยันว่ามีสิทธิ<br>ภายใน 6 เดือน</td><td>ใช้ baseline IDs เดิม ตรวจ WFEL9 และผลยืนยันการรับจริง พร้อมรายงานผู้ตาย/removed หรือหลุดการติดตามแยกต่างหาก</td></tr>
<tr><td>ติดตามการดำเนินการ</td><td>ดู prob_summary.prob_accessibility.status,<br>plans.sol_code และ activities.act_progression<br>การปิดเคสไม่ใช่หลักฐานว่าจ่ายเงินจริงเสมอ</td></tr></table>
<p class="small">query ที่รันซ้ำ: ใช้ PILOT_IDS ซึ่งเป็นรายชื่อฐานเริ่มต้นที่สร้างไว้ใน notebook</p>
<pre>db.mso_member.count_documents({"_id": {"$in": PILOT_IDS},
  "vital_status": 1, "status": {"$ne": "removed"},
  "welf_eldery.code": {"$ne": "WFEL9"}})</pre>
<p class="small">รายงานจำนวนที่ยังขาดบันทึกในกลุ่มเดิมควบคู่ผลยืนยันการรับเงิน และแยกการเปลี่ยนแปลงสถานะสมาชิกออกจากผลของโครงการ</p>

<h2>06 &nbsp; ข้อจำกัด</h2>
<p class="small">MSO เป็นข้อมูลสังเคราะห์ตามโจทย์ ผลวิเคราะห์จึงไม่ใช่ค่าประมาณประชากรไทย การไม่มี WFEL9 หมายถึงไม่มีบันทึกรหัส ไม่ใช่ผลยืนยันการรับเงินจริง โดย 204 คนไม่มีฟิลด์ welf_eldery และ 39 คนมีเฉพาะสวัสดิการสูงอายุอื่น PBAC8 ครอบคลุมเบี้ยพิการด้วย ต้องตรวจเงื่อนไขสิทธิรายกรณี ข้อมูลทะเบียนเป็นรายปีต่างจาก snapshot กลางปี และบันทึกติดตามที่ว่างจำกัดการอธิบายสาเหตุ</p>

<h2 style="margin-top:3mm">แหล่งข้อมูลและการตรวจซ้ำ</h2>
<div class="source">MSO-Logbook synthetic handout, snapshot 30 มิ.ย. 2024; notebook A4_6624650526: Q1, Q2, Q5, Q6/Q6b และ targeting<br>
NSO, ประชากรอายุ 60 ปีขึ้นไป จากการทะเบียน; ต้นทาง DOPA; ปี 2024 และ 2025; เข้าถึง 28 ต.ค. 2026<br>
<a href="https://gdcatalog.go.th/dataset/gdpublish-605">Catalog: https://gdcatalog.go.th/dataset/gdpublish-605</a><br>
<a href="https://catalogapi.nso.go.th/api/index?table=OS_0405_01_0008_01&format=json">API: https://catalogapi.nso.go.th/api/index?table=OS_0405_01_0008_01&amp;format=json</a><br>
ต้นฉบับ ข้อมูลสะอาด และสคริปต์: ext_data/</div>
<div class="footer"><span>DSI463 · 6624650526 / 6624650302</span><span>2 / 2</span></div>
</section></body></html>'''

html = html.replace('<style>', '<style>\n' + font_rules, 1)
source = OUT/'A4_6624650526_brief.html'
source.write_text(html,encoding='utf-8')
pdf = OUT/'A4_6624650526_brief.pdf'
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True,args=['--disable-gpu','--disable-extensions'])
    page=browser.new_page()
    page.goto(source.as_uri(),wait_until='load')
    page.evaluate('document.fonts.ready')
    assert page.evaluate("document.fonts.check('16px \"TH Sarabun New\"')")
    # Verify that content stays above each fixed footer before printing.
    boxes=page.evaluate('''() => [...document.querySelectorAll('.page')].map(p => {
        const footer=p.querySelector('.footer').getBoundingClientRect();
        const content=[...p.children].filter(x=>!x.classList.contains('footer'));
        return {lastContentBottom:Math.max(...content.map(x=>x.getBoundingClientRect().bottom)),footerTop:footer.top};
    })''')
    print('Layout bounds:', boxes)
    assert all(b['lastContentBottom'] < b['footerTop']-4 for b in boxes), 'Content overlaps footer'
    page.pdf(path=str(pdf),format='A4',print_background=True,prefer_css_page_size=True)
    browser.close()
doc=fitz.open(pdf)
assert len(doc)==2
embedded_fonts = {font[3] for page in doc for font in page.get_fonts()}
assert any('Sarabun' in font for font in embedded_fonts), embedded_fonts
print('Embedded fonts:', sorted(embedded_fonts))
for i,page in enumerate(doc):
    page.get_pixmap(matrix=fitz.Matrix(1.35,1.35)).save(OUT/f'brief_page_{i+1}.png')
text='\n'.join(page.get_text() for page in doc)
assert all(term in text for term in ['Anupat Suttilert','6624650526','Nongnapat Sunontanum','6624650302','12,900','WFEL9'])
(OUT/'brief_extracted.txt').write_text(text,encoding='utf-8')
print('PDF complete:',pdf,'pages:',len(doc))
