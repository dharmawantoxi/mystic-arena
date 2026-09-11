# ================================
# hero_archetypes.py
#
# Kategori arketipe SEMUA hero yang bisa dimainkan (starter + 216 hero
# unlock dari mini boss & true boss):
#   dmg_type  : PHYSICAL / MAGIC  -> menentukan mitigasi lawan
#   playstyle : TANK / FIGHTER / CARRY -> label UI
#   tier      : S/A/B/C/D vs sesama kelas boss  (label UI)
#   power     : skor absolut 82% DPS + 18% EHP  (label UI)
#
# Sumber data: tools/analyze_hero_archetypes.py
# Regenerate:  python3 tools/analyze_hero_archetypes.py --emit-module \
#                hero_archetypes.py --emit-json hero_archetypes.json
# Port Godot:  godot/scripts/core/HeroArchetypes.gd (mirror 1:1; ikut
#              di-refresh dengan menambah --emit-gdscript pada command
#              regenerate di atas). Dikunci HeroArchetypesParityTest.
# ================================

# hero_type -> {dmg_type, playstyle, tier, power}
ARCHETYPES = {
    "aelyrion": {"dmg_type": "PHYSICAL", "playstyle": "FIGHTER", "tier": "B", "power": 56},
    "aeralith": {"dmg_type": "PHYSICAL", "playstyle": "FIGHTER", "tier": "D", "power": 27},
    "akahime": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "B", "power": 46},
    "akaroth": {"dmg_type": "PHYSICAL", "playstyle": "TANK", "tier": "S", "power": 79},
    "akashari": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "D", "power": 23},
    "akiraze": {"dmg_type": "PHYSICAL", "playstyle": "TANK", "tier": "S", "power": 81},
    "astraelion": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "B", "power": 51},
    "aurelian": {"dmg_type": "PHYSICAL", "playstyle": "TANK", "tier": "S", "power": 85},
    "aurelix": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "D", "power": 25},
    "aurelyssa": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "C", "power": 37},
    "aurex": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "C", "power": 33},
    "auroth": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "C", "power": 37},
    "azkharion": {"dmg_type": "PHYSICAL", "playstyle": "TANK", "tier": "A", "power": 68},
    "azureth": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "D", "power": 29},
    "bhorgathul": {"dmg_type": "PHYSICAL", "playstyle": "FIGHTER", "tier": "B", "power": 55},
    "broggmar": {"dmg_type": "PHYSICAL", "playstyle": "TANK", "tier": "A", "power": 75},
    "brumhar": {"dmg_type": "PHYSICAL", "playstyle": "TANK", "tier": "A", "power": 71},
    "celwynn": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "B", "power": 49},
    "cryssalia": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "C", "power": 36},
    "dorakai": {"dmg_type": "MAGIC", "playstyle": "TANK", "tier": "A", "power": 68},
    "drakar": {"dmg_type": "PHYSICAL", "playstyle": "FIGHTER", "tier": "D", "power": 19},
    "drav": {"dmg_type": "PHYSICAL", "playstyle": "FIGHTER", "tier": "C", "power": 42},
    "emberwick": {"dmg_type": "MAGIC", "playstyle": "CARRY", "tier": "B", "power": 57},
    "garumenshi": {"dmg_type": "PHYSICAL", "playstyle": "TANK", "tier": "A", "power": 67},
    "ghrakmaal": {"dmg_type": "PHYSICAL", "playstyle": "FIGHTER", "tier": "B", "power": 50},
    "gorath": {"dmg_type": "PHYSICAL", "playstyle": "FIGHTER", "tier": "D", "power": 21},
    "gornak": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "D", "power": 19},
    "gravefang": {"dmg_type": "PHYSICAL", "playstyle": "FIGHTER", "tier": "D", "power": 25},
    "gravewake": {"dmg_type": "PHYSICAL", "playstyle": "FIGHTER", "tier": "D", "power": 24},
    "grimjack": {"dmg_type": "MAGIC", "playstyle": "CARRY", "tier": "A", "power": 59},
    "grimstalker": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "B", "power": 55},
    "grondarthul": {"dmg_type": "PHYSICAL", "playstyle": "FIGHTER", "tier": "B", "power": 56},
    "hitokage": {"dmg_type": "PHYSICAL", "playstyle": "TANK", "tier": "S", "power": 97},
    "ignakhor": {"dmg_type": "PHYSICAL", "playstyle": "CARRY", "tier": "B", "power": 60},
    "ignirus": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "C", "power": 33},
    "infrakzaar": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "B", "power": 51},
    "kaedrin": {"dmg_type": "PHYSICAL", "playstyle": "CARRY", "tier": "A", "power": 61},
    "kaeldris": {"dmg_type": "PHYSICAL", "playstyle": "FIGHTER", "tier": "C", "power": 35},
    "kaelthar": {"dmg_type": "PHYSICAL", "playstyle": "FIGHTER", "tier": "B", "power": 48},
    "kaelthorn": {"dmg_type": "PHYSICAL", "playstyle": "FIGHTER", "tier": "C", "power": 44},
    "kaelthys": {"dmg_type": "PHYSICAL", "playstyle": "TANK", "tier": "S", "power": 86},
    "kaelvyrn": {"dmg_type": "PHYSICAL", "playstyle": "FIGHTER", "tier": "B", "power": 50},
    "kaerissa": {"dmg_type": "PHYSICAL", "playstyle": "TANK", "tier": "S", "power": 74},
    "kaervosth": {"dmg_type": "MAGIC", "playstyle": "CARRY", "tier": "B", "power": 58},
    "kairenji": {"dmg_type": "PHYSICAL", "playstyle": "TANK", "tier": "S", "power": 90},
    "kaizoku_raijin": {"dmg_type": "MAGIC", "playstyle": "TANK", "tier": "A", "power": 66},
    "kaoruken": {"dmg_type": "PHYSICAL", "playstyle": "TANK", "tier": "S", "power": 74},
    "karzhul": {"dmg_type": "PHYSICAL", "playstyle": "TANK", "tier": "A", "power": 68},
    "kassadin": {"dmg_type": "MAGIC", "playstyle": "TANK", "tier": "B", "power": 60},
    "kazreth": {"dmg_type": "PHYSICAL", "playstyle": "CARRY", "tier": "B", "power": 58},
    "kazuren": {"dmg_type": "MAGIC", "playstyle": "TANK", "tier": "S", "power": 95},
    "kazureth": {"dmg_type": "MAGIC", "playstyle": "CARRY", "tier": "A", "power": 61},
    "kenshiro": {"dmg_type": "PHYSICAL", "playstyle": "FIGHTER", "tier": "D", "power": 31},
    "khalros": {"dmg_type": "PHYSICAL", "playstyle": "FIGHTER", "tier": "D", "power": 22},
    "khalzaredh": {"dmg_type": "PHYSICAL", "playstyle": "FIGHTER", "tier": "B", "power": 56},
    "khazan": {"dmg_type": "PHYSICAL", "playstyle": "FIGHTER", "tier": "D", "power": 32},
    "korokai": {"dmg_type": "PHYSICAL", "playstyle": "TANK", "tier": "A", "power": 69},
    "krognarr": {"dmg_type": "PHYSICAL", "playstyle": "FIGHTER", "tier": "D", "power": 31},
    "kryvoxar": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "C", "power": 43},
    "kurogari": {"dmg_type": "PHYSICAL", "playstyle": "FIGHTER", "tier": "B", "power": 52},
    "kyumirra": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "B", "power": 45},
    "leoric": {"dmg_type": "PHYSICAL", "playstyle": "FIGHTER", "tier": "C", "power": 40},
    "luminar": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "D", "power": 30},
    "lyrenya": {"dmg_type": "MAGIC", "playstyle": "CARRY", "tier": "B", "power": 59},
    "lyrienne": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "C", "power": 43},
    "malzareth": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "D", "power": 21},
    "morgath": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "D", "power": 14},
    "morkhaera": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "C", "power": 37},
    "morkhelvis": {"dmg_type": "PHYSICAL", "playstyle": "FIGHTER", "tier": "B", "power": 54},
    "morthyrax": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "B", "power": 46},
    "morvaenthir": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "C", "power": 39},
    "morvaeth": {"dmg_type": "PHYSICAL", "playstyle": "CARRY", "tier": "B", "power": 57},
    "morvaeth2": {"dmg_type": "PHYSICAL", "playstyle": "CARRY", "tier": "B", "power": 60},
    "morvakhul": {"dmg_type": "PHYSICAL", "playstyle": "FIGHTER", "tier": "B", "power": 45},
    "morvath": {"dmg_type": "PHYSICAL", "playstyle": "TANK", "tier": "A", "power": 64},
    "morvein": {"dmg_type": "PHYSICAL", "playstyle": "FIGHTER", "tier": "C", "power": 40},
    "morvekhar": {"dmg_type": "PHYSICAL", "playstyle": "FIGHTER", "tier": "B", "power": 48},
    "morvyssk": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "B", "power": 54},
    "nixweaver": {"dmg_type": "PHYSICAL", "playstyle": "CARRY", "tier": "A", "power": 62},
    "nyxallaria": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "B", "power": 53},
    "nyxara": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "D", "power": 21},
    "nyxareva": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "C", "power": 35},
    "nyxariel": {"dmg_type": "MAGIC", "playstyle": "CARRY", "tier": "B", "power": 58},
    "nyxaroth": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "C", "power": 43},
    "nyxraal": {"dmg_type": "MAGIC", "playstyle": "TANK", "tier": "B", "power": 61},
    "nyxthrael": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "C", "power": 39},
    "nyzrak": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "D", "power": 20},
    "obanai": {"dmg_type": "PHYSICAL", "playstyle": "TANK", "tier": "S", "power": 91},
    "pyraklos": {"dmg_type": "PHYSICAL", "playstyle": "FIGHTER", "tier": "C", "power": 33},
    "pyrenth": {"dmg_type": "PHYSICAL", "playstyle": "FIGHTER", "tier": "D", "power": 25},
    "pyrhaan": {"dmg_type": "MAGIC", "playstyle": "TANK", "tier": "S", "power": 74},
    "rakzhan": {"dmg_type": "MAGIC", "playstyle": "CARRY", "tier": "A", "power": 67},
    "raz": {"dmg_type": "PHYSICAL", "playstyle": "FIGHTER", "tier": "C", "power": 34},
    "razak": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "D", "power": 20},
    "rynvara": {"dmg_type": "PHYSICAL", "playstyle": "CARRY", "tier": "A", "power": 65},
    "sanguire": {"dmg_type": "MAGIC", "playstyle": "TANK", "tier": "A", "power": 67},
    "sanguiveth": {"dmg_type": "PHYSICAL", "playstyle": "FIGHTER", "tier": "B", "power": 48},
    "sasori": {"dmg_type": "PHYSICAL", "playstyle": "TANK", "tier": "A", "power": 69},
    "selunara": {"dmg_type": "PHYSICAL", "playstyle": "FIGHTER", "tier": "B", "power": 51},
    "sethrakhar": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "B", "power": 47},
    "shimorakh": {"dmg_type": "MAGIC", "playstyle": "TANK", "tier": "B", "power": 60},
    "shirotaka": {"dmg_type": "PHYSICAL", "playstyle": "FIGHTER", "tier": "C", "power": 44},
    "sirakzan": {"dmg_type": "PHYSICAL", "playstyle": "CARRY", "tier": "A", "power": 69},
    "solara": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "C", "power": 38},
    "solvanth": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "C", "power": 35},
    "sylvantheros": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "C", "power": 38},
    "syrentha": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "D", "power": 19},
    "syrindra": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "B", "power": 48},
    "thalgryn": {"dmg_type": "PHYSICAL", "playstyle": "FIGHTER", "tier": "D", "power": 20},
    "thargoroth": {"dmg_type": "PHYSICAL", "playstyle": "FIGHTER", "tier": "B", "power": 53},
    "thoraz": {"dmg_type": "PHYSICAL", "playstyle": "TANK", "tier": "S", "power": 80},
    "thorgaruk": {"dmg_type": "PHYSICAL", "playstyle": "TANK", "tier": "A", "power": 65},
    "thornvaegrim": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "C", "power": 39},
    "thorvak": {"dmg_type": "PHYSICAL", "playstyle": "FIGHTER", "tier": "C", "power": 38},
    "thorvin": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "B", "power": 46},
    "urgharun": {"dmg_type": "PHYSICAL", "playstyle": "TANK", "tier": "S", "power": 76},
    "ursath": {"dmg_type": "MAGIC", "playstyle": "TANK", "tier": "A", "power": 63},
    "vaelkorr": {"dmg_type": "MAGIC", "playstyle": "TANK", "tier": "A", "power": 64},
    "vaerith": {"dmg_type": "PHYSICAL", "playstyle": "FIGHTER", "tier": "D", "power": 29},
    "valekris": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "B", "power": 50},
    "valthar": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "C", "power": 42},
    "vardrok": {"dmg_type": "PHYSICAL", "playstyle": "TANK", "tier": "B", "power": 57},
    "vargrath": {"dmg_type": "PHYSICAL", "playstyle": "FIGHTER", "tier": "C", "power": 35},
    "vargroth": {"dmg_type": "PHYSICAL", "playstyle": "FIGHTER", "tier": "B", "power": 55},
    "varkul": {"dmg_type": "PHYSICAL", "playstyle": "FIGHTER", "tier": "D", "power": 19},
    "varkuthar": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "B", "power": 54},
    "velmyrth": {"dmg_type": "PHYSICAL", "playstyle": "FIGHTER", "tier": "C", "power": 40},
    "verdanix": {"dmg_type": "PHYSICAL", "playstyle": "TANK", "tier": "B", "power": 59},
    "veshtrax": {"dmg_type": "PHYSICAL", "playstyle": "FIGHTER", "tier": "B", "power": 47},
    "vessyra": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "B", "power": 48},
    "vhaerinth": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "B", "power": 54},
    "vhaerith": {"dmg_type": "MAGIC", "playstyle": "TANK", "tier": "A", "power": 66},
    "vhalzun": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "D", "power": 20},
    "vhyssarion": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "D", "power": 22},
    "vokrahn": {"dmg_type": "PHYSICAL", "playstyle": "FIGHTER", "tier": "D", "power": 25},
    "vorenmarr": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "D", "power": 21},
    "vorgath": {"dmg_type": "PHYSICAL", "playstyle": "FIGHTER", "tier": "C", "power": 43},
    "vorthakul": {"dmg_type": "PHYSICAL", "playstyle": "TANK", "tier": "A", "power": 70},
    "vraskhan": {"dmg_type": "PHYSICAL", "playstyle": "FIGHTER", "tier": "C", "power": 36},
    "vulkareth": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "C", "power": 44},
    "vyraeth": {"dmg_type": "MAGIC", "playstyle": "CARRY", "tier": "B", "power": 60},
    "wiro": {"dmg_type": "PHYSICAL", "playstyle": "FIGHTER", "tier": "D", "power": 32},
    "xaerissa": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "B", "power": 49},
    "xareth": {"dmg_type": "PHYSICAL", "playstyle": "TANK", "tier": "A", "power": 70},
    "xarnathul": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "B", "power": 50},
    "xarnthuul": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "B", "power": 56},
    "xerakhotep": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "B", "power": 45},
    "xerakkuth": {"dmg_type": "MAGIC", "playstyle": "TANK", "tier": "S", "power": 78},
    "xerathis": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "D", "power": 17},
    "xharokh": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "B", "power": 52},
    "xirthalis": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "D", "power": 31},
    "xyrael": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "B", "power": 47},
    "yhoranth": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "B", "power": 56},
    "zahkareth": {"dmg_type": "PHYSICAL", "playstyle": "CARRY", "tier": "B", "power": 58},
    "zhaeris": {"dmg_type": "PHYSICAL", "playstyle": "TANK", "tier": "S", "power": 88},
    "zharok": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "D", "power": 18},
    "zhyrakaan": {"dmg_type": "PHYSICAL", "playstyle": "TANK", "tier": "A", "power": 68},
    "zhyvrek": {"dmg_type": "PHYSICAL", "playstyle": "TANK", "tier": "S", "power": 72},
    "zorashi": {"dmg_type": "MAGIC", "playstyle": "CARRY", "tier": "B", "power": 59},
    "zorathiel": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "B", "power": 52},
    "zorothrax": {"dmg_type": "MAGIC", "playstyle": "TANK", "tier": "B", "power": 58},
    "zulkhaven": {"dmg_type": "PHYSICAL", "playstyle": "FIGHTER", "tier": "B", "power": 57},
    "grimjaw": {"dmg_type": "PHYSICAL", "playstyle": "FIGHTER", "tier": "B", "power": 8},
    "kaizen": {"dmg_type": "PHYSICAL", "playstyle": "FIGHTER", "tier": "A", "power": 9},
    "sylara": {"dmg_type": "PHYSICAL", "playstyle": "FIGHTER", "tier": "B", "power": 6},
    "thorne": {"dmg_type": "PHYSICAL", "playstyle": "FIGHTER", "tier": "B", "power": 11},
    "vex": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "C", "power": 6},
    "zephyr": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "B", "power": 6},
    "abaddon": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "D", "power": 24},
    "akirakumo": {"dmg_type": "PHYSICAL", "playstyle": "TANK", "tier": "S", "power": 100},
    "alchemist": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "D", "power": 24},
    "ancient_apparition": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "D", "power": 19},
    "aurelion": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "C", "power": 41},
    "aurethzar": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "D", "power": 33},
    "cogsworth": {"dmg_type": "PHYSICAL", "playstyle": "TANK", "tier": "A", "power": 83},
    "deidara": {"dmg_type": "PHYSICAL", "playstyle": "TANK", "tier": "A", "power": 79},
    "grimkor": {"dmg_type": "PHYSICAL", "playstyle": "TANK", "tier": "S", "power": 85},
    "grondmauris": {"dmg_type": "MAGIC", "playstyle": "TANK", "tier": "B", "power": 60},
    "hollowbane": {"dmg_type": "PHYSICAL", "playstyle": "TANK", "tier": "S", "power": 100},
    "ignis_drachorn": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "D", "power": 26},
    "kaerinya": {"dmg_type": "PHYSICAL", "playstyle": "TANK", "tier": "A", "power": 81},
    "kagetsuka": {"dmg_type": "PHYSICAL", "playstyle": "TANK", "tier": "S", "power": 95},
    "kaineroth": {"dmg_type": "MAGIC", "playstyle": "TANK", "tier": "A", "power": 74},
    "kaithros": {"dmg_type": "PHYSICAL", "playstyle": "TANK", "tier": "S", "power": 100},
    "krobellus": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "D", "power": 24},
    "kunkka": {"dmg_type": "PHYSICAL", "playstyle": "FIGHTER", "tier": "D", "power": 30},
    "kyrenzai": {"dmg_type": "PHYSICAL", "playstyle": "TANK", "tier": "S", "power": 84},
    "lyssarethys": {"dmg_type": "MAGIC", "playstyle": "TANK", "tier": "B", "power": 63},
    "malzeroth": {"dmg_type": "MAGIC", "playstyle": "CARRY", "tier": "B", "power": 58},
    "molgravar": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "C", "power": 45},
    "morthraxis": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "B", "power": 53},
    "naraka": {"dmg_type": "PHYSICAL", "playstyle": "FIGHTER", "tier": "C", "power": 39},
    "nazulmor": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "C", "power": 41},
    "nexthyrius": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "C", "power": 46},
    "nyrellieth": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "B", "power": 54},
    "nyrethzalv": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "B", "power": 52},
    "nyxarath": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "D", "power": 24},
    "nyxareth": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "C", "power": 40},
    "nyxaris": {"dmg_type": "MAGIC", "playstyle": "TANK", "tier": "S", "power": 90},
    "nyxharr": {"dmg_type": "MAGIC", "playstyle": "CARRY", "tier": "B", "power": 58},
    "okeanora": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "C", "power": 48},
    "pyraena": {"dmg_type": "MAGIC", "playstyle": "TANK", "tier": "A", "power": 81},
    "pyraethis": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "C", "power": 38},
    "ravokkar": {"dmg_type": "PHYSICAL", "playstyle": "CARRY", "tier": "B", "power": 58},
    "seiryukong": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "C", "power": 40},
    "seraphienne": {"dmg_type": "PHYSICAL", "playstyle": "FIGHTER", "tier": "B", "power": 56},
    "solareth": {"dmg_type": "PHYSICAL", "playstyle": "TANK", "tier": "B", "power": 58},
    "solvarin": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "C", "power": 41},
    "sunakage": {"dmg_type": "MAGIC", "playstyle": "TANK", "tier": "A", "power": 80},
    "thalakryon": {"dmg_type": "PHYSICAL", "playstyle": "FIGHTER", "tier": "C", "power": 40},
    "thalryndel": {"dmg_type": "MAGIC", "playstyle": "TANK", "tier": "A", "power": 72},
    "tsukiyora": {"dmg_type": "MAGIC", "playstyle": "TANK", "tier": "S", "power": 92},
    "vaelindra": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "C", "power": 43},
    "vaelmyrra": {"dmg_type": "PHYSICAL", "playstyle": "TANK", "tier": "B", "power": 61},
    "vhorethzir": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "D", "power": 24},
    "xaelmoran": {"dmg_type": "MAGIC", "playstyle": "TANK", "tier": "A", "power": 69},
    "xelnarath": {"dmg_type": "MAGIC", "playstyle": "TANK", "tier": "B", "power": 66},
    "yamako": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "C", "power": 39},
    "yomigetsu": {"dmg_type": "PHYSICAL", "playstyle": "TANK", "tier": "S", "power": 100},
    "zarethyr": {"dmg_type": "MAGIC", "playstyle": "FIGHTER", "tier": "B", "power": 51},
    "zharakzuul": {"dmg_type": "MAGIC", "playstyle": "TANK", "tier": "B", "power": 60},
    "zyvareth": {"dmg_type": "MAGIC", "playstyle": "TANK", "tier": "S", "power": 93},
}


