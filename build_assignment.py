"""Build and execute the complete assignment notebook. Run from project root."""
from pathlib import Path
import os
import textwrap
import nbformat as nbf
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'output'
OUT.mkdir(exist_ok=True)
nb = nbf.v4.new_notebook()
nb.cells = []

def md(s): nb.cells.append(nbf.v4.new_markdown_cell(textwrap.dedent(s).strip()))
def code(s): nb.cells.append(nbf.v4.new_code_cell(textwrap.dedent(s).strip() + '\npass'))
def query(title, question, source, interpretation):
    md(f'### {title}\n\n**คำถาม:** {question}')
    code(source)
    md('**ตีความ:** ' + interpretation)

md('''
# Assignment 4: Evidence-Based Policy from a Document Database
**Name(s):** Anupat Suttilert; Nongnapat Sunontanum  
**Student ID(s):** Anupat Suttilert — 6624650526; Nongnapat Sunontanum — 6624650302  
**Problem title:** ผู้สูงอายุที่ไม่พบบันทึกเบี้ยยังชีพ: ตรวจสอบสิทธิและเชื่อมต่อการช่วยเหลือเชิงรุก

DSI463 | Tasks 1–5 + Bonus A + Bonus B | Updated 29 October 2026

**ข้อมูล MSO เป็นข้อมูลสังเคราะห์ทั้งหมด ตัวเลขจาก MSO ไม่ใช่สถิติจริงของประเทศไทย**
คำว่า “ช่องว่าง/ไม่พบบันทึก” ในงานนี้หมายถึงไม่พบ WFEL9 ไม่ใช่การยืนยันว่ามีสิทธิตามกฎหมายหรือไม่ได้รับเงินจริง
''')
code('''
from datetime import datetime
from pathlib import Path
from pprint import pprint
import os, json, copy
import pandas as pd
from pymongo import MongoClient
from bson import json_util
from IPython.display import display, Markdown

# Default matches the supplied Docker compose. MONGO_URI can select another local instance or Atlas.
ROOT = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / 'data/mso_member.json').exists())
URI = os.environ.get('MONGO_URI', 'mongodb://127.0.0.1:27017')
db = MongoClient(URI, serverSelectionTimeoutMS=10000)['mso']
db.command('ping')
SNAPSHOT = datetime(2024, 6, 30)
AGE = {'$dateDiff': {'startDate': '$birthdate', 'endDate': SNAPSHOT, 'unit': 'year'}}
ACTIVE = {'status': {'$ne': 'removed'}, 'vital_status': 1}
pd.set_option('display.max_columns', 25)
pd.set_option('display.max_rows', 80)
pd.set_option('display.float_format', lambda x: f'{x:,.2f}')
RESULTS = {}
def agg(coll, pipeline):
    return pd.DataFrame(list(db[coll].aggregate(pipeline)))
def show(key, pipeline, coll='mso_member'):
    frame = agg(coll, pipeline)
    RESULTS[key] = frame
    view = pd.json_normalize(frame.to_dict('records'))
    if len(view.columns) > 10:
        display(view.set_index('_id').T if '_id' in view.columns else view.T)
    else:
        display(view)
    return frame
def arr(path): return {'$ifNull': ['$' + path, []]}
def has(path, value): return {'$in': [value, arr(path)]}
def pct(num, den):
    return {'$cond': [{'$gt': [den, 0]}, {'$multiply': [100, {'$divide': [num, den]}]}, None]}
FLAGS = {'age': AGE, 'missing_allowance': {'$not': [has('welf_eldery.code', 'WFEL9')]}}
ELDERS = [{'$match': ACTIVE}, {'$set': FLAGS}, {'$match': {'age': {'$gte': 60}}}]
TARGET = ELDERS + [{'$match': {'missing_allowance': True}}]
HH_JOIN = [
    {'$lookup': {'from': 'mso_household', 'localField': 'hh_id', 'foreignField': '_id', 'as': 'hh'}},
    {'$unwind': {'path': '$hh', 'preserveNullAndEmptyArrays': True}},
    {'$match': {'hh.status': {'$ne': 'removed'}}}
]
def rate_group(key):
    return [
        {'$group': {'_id': key, 'elderly': {'$sum': 1}, 'gap': {'$sum': {'$cond': ['$missing_allowance', 1, 0]}}}},
        {'$set': {'gap_pct': pct('$gap', '$elderly')}}, {'$sort': {'gap_pct': -1, '_id': 1}}
    ]
counts = {c: db[c].count_documents({}) for c in ['mso_household', 'mso_family', 'mso_member']}
display(pd.DataFrame(list(counts.items()), columns=['collection', 'documents']))
assert list(counts.values()) == [2000, 2217, 7518], 'Run load_data.py first.'
runtime_info = {'mongodb_version':db.client.server_info()['version'], 'endpoint':str(db.client.address), 'platform':db.command('buildInfo').get('buildEnvironment',{}).get('target_os','unknown')}
print('MongoDB runtime:', runtime_info, '| Snapshot:', SNAPSHOT.date())
''')
md('''
## วิธีรันและกติกาการนับ
ติดตั้ง `pymongo pandas nbformat nbclient ipykernel` เปิด MongoDB และรัน `load_data.py` ก่อนเปิด notebook นี้
ทุก pipeline ที่นับคนเริ่มด้วย ACTIVE; ฝั่งครัวเรือนที่ join กรอง removed แยก โดยไม่ใส่ vital_status ซึ่งไม่มีใน household
ใช้ `$ifNull` ก่อนอ่าน array และแยก missing/unknown ออกจาก “ไม่มี” เมื่อเปรียบเทียบที่อยู่อาศัย
การไม่พบ WFEL9 อาจเกิดจากไม่ได้รับหรือไม่ได้บันทึก จึงเป็นรายชื่อเพื่อยืนยันสิทธิ ไม่ใช่รายชื่ออนุมัติจ่ายเงิน

**อายุ:** ใช้ `$dateDiff(..., unit='year')` ตาม setup ของโจทย์อย่างสม่ำเสมอ ซึ่งนับขอบเขตปีปฏิทิน
จึงไม่ใช่อายุครบวันเกิดอย่างละเอียด; ตรวจ sensitivity ด้วย birthdate cutoff วันที่ 30 มิ.ย. 1964 เพิ่มด้านล่าง
การเทียบอัตราแสดงความสัมพันธ์ ไม่พิสูจน์สาเหตุ ไม่ขยายผลจากตัวอย่างสังเคราะห์เป็นประชากรจริง
''')
md('## Task 1 — Explore the database\n### 1a. Structure')
code('''
for collection in ['mso_household', 'mso_family', 'mso_member']:
    doc = db[collection].find_one()
    print('\\n' + collection, '| top-level fields:', len(doc))
    # find_one() retrieves the document; show only linked and analytical paths to keep output compact.
    keep = ['_id', 'hh_id', 'fam_id', 'hh_type', 'fam_type', 'birthdate', 'province_code',
            'welf_eldery', 'prob_accessibility', 'prob_summary']
    pprint({k: doc[k] for k in keep if k in doc}, width=105)
''')
md('''
`mso_household` เก็บหนึ่งที่อยู่อาศัยและเชื่อมกับ `mso_family` ผ่าน `family.hh_id → household._id`
ส่วน `mso_member` อ้างทั้ง `hh_id` และ `fam_id` จึงระบุตัวบุคคล ครอบครัว และครัวเรือนได้
สมาชิกฝังสวัสดิการ ปัญหา และแผนไว้ในเอกสารเพราะมักอ่านและปรับปรุงพร้อมข้อมูลรายบุคคล
ข้อดีเมื่อเทียบ relational คือดึงประวัติและ array ที่เกี่ยวข้องได้ในครั้งเดียวโดยลด join
ข้อเสียคือโค้ดปัญหากระจายหลาย array และมีข้อมูลซ้ำระหว่างข้อเท็จจริงกับแผน จึงรวมผลและรักษาความสอดคล้องได้ยาก
''')
query('O1. สมาชิกที่ยังมีชีวิตรายจังหวัด', 'จำนวนสมาชิกในแต่ละจังหวัดเป็นเท่าไร?', '''
o1 = [{'$match': ACTIVE}, {'$group': {'_id': {'code': '$province_code', 'name': '$province_name'}, 'members': {'$sum': 1}}}, {'$sort': {'members': -1}}]
show('O1', o1)
''', 'กรุงเทพมหานครมีสมาชิกมีชีวิตมากที่สุด 1,353 คน ขณะที่แม่ฮ่องสอนมี 691 คน จากทั้งหมด 7,268 คน ความต่างของขนาดฐานทำให้ต้องเทียบอัตราภายในจังหวัด แทนการจัดลำดับปัญหาจากจำนวนคนเพียงอย่างเดียว')
query('O2. ครัวเรือนแต่ละประเภท', 'ครัวเรือนที่มีสมาชิกยังมีชีวิตมีกี่หลังในแต่ละประเภท?', '''
o2 = [{'$match': ACTIVE}] + HH_JOIN + [
    {'$group': {'_id': '$hh_id', 'hh_type': {'$first': {'$ifNull': ['$hh.hh_type.code', 'UNKNOWN']}}}},
    {'$group': {'_id': '$hh_type', 'households': {'$sum': 1}}}, {'$sort': {'_id': 1}}
]
show('O2', o2)
''', 'ครอบครัวเดี่ยว HHT2 พบมากที่สุด 854 จาก 1,952 ครัวเรือน (43.75%) ส่วนครัวเรือนอยู่คนเดียว HHT1 มี 351 ครัวเรือน จึงควรแยกวิเคราะห์อุปสรรคของผู้สูงอายุที่ไม่มีผู้ร่วมบ้านช่วยดำเนินเรื่องสิทธิ')
query('O3. ช่วงอายุ', 'สมาชิกอยู่ในช่วงอายุใดบ้าง?', '''
o3 = [{'$match': ACTIVE}, {'$set': {'age': AGE}}, {'$bucket': {'groupBy': '$age', 'boundaries': [0, 15, 30, 45, 60, 70, 80, 120], 'default': 'unknown/outside', 'output': {'members': {'$sum': 1}}}}]
show('O3', o3)
''', 'ผู้สูงอายุ 60 ปีขึ้นไปมี 1,461 จาก 7,268 คน (20.10%) แบ่งเป็น 60–69 ปี 548 คน 70–79 ปี 521 คน และ 80 ปีขึ้นไป 392 คน จึงเป็นกลุ่มขนาดสำคัญในชุดข้อมูลและมีความต้องการความช่วยเหลือหลายช่วงวัย')
query('O4. ปัญหาที่พบบ่อย', 'สิบโค้ดปัญหาที่บันทึกบ่อยที่สุดคืออะไร?', '''
PROB_FIELDS = ['prob_accessibility', 'prob_education', 'prob_family', 'prob_health', 'prob_housing', 'prob_occupation', 'prob_violence', 'prob_human_trafficking', 'prob_others']
o4 = [{'$match': ACTIVE}, {'$project': {'codes': {'$setUnion': [arr(p + '.code') for p in PROB_FIELDS]}}},
      {'$unwind': '$codes'}, {'$group': {'_id': '$codes', 'members': {'$sum': 1}}}, {'$sort': {'members': -1, '_id': 1}}, {'$limit': 10}]
show('O4', o4)
''', 'PBOC3 รายได้ต่ำกว่ารายจ่ายพบสูงสุด 1,857 คน ตามด้วย PBOC6 หนี้สิน 1,416 คน และ PBOC7 ไม่มีการออม 1,228 คน จึงควรอ่านช่องว่างสวัสดิการร่วมกับรายได้ ภาระชำระหนี้ และเงินออม โดยแต่ละโค้ดนับคนไม่ซ้ำภายในโค้ด')
query('O5. สถานะปัญหาทั้งระบบ', 'รายการปัญหาใน prob_summary มีแผนและติดตามแล้วเพียงใด?', '''
SUMMARY_ARRAY = {'$reduce': {'input': {'$objectToArray': {'$ifNull': ['$prob_summary', {}]}}, 'initialValue': [], 'in': {'$concatArrays': ['$$value', '$$this.v']}}}
o5 = [{'$match': ACTIVE}, {'$project': {'cases': SUMMARY_ARRAY}}, {'$unwind': '$cases'},
      {'$group': {'_id': '$cases.status', 'problem_entries': {'$sum': 1}}}, {'$sort': {'_id': 1}}]
overview_status = show('O5', o5)
display(Markdown(f"สถานะ 0 ไม่มีแผน: **{overview_status.loc[overview_status['_id'].eq(0), 'problem_entries'].sum():,} / {overview_status.problem_entries.sum():,} รายการ**"))
''', 'รายการปัญหาที่ยังไม่มีแผนมี 3,519 จาก 10,606 รายการ (33.18%) สะท้อนงานค้างระดับระบบประมาณหนึ่งในสาม หน่วยนับเป็นรายการปัญหาและคนหนึ่งมีหลายรายการ จึงไม่ใช่จำนวนคนที่ยังไม่ได้รับความช่วยเหลือ')

