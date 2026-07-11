import os
from dotenv import load_dotenv

# =====================================================
# Environment Variables
# =====================================================

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# =====================================================
# Group Checker Mapping
# =====================================================

USER_GROUP_MAP = {
    503493798: "FAMILY",
    485107813: "CAREER MALES",
    7681981308: "CAREER FEMALES",
    2016438287: "CAMPUS FEMALES",
    544095264: "JS",
    515714808: "HQ PLUS HL",
}

# =====================================================
# Checker Display Names
# =====================================================

USER_NAMES = {
    503493798: "Fatima",
    485107813: "Jabs",
    707729145: "Shaja",
    518836085: "Mel",
    7681981308: "D Rue",
    2016438287: "Divine",
    544095264: "MCor",
    515714808: "Jervene",
}

# =====================================================
# Department Members
# =====================================================

MEMBER_LISTS = {

    "FAMILY": [
        "Fatima",
        "Vangie",
        "M Ru",
        "Dcns Frances",
        "Shayne",
        "Dcns Issa",
        "Hannah",
        "Dcn Ian",
        "M Jervene",
        "Jessie",
        "Almen",
        "Dcn Probo",
        "Fernan",
        "Jiboy",
        "Riza",
        "Lavinia",
        "Iven",
    ],

    "CAREER MALES": [
        "Jabs",
        "Xander",
        "Franz",
        "Daniel",
        "Venancio",
        "Gideon",
    ],

    "CAREER FEMALES": [
        "Shaja",
        "Grace",
        "Daryl",
        "Clarice",
        "Aliza",
        "Anica",
        "Mel",
        "Andrea",
        "Angel",
        "Inia",
        "M Rose",
        "Vicky",
        "Donna",
        "D Rue",
        "PP Bam",
        "Zhandra",
        "Trina",
        "Dr Kristine",
        "Milca",
        "M Saeyoung"
    ],

    "CAMPUS FEMALES": [
        "Divine",
        "Marinell",
    ],

    "JS": [
        "MCor",
        "Tita Merlita",
        "Grace",
        "Emeru",
        "Michelle",
        "Edilyn",
        "Raquel",
        "Florelyn",
    ],

    "HQ PLUS HL": [
        "PK",
        "M Ju Nara",
        "MA",
        "M Sarah",
        "Mjhay",
        "PA",
    ],
}
# =====================================================
# Master Member Registry
# =====================================================