# ════════════════════════════════════════════════════════════════════════
# Helper arketipe
# ------------------------------------------------------------------------
# Dipakai _entity.Hero (menentukan self.dmg_school) dan boss (menentukan
# armor vs magic_resist). Modul ini SENGAJA tidak mengimpor apa pun dari
# game supaya bisa dipakai tools/ dan ikut ter-bundle ke APK.
# ════════════════════════════════════════════════════════════════════════

# Hero tanpa entri eksplisit (mis. boss baru yang belum dianalisis)
# dianggap fisik supaya tidak tiba-tiba kebal armor.
DEFAULT_DMG_TYPE = "PHYSICAL"


def get_archetype(hero_type, stats=None):
    """Return dict arketipe hero.

    Kalau `stats` punya kunci ``dmg_type`` (override manual di
    boss_data['hero_unlock']), kunci itu menang - desainer bisa
    menimpa hasil analisis per hero tanpa regenerasi data.
    """
    if stats:
        forced = stats.get("dmg_type")
        if forced:
            forced = str(forced).upper()
            entry = dict(ARCHETYPES.get(hero_type, {}))
            entry["dmg_type"] = forced if forced in ("PHYSICAL", "MAGIC") \
                else DEFAULT_DMG_TYPE
            entry.setdefault("playstyle", "FIGHTER")
            return entry
    entry = ARCHETYPES.get(hero_type)
    if entry:
        return entry
    return {"dmg_type": DEFAULT_DMG_TYPE, "playstyle": "FIGHTER",
            "tier": "", "power": 0, "derived": True}