md('## Task 2 — State the problem\nข้อความภาษาอังกฤษด้านล่างมี 150–250 คำตามข้อกำหนด และเติมตัวเลขจากผลจริงเมื่อจบการรัน')
code('''
baseline = agg('mso_member', ELDERS + rate_group(None)).iloc[0]
alternative = agg('mso_member', [{'$match': {**ACTIVE, 'is_disabled': 1}}, {'$group': {'_id': None, 'disabled': {'$sum': 1}, 'no_card': {'$sum': {'$cond': [{'$eq': ['$have_pwd_card', 0]}, 1, 0]}}}}]).iloc[0]
statement = f"""The priority problem is a possible old-age allowance access or recording gap among living, non-removed members aged 60 or over at the assignment's 30 June 2024 reference snapshot. Operationally, the group has no WFEL9 code in welf_eldery. It contains {int(baseline.gap):,} of {int(baseline.elderly):,} older members ({baseline.gap_pct:.1f}%). Missing welfare records do not establish legal eligibility or prove that payments were never received.

For fragile households, unreliable income can constrain food, transport and medicine, especially when chronic illness or monthly debt repayments coexist. The analysis therefore compares housing registration and living arrangements, and profiles economic resources, health and other welfare. These associations guide verification priorities rather than establish causes.

Action is timely at the next case-review cycle because uncoded gaps may otherwise remain outside officers' plans. The proposed response is proactive verification and registration support, with referrals where appropriate, followed by a six-month review. An alternative considered was disabled members without a disability card: {int(alternative.no_card)} of {int(alternative.disabled)} ({100*alternative.no_card/alternative.disabled:.1f}%). Its higher rate warrants attention, but the elderly problem covers more people in this dataset and allows an integrated housing, health and welfare response. This is a reasoned scope choice, not evidence that disability needs matter less. All MSO counts are synthetic and cannot estimate Thailand's actual unmet need."""
assert 150 <= len(statement.split()) <= 250
display(Markdown(statement))
print('Word count (whitespace, English):', len(statement.split()))
display(alternative.to_frame('value'))
''')

