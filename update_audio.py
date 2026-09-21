import json
from pymongo import MongoClient

with open('config.json', 'r', encoding='utf-8') as f:
    cfg = json.load(f)

client = MongoClient(cfg['mongodb_uri'])
db = client['newskid']
audio_url = 'https://ik.imagekit.io/2qoga5wjp/newskid_audio/mamta_voiceover_qfSGISWAd.mp3'

res = db['cards'].update_one(
    {'category': 'breaking'},
    {'$set': {'audioUrl': audio_url}}
)
print(f"Updated Breaking News with Studio Audio: Matched={res.matched_count}, Modified={res.modified_count}")