def school_of(hero_type, stats=None):
    """'physical' | 'magic' - bentuk lowercase untuk pipeline damage."""
    return get_archetype(hero_type, stats)["dmg_type"].lower()


# ════════════════════════════════════════════════════════════════════════
# RESISTANSI BOSS PER PROFIL (armor vs magic resist)
# ------------------------------------------------------------------------
# v1 dulu memakai SATU angka untuk semua boss (mini 12/0.10, true 18/0.20)
# sehingga "sekolah" damage tidak punya arti taktis: magic selalu untung
# (menembus armor menara yang MR-nya 0) dan fisik selalu rugi
# (magic/phys = 1.32 vs mini, 1.12 vs true).
#
# Sekarang tiap boss dapat profil dari tema boss-nya (leksikon tools/),
# lalu VARIASI antar profil itu dikalibrasi per kelas boss supaya rata-rata
# efektivitas fisik vs magic seimbang (tools/balance_audit.py ->
# effective_dps_vs_boss), sementara rata-rata mitigasi tiap kelas TETAP
# di baseline-nya. Boss mini bertema baja = wilayah hero magic; boss true
# bertema sihir = wilayah hero fisik.
#
# Regenerate SEMUA blok DATA di bawah:
#   python3 tools/analyze_hero_archetypes.py --quiet \
#       --emit-module hero_archetypes.py --emit-json hero_archetypes.json \
#       --emit-boss-res
# ════════════════════════════════════════════════════════════════════════