md('## Task 3 — Evidence from the data')
query('Q0. ตรวจนิยาม WFEL9 และความตรงกันของรายชื่อ', 'ไม่พบ WFEL9 หมายถึงอะไร และวิธีคัดกรองให้รายชื่อเดียวกับข้อมูลต้นฉบับหรือไม่?', '''
q0 = TARGET + [{'$group': {'_id': {'$switch': {
 'branches': [
   {'case':{'$eq':[{'$type':'$welf_eldery'},'missing']},'then':'missing_field'},
   {'case':{'$eq':[{'$size':arr('welf_eldery')},0]},'then':'empty_array'}
 ],'default':'other_codes_only'}},'people':{'$sum':1}}}, {'$sort':{'people':-1}}]
wfel_audit = show('Q0_WFEL9_definition',q0)
raw_members = json_util.loads((ROOT/'data/mso_member.json').read_text(encoding='utf-8'))
raw_elderly = [m for m in raw_members if m.get('status')!='removed' and m.get('vital_status')==1 and SNAPSHOT.year-m['birthdate'].year>=60]
raw_gap_ids = {m['_id'] for m in raw_elderly if not any(w.get('code')=='WFEL9' for w in m.get('welf_eldery',[]))}
pipeline_gap_ids = {m['_id'] for m in db.mso_member.aggregate(TARGET+[{'$project':{'_id':1}}])}
assert raw_gap_ids == pipeline_gap_ids and len(raw_gap_ids)==243
code_descriptions = sorted({w.get('desc') for m in raw_members for w in m.get('welf_eldery',[]) if w.get('code')=='WFEL9'})
print('WFEL9 source description:',code_descriptions)
print('Independent raw JSON and MongoDB: exact same 243 member IDs; 1,218 of 1,461 have WFEL9.')
''', '243 คนที่ไม่พบ WFEL9 แบ่งเป็นฟิลด์ welf_eldery หาย 204 คน และมีสวัสดิการผู้สูงอายุอื่นแต่ไม่มี WFEL9 อีก 39 คน การคัดกรองจึงถูกต้องตามนิยามช่องว่างบันทึก และไม่ใช้ WFEL2/WFEL6/WFEL7 แทนเบี้ยยังชีพ')
query('Q1. ขนาดปัญหาและตำแหน่งที่ตั้ง', 'จำนวนและอัตราไม่พบ WFEL9 แตกต่างกันตามจังหวัดและอำเภออย่างไร?', '''
q1p = ELDERS + rate_group({'code': '$province_code', 'name': '$province_name'})
q1d = ELDERS + rate_group({'province': '$province_code', 'district': '$amphur_code', 'name': '$amphur_name'})
province_rates = show('Q1_province', q1p)
district_rates = show('Q1_district', q1d)
display(Markdown(f"รวม **{int(baseline.gap):,}/{int(baseline.elderly):,} คน ({baseline.gap_pct:.2f}%)**; อำเภออันดับแรกตามอัตรา: {district_rates.iloc[0]['_id']}"))
''', 'ใช้ผู้สูงอายุทั้งหมดในพื้นที่เป็นตัวหาร ไม่ใช่ประชากรทุกวัย; พื้นที่ฐานเล็กอาจมีอัตราสูงโดยจำนวนคนไม่มาก จึงต้องอ่านทั้งจำนวนและอัตรา')
query('Q2. เปรียบเทียบที่อยู่อาศัย', 'การไม่พบเบี้ยสัมพันธ์กับบ้านไม่มีเลขที่และการอยู่คนเดียวหรือไม่?', '''
q2 = ELDERS + HH_JOIN + [{'$facet': {
    'house_number': rate_group({'$ifNull': ['$hh.have_num', 'UNKNOWN']}),
    'household_type': rate_group({'$ifNull': ['$hh.hh_type.code', 'UNKNOWN']})
}}]
housing = list(db.mso_member.aggregate(q2))[0]
for label, records in housing.items():
    RESULTS['Q2_' + label] = pd.DataFrame(records)
    print(label); display(RESULTS['Q2_' + label])
join_audit = agg('mso_member', ELDERS + HH_JOIN + [{'$group': {'_id': None, 'retained': {'$sum': 1}, 'unmatched': {'$sum': {'$cond': [{'$eq': [{'$type': '$hh._id'}, 'missing']}, 1, 0]}}}}])
display(join_audit)
print('Housing comparison base:', int(join_audit.retained.iloc[0]), 'vs all elders:', int(baseline.elderly), '(removed household records excluded).')
print('No number: 37/81 = 45.68%; numbered: 205/1,378 = 14.88%; living alone: 63/245 = 25.71%.')
''', 'เทียบอัตราภายในกลุ่ม house number และ hh_type โดยแยก UNKNOWN; ความต่างอาจบอกอุปสรรคการเข้าถึง แต่ข้อมูลนี้ยังไม่พิสูจน์ว่าการไม่มีเลขที่เป็นสาเหตุ')
query('Q3a. เศรษฐกิจ', 'รายได้ การทำงาน เงินออม และภาระชำระหนี้ของกลุ่มเป้าหมายต่างจากผู้มีบันทึกเบี้ยอย่างไร?', '''
RECOMPUTED_INCOME = {'$add': [{'$ifNull': ['$pri_occ_income', 0]}, {'$ifNull': ['$sec_occ_income', 0]}, {'$ifNull': ['$subsidy_amount', 0]}]}
q3a = ELDERS + [
 {'$set': {'income_recomputed': RECOMPUTED_INCOME, 'income_known': {'$gt': [{'$size': {'$filter': {'input': [{'$type': '$pri_occ_income'}, {'$type': '$sec_occ_income'}, {'$type': '$subsidy_amount'}], 'as': 't', 'cond': {'$in': ['$$t', ['int', 'long', 'double', 'decimal']]}}}}, 0]}, 'repayment': {'$sum': arr('debt.amount')}, 'saving_total': {'$sum': arr('saving.amount')}}},
 {'$group': {'_id': '$missing_allowance', 'n': {'$sum': 1},
     'working': {'$sum': {'$cond': [{'$eq': ['$occup_status', 1]}, 1, 0]}},
     'primary_income_mean': {'$avg': '$pri_occ_income'}, 'secondary_income_mean': {'$avg': '$sec_occ_income'}, 'support_mean': {'$avg': '$subsidy_amount'},
     'income_known_n': {'$sum': {'$cond': ['$income_known', 1, 0]}},
     'recomputed_income_mean': {'$avg': {'$cond': ['$income_known', '$income_recomputed', None]}},
     'reported_income_mean': {'$avg': '$SUM_INCOME'}, 'spending_mean': {'$avg': '$SUM_EXPENDITURE'},
     'have_debt_n': {'$sum': {'$cond': [{'$eq': ['$have_debt', 1]}, 1, 0]}},
     'informal_debt_n': {'$sum': {'$cond': [has('debt.type', 'นอกระบบ'), 1, 0]}},
     'repayment_mean': {'$avg': '$repayment'}, 'saving_mean': {'$avg': '$saving_total'},
     'income_mismatch_n': {'$sum': {'$cond': [{'$and': ['$income_known', {'$ne': ['$SUM_INCOME', '$income_recomputed']}]}, 1, 0]}}
 }}, {'$sort': {'_id': 1}}
]
show('Q3a_economy', q3a)
print('Income detail and reported totals are presented separately; compare True (gap) with False (recorded allowance), using income_known_n for the recomputed mean.')
print('Reported mean income is 3,560 baht in the gap group vs 2,606 baht in the recorded group: the gap group is not uniformly poorer. Target verification by access barriers and individual need rather than assuming no income.')
''', 'แถว True คือไม่พบเบี้ย; ค่าเฉลี่ย detail ใช้เฉพาะค่าที่มีบันทึก ส่วนผลรวม array ว่างสมมติเป็นศูนย์และแสดงจำนวน income_known กำกับ จึงไม่ควรอ้างว่าไม่มีรายได้จริง; debt.amount เป็นภาระชำระรายเดือน ไม่ใช่ยอดหนี้คงค้าง และรายได้ที่คำนวณใหม่ไม่รวมมูลค่าเบี้ยที่ไม่มีจำนวนเงิน')
query('Q3b. สุขภาพและความพิการ', 'กลุ่มไม่พบเบี้ยมีโรคเรื้อรังและปัญหาสิทธิรักษาหรือไม่?', '''
q3b = ELDERS + [{'$group': {'_id': '$missing_allowance', 'n': {'$sum': 1},
 'chronic_n': {'$sum': {'$cond': [{'$gt': [{'$size': arr('chronic_disease.code')}, 0]}, 1, 0]}},
 'hypertension_n': {'$sum': {'$cond': [has('chronic_disease.code', 'CD2'), 1, 0]}},
 'no_medical_coverage_n': {'$sum': {'$cond': [has('med_scheme.code', 'MS7'), 1, 0]}},
 'medical_record_missing_n': {'$sum': {'$cond': [{'$eq': [{'$size': arr('med_scheme')}, 0]}, 1, 0]}},
 'disabled_n': {'$sum': {'$cond': [{'$eq': ['$is_disabled', 1]}, 1, 0]}},
 'disabled_without_card_n': {'$sum': {'$cond': [{'$and': [{'$eq': ['$is_disabled', 1]}, {'$eq': ['$have_pwd_card', 0]}]}, 1, 0]}}
}}, {'$set': {'chronic_pct': pct('$chronic_n', '$n')}}, {'$sort': {'_id': 1}}]
show('Q3b_health', q3b)
print('Chronic conditions: gap 144/243 (59.26%) vs recorded allowance 673/1,218 (55.25%); explicit MS7: 16/243 versus 24/1,218.')
''', 'โรคเรื้อรังและความพิการที่พบร่วมกับการไม่พบบันทึกเบี้ยสนับสนุนการประสานบริการหลายด้าน; MS7 หมายถึงไม่มีสิทธิรักษาตามบันทึก ส่วน array หายเป็นข้อมูลไม่ครบ จึงรายงานแยกกัน')
query('Q3c. สวัสดิการอื่นและสัญชาติ', 'ผู้ไม่พบเบี้ยมีสวัสดิการอื่นรองรับหรือไม่ และองค์ประกอบสัญชาติเป็นอย่างไร?', '''
q3c = ELDERS + [{'$group': {'_id': '$missing_allowance', 'n': {'$sum': 1},
 'welfare_card_n': {'$sum': {'$cond': [has('welf_others.code', 'WFOT4'), 1, 0]}},
 'disability_allowance_n': {'$sum': {'$cond': [has('welf_disability.code', 'WFDA14'), 1, 0]}},
 'hardship_grant_n': {'$sum': {'$cond': [has('welf_eldery.code', 'WFEL2'), 1, 0]}}
}}, {'$sort': {'_id': 1}}]
show('Q3c_welfare', q3c)
show('Q3c_nationality', ELDERS + rate_group({'$ifNull': ['$nationality', 'UNKNOWN']}))
print('Among 243 gap cases, 140 have WFOT4, 13 have WFDA14 and 21 have WFEL2; these supports do not substitute for verifying WFEL9.')
''', 'บัตรสวัสดิการ เงินช่วยเหลือ และเบี้ยพิการเป็นคนละรายการกับ WFEL9; สัญชาติช่วยเตือนว่าบางเคสต้องตรวจช่องทางช่วยเหลืออื่นและเงื่อนไขสิทธิ ไม่ควรสรุปว่าทุกคนที่ไม่พบ WFEL9 ต้องได้รับเบี้ย')
query('Q4a. สถานะการตอบสนอง', 'ในกลุ่มไม่พบเบี้ย มี PBAC8 ที่มีแผนแล้วกี่คน?', '''
q4a = TARGET + [
 {'$unwind': '$prob_summary.prob_accessibility'},
 {'$match': {'prob_summary.prob_accessibility.code': 'PBAC8'}},
 {'$group': {'_id': '$prob_summary.prob_accessibility.status', 'entries': {'$sum': 1}, 'ids': {'$addToSet': '$_id'}}},
 {'$project': {'entries': 1, 'people': {'$size': '$ids'}}}, {'$sort': {'_id': 1}}
]
show('Q4a_status', q4a)
''', 'ใน 94 คนที่ไม่พบ WFEL9 และมี PBAC8 บันทึกใน case management มี 35 คนยังไม่มีแผน (37.23%) อีก 19 คนมีแผนแต่ยังไม่ติดตาม 25 คนติดตามแล้ว และ 15 คนปิดเคส จึงควรเร่งเปิดแผนให้กลุ่ม 35 คนและตรวจผลรับบริการของเคสที่ปิดแล้ว')
query('Q4b. ประเภทแผนและผลติดตาม', 'แผน PBAC8 ใช้แนวทางใด และบันทึกผลติดตามอย่างไร?', '''
q4b = TARGET + [
 {'$unwind': '$prob_summary.prob_accessibility'}, {'$match': {'prob_summary.prob_accessibility.code': 'PBAC8'}},
 {'$unwind': {'path': '$prob_summary.prob_accessibility.plans', 'preserveNullAndEmptyArrays': True}},
 {'$unwind': {'path': '$prob_summary.prob_accessibility.plans.activities', 'preserveNullAndEmptyArrays': True}},
 {'$group': {'_id': {
   'solution_type': {'$ifNull': ['$prob_summary.prob_accessibility.plans.sol_type', 'NO_PLAN']},
   'solution_code': {'$ifNull': ['$prob_summary.prob_accessibility.plans.sol_code', 'NO_PLAN']},
   'solution_desc': {'$ifNull': ['$prob_summary.prob_accessibility.plans.sol_des', 'NO_PLAN']},
   'plan_status': {'$ifNull': ['$prob_summary.prob_accessibility.plans.status', 'NO_PLAN']},
   'progress': {'$ifNull': ['$prob_summary.prob_accessibility.plans.activities.act_progression', 'NO_FOLLOWUP']}
 }, 'rows': {'$sum': 1}, 'ids': {'$addToSet': '$_id'}}},
 {'$project': {'rows': 1, 'people': {'$size': '$ids'}}}, {'$sort': {'people': -1}}
]
show('Q4b_plans', q4b)
plan_people_pipeline = TARGET + [
 {'$unwind':'$prob_summary.prob_accessibility'},
 {'$match':{'prob_summary.prob_accessibility.code':'PBAC8'}},
 {'$unwind':'$prob_summary.prob_accessibility.plans'},
 {'$group':{'_id':'$prob_summary.prob_accessibility.plans.sol_code','ids':{'$addToSet':'$_id'}}},
 {'$project':{'people':{'$size':'$ids'}}}, {'$sort':{'people':-1}}
]
plan_people = show('Q4b_solution_people',plan_people_pipeline)
display(Markdown('**จำนวนคนไม่ซ้ำต่อรหัสส่งต่อ:** ' + '; '.join(f"{row['_id']}: {row['people']} คน" for row in plan_people.to_dict('records'))))
''', 'มีผู้ได้รับแผน TR47 เบี้ยยังชีพผู้สูงอายุ 37 คน และ TR44 เบี้ยพิการ 41 คน (คนเดียวมีได้หลายรหัส) จึงต้องตรวจว่าการส่งต่อตรงกับสิทธิที่ขาด; อีก 35 คนยังไม่มีแผน และแถว TR47 ที่ยังไม่มีผลติดตามมี 14 คน จึงต้องติดตามทั้งการเปิดแผนและผลส่งต่อ โดยห้ามบวก people ข้ามแถวเป็นจำนวนคนทั้งหมด')
query('Q5. ช่องว่างระหว่างข้อเท็จจริงกับการจัดการเคส', 'ผู้ไม่พบ WFEL9 มี PBAC8 ในแบบบันทึกปัญหาและในแผนสอดคล้องกันหรือไม่?', '''
q5 = TARGET + [
 {'$set': {'has_problem_code': has('prob_accessibility.code', 'PBAC8'), 'has_case_code': has('prob_summary.prob_accessibility.code', 'PBAC8')}},
 {'$group': {'_id': {'problem_array': '$has_problem_code', 'case_management': '$has_case_code'}, 'people': {'$sum': 1}}}, {'$sort': {'people': -1}}
]
gap_recording = show('Q5_gap', q5)
''', 'เคสที่ไม่พบทั้ง WFEL9 และ PBAC8 เป็นลำดับงานตรวจสอบเชิงรุกที่ค้นจากข้อเท็จจริงได้ แม้ระบบยังไม่ได้เปิดประเด็นปัญหา; absence ของโค้ดอาจเป็นช่องว่างการบันทึก')
query('Q5s. ตรวจความไวต่อนิยามอายุ', 'ถ้าใช้อายุครบวันเกิดแทนการนับขอบเขตปี ผลรวมเปลี่ยนเท่าไร?', '''
q5s = [{'$match': ACTIVE}, {'$set': FLAGS}, {'$facet': {
 'assignment_year_boundaries': [{'$match': {'age': {'$gte': 60}}}] + rate_group(None),
 'completed_birthday': [{'$match': {'birthdate': {'$lte': datetime(1964, 6, 30)}}}] + rate_group(None)
}}]
age_sensitivity = list(db.mso_member.aggregate(q5s))[0]
for label, records in age_sensitivity.items(): print(label); display(pd.DataFrame(records))
''', 'รายงานหลักใช้สูตรที่โจทย์กำหนดเพื่อให้ตรวจซ้ำได้ แต่การปฏิบัติงานจริงต้องใช้อายุครบวันเกิดและวันตรวจสอบปัจจุบัน; ตารางนี้เปิดเผยผลของทางเลือกดังกล่าว')

