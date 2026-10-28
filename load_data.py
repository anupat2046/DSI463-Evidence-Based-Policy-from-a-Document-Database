"""
Load the Assignment 4 data into MongoDB and print a quick check.

    pip install pymongo
    python load_data.py                                   # localhost:27017, database "mso"
    python load_data.py --uri "mongodb+srv://user:pass@cluster.xxxxx.mongodb.net"   # MongoDB Atlas

The script drops and re-creates the three collections, so it is safe to run again.
"""

import argparse
import os

from bson import json_util
from pymongo import ASCENDING, MongoClient

COLLECTIONS = ["mso_household", "mso_family", "mso_member"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--uri", default="mongodb://localhost:27017")
    ap.add_argument("--db", default="mso")
    ap.add_argument("--data", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "data"))
    args = ap.parse_args()

    db = MongoClient(args.uri)[args.db]
    for name in COLLECTIONS:
        with open(os.path.join(args.data, name + ".json"), encoding="utf-8") as f:
            docs = json_util.loads(f.read())   # Extended JSON -> ObjectId / datetime
        db[name].drop()
        db[name].insert_many(docs, ordered=False)
        print("%-14s %6d documents loaded" % (name, db[name].count_documents({})))

    # indexes on the join keys and common filters
    db.mso_family.create_index([("hh_id", ASCENDING)])
    db.mso_member.create_index([("hh_id", ASCENDING)])
    db.mso_member.create_index([("fam_id", ASCENDING)])
    for c in COLLECTIONS:
        db[c].create_index([("province_code", ASCENDING), ("amphur_code", ASCENDING)])
    print("indexes created")

    # sanity check: members per province (active records only)
    print("\nmembers per province (status != 'removed'):")
    for row in db.mso_member.aggregate([
        {"$match": {"status": {"$ne": "removed"}}},
        {"$group": {"_id": {"code": "$province_code", "name": "$province_name"}, "members": {"$sum": 1}}},
        {"$sort": {"_id.code": 1}},
    ]):
        print("  %s %-18s %5d" % (row["_id"]["code"], row["_id"]["name"], row["members"]))


if __name__ == "__main__":
    main()