# kurva mitigasi armor: red = armor*FACTOR/(1+armor*FACTOR)
ARMOR_FACTOR = 0.06
ARMOR_MAX = 40
MR_MAX = 0.45

# armor/mitigasi dasar per kelas boss (rata-rata yang dijaga kalibrasi)
BOSS_RESIST_BASE = {"mini": (12, 0.10), "true": (18, 0.20)}

# ── BUKAN AUTO-GENERATED: desain dasar, diedit manual ──────────────────
# modifier per profil tema boss (delta armor, delta magic_resist) relatif
# terhadap baseline kelas. tool kalibrasi menggeser PUSAT sebaran ini ke
# rata-rata baseline lalu mengalikannya (BOSS_RESIST_SCALE) untuk mengejar
# parity fisik/magic - angka di bawah adalah niat desainnya.
BOSS_RESIST_PROFILE_MODS = {
    "armored": (10.0, -0.040),    # baja/batu/fortress: anti-fisik, tembus sihir
    "brute":   (3.0, 0.020),      # petarung kasar: sedikit lebih tahan fisik
    "balanced": (0.0, 0.0),       # boss standar = baseline kelas
    "soft":    (-2.0, -0.020),    # HP tipis: menahan sedikit lebih sedikit
    "magic":   (-4.0, 0.060),     # caster/undead/void: sihir mental, fisik masuk
}

# hasil kalibrasi: pengali selisih profil per kelas boss
BOSS_RESIST_SCALE = {
    "mini": {"armor": 1.3200, "mr": 1.8000},
    "true": {"armor": 1.2720, "mr": 1.8000},
}

# rasio target rata-rata (magic DPS efektif) / (fisik DPS efektif)
BOSS_RESIST_TARGET_RATIO = 1.00