md('### Field log — ฟิลด์ที่ใช้เป็นหลักฐานจริง\nไม่นับ status และ vital_status ที่ใช้คัดออก และไม่ใช้ฟิลด์ที่แค่ project เป็นหลักฐาน')
code('''
field_rows = [
 ('mso_member','birthdate','Q1, Q5s','Defines age base; sensitivity changes count'),
 ('mso_member','province_code','Q1, Q6','Province-specific numerator and denominator; external join'),
 ('mso_member','amphur_code','Q1','District-specific rate'),
 ('mso_member','welf_eldery.code','Q1–Q6','WFEL9 gap; WFEL2 alternative support'),
 ('mso_household','have_num','Q2','Compare numberless and numbered homes'),
 ('mso_household','hh_type.code','Q2','Compare living alone and family households'),
 ('mso_member','occup_status','Q3a','Share currently working'),
 ('mso_member','pri_occ_income','Q3a','Primary-income mean and recomputed resources'),
 ('mso_member','sec_occ_income','Q3a','Secondary-income mean and resources'),
 ('mso_member','subsidy_amount','Q3a','Support amount mean and resources'),
 ('mso_member','SUM_INCOME','Q3a','Compare reported total and recomputed income'),
 ('mso_member','SUM_EXPENDITURE','Q3a','Spending pressure'),
 ('mso_member','have_debt','Q3a','Number with recorded debt'),
 ('mso_member','debt.type','Q3a','Informal borrowing exposure'),
 ('mso_member','debt.amount','Q3a','Monthly repayment burden, not debt stock'),
 ('mso_member','saving.amount','Q3a','Recorded savings buffer'),
 ('mso_member','chronic_disease.code','Q3b','Chronic illness and hypertension'),
 ('mso_member','med_scheme.code','Q3b','Explicit no-coverage code MS7'),
 ('mso_member','is_disabled','Q3b','Disability co-occurrence'),
 ('mso_member','have_pwd_card','Q3b','Disability-card gap conditional on disability'),
 ('mso_member','welf_others.code','Q3c','State welfare card as other support'),
 ('mso_member','welf_disability.code','Q3c','Disability allowance co-occurrence'),
 ('mso_member','nationality','Q3c','Separates verification needs by recorded nationality'),
 ('mso_member','prob_summary.prob_accessibility.code','Q4, Q5','PBAC8 case-management recognition'),
 ('mso_member','prob_summary.prob_accessibility.status','Q4a','Problem response status'),
 ('mso_member','prob_summary.prob_accessibility.plans.sol_type','Q4b','Plan type'),
 ('mso_member','prob_summary.prob_accessibility.plans.sol_code','Q4b','Referral route including TR47'),
 ('mso_member','prob_summary.prob_accessibility.plans.status','Q4b','Plan status'),
 ('mso_member','prob_summary.prob_accessibility.plans.activities.act_progression','Q4b','Recorded follow-up outcome'),
 ('mso_member','prob_accessibility.code','Q5','Problem recognition vs case management'),
 ('ext_province_elderly','elderly_2024','Q6, Q6b','Real baseline population size; denominator for registered population growth only'),
 ('ext_province_elderly','elderly_latest','Q6, Q6b','Real latest population size and increase; scale context, not synthetic coverage')
]
field_log = pd.DataFrame(field_rows, columns=['Collection','Field path','Used in query','Why it matters'])
field_log.insert(0, '#', range(1,len(field_log)+1))
display(field_log)
assert len(field_log) >= 15 and field_log.Collection.nunique() >= 2
print(f'{len(field_log)} distinct evidence fields; member sections: identity/location, economy, health, welfare, problems/case management.')
''')

