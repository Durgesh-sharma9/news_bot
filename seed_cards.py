import os
import sys
from datetime import datetime, timezone, timedelta
from pymongo import MongoClient

MONGODB_URI = "mongodb+srv://dev:ipZlD6vupMTc0rmM@backend.uuio5ow.mongodb.net/newskid"

now = datetime.now(timezone.utc)

# 100% Copyright-Free, Royalty-Free Commercial-Use Licensed Real News Photos (Unsplash / Pexels / NASA Public Domain)
SAMPLE_CARDS = [
    {
        "title": "ममता बनर्जी पर गहराया संकट: बंगाल में राजनीतिक घमासान तेज",
        "title_en": "Deepening Crisis for Mamata Banerjee: Political Turmoil Escalates in Bengal",
        "summary": "पश्चिम बंगाल की मुख्यमंत्री ममता बनर्जी पर कानून व्यवस्था और प्रशासनिक फैसलों को लेकर विपक्ष ने कड़े सवाल उठाए हैं। हालिया घटनाओं के बाद राज्य की राजनीति में तनाव काफी बढ़ गया है और कई मोर्चों पर सरकार की घेराबंदी हो रही है।",
        "summary_en": "West Bengal CM Mamata Banerjee faces severe political heat over recent law and order incidents and administrative decisions as the opposition ramps up state-wide protests.",
        "category": "breaking",
        "badge": "🔴 बड़ी खबर",
        "imageUrl": "https://images.unsplash.com/photo-1541872703-74c5e44368f9?w=1080&q=80",
        "images": [
            "https://images.unsplash.com/photo-1541872703-74c5e44368f9?w=1080&q=80",
            "https://images.unsplash.com/photo-1577962917302-cd874c4e31d2?w=1080&q=80",
            "https://images.unsplash.com/photo-1529107386315-e1a2ed48a620?w=1080&q=80"
        ],
        "audioUrl": "https://ik.imagekit.io/2qoga5wjp/newskid_audio/mamta_voiceover_qfSGISWAd.mp3",
        "source": "NEWS KID Verified",
        "publishedAt": (now - timedelta(minutes=5)).isoformat(),
        "views": 2540,
        "likes": 128
    },
    {
        "title": "ISRO का नया कीर्तिमान: चंद्रयान-4 और वीनस मिशन को मिली कैबिनेट मंजूरी",
        "title_en": "ISRO's Historic Milestone: Cabinet Approves Chandrayaan-4 & Venus Orbiter Mission",
        "summary": "भारतीय अंतरिक्ष अनुसंधान संगठन (ISRO) अब चंद्रमा की सतह से मिट्टी और चट्टानों के नमूने धरती पर वापस लाएगा। कैबिनेट ने चंद्रयान-4 और शुक्र ग्रह मिशन के लिए भारी बजट मंजूर कर दिया है। यह मिशन 2028 तक अंतरिक्ष में रवाना होगा।",
        "summary_en": "ISRO secures mega cabinet approval for Chandrayaan-4 lunar sample-return mission and Venus Orbiter Mission, marking India's next leap in deep space exploration.",
        "category": "tech",
        "badge": "🚀 टेक & AI",
        "imageUrl": "https://images.unsplash.com/photo-1517976487502-5f69a0db01c6?w=1080&q=80",
        "images": [
            "https://images.unsplash.com/photo-1517976487502-5f69a0db01c6?w=1080&q=80",
            "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=1080&q=80",
            "https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?w=1080&q=80"
        ],
        "source": "NEWS KID Science Desk",
        "publishedAt": (now - timedelta(minutes=25)).isoformat(),
        "views": 4820,
        "likes": 342
    },
    {
        "title": "सोनिया गांधी को कोर्ट से झटका: वोटर लिस्ट मामले में नए सिरे से होगी जांच",
        "title_en": "Court Setback for Sonia Gandhi: Fresh Investigation in Voter List Case",
        "summary": "दिल्ली की सेशन कोर्ट ने वोटर लिस्ट विवाद मामले में निचली अदालत का फैसला पलट दिया है। अदालत के इस आदेश के बाद अब शिकायत पर दोबारा सुनवाई शुरू होगी, जिससे कांग्रेस खेमे में हलचल तेज हो गई है।",
        "summary_en": "Delhi Sessions Court sets aside the magistrate order dismissing the complaint against Sonia Gandhi in voter registration row, ordering a fresh hearing on the matter.",
        "category": "national",
        "badge": "🇮🇳 देश",
        "imageUrl": "https://images.unsplash.com/photo-1589829545856-d10d557cf95f?w=1080&q=80",
        "images": [
            "https://images.unsplash.com/photo-1589829545856-d10d557cf95f?w=1080&q=80",
            "https://images.unsplash.com/photo-1479142506502-19b3a3b7ff33?w=1080&q=80",
            "https://images.unsplash.com/photo-1505664194779-8beaceb93744?w=1080&q=80"
        ],
        "source": "NEWS KID National",
        "publishedAt": (now - timedelta(minutes=45)).isoformat(),
        "views": 3120,
        "likes": 98
    },
    {
        "title": "शेयर बाजार में बंपर तेजी: सेंसेक्स और निफ्टी ने बनाया नया ऑल-टाइम हाई",
        "title_en": "Bull Run in Stock Market: Sensex and Nifty Breach Fresh Record Highs",
        "summary": "भारतीय शेयर बाजार में चौतरफा खरीदारी देखने को मिली। विदेशी निवेशकों की जबरदस्त लिवाली और मजबूत आर्थिक आंकड़ों के चलते सेंसेक्स 85,000 अंक के पार पहुंच गया। बैंकिंग और ऑटो शेयर्स में सबसे ज्यादा बढ़त दर्ज हुई।",
        "summary_en": "Indian equity benchmarks surged to unprecedented highs propelled by vigorous foreign institutional inflows and stellar corporate quarterly earnings outlook.",
        "category": "business",
        "badge": "💼 बिजनेस",
        "imageUrl": "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=1080&q=80",
        "images": [
            "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=1080&q=80",
            "https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?w=1080&q=80",
            "https://images.unsplash.com/photo-1642543492481-44e81e3914a7?w=1080&q=80"
        ],
        "source": "NEWS KID Market Desk",
        "publishedAt": (now - timedelta(minutes=70)).isoformat(),
        "views": 5120,
        "likes": 412
    },
    {
        "title": "टीम इंडिया का दबदबा: टेस्ट सीरीज में 2-0 की अजेय बढ़त बनाई",
        "title_en": "Team India Dominates: Takes Unassailable 2-0 Lead in Test Series",
        "summary": "भारतीय क्रिकेट टीम ने गेंदबाजों के आक्रामक स्पेल और मिडिल ऑर्डर के शतकीय पारियों की बदौलत टेस्ट मैच 180 रनों से जीत लिया। इस जीत के साथ ही भारत ने वर्ल्ड टेस्ट चैंपियनशिप की रैंकिंग में अपनी शीर्ष स्थिति मजबूत कर ली है।",
        "summary_en": "Team India scripted an authoritative 180-run triumph over the visitors, consolidating its top position in the ICC World Test Championship points table.",
        "category": "sports",
        "badge": "🏏 खेल",
        "imageUrl": "https://images.unsplash.com/photo-1540747913346-19e32dc3e97e?w=1080&q=80",
        "images": [
            "https://images.unsplash.com/photo-1540747913346-19e32dc3e97e?w=1080&q=80",
            "https://images.unsplash.com/photo-1531415074868-036b1c57e329?w=1080&q=80",
            "https://images.unsplash.com/photo-1519766304817-4f37bda74a29?w=1080&q=80"
        ],
        "source": "NEWS KID Sports Desk",
        "publishedAt": (now - timedelta(minutes=95)).isoformat(),
        "views": 6800,
        "likes": 589
    },
    {
        "title": "OpenAI ने पेश किया नया Reasoning Model o1: कोडिंग और मैथ्स में रचा इतिहास",
        "title_en": "OpenAI Unveils Reasoning Model o1: Breaks All Records in Coding & Math",
        "summary": "आर्टिफिशियल इंटेलिजेंस की दुनिया में बड़ा धमाका हुआ है। OpenAI ने नया o1 मॉडल लॉन्च किया है जो इंसान की तरह गहराई से सोचकर और स्टेप-बाय-स्टेप लॉजिक लगाकर कठिन गणित और कोडिंग की समस्याओं को हल कर सकता है।",
        "summary_en": "OpenAI officially rolled out its revolutionary reasoning model family capable of complex step-by-step thinking for competitive mathematics, coding, and scientific research.",
        "category": "tech",
        "badge": "🚀 AI & Tech",
        "imageUrl": "https://images.unsplash.com/photo-1677442136019-21780efad99a?w=1080&q=80",
        "images": [
            "https://images.unsplash.com/photo-1677442136019-21780efad99a?w=1080&q=80",
            "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?w=1080&q=80",
            "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=1080&q=80"
        ],
        "source": "NEWS KID Tech AI",
        "publishedAt": (now - timedelta(minutes=120)).isoformat(),
        "views": 7430,
        "likes": 845
    }
]

def seed():
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    db = client["newskid"]
    cards_coll = db["cards"]
    
    cards_coll.delete_many({})
    result = cards_coll.insert_many(SAMPLE_CARDS)
    print(f"Successfully seeded {len(result.inserted_ids)} 100% copyright-free cards into MongoDB Atlas!")

if __name__ == "__main__":
    seed()
