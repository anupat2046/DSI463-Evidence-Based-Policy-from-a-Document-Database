from pymongo import MongoClient
from pymongo.errors import AutoReconnect
c=MongoClient('mongodb://127.0.0.1:27018',serverSelectionTimeoutMS=2000)
try:
 print('Stopping only prior assignment MongoDB on 27018:',c.admin.command('buildInfo')['version'])
 c.admin.command('shutdown',force=False)
except AutoReconnect:
 print('Previous MongoDB stopped.')