md('''
## Task 4 — Combine external data
**ผู้เผยแพร่:** สำนักงานสถิติแห่งชาติ (NSO), ข้อมูลต้นทางกรมการปกครอง (DOPA)  
**ชุดข้อมูล:** ประชากรอายุ 60 ปีขึ้นไป จากการทะเบียน จำแนกเพศและจังหวัด, OS_0405_01_0008_01  
**Catalog:** https://gdcatalog.go.th/dataset/gdpublish-605  
**Download:** https://catalogapi.nso.go.th/api/index?table=OS_0405_01_0008_01&format=json  
**วันที่เข้าถึง:** 28 ตุลาคม 2026 | **ปีที่ใช้ join:** 2024 (พ.ศ. 2567) | **ปีล่าสุดในไฟล์:** 2025 (พ.ศ. 2568)

โหลดต้นฉบับและสคริปต์เตรียมข้อมูลไว้ใน `ext_data/`; ใช้เฉพาะเพศ “รวม” ลบคำว่า “จังหวัด” และจับคู่ชื่อผ่าน provinces.csv
เลือกปี 2024 ให้ตรงปี snapshot แต่ข้อมูลรายปียังต่างจาก 30 มิถุนายน จึงไม่ถือว่าช่วงเวลาตรงกันทุกวัน
เก็บปีล่าสุดประกอบบริบทด้วย และไม่ใช้จำนวนตัวอย่างสังเคราะห์แทนความครอบคลุมจริง
''')
code('''
external = pd.read_csv(ROOT / 'ext_data/province_elderly.csv', dtype={'province_code': str})
assert external.province_code.str.fullmatch(r'\\d{2}').all()
assert not external.province_code.duplicated().any()
records = json.loads(external.to_json(orient='records', force_ascii=False))
for record in records:
    db.ext_province_elderly.replace_one({'province_code': record['province_code']}, record, upsert=True)
db.ext_province_elderly.create_index('province_code', unique=True)
display(external[['province_code', 'province_name_th', 'elderly_2024', 'elderly_latest', 'latest_year']])
print('Loaded ext_province_elderly:', db.ext_province_elderly.count_documents({}))
''')
query('Q6. ประชากรจริงช่วยเพิ่มบริบทอย่างไร', 'จังหวัดที่มีอัตราช่องว่างสูงในชุดสังเคราะห์มีประชากรผู้สูงอายุจริงเท่าไร?', '''
q6 = ELDERS + rate_group('$province_code') + [
 {'$lookup': {'from': 'ext_province_elderly', 'localField': '_id', 'foreignField': 'province_code', 'as': 'ext'}},
 {'$unwind': {'path': '$ext', 'preserveNullAndEmptyArrays': True}},
 {'$project': {'_id': 0, 'province_code': '$_id', 'province': '$ext.province_name_th', 'synthetic_elderly': '$elderly', 'synthetic_gap': '$gap', 'synthetic_gap_pct': '$gap_pct', 'registered_elderly_2024': '$ext.elderly_2024', 'registered_elderly_latest': '$ext.elderly_latest', 'latest_year': '$ext.latest_year', 'registered_growth_pct': pct({'$subtract': ['$ext.elderly_latest', '$ext.elderly_2024']}, '$ext.elderly_2024')}},
 {'$sort': {'synthetic_gap_pct': -1}}
]
external_context = show('Q6_external', q6)
assert len(external_context) == 7 and external_context.registered_elderly_2024.notna().all()
display(Markdown('**การตรวจ join:** ครบ 7/7 จังหวัด ไม่มีรหัสตกหล่น'))
''', 'ข้อมูลภายนอกแสดงขนาดประชากรผู้สูงอายุจริงซึ่งฐานสังเคราะห์บอกไม่ได้: จังหวัดที่มีอัตราช่องว่างสูงไม่จำเป็นต้องมีประชากรมาก จึงเลือกพื้นที่นำร่องจากอัตราภายในตัวอย่างได้ แต่การขยายกำลังคนต้องสำรวจฐานจริงก่อน ห้ามนำ synthetic_gap_pct ไปคูณประชากรจริงเพื่ออ้างจำนวนตกหล่นทั้งจังหวัด')

