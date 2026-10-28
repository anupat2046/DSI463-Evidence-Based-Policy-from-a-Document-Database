"""Audit deliverables and create a portable submission package."""
from pathlib import Path
import ast
import json
import zipfile
import hashlib
import subprocess
from datetime import datetime
import nbformat
from nbconvert import HTMLExporter
import fitz

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'output'
path=OUT/'A4_6624650526.ipynb'
nb=nbformat.read(path,as_version=4)
nbformat.validate(nb)
cells=[c for c in nb.cells if c.cell_type=='code']
assert all(c.execution_count is not None for c in cells)
assert not [o for c in cells for o in c.outputs if o.output_type=='error']
assert all(c.outputs for c in cells)
assert 'PASS:' in ''.join(o.get('text','') for c in cells for o in c.outputs)
html,_=HTMLExporter().from_notebook_node(nb)
(OUT/'A4_6624650526_read.html').write_text(html,encoding='utf-8')
pdf=fitz.open(OUT/'A4_6624650526_brief.pdf')
assert len(pdf)==2
pdftext='\n'.join(p.get_text() for p in pdf)
for term in ['6624650526','Anupat Suttilert','Nongnapat Sunontanum','6624650302','12,900','WFEL9','TR47']:
    assert term in pdftext,term
summary=json.loads((OUT/'verified_results.json').read_text(encoding='utf-8'))
assert summary['runtime']['platform'] == 'linux'
assert "27017" in summary['runtime']['endpoint']
container=json.loads(subprocess.check_output(['docker','inspect','dsi463-mongo'],text=True,encoding='utf-8'))[0]
assert container['State']['Running'] and container['Config']['Image']=='mongo:7.0'
docker_evidence={'container_name':'dsi463-mongo','container_id':container['Id'],'image':container['Config']['Image'],'image_id':container['Image'],'state':container['State']['Status'],'ports':container['NetworkSettings']['Ports'],'notebook_runtime':summary['runtime']}
(OUT/'docker_runtime.json').write_text(json.dumps(docker_evidence,indent=2),encoding='utf-8')
assert summary['gap']==243 and summary['elderly']==1461 and summary['pilot_people']==43
assert summary['v2_comparison'][0]['exact_match'] and summary['v2_comparison'][1]['exact_match']

# Independently compare the literal PDF filter with the notebook filter (not rendered text).
brief_ast=ast.parse((ROOT/'build_brief.py').read_text(encoding='utf-8'))
query_text=next(ast.literal_eval(n.value) for n in brief_ast.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='query' for t in n.targets))
brief_ns={'datetime':datetime}
exec(query_text.rsplit('db.mso_member.find',1)[0],brief_ns)
source_cell=next(c.source for c in cells if 'TARGET_FILTER = {' in c.source)
filter_node=next(n for n in ast.parse(source_cell).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='TARGET_FILTER' for t in n.targets))
age={'$dateDiff':{'startDate':'$birthdate','endDate':datetime(2024,6,30),'unit':'year'}}
notebook_filter=eval(compile(ast.Expression(filter_node.value),'<filter>','eval'),{'datetime':datetime,'AGE':age})
assert notebook_filter==brief_ns['target']

files={
 path:'A4_6624650526.ipynb',
 OUT/'A4_6624650526_brief.pdf':'A4_6624650526_brief.pdf',
 OUT/'A4_6624650526_brief.html':'A4_6624650526_brief.html',
 OUT/'A4_6624650526_read.html':'A4_6624650526_read.html',
 OUT/'pilot_baseline_ids.json':'pilot_baseline_ids.json',
 OUT/'verified_results.json':'verified_results.json',
 OUT/'docker_runtime.json':'docker_runtime.json',
 OUT/'field_log.csv':'field_log.csv',
 ROOT/'README_ส่งงาน.md':'README_ส่งงาน.md',
}
for name in ['load_data.py','docker-compose.yml','provinces.csv','schema_guide.md','assignment4_instructions.md','external_data_sources.md','build_assignment.py','build_brief.py','package_and_verify.py','requirements.txt']:
    files[ROOT/name]=name
for p in (ROOT/'data').glob('*.json'): files[p]='data/'+p.name
for name in ['prepare_external.py','nso_elderly_raw.json','province_elderly.csv','source_metadata.json']:
    files[ROOT/'ext_data'/name]='ext_data/'+name
archive=OUT/'A4_6624650526_submission.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=8) as z:
    for source, destination in files.items():
        assert source.is_file(),source
        z.write(source,destination)
    manifest={name:hashlib.sha256(p.read_bytes()).hexdigest() for p,name in files.items()}
    z.writestr('SHA256_manifest.json',json.dumps(manifest,ensure_ascii=False,indent=2))
assert zipfile.ZipFile(archive).testzip() is None
report={'runtime':summary['runtime'],'docker_container':docker_evidence['container_name'],'notebook_code_cells':len(cells),'executed_cells':len(cells),'error_outputs':0,'pdf_pages':len(pdf),'target_filter_matches_pdf':True,'v2_exact_equivalence':True,'zip_integrity':'PASS','packaged_files':len(files),'zip_bytes':archive.stat().st_size}
(OUT/'validation_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
