import requests, pathlib
urls=['https://catalogapi.nso.go.th/api/index?table=OS_0405_01_0008_01&format=json','http://catalogapi.nso.go.th/api/index?table=OS_0405_01_0008_01&format=csv','https://catalogapi.nso.go.th/api/index?table=OS_0405_01_0008_01%26format=csv']
for i,u in enumerate(urls):
 try:
  r=requests.get(u,headers={'User-Agent':'Mozilla/5.0'},timeout=25); print(i,r.status_code,len(r.content),r.content[:100]);
  if r.status_code==200: pathlib.Path(f'ext_data/nso_raw_{i}.txt').write_bytes(r.content)
 except Exception as e: print(type(e).__name__)