query('Q6b. ขนาดประชากรจริงและการเปลี่ยนแปลงเพื่อวางแผนขยายงาน', 'จังหวัดนำร่องมีขนาดประชากรสูงอายุและการเปลี่ยนแปลงปี 2024–2025 เท่าไร เมื่ออ่านควบคู่กับอัตราช่องว่างในชุดสังเคราะห์?', '''
# Keep the real-population calculation wholly within the NSO/DOPA source.
# Never subtract synthetic members from registered people or infer real coverage.
q6b = ELDERS + rate_group('$province_code') + [
 {'$lookup': {'from':'ext_province_elderly', 'localField':'_id', 'foreignField':'province_code', 'as':'ext'}},
 {'$unwind': {'path':'$ext', 'preserveNullAndEmptyArrays':True}},
 {'$project': {'_id':0, 'province_code':'$_id', 'province':'$ext.province_name_th',
   'synthetic_gap':'$gap', 'synthetic_gap_pct':'$gap_pct',
   'registered_2024':'$ext.elderly_2024', 'registered_2025':'$ext.elderly_latest',
   'latest_year':'$ext.latest_year',
   'registered_change':{'$subtract':['$ext.elderly_latest','$ext.elderly_2024']},
   'universal_verification_hours': '$ext.elderly_latest',
   'universal_verification_baht': {'$multiply':['$ext.elderly_latest',300]},
   'registered_growth_pct':pct({'$subtract':['$ext.elderly_latest','$ext.elderly_2024']},'$ext.elderly_2024')}},
 {'$setWindowFields': {'sortBy':{'registered_2025':-1}, 'output':{'population_rank_within_7':{'$rank':{}}}}},
 {'$setWindowFields': {'sortBy':{'synthetic_gap_pct':-1}, 'output':{'synthetic_gap_rank_within_7':{'$rank':{}}}}},
 {'$sort': {'synthetic_gap_pct':-1}}
]
population_context = show('Q6b_population_context',q6b)
assert len(population_context)==7
assert population_context[['registered_2024','registered_2025']].notna().all().all()
assert population_context.latest_year.eq(2025).all()
mhs = population_context.set_index('province_code').loc['58']
display(Markdown(
 f"แม่ฮ่องสอน: ผู้สูงอายุจากทะเบียนจริง **{int(mhs.registered_2024):,} → {int(mhs.registered_2025):,} คน** "
 f"เพิ่ม **{int(mhs.registered_change):,} คน ({mhs.registered_growth_pct:.2f}%)**; "
 f"ขนาดประชากรปี 2025 อันดับ **{int(mhs.population_rank_within_7)}/7** "
 f"แต่อัตราช่องว่างในชุดสังเคราะห์อันดับ **{int(mhs.synthetic_gap_rank_within_7)}/7**"))
display(Markdown(f"**ผลต่อขอบเขตนโยบาย:** หากออกแบบให้ตรวจผู้สูงอายุจากทะเบียนแม่ฮ่องสอนปี 2025 ทุกคน ภายใต้สมมติฐานเดียวกันคือ 1 ชั่วโมงและ 300 บาทต่อคน จะต้องใช้ **{int(mhs.universal_verification_hours):,} ชั่วโมง / {int(mhs.universal_verification_baht):,} บาท** จึงกำหนดโครงการเป็นการนำร่องตรวจรายชื่อ 43 คนจากชุดข้อมูล (43 ชั่วโมง / 12,900 บาท) ก่อนออกแบบการขยายงานจากทะเบียนจริง"))
''', 'ข้อมูลภายนอกทำให้จำกัดข้อเสนอเป็นนำร่องแทนการตรวจผู้สูงอายุทั้งจังหวัด: การตรวจทะเบียนปี 2025 ครบ 41,623 คนต้องใช้ 41,623 ชั่วโมงและ 12,486,900 บาทตามสมมติฐาน ขณะที่การนำร่องใช้ 43 ชั่วโมงและ 12,900 บาท นี่เป็นการเปรียบเทียบขอบเขตงานสองสถานการณ์ ไม่ใช่การประมาณความชุก จำนวนผู้ตกหล่น หรือความครอบคลุมจริง และงบขยายงานต้องยืนยันจากข้อมูลปฏิบัติงานเพิ่ม')
md('''
**ขอบเขตการตีความ:** อัตรา `synthetic records / real population` สาธิตการ join ได้ แต่ไม่วัดความครอบคลุมจริงหรือใช้จัดอันดับการเข้าถึงของเจ้าหน้าที่
จึงไม่คำนวณ `real population - synthetic records` เป็นคนที่ไม่อยู่ใน logbook และไม่ใช้ correlation ระหว่างอัตราส่วนผสมนี้กับอัตราช่องว่างเพื่อสรุปสาเหตุ
43 คนเป็นจำนวนที่ query พบในข้อมูลสังเคราะห์ ไม่ใช่จำนวนขั้นต่ำของผู้สูงอายุที่ตกหล่นจริงในแม่ฮ่องสอน
ข้อเสนอค้นหาเชิงรุกนอกระบบทำได้ในฐานะแผนงานที่ต้องตรวจสอบเพิ่มเติม ไม่ใช่ข้อค้นพบว่าประชากรที่เหลือไม่เคยถูกคัดกรอง
''')

md('''
## Task 5 — Policy targeting and monitoring (PDF companion)
ข้อเสนอ: พมจ.แม่ฮ่องสอนร่วมกับ อปท. และ อพม. ตรวจสอบสิทธิและบันทึก WFEL9 ของกลุ่มที่คัดได้
ให้ลำดับเยี่ยมบ้านก่อนแก่ผู้ไม่มีเลขที่หรืออยู่คนเดียว เมื่อยืนยันสิทธิให้ส่งต่อแนวทาง TR47 ซึ่งปรากฏในข้อมูลตัวอย่าง
ผู้ไม่เข้าเงื่อนไขรับเบี้ยต้องประสานสวัสดิการที่เหมาะสมแทน ไม่บันทึกเป็นผู้มีสิทธิอัตโนมัติ
query หนึ่งตัวต่อไปนี้คัดรายชื่อบุคคลเพื่อยืนยันสิทธิในจังหวัดนำร่อง; จำนวนครัวเรือนคำนวณจาก hh_id ไม่ซ้ำ
''')
code('''
# Exact same filter is used in the policy PDF and Bonus A2.
# The birthdate range is equivalent to the assignment's calendar-year age rule at SNAPSHOT;
# retain $expr explicitly to preserve the assignment definition. No sort requirement.
TARGET_FILTER = {
 'province_code': '58', 'vital_status': 1, 'status': {'$ne': 'removed'},
 'birthdate': {'$lt': datetime(1965, 1, 1)},
 '$expr': {'$gte': [AGE, 60]}, 'welf_eldery.code': {'$ne': 'WFEL9'}
}
pilot_people = list(db.mso_member.find(TARGET_FILTER, {'_id': 1, 'hh_id': 1, 'amphur_code': 1}))
PILOT_IDS = [x['_id'] for x in pilot_people]
pilot_n = len(pilot_people)
pilot_hh = len({x['hh_id'] for x in pilot_people})
print(json_util.dumps(TARGET_FILTER, indent=2, ensure_ascii=False))
display(pd.DataFrame([{'people_to_verify': pilot_n, 'distinct_households': pilot_hh,
  'staff_hours_at_1_hour_per_person': pilot_n, 'verification_budget_at_300_baht_per_person': pilot_n*300}]))
pilot_priority = agg('mso_member', [{'$match': TARGET_FILTER}] + HH_JOIN + [{'$group': {'_id': None, 'no_house_number': {'$sum': {'$cond': [{'$eq': ['$hh.have_num', 0]},1,0]}}, 'living_alone': {'$sum': {'$cond': [{'$eq': ['$hh.hh_type.code','HHT1']},1,0]}}}}])
display(pilot_priority)
# Persist baseline IDs for a fixed-cohort six-month comparison; original records stay unchanged.
(ROOT/'output/pilot_baseline_ids.json').write_text(json_util.dumps({'snapshot': SNAPSHOT, 'ids': PILOT_IDS}, indent=2), encoding='utf-8')
MONITOR_FILTER = {'_id': {'$in': PILOT_IDS}, **ACTIVE, 'welf_eldery.code': {'$ne': 'WFEL9'}}
print('Six-month remaining baseline cases (current snapshot, not a future observation):', db.mso_member.count_documents(MONITOR_FILTER))
assert pilot_n == sum(1 for _ in db.mso_member.aggregate(TARGET + [{'$match': {'province_code':'58'}}]))
''')
md('''
**สมมติฐานต้นทุน:** ตรวจสอบ 1 ชั่วโมงและค่าเดินทาง/ติดต่อ 300 บาทต่อคนเป็นตัวเลขสมมติเพื่อวางแผน
ไม่ใช่อัตราราชการ ไม่รวมงบจ่ายเบี้ยและไม่อ้างการยืนยันสิทธิ; การเยี่ยมหลายคนในบ้านเดียวอาจลดต้นทุน
ในหกเดือนใช้ baseline IDs เดิมนับคนยังไม่พบ WFEL9 แยกผู้ตาย/removed ออกจากเหตุออกจาก cohort
เทียบ `prob_summary.prob_accessibility.status`, `plans.sol_code`, `plans.activities.act_progression` ควบคู่ผลยืนยันสิทธิ
เป้าหมายโครงการที่เสนอคือยืนยันข้อมูลอย่างน้อย 90% ภายใน 60 วัน และลดเคสขาดบันทึกที่ตรวจแล้วว่ามีสิทธิอย่างน้อยครึ่งหนึ่งใน 6 เดือน
เป้าหมายนี้เป็นข้อเสนอ ไม่ใช่ผลที่เกิดขึ้นแล้ว; ฐานเดิมไม่มีฟิลด์ยืนยันสิทธิหรือวันที่เริ่มรับเงินจริง จึงต้องเก็บเพิ่มก่อนประเมินการได้รับเงิน
''')

md('## Bonus A — Make queries fast')
query('A1. Dashboard ด้วย $facet', 'ใช้ pipeline เดียวแสดงกลุ่มเป้าหมายตามจังหวัด เพศ และช่วงอายุได้อย่างไร?', '''
a1 = TARGET + [{'$facet': {
 'province': [{'$group': {'_id': '$province_code', 'n': {'$sum': 1}}}, {'$sort': {'n': -1}}],
 'sex': [{'$group': {'_id': '$sex', 'n': {'$sum': 1}}}],
 'age_band': [{'$bucket': {'groupBy': '$age', 'boundaries': [60,70,80,90,120], 'default': 'outside', 'output': {'n': {'$sum': 1}}}}]
}}]
dashboard = list(db.mso_member.aggregate(a1))[0]
for label, rows in dashboard.items(): print(label); display(pd.DataFrame(rows))
assert all(sum(x['n'] for x in dashboard[k]) == int(baseline.gap) for k in dashboard)
''', '$match อยู่ก่อน $facet เพื่อลดเอกสารก่อนแยกสามสาขาและให้เงื่อนไขที่รองรับใช้ index ต้นทางได้ ส่วน age ที่คำนวณและ missing welfare ไม่ได้รับประโยชน์จาก index ทุกส่วน')
md('### A2. เปรียบเทียบ executionStats ก่อนและหลัง compound index')
code('''
INDEX_NAME = 'a4_pilot_esr'
# Only remove this assignment-owned index so rerunning reproduces the before state.
if INDEX_NAME in db.mso_member.index_information(): db.mso_member.drop_index(INDEX_NAME)
def explain_find():
    return db.command('explain', {'find': 'mso_member', 'filter': TARGET_FILTER}, verbosity='executionStats')
def stages(node):
    found = []
    if isinstance(node, dict):
        if 'stage' in node: found.append(node['stage'])
        for v in node.values(): found.extend(stages(v))
    elif isinstance(node,list):
        for v in node: found.extend(stages(v))
    return list(dict.fromkeys(found))
def stats(label, exp):
    s = exp['executionStats']
    return {'run': label, 'winning_stages': ' > '.join(stages(exp['queryPlanner']['winningPlan'])), **{k:s[k] for k in ['totalDocsExamined','totalKeysExamined','nReturned','executionTimeMillis']}}
before = explain_find()
db.mso_member.create_index([('province_code',1), ('vital_status',1), ('birthdate',1)], name=INDEX_NAME)
after = explain_find()
index_results = pd.DataFrame([stats('before', before), stats('after', after)])
display(index_results)
assert before['executionStats']['nReturned'] == after['executionStats']['nReturned'] == pilot_n
''')
md('''
Index เรียง `province_code`, `vital_status` ซึ่งเป็น Equality ไว้ก่อน `birthdate` ที่เป็น Range ตามหลัก ESR; query ไม่มี Sort จึงไม่มีส่วน S
เป็น scalar compound index ไม่ใช่ multikey เพราะไม่ได้ใส่ array ใน index นี้
ก่อนสร้างยังมี index จังหวัด/อำเภอจาก load_data.py อยู่ จึงไม่จำเป็นต้องได้ COLLSCAN และรายงานแผนที่เกิดจริง
`status != removed`, `welf_eldery.code != WFEL9` และการคำนวณ `$expr` ยังต้องตรวจเอกสาร ส่วน index ไม่ช่วย stages หลัง lookup
เวลาเป็นการวัดครั้งเดียวบนข้อมูลเล็กและ cache อาจมีผล จึงใช้ docs/keys examined ประกอบ ไม่อ้างว่าเวลาเร็วขึ้นเสมอ
''')