def _resist_from_profile(profile, boss_class, base=None, mods=None,
                         armor_scale=1.0, mr_scale=1.0, armor_off=0):
    """(armor, magic_resist) satu profil boss pada kelas `boss_class`.

    Baseline kelas (mini 12/0.10, true 18/0.20) adalah PUSAT sebarannya;
    yang diskalakan hanya selisih antar profil, jadi kalibrasi parity
    sekolah menggeser "siapa ditahan siapa", bukan mematikan mitigasi.
    """
    base = base or BOSS_RESIST_BASE
    mods = mods or BOSS_RESIST_PROFILE_MODS
    b_armor, b_mr = base.get(boss_class, base.get("mini", (12, 0.10)))
    d_armor, d_mr = mods.get(profile, (0.0, 0.0))
    armor = float(b_armor) + float(d_armor) * float(armor_scale) + armor_off
    armor = int(max(0, min(ARMOR_MAX, round(armor))))
    mr = float(b_mr) + float(d_mr) * float(mr_scale)
    mr = max(0.0, min(MR_MAX, mr))
    return armor, mr


def physical_mitigation(armor):
    """Fraksi damage fisik yang LOLOS armor (0..1)."""
    armor = max(0.0, float(armor))
    return 1.0 - armor * ARMOR_FACTOR / (1.0 + armor * ARMOR_FACTOR)


def get_boss_resistances(boss_type, boss_class="mini"):
    """(armor, magic_resist) untuk satu boss; default dari profil/rumus."""
    entry = BOSS_RESISTANCES.get(boss_type)
    if entry:
        return int(entry["armor"]), float(entry["magic_resist"])
    sc = BOSS_RESIST_SCALE.get(boss_class, {})
    return _resist_from_profile("balanced", boss_class,
                                armor_scale=sc.get("armor", 1.0),
                                mr_scale=sc.get("mr", 1.0))


