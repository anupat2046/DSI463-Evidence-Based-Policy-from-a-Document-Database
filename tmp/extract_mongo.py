import zipfile,pathlib
z=zipfile.ZipFile('tools/mongodb.zip')
n=next(n for n in z.namelist() if n.endswith('/bin/mongod.exe'))
p=pathlib.Path('tools/mongod.exe'); p.write_bytes(z.read(n)); print(p.resolve())