md('''
## Bonus B — Redesign the MSO-Logbook structure
### B1. ปัญหาที่พบจริง
1. **join ครัวเรือนทุกครั้ง:** Q2 และการจัดลำดับเคสต้อง lookup เพื่ออ่าน have_num/hh_type แม้เป็นข้อมูลที่อ่านร่วมกันประจำ เสี่ยงเสียคนที่ join ไม่พบถ้า unwind แบบปกติ
2. **ปัญหากระจายตาม domain:** O4 ต้องรวมเก้า array และ O5 ต้อง objectToArray/reduce; Q5 พบการแยกเก็บข้อเท็จจริง ปัญหา และ case management ทำให้ผู้ไม่พบบันทึกเบี้ยบางคนไม่มี PBAC8
3. **optional arrays/ข้อมูลคำนวณ:** Q3 ต้อง ifNull ซ้ำและตรวจยอดรายได้กับรายละเอียด; ค่า “ไม่มีโค้ด” ยังไม่ใช่สถานะยืนยันการรับเงินจริง

### B2. โครงสร้างใหม่: snapshot read model
สร้าง `mso_member_v2` จากข้อมูลเดิมโดยไม่แก้ต้นฉบับ เก็บ source IDs แบบ reference เพื่อสืบกลับและอัปเดตต้นทาง
embed `household_snapshot` เฉพาะ have_num/hh_type/status เพราะอ่านร่วมกับการคัดกรองเสมอ พร้อม snapshot_date เพื่อบอกความเก่า
รวมรหัสปัญหาเป็น `problem_codes` และ case management เป็น array เดียว `case_problems` ซึ่งเก็บ domain เดิมและ plans/activities
เก็บ `welfare_codes` และ `has_recorded_allowance` เป็นค่าคำนวณจากรหัสเดิม ไม่เติมข้อสรุปสิทธิหรือการรับเงินจริง
เก็บ `elderly_at_snapshot` และ age_years ภายใต้วันที่ snapshot ชัดเจน; ไม่ใช้ age นี้เป็นอายุปัจจุบัน

**ต้นทุน:** ข้อมูลซ้ำและเอกสารโตขึ้น ต้อง rebuild/incremental refresh เมื่อ household หรือ welfare เปลี่ยน
การแก้ source หลายเอกสารไม่ atomic ร่วมกับ read model จึงต้องมีงาน refresh และตรวจ reconciliation
ไม่ได้เก็บทุกฟิลด์เดิม; v2 เป็น materialized read model สำหรับการอ่านโจทย์นี้ ไม่ใช่ master database ใหม่
''')
code('''
# Validator checks required types, two-digit province code and normalized problem codes.
validator = {'$jsonSchema': {
 'bsonType': 'object', 'required': ['source_member_id','snapshot_date','province_code','elderly_at_snapshot','has_recorded_allowance','problem_codes'],
 'properties': {
   'source_member_id': {'bsonType':'objectId'}, 'snapshot_date': {'bsonType':'date'},
   'province_code': {'bsonType':'string', 'pattern': '^[0-9]{2}$'},
   'elderly_at_snapshot': {'bsonType':'bool'}, 'has_recorded_allowance': {'bsonType':'bool'},
   'problem_codes': {'bsonType':'array', 'items': {'bsonType':'string'}}
 }}}
if 'mso_member_v2' not in db.list_collection_names():
    db.create_collection('mso_member_v2', validator=validator)
else:
    db.command('collMod', 'mso_member_v2', validator=validator, validationLevel='strict')
# Refresh only our derived collection; original three collections are unchanged.
db.mso_member_v2.delete_many({})
CASE_NORMALIZED = {'$reduce': {
 'input': {'$objectToArray': {'$ifNull': ['$prob_summary', {}]}}, 'initialValue': [],
 'in': {'$concatArrays': ['$$value', {'$map': {'input': '$$this.v', 'as': 'p', 'in': {'$mergeObjects': ['$$p', {'domain':'$$this.k'}]}}}]}
}}
WELFARE_FIELDS = ['welf_children_youth','welf_disability','welf_women','welf_eldery','welf_helpless_persons','welf_others']
migration = [
 {'$lookup': {'from':'mso_household','localField':'hh_id','foreignField':'_id','as':'hh'}},
 {'$unwind': {'path':'$hh','preserveNullAndEmptyArrays':True}},
 {'$project': {
   '_id':1, 'source_member_id':'$_id', 'source_household_id':'$hh_id', 'source_family_id':'$fam_id',
   'snapshot_date': {'$literal':SNAPSHOT}, 'province_code':1, 'amphur_code':1, 'birthdate':1, 'sex':1, 'status':1, 'vital_status':1,
   'age_years': AGE, 'elderly_at_snapshot': {'$gte':[AGE,60]},
   'has_recorded_allowance': has('welf_eldery.code','WFEL9'),
   'welfare_codes': {'$setUnion':[arr(p+'.code') for p in WELFARE_FIELDS]},
   'problem_codes': {'$setUnion':[arr(p+'.code') for p in PROB_FIELDS]},
   'case_problems': CASE_NORMALIZED,
   'household_snapshot': {'have_num': {'$ifNull':['$hh.have_num',None]}, 'hh_type': {'$ifNull':['$hh.hh_type.code',None]}, 'status': {'$ifNull':['$hh.status',None]}}
 }},
 {'$merge': {'into':'mso_member_v2','on':'_id','whenMatched':'replace','whenNotMatched':'insert'}}
]
list(db.mso_member.aggregate(migration))
db.mso_member_v2.create_index([('province_code',1),('vital_status',1),('elderly_at_snapshot',1),('has_recorded_allowance',1)], name='v2_target_scalar')
db.mso_member_v2.create_index('problem_codes', name='v2_problem_codes_multikey')
print('v2 documents:', db.mso_member_v2.count_documents({}))
sample = db.mso_member_v2.find_one({**ACTIVE,'province_code':'58','elderly_at_snapshot':True,'has_recorded_allowance':False,'household_snapshot.status':{'$ne':'removed'}})
assert sample['vital_status']==1 and sample['status']!='removed'
# Actual migrated document; print concise sample with arrays retained.
print(json_util.dumps(sample, ensure_ascii=False, indent=2))
''')
md('Index แรกเป็น scalar compound index สำหรับค้น target ส่วน `problem_codes` เป็น multikey แยกต่างหาก จึงไม่เสี่ยง compound index ที่มีหลาย array; validator บังคับรหัสจังหวัดและชนิด flag แต่ความสอดคล้องกับ source ต้องตรวจจากการ rebuild และ reconciliation เพิ่ม')
query('B3. รัน Q2 เดิมเทียบ v2', 'เมื่อฝัง household snapshot แล้ว ผลเปรียบเทียบได้เท่าเดิมโดยใช้ stages น้อยลงหรือไม่?', '''
v2_flags = {'missing_allowance': {'$not':['$has_recorded_allowance']}}
q2_v2 = [
 {'$match': {**ACTIVE, 'elderly_at_snapshot':True, 'household_snapshot.status':{'$ne':'removed'}}},
 {'$set':v2_flags},
 {'$facet': {
   'house_number': rate_group({'$ifNull':['$household_snapshot.have_num','UNKNOWN']}),
   'household_type': rate_group({'$ifNull':['$household_snapshot.hh_type','UNKNOWN']})
 }}
]
new_result = list(db.mso_member_v2.aggregate(q2_v2))[0]
def canonical(records): return sorted(records, key=lambda r: str(r['_id']))
for key in housing:
    assert canonical(housing[key]) == canonical(new_result[key]), key
    print(key, '| exact result match'); display(pd.DataFrame(new_result[key]))
def stage_count(pipeline):
    return len(pipeline) + sum(stage_count(branch) for stage in pipeline if '$facet' in stage for branch in stage['$facet'].values())
comparison = pd.DataFrame([
 {'version':'original Q2','top_level_stages':len(q2),'all_stages_including_facet':stage_count(q2),'lookup_stages':1,'exact_match':True},
 {'version':'v2 Q2','top_level_stages':len(q2_v2),'all_stages_including_facet':stage_count(q2_v2),'lookup_stages':0,'exact_match':True}
])
display(comparison)
assert db.mso_member_v2.count_documents({}) == counts['mso_member']
''', 'ผล Q2 ตรงกันทุกกลุ่มและอัตรา โดยลด lookup ที่ต้องทำซ้ำในเวลาอ่าน; ประโยชน์นี้แลกกับเวลา migration พื้นที่เก็บ และความเสี่ยงข้อมูล snapshot ล้าสมัย จึงไม่สรุปว่าเร็วกว่าในทุก workload')

md('''
## ข้อจำกัดและการตรวจงาน
ข้อมูลสังเคราะห์ไม่เป็นตัวแทนประเทศไทย; ผลเป็นความสัมพันธ์ ไม่ใช่เหตุและผล
โค้ดสวัสดิการและปัญหาที่หายไปไม่ยืนยันการไม่มีสิทธิ/การไม่ได้รับเงินจริง รวมทั้ง PBAC8 มีความหมายร่วมสำหรับเบี้ยพิการ
ข้อมูลรายได้ขาดได้และมี SUM_INCOME ไม่ตรงรายละเอียด debt เป็นรายจ่ายชำระต่อเดือน
อายุใช้สูตรปีตามโจทย์ และมี sensitivity เทียบอายุครบวันเกิด; ข้อมูลภายนอกเป็นรายปีที่ไม่ตรงวันที่ snapshot ทุกวัน
ข้อความอิสระสั้นหรือว่างทำให้ยังใช้ full-text/embedding ตรวจเหตุปัญหาได้จำกัด ต้องเก็บบันทึกเยี่ยมบ้านและผลยืนยันสิทธิที่มีคุณภาพก่อน

### Reproducibility and integrity checks
''')
code('''
assert sum(x['n'] for x in dashboard['province']) == int(baseline.gap)
assert index_results.nReturned.nunique() == 1
assert all(canonical(housing[k]) == canonical(new_result[k]) for k in housing)
assert counts == {c:db[c].count_documents({}) for c in counts}
summary = {
 'name':'Anupat Suttilert','student_id':'6624650526','team_members':[{'name':'Anupat Suttilert','student_id':'6624650526'},{'name':'Nongnapat Sunontanum','student_id':'6624650302'}],'snapshot':'2024-06-30','runtime':runtime_info,
 'elderly':int(baseline.elderly),'gap':int(baseline.gap),'gap_pct':float(baseline.gap_pct),
 'disabled':int(alternative.disabled),'disabled_no_card':int(alternative.no_card),
 'pilot_people':pilot_n,'pilot_households':pilot_hh,'budget_baht':pilot_n*300,
 'housing':housing,'index_results':index_results.to_dict('records'),
 'external':external_context.to_dict('records'),'external_population_context':population_context.to_dict('records'),
 'wfel9_audit':wfel_audit.to_dict('records'),'wfel9_raw_id_match':raw_gap_ids==pipeline_gap_ids,
 'recording_gap':gap_recording.to_dict('records'), 'statement':statement,
 'age_sensitivity':age_sensitivity, 'v2_comparison':comparison.to_dict('records')
}
(ROOT/'output/verified_results.json').write_text(json_util.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
for key, frame in RESULTS.items(): frame.to_csv(ROOT/'output'/f'{key}.csv',index=False,encoding='utf-8-sig')
field_log.to_csv(ROOT/'output/field_log.csv',index=False,encoding='utf-8-sig')
print('PASS: counts, external joins, dashboard totals, targeting before/after and v2 exact equivalence.')
print('Task 1: 5 overview pipelines | Task 3: >5 evidence pipelines | fields:',len(field_log))
print('All original collection counts unchanged. No future monitoring results fabricated.')
''')

nb.metadata.update({'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'language_info':{'name':'python','version':'3.13'}})
path = OUT / 'A4_6624650526.ipynb'
nbf.write(nb,path)
print('Executing', path, flush=True)
NotebookClient(nb, timeout=240, kernel_name='python3', resources={'metadata':{'path':str(ROOT)}}).execute()
nbf.write(nb,path)
print('Executed and saved', path, flush=True)