# boss_type -> {armor, magic_resist, profile, boss_class}
BOSS_RESISTANCES = {
    "abaddon": {"armor": 32, "magic_resist": 0.095, "profile": "armored", "boss_class": "true"},
    "aelyrion": {"armor": 26, "magic_resist": 0.007, "profile": "armored", "boss_class": "mini"},
    "aeralith": {"armor": 13, "magic_resist": 0.079, "profile": "balanced", "boss_class": "mini"},
    "akahime": {"armor": 10, "magic_resist": 0.043, "profile": "soft", "boss_class": "mini"},
    "akaroth": {"armor": 26, "magic_resist": 0.007, "profile": "armored", "boss_class": "mini"},
    "akashari": {"armor": 10, "magic_resist": 0.043, "profile": "soft", "boss_class": "mini"},
    "akirakumo": {"armor": 17, "magic_resist": 0.131, "profile": "soft", "boss_class": "true"},
    "akiraze": {"armor": 10, "magic_resist": 0.043, "profile": "soft", "boss_class": "mini"},
    "alchemist": {"armor": 14, "magic_resist": 0.275, "profile": "magic", "boss_class": "true"},
    "ancient_apparition": {"armor": 14, "magic_resist": 0.275, "profile": "magic", "boss_class": "true"},
    "astraelion": {"armor": 10, "magic_resist": 0.043, "profile": "soft", "boss_class": "mini"},
    "aurelian": {"armor": 10, "magic_resist": 0.043, "profile": "soft", "boss_class": "mini"},
    "aurelion": {"armor": 23, "magic_resist": 0.203, "profile": "brute", "boss_class": "true"},
    "aurelix": {"armor": 8, "magic_resist": 0.187, "profile": "magic", "boss_class": "mini"},
    "aurelyssa": {"armor": 8, "magic_resist": 0.187, "profile": "magic", "boss_class": "mini"},
    "aurethzar": {"armor": 14, "magic_resist": 0.275, "profile": "magic", "boss_class": "true"},
    "aurex": {"armor": 26, "magic_resist": 0.007, "profile": "armored", "boss_class": "mini"},
    "auroth": {"armor": 26, "magic_resist": 0.007, "profile": "armored", "boss_class": "mini"},
    "azkharion": {"armor": 13, "magic_resist": 0.079, "profile": "balanced", "boss_class": "mini"},
    "azureth": {"armor": 8, "magic_resist": 0.187, "profile": "magic", "boss_class": "mini"},
    "bhorgathul": {"armor": 13, "magic_resist": 0.079, "profile": "balanced", "boss_class": "mini"},
    "broggmar": {"armor": 17, "magic_resist": 0.115, "profile": "brute", "boss_class": "mini"},
    "brumhar": {"armor": 10, "magic_resist": 0.043, "profile": "soft", "boss_class": "mini"},
    "celwynn": {"armor": 8, "magic_resist": 0.187, "profile": "magic", "boss_class": "mini"},
    "cogsworth": {"armor": 19, "magic_resist": 0.167, "profile": "balanced", "boss_class": "true"},
    "cryssalia": {"armor": 8, "magic_resist": 0.187, "profile": "magic", "boss_class": "mini"},
    "deidara": {"armor": 19, "magic_resist": 0.167, "profile": "balanced", "boss_class": "true"},
    "dorakai": {"armor": 10, "magic_resist": 0.043, "profile": "soft", "boss_class": "mini"},
    "drakar": {"armor": 13, "magic_resist": 0.079, "profile": "balanced", "boss_class": "mini"},
    "drav": {"armor": 17, "magic_resist": 0.115, "profile": "brute", "boss_class": "mini"},
    "emberwick": {"armor": 10, "magic_resist": 0.043, "profile": "soft", "boss_class": "mini"},
    "garumenshi": {"armor": 13, "magic_resist": 0.079, "profile": "balanced", "boss_class": "mini"},
    "ghrakmaal": {"armor": 17, "magic_resist": 0.115, "profile": "brute", "boss_class": "mini"},
    "gorath": {"armor": 17, "magic_resist": 0.115, "profile": "brute", "boss_class": "mini"},
    "gornak": {"armor": 8, "magic_resist": 0.187, "profile": "magic", "boss_class": "mini"},
    "gravefang": {"armor": 26, "magic_resist": 0.007, "profile": "armored", "boss_class": "mini"},
    "gravewake": {"armor": 13, "magic_resist": 0.079, "profile": "balanced", "boss_class": "mini"},
    "grimjack": {"armor": 8, "magic_resist": 0.187, "profile": "magic", "boss_class": "mini"},
    "grimkor": {"armor": 19, "magic_resist": 0.167, "profile": "balanced", "boss_class": "true"},
    "grimstalker": {"armor": 8, "magic_resist": 0.187, "profile": "magic", "boss_class": "mini"},
    "grondarthul": {"armor": 13, "magic_resist": 0.079, "profile": "balanced", "boss_class": "mini"},
    "grondmauris": {"armor": 23, "magic_resist": 0.203, "profile": "brute", "boss_class": "true"},
    "hitokage": {"armor": 10, "magic_resist": 0.043, "profile": "soft", "boss_class": "mini"},
    "hollowbane": {"armor": 17, "magic_resist": 0.131, "profile": "soft", "boss_class": "true"},
    "ignakhor": {"armor": 13, "magic_resist": 0.079, "profile": "balanced", "boss_class": "mini"},
    "ignirus": {"armor": 8, "magic_resist": 0.187, "profile": "magic", "boss_class": "mini"},
    "ignis_drachorn": {"armor": 23, "magic_resist": 0.203, "profile": "brute", "boss_class": "true"},
    "infrakzaar": {"armor": 8, "magic_resist": 0.187, "profile": "magic", "boss_class": "mini"},
    "kaedrin": {"armor": 13, "magic_resist": 0.079, "profile": "balanced", "boss_class": "mini"},
    "kaeldris": {"armor": 13, "magic_resist": 0.079, "profile": "balanced", "boss_class": "mini"},
    "kaelthar": {"armor": 10, "magic_resist": 0.043, "profile": "soft", "boss_class": "mini"},
    "kaelthorn": {"armor": 26, "magic_resist": 0.007, "profile": "armored", "boss_class": "mini"},
    "kaelthys": {"armor": 13, "magic_resist": 0.079, "profile": "balanced", "boss_class": "mini"},
    "kaelvyrn": {"armor": 10, "magic_resist": 0.043, "profile": "soft", "boss_class": "mini"},
    "kaerinya": {"armor": 23, "magic_resist": 0.203, "profile": "brute", "boss_class": "true"},
    "kaerissa": {"armor": 13, "magic_resist": 0.079, "profile": "balanced", "boss_class": "mini"},
    "kaervosth": {"armor": 8, "magic_resist": 0.187, "profile": "magic", "boss_class": "mini"},
    "kagetsuka": {"armor": 19, "magic_resist": 0.167, "profile": "balanced", "boss_class": "true"},
    "kaineroth": {"armor": 17, "magic_resist": 0.131, "profile": "soft", "boss_class": "true"},
    "kairenji": {"armor": 10, "magic_resist": 0.043, "profile": "soft", "boss_class": "mini"},
    "kaithros": {"armor": 14, "magic_resist": 0.275, "profile": "magic", "boss_class": "true"},
    "kaizoku_raijin": {"armor": 8, "magic_resist": 0.187, "profile": "magic", "boss_class": "mini"},
    "kaoruken": {"armor": 13, "magic_resist": 0.079, "profile": "balanced", "boss_class": "mini"},
    "karzhul": {"armor": 13, "magic_resist": 0.079, "profile": "balanced", "boss_class": "mini"},
    "kassadin": {"armor": 10, "magic_resist": 0.043, "profile": "soft", "boss_class": "mini"},
    "kazreth": {"armor": 13, "magic_resist": 0.079, "profile": "balanced", "boss_class": "mini"},
    "kazuren": {"armor": 8, "magic_resist": 0.187, "profile": "magic", "boss_class": "mini"},
    "kazureth": {"armor": 8, "magic_resist": 0.187, "profile": "magic", "boss_class": "mini"},
    "kenshiro": {"armor": 13, "magic_resist": 0.079, "profile": "balanced", "boss_class": "mini"},
    "khalros": {"armor": 10, "magic_resist": 0.043, "profile": "soft", "boss_class": "mini"},
    "khalzaredh": {"armor": 10, "magic_resist": 0.043, "profile": "soft", "boss_class": "mini"},
    "khazan": {"armor": 13, "magic_resist": 0.079, "profile": "balanced", "boss_class": "mini"},
    "korokai": {"armor": 13, "magic_resist": 0.079, "profile": "balanced", "boss_class": "mini"},
    "krobellus": {"armor": 17, "magic_resist": 0.131, "profile": "soft", "boss_class": "true"},
    "krognarr": {"armor": 26, "magic_resist": 0.007, "profile": "armored", "boss_class": "mini"},
    "kryvoxar": {"armor": 8, "magic_resist": 0.187, "profile": "magic", "boss_class": "mini"},
    "kunkka": {"armor": 17, "magic_resist": 0.131, "profile": "soft", "boss_class": "true"},
    "kurogari": {"armor": 8, "magic_resist": 0.187, "profile": "magic", "boss_class": "mini"},
    "kyrenzai": {"armor": 19, "magic_resist": 0.167, "profile": "balanced", "boss_class": "true"},
    "kyumirra": {"armor": 8, "magic_resist": 0.187, "profile": "magic", "boss_class": "mini"},
    "leoric": {"armor": 17, "magic_resist": 0.115, "profile": "brute", "boss_class": "mini"},
    "luminar": {"armor": 10, "magic_resist": 0.043, "profile": "soft", "boss_class": "mini"},
    "lyrenya": {"armor": 10, "magic_resist": 0.043, "profile": "soft", "boss_class": "mini"},
    "lyrienne": {"armor": 13, "magic_resist": 0.079, "profile": "balanced", "boss_class": "mini"},
    "lyssarethys": {"armor": 14, "magic_resist": 0.275, "profile": "magic", "boss_class": "true"},
    "malzareth": {"armor": 8, "magic_resist": 0.187, "profile": "magic", "boss_class": "mini"},
    "malzeroth": {"armor": 14, "magic_resist": 0.275, "profile": "magic", "boss_class": "true"},
    "molgravar": {"armor": 32, "magic_resist": 0.095, "profile": "armored", "boss_class": "true"},
    "morgath": {"armor": 8, "magic_resist": 0.187, "profile": "magic", "boss_class": "mini"},
    "morkhaera": {"armor": 8, "magic_resist": 0.187, "profile": "magic", "boss_class": "mini"},
    "morkhelvis": {"armor": 13, "magic_resist": 0.079, "profile": "balanced", "boss_class": "mini"},
    "morthraxis": {"armor": 17, "magic_resist": 0.131, "profile": "soft", "boss_class": "true"},
    "morthyrax": {"armor": 10, "magic_resist": 0.043, "profile": "soft", "boss_class": "mini"},
    "morvaenthir": {"armor": 8, "magic_resist": 0.187, "profile": "magic", "boss_class": "mini"},
    "morvaeth": {"armor": 13, "magic_resist": 0.079, "profile": "balanced", "boss_class": "mini"},
    "morvaeth2": {"armor": 13, "magic_resist": 0.079, "profile": "balanced", "boss_class": "mini"},
    "morvakhul": {"armor": 8, "magic_resist": 0.187, "profile": "magic", "boss_class": "mini"},
    "morvath": {"armor": 10, "magic_resist": 0.043, "profile": "soft", "boss_class": "mini"},
    "morvein": {"armor": 8, "magic_resist": 0.187, "profile": "magic", "boss_class": "mini"},
    "morvekhar": {"armor": 26, "magic_resist": 0.007, "profile": "armored", "boss_class": "mini"},
    "morvyssk": {"armor": 10, "magic_resist": 0.043, "profile": "soft", "boss_class": "mini"},
    "naraka": {"armor": 14, "magic_resist": 0.275, "profile": "magic", "boss_class": "true"},
    "nazulmor": {"armor": 19, "magic_resist": 0.167, "profile": "balanced", "boss_class": "true"},
    "nexthyrius": {"armor": 14, "magic_resist": 0.275, "profile": "magic", "boss_class": "true"},
    "nixweaver": {"armor": 13, "magic_resist": 0.079, "profile": "balanced", "boss_class": "mini"},
    "nyrellieth": {"armor": 14, "magic_resist": 0.275, "profile": "magic", "boss_class": "true"},
    "nyrethzalv": {"armor": 19, "magic_resist": 0.167, "profile": "balanced", "boss_class": "true"},
    "nyxallaria": {"armor": 8, "magic_resist": 0.187, "profile": "magic", "boss_class": "mini"},
    "nyxara": {"armor": 8, "magic_resist": 0.187, "profile": "magic", "boss_class": "mini"},
    "nyxarath": {"armor": 14, "magic_resist": 0.275, "profile": "magic", "boss_class": "true"},
    "nyxareth": {"armor": 14, "magic_resist": 0.275, "profile": "magic", "boss_class": "true"},
    "nyxareva": {"armor": 13, "magic_resist": 0.079, "profile": "balanced", "boss_class": "mini"},
    "nyxariel": {"armor": 10, "magic_resist": 0.043, "profile": "soft", "boss_class": "mini"},
    "nyxaris": {"armor": 17, "magic_resist": 0.131, "profile": "soft", "boss_class": "true"},
    "nyxaroth": {"armor": 10, "magic_resist": 0.043, "profile": "soft", "boss_class": "mini"},
    "nyxharr": {"armor": 14, "magic_resist": 0.275, "profile": "magic", "boss_class": "true"},
    "nyxraal": {"armor": 10, "magic_resist": 0.043, "profile": "soft", "boss_class": "mini"},
    "nyxthrael": {"armor": 8, "magic_resist": 0.187, "profile": "magic", "boss_class": "mini"},
    "nyzrak": {"armor": 10, "magic_resist": 0.043, "profile": "soft", "boss_class": "mini"},
    "obanai": {"armor": 10, "magic_resist": 0.043, "profile": "soft", "boss_class": "mini"},
    "okeanora": {"armor": 17, "magic_resist": 0.131, "profile": "soft", "boss_class": "true"},
    "pyraena": {"armor": 14, "magic_resist": 0.275, "profile": "magic", "boss_class": "true"},
    "pyraethis": {"armor": 14, "magic_resist": 0.275, "profile": "magic", "boss_class": "true"},
    "pyraklos": {"armor": 17, "magic_resist": 0.115, "profile": "brute", "boss_class": "mini"},
    "pyrenth": {"armor": 13, "magic_resist": 0.079, "profile": "balanced", "boss_class": "mini"},
    "pyrhaan": {"armor": 10, "magic_resist": 0.043, "profile": "soft", "boss_class": "mini"},
    "rakzhan": {"armor": 8, "magic_resist": 0.187, "profile": "magic", "boss_class": "mini"},
    "ravokkar": {"armor": 19, "magic_resist": 0.167, "profile": "balanced", "boss_class": "true"},
    "raz": {"armor": 13, "magic_resist": 0.079, "profile": "balanced", "boss_class": "mini"},
    "razak": {"armor": 10, "magic_resist": 0.043, "profile": "soft", "boss_class": "mini"},
    "rynvara": {"armor": 10, "magic_resist": 0.043, "profile": "soft", "boss_class": "mini"},
    "sanguire": {"armor": 8, "magic_resist": 0.187, "profile": "magic", "boss_class": "mini"},
    "sanguiveth": {"armor": 13, "magic_resist": 0.079, "profile": "balanced", "boss_class": "mini"},
    "sasori": {"armor": 10, "magic_resist": 0.043, "profile": "soft", "boss_class": "mini"},
    "seiryukong": {"armor": 17, "magic_resist": 0.131, "profile": "soft", "boss_class": "true"},
    "selunara": {"armor": 10, "magic_resist": 0.043, "profile": "soft", "boss_class": "mini"},
    "seraphienne": {"armor": 19, "magic_resist": 0.167, "profile": "balanced", "boss_class": "true"},
    "sethrakhar": {"armor": 13, "magic_resist": 0.079, "profile": "balanced", "boss_class": "mini"},
    "shimorakh": {"armor": 13, "magic_resist": 0.079, "profile": "balanced", "boss_class": "mini"},
    "shirotaka": {"armor": 13, "magic_resist": 0.079, "profile": "balanced", "boss_class": "mini"},
    "sirakzan": {"armor": 13, "magic_resist": 0.079, "profile": "balanced", "boss_class": "mini"},
    "solara": {"armor": 26, "magic_resist": 0.007, "profile": "armored", "boss_class": "mini"},
    "solareth": {"armor": 19, "magic_resist": 0.167, "profile": "balanced", "boss_class": "true"},
    "solvanth": {"armor": 17, "magic_resist": 0.115, "profile": "brute", "boss_class": "mini"},
    "solvarin": {"armor": 32, "magic_resist": 0.095, "profile": "armored", "boss_class": "true"},
    "sunakage": {"armor": 14, "magic_resist": 0.275, "profile": "magic", "boss_class": "true"},
    "sylvantheros": {"armor": 13, "magic_resist": 0.079, "profile": "balanced", "boss_class": "mini"},
    "syrentha": {"armor": 8, "magic_resist": 0.187, "profile": "magic", "boss_class": "mini"},
    "syrindra": {"armor": 10, "magic_resist": 0.043, "profile": "soft", "boss_class": "mini"},
    "thalakryon": {"armor": 19, "magic_resist": 0.167, "profile": "balanced", "boss_class": "true"},
    "thalgryn": {"armor": 13, "magic_resist": 0.079, "profile": "balanced", "boss_class": "mini"},
    "thalryndel": {"armor": 14, "magic_resist": 0.275, "profile": "magic", "boss_class": "true"},
    "thargoroth": {"armor": 17, "magic_resist": 0.115, "profile": "brute", "boss_class": "mini"},
    "thoraz": {"armor": 17, "magic_resist": 0.115, "profile": "brute", "boss_class": "mini"},
    "thorgaruk": {"armor": 8, "magic_resist": 0.187, "profile": "magic", "boss_class": "mini"},
    "thornvaegrim": {"armor": 17, "magic_resist": 0.115, "profile": "brute", "boss_class": "mini"},
    "thorvak": {"armor": 17, "magic_resist": 0.115, "profile": "brute", "boss_class": "mini"},
    "thorvin": {"armor": 26, "magic_resist": 0.007, "profile": "armored", "boss_class": "mini"},
    "tsukiyora": {"armor": 17, "magic_resist": 0.131, "profile": "soft", "boss_class": "true"},
    "urgharun": {"armor": 13, "magic_resist": 0.079, "profile": "balanced", "boss_class": "mini"},
    "ursath": {"armor": 17, "magic_resist": 0.115, "profile": "brute", "boss_class": "mini"},
    "vaelindra": {"armor": 17, "magic_resist": 0.131, "profile": "soft", "boss_class": "true"},
    "vaelkorr": {"armor": 8, "magic_resist": 0.187, "profile": "magic", "boss_class": "mini"},
    "vaelmyrra": {"armor": 23, "magic_resist": 0.203, "profile": "brute", "boss_class": "true"},
    "vaerith": {"armor": 8, "magic_resist": 0.187, "profile": "magic", "boss_class": "mini"},
    "valekris": {"armor": 10, "magic_resist": 0.043, "profile": "soft", "boss_class": "mini"},
    "valthar": {"armor": 17, "magic_resist": 0.115, "profile": "brute", "boss_class": "mini"},
    "vardrok": {"armor": 13, "magic_resist": 0.079, "profile": "balanced", "boss_class": "mini"},
    "vargrath": {"armor": 10, "magic_resist": 0.043, "profile": "soft", "boss_class": "mini"},
    "vargroth": {"armor": 13, "magic_resist": 0.079, "profile": "balanced", "boss_class": "mini"},
    "varkul": {"armor": 8, "magic_resist": 0.187, "profile": "magic", "boss_class": "mini"},
    "varkuthar": {"armor": 10, "magic_resist": 0.043, "profile": "soft", "boss_class": "mini"},
    "velmyrth": {"armor": 10, "magic_resist": 0.043, "profile": "soft", "boss_class": "mini"},
    "verdanix": {"armor": 8, "magic_resist": 0.187, "profile": "magic", "boss_class": "mini"},
    "veshtrax": {"armor": 17, "magic_resist": 0.115, "profile": "brute", "boss_class": "mini"},
    "vessyra": {"armor": 17, "magic_resist": 0.115, "profile": "brute", "boss_class": "mini"},
    "vhaerinth": {"armor": 10, "magic_resist": 0.043, "profile": "soft", "boss_class": "mini"},
    "vhaerith": {"armor": 8, "magic_resist": 0.187, "profile": "magic", "boss_class": "mini"},
    "vhalzun": {"armor": 8, "magic_resist": 0.187, "profile": "magic", "boss_class": "mini"},
    "vhorethzir": {"armor": 14, "magic_resist": 0.275, "profile": "magic", "boss_class": "true"},
    "vhyssarion": {"armor": 8, "magic_resist": 0.187, "profile": "magic", "boss_class": "mini"},
    "vokrahn": {"armor": 13, "magic_resist": 0.079, "profile": "balanced", "boss_class": "mini"},
    "vorenmarr": {"armor": 8, "magic_resist": 0.187, "profile": "magic", "boss_class": "mini"},
    "vorgath": {"armor": 17, "magic_resist": 0.115, "profile": "brute", "boss_class": "mini"},
    "vorthakul": {"armor": 10, "magic_resist": 0.043, "profile": "soft", "boss_class": "mini"},
    "vraskhan": {"armor": 13, "magic_resist": 0.079, "profile": "balanced", "boss_class": "mini"},
    "vulkareth": {"armor": 8, "magic_resist": 0.187, "profile": "magic", "boss_class": "mini"},
    "vyraeth": {"armor": 8, "magic_resist": 0.187, "profile": "magic", "boss_class": "mini"},
    "wiro": {"armor": 10, "magic_resist": 0.043, "profile": "soft", "boss_class": "mini"},
    "xaelmoran": {"armor": 17, "magic_resist": 0.131, "profile": "soft", "boss_class": "true"},
    "xaerissa": {"armor": 13, "magic_resist": 0.079, "profile": "balanced", "boss_class": "mini"},
    "xareth": {"armor": 10, "magic_resist": 0.043, "profile": "soft", "boss_class": "mini"},
    "xarnathul": {"armor": 10, "magic_resist": 0.043, "profile": "soft", "boss_class": "mini"},
    "xarnthuul": {"armor": 10, "magic_resist": 0.043, "profile": "soft", "boss_class": "mini"},
    "xelnarath": {"armor": 14, "magic_resist": 0.275, "profile": "magic", "boss_class": "true"},
    "xerakhotep": {"armor": 8, "magic_resist": 0.187, "profile": "magic", "boss_class": "mini"},
    "xerakkuth": {"armor": 8, "magic_resist": 0.187, "profile": "magic", "boss_class": "mini"},
    "xerathis": {"armor": 8, "magic_resist": 0.187, "profile": "magic", "boss_class": "mini"},
    "xharokh": {"armor": 8, "magic_resist": 0.187, "profile": "magic", "boss_class": "mini"},
    "xirthalis": {"armor": 8, "magic_resist": 0.187, "profile": "magic", "boss_class": "mini"},
    "xyrael": {"armor": 10, "magic_resist": 0.043, "profile": "soft", "boss_class": "mini"},
    "yamako": {"armor": 23, "magic_resist": 0.203, "profile": "brute", "boss_class": "true"},
    "yhoranth": {"armor": 10, "magic_resist": 0.043, "profile": "soft", "boss_class": "mini"},
    "yomigetsu": {"armor": 17, "magic_resist": 0.131, "profile": "soft", "boss_class": "true"},
    "zahkareth": {"armor": 13, "magic_resist": 0.079, "profile": "balanced", "boss_class": "mini"},
    "zarethyr": {"armor": 14, "magic_resist": 0.275, "profile": "magic", "boss_class": "true"},
    "zhaeris": {"armor": 10, "magic_resist": 0.043, "profile": "soft", "boss_class": "mini"},
    "zharakzuul": {"armor": 14, "magic_resist": 0.275, "profile": "magic", "boss_class": "true"},
    "zharok": {"armor": 10, "magic_resist": 0.043, "profile": "soft", "boss_class": "mini"},
    "zhyrakaan": {"armor": 8, "magic_resist": 0.187, "profile": "magic", "boss_class": "mini"},
    "zhyvrek": {"armor": 10, "magic_resist": 0.043, "profile": "soft", "boss_class": "mini"},
    "zorashi": {"armor": 10, "magic_resist": 0.043, "profile": "soft", "boss_class": "mini"},
    "zorathiel": {"armor": 8, "magic_resist": 0.187, "profile": "magic", "boss_class": "mini"},
    "zorothrax": {"armor": 8, "magic_resist": 0.187, "profile": "magic", "boss_class": "mini"},
    "zulkhaven": {"armor": 13, "magic_resist": 0.079, "profile": "balanced", "boss_class": "mini"},
    "zyvareth": {"armor": 14, "magic_resist": 0.275, "profile": "magic", "boss_class": "true"},
}