MEMBERS = {

    # ===== FAMILY =====

    1: {
        "name": "Fatima",
        "aliases": ["Fatima Venturina","Fatima Berliene Venturina"],
        "department": "FAMILY",
        "type": "Member",
        "status": "ACTIVE",
    },

    2: {
        "name": "Vangie",
        "aliases": ["Vangie Dolom"],
        "department": "FAMILY",
        "type": "Member",
        "status": "ACTIVE",
    },

    3: {
        "name": "M Ru",
        "aliases": ["Ruby","Ruby Valderrama","Ruby Santos","Ruby Valderrama Santos","Ruby Valderrama-Santos"],
        "department": "FAMILY",
        "type": "Member",
        "status": "ACTIVE",
    },

    4: {
        "name": "Dcns Frances",
        "aliases": ["Frances Canillas","Frances Ann Canillas"],
        "department": "FAMILY",
        "type": "Member",
        "status": "ACTIVE",
    },

    5: {
        "name": "Shayne",
        "aliases": ["Shayne Ericka","Shayne Ombao","Shayne Ericka Ombao","Shayne Dalde"],
        "department": "FAMILY",
        "type": "Member",
        "status": "ACTIVE",
    },

    6: {
        "name": "Dcns Issa",
        "aliases": ["Issa","Marissa", "Issa Liponhay", "Marissa Pastor","Marissa Pastor Liponhay","Issa Pastor","Issa Pastor Liponhay"],
        "department": "FAMILY",
        "type": "Member",
    },

    7: {
        "name": "Hannah",
        "aliases": ["Hannah Zotomayor", "Hannah Sanz"],
        "department": "FAMILY",
        "type": "Member",
    },

    8: {
        "name": "Dcn Ian",
        "aliases": ["Jhong","Ian Liponhay","Jhong Liponhay"],
        "department": "FAMILY",
        "type": "Member",
    },

    9: {
        "name": "M Jervene",
        "aliases": ["Jervene Venturina","Jervene"],
        "department": "FAMILY",
        "type": "Member",
    },

    10: {
        "name": "Jessie",
        "aliases": ["Jessie Dalde","Jessie"],
        "department": "FAMILY",
        "type": "Member",
    },

    11: {
        "name": "Almen",
        "aliases": ["Almen Dolom","Almen"],
        "department": "FAMILY",
        "type": "Member",
    },

    12: {
        "name": "Dcn Probo",
        "aliases": ["Probo Canillas","Probo"],
        "department": "FAMILY",
        "type": "Member",
    },

    13: {
        "name": "Fernan",
        "aliases": ["Fernan Zotomayor","Fernan"],
        "department": "FAMILY",
        "type": "Member",
    },

    14: {
        "name": "Jiboy",
        "aliases": ["Jiboy","Honesto Juego","Jiboy Juego","Juego, Honesto Jr, Martinez"],
        "department": "FAMILY",
        "type": "Member",
    },

    15: {
        "name": "Riza",
        "aliases": ["Riza Gabriela","Riza","Riza Bonifacio"],
        "department": "FAMILY",
        "type": "Member",
    },

    16: {
        "name": "Lavinia",
        "aliases": ["Lavinia","Inia","Lavina Arances","Lavina Harris"],
        "department": "FAMILY",
        "type": "Member",
    },

    17: {
        "name": "Iven",
        "aliases": ["Iven", "Axel","Iven Harris","Iven Axel Harris"],
        "department": "FAMILY",
        "type": "Member",
    },
    # ===== CAREER MALES =====

    18: {
        "name": "Jabs",
        "aliases": ["Jabs","Edgardo","Jabs Magdua","Edgardo Magdua Jr"],
        "department": "CAREER MALES",
        "type": "Member",
    },

    19: {
        "name": "Xander",
        "aliases": ["Alex","Alex Astucia", "Xander"],
        "department": "CAREER MALES",
        "type": "Member",
    },

    20: {
        "name": "Franz",
        "aliases": [
            "Franz Javier",
            "Franz Javier Jr",
            "Franz Jr","Franz"
        ],
        "department": "CAREER MALES",
        "type": "Member",
    },

    21: {
        "name": "Daniel",
        "aliases": ["Daniel Inson","Daniel","Daniel Ezekiel","Daniel Ezekiel Inson","MCareer_Daniel Ezekiel"],
        "department": "CAREER MALES",
        "type": "Member",
    },

    22: {
        "name": "Venancio",
        "aliases": ["Ven","Venancio Jimenez","Venancio Jimenez III"],
        "department": "CAREER MALES",
        "type": "Member",
    },

    23: {
        "name": "Gideon",
        "aliases": [
            "Gideon Alidon","Gideon"
        ],
        "department": "CAREER MALES",
        "type": "Member",
    },
        # ===== CAREER FEMALES =====

    24: {
        "name": "Shaja",
        "aliases": ["Shaja","Shaja Alcantara"],
        "department": "CAREER FEMALES",
        "type": "Member",
    },

    25: {
        "name": "Grace",
        "aliases": ["Grace","Grace Leguarda"],
        "department": "CAREER FEMALES",
        "type": "Member",
    },

    26: {
        "name": "Daryl",
        "aliases": ["Daryl","Daryl Mitzi Evangelista"],
        "department": "CAREER FEMALES",
        "type": "Member",
    },

    27: {
        "name": "Clarice",
        "aliases": ["Clarice"],
        "department": "CAREER FEMALES",
        "type": "Member",
    },

    28: {
        "name": "Aliza",
        "aliases": ["Aliza","Aliza Manuel"],
        "department": "CAREER FEMALES",
        "type": "Member",
    },

    29: {
        "name": "Anica",
        "aliases": ["Anica","Anica Astucia"],
        "department": "CAREER FEMALES",
        "type": "Member",
    },

    30: {
        "name": "Mel",
        "aliases": ["Mel","Melanie","Melanie Vaflor"],
        "department": "CAREER FEMALES",
        "type": "Member",
    },

    31: {
        "name": "Andrea",
        "aliases": ["Andrea","Andrea Bonifacio"],
        "department": "CAREER FEMALES",
        "type": "Member",
    },

    32: {
        "name": "Angel",
        "aliases": ["Angel","Angel Galez"],
        "department": "CAREER FEMALES",
        "type": "Member",
    },

    34: {
        "name": "M Rose",
        "aliases": [
            "Rose","Rosemarie","Philippines_Rosemarie"
        ],
        "department": "CAREER FEMALES",
        "type": "Member",
    },

    35: {
        "name": "Vicky",
        "aliases": ["Vicky","Vicky Leguarda"],
        "department": "CAREER FEMALES",
        "type": "Member",
    },

    36: {
        "name": "Donna",
        "aliases": ["Donna","Donna Velasquez"],
        "department": "CAREER FEMALES",
        "type": "Member",
    },
        # ===== CAREER FEMALES 3 =====

    37: {
        "name": "D Rue",
        "aliases": ["Rue","Rue Narra","Rubilyn Narra"],
        "department": "CAREER FEMALES",
        "status": "ACTIVE",
    },

    38: {
        "name": "PP Bam",
        "aliases": ["Bambi","Bambi Ladaga","Gene Ann Ladaga"],
        "department": "CAREER FEMALES",
        "status": "ACTIVE",
    },

    39: {
        "name": "Zhandra",
        "aliases": ["Zhandra","Zhandra Tam"],
        "department": "CAREER FEMALES",
        "status": "ACTIVE",
    },

    40: {
        "name": "Trina",
        "aliases": ["Trina","Trina Yabut"],
        "department": "CAREER FEMALES",
        "status": "ACTIVE",
    },

    41: {
        "name": "Dr Kristine",
        "aliases": [
            "Kristine"
        ],
        "department": "CAREER FEMALES",
        "status": "INACTIVE",
    },

    42: {
        "name": "Milca",
        "aliases": ["Milca","Milca Angeles"],
        "department": "CAREER FEMALES",
        "status": "ACTIVE",
    },
    43: {
        "name": "Nelissa",
        "aliases": ["Nelissa",],
        "department": "CAREER FEMALES",
        "status": "ACTIVE",
    },
    44: {
        "name": "Reisa",
        "aliases": ["Reisa Gonzaga","Reisa"],
        "department": "CAREER FEMALES",
        "status": "ACTIVE",
    },
}

# =====================================================
# Helper Functions
# =====================================================

def get_member(member_id):
    return MEMBERS.get(member_id)


def get_name(member_id):
    member = MEMBERS.get(member_id)
    return member["name"] if member else None


def get_department(member_id):
    member = MEMBERS.get(member_id)
    return member["department"] if member else None


def get_members_by_department(department):
    return {
        member_id: member
        for member_id, member in MEMBERS.items()
        if member["department"] == department
    }
# =====================================================
# Reverse Lookup
# =====================================================

GROUP_MEMBERS = {}

for user_id, group in USER_GROUP_MAP.items():
    GROUP_MEMBERS.setdefault(group, []).append(user_id)