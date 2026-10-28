from pathlib import Path
import nbformat,json
root=Path.cwd()
p=root/'output/A4_6624650526.ipynb'
n=nbformat.read(p,as_version=4)
n.cells[0].source=n.cells[0].source.replace('**Name(s):** Anupat Suttilert  ','**Name(s):** Anupat Suttilert; Nongnapat Sunontanum  ').replace('**Student ID(s):** 6624650526  ','**Student ID(s):** Anupat Suttilert - 6624650526; Nongnapat Sunontanum - 6624650302  ')
assert 'Nongnapat Sunontanum' in n.cells[0].source and '6624650302' in n.cells[0].source
nbformat.write(n,p)
p=root/'output/verified_results.json'
r=json.loads(p.read_text(encoding='utf-8'))
r['team_members']=[{'name':'Anupat Suttilert','student_id':'6624650526'},{'name':'Nongnapat Sunontanum','student_id':'6624650302'}]
p.write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
print('Updated team; preserved executed notebook outputs.')
