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

   MEMBERS = {

    # =================================================
    # FAMILY
    # =================================================

    "FAM001": {
        "display_name": "Fatima",
        "official_name": "Fatima Berliene Venturina",
        "aliases": [
            "Fatima",
            "Fatima Venturina",
            "Fatima Berliene Venturina",
            "D.Fatima",
            "DFatima",
            "D Fatima",
        ],
        "department": FAMILY,
        "status": ACTIVE,
        "attendance": DEFAULT_ATTENDANCE.copy(),
        "sort_order": 1,
    },

    "FAM002": {
        "display_name": "Vangie",
        "official_name": "Vangie Dolom",
        "aliases": [
            "Vangie",
            "Vangie Dolom",
        ],
        "department": FAMILY,
        "status": ACTIVE,
        "attendance": DEFAULT_ATTENDANCE.copy(),
        "sort_order": 2,
    },

    "FAM003": {
        "display_name": "M Ru",
        "official_name": "Ruby Valderrama Santos",
        "aliases": [
            "Ruby",
            "Ruby Valderrama",
            "Ruby Santos",
            "Ruby Valderrama Santos",
            "Ruby Valderrama-Santos",
            "MRu",
            "M.Ru",
            "M Ru",
        ],
        "department": FAMILY,
        "status": ACTIVE,
        "attendance": DEFAULT_ATTENDANCE.copy(),
        "sort_order": 3,
    },

    "FAM004": {
        "display_name": "Dcns Frances",
        "official_name": "Frances Ann Canillas",
        "aliases": [
            "Frances",
            "Frances Canillas",
            "Frances Ann Canillas",
            "Dcns Frances",
        ],
        "department": FAMILY,
        "status": ACTIVE,
        "attendance": DEFAULT_ATTENDANCE.copy(),
        "sort_order": 4,
    },

    "FAM005": {
        "display_name": "Shayne",
        "official_name": "Shayne Ericka Ombao",
        "aliases": [
            "Shayne",
            "Shayne Ericka",
            "Shayne Ombao",
            "Shayne Ericka Ombao",
            "Shayne Dalde",
        ],
        "department": FAMILY,
        "status": ACTIVE,
        "attendance": DEFAULT_ATTENDANCE.copy(),
        "sort_order": 5,
    },

    "FAM006": {
        "display_name": "Dcns Issa",
        "official_name": "Marissa Pastor Liponhay",
        "aliases": [
            "Issa",
            "Marissa",
            "Issa Liponhay",
            "Marissa Pastor",
            "Marissa Pastor Liponhay",
            "Issa Pastor",
            "Issa Pastor Liponhay",
            "Dcns Issa",
        ],
        "department": FAMILY,
        "status": ACTIVE,
        "attendance": DEFAULT_ATTENDANCE.copy(),
        "sort_order": 6,
    },

    "FAM007": {
        "display_name": "Hannah",
        "official_name": "Hannah Zotomayor",
        "aliases": [
            "Hannah",
            "Hannah Zotomayor",
            "Hannah Sanz",
        ],
        "department": FAMILY,
        "status": ACTIVE,
        "attendance": DEFAULT_ATTENDANCE.copy(),
        "sort_order": 7,
    },

    "FAM008": {
        "display_name": "Dcn Ian",
        "official_name": "Ian Liponhay",
        "aliases": [
            "Ian",
            "Jhong",
            "Ian Liponhay",
            "Jhong Liponhay",
            "Dcn Jhong",
            "Dcn Ian",
        ],
        "department": FAMILY,
        "status": ACTIVE,
        "attendance": DEFAULT_ATTENDANCE.copy(),
        "sort_order": 8,
    },

    "FAM009": {
        "display_name": "M Jervene",
        "official_name": "Jervene Venturina",
        "aliases": [
            "Jervene",
            "Jervene Venturina",
            "M Jervene",
            "M.Jervene",
        ],
        "department": FAMILY,
        "status": ACTIVE,
        "attendance": DEFAULT_ATTENDANCE.copy(),
        "sort_order": 9,
    },

    "FAM010": {
        "display_name": "Jessie",
        "official_name": "Jessie Dalde",
        "aliases": [
            "Jessie",
            "Jessie Dalde",
            "D.Jessie",
            "DJessie",
            "D Jessie",
        ],
        "department": FAMILY,
        "status": ACTIVE,
        "attendance": DEFAULT_ATTENDANCE.copy(),
        "sort_order": 10,
    },

    "FAM011": {
        "display_name": "Almen",
        "official_name": "Almen Dolom",
        "aliases": [
            "Almen",
            "Almen Dolom",
        ],
        "department": FAMILY,
        "status": ACTIVE,
        "attendance": DEFAULT_ATTENDANCE.copy(),
        "sort_order": 11,
    },

    "FAM012": {
        "display_name": "Dcn Probo",
        "official_name": "Probo Canillas",
        "aliases": [
            "Probo",
            "Probo Canillas",
            "Dcn Probo",
        ],
        "department": FAMILY,
        "status": ACTIVE,
        "attendance": DEFAULT_ATTENDANCE.copy(),
        "sort_order": 12,
    },

    "FAM013": {
        "display_name": "Fernan",
        "official_name": "Fernan Zotomayor",
        "aliases": [
            "Fernan",
            "Fernan Zotomayor",
        ],
        "department": FAMILY,
        "status": ACTIVE,
        "attendance": DEFAULT_ATTENDANCE.copy(),
        "sort_order": 13,
    },

    "FAM014": {
        "display_name": "Jiboy",
        "official_name": "Honesto Martinez Juego Jr.",
        "aliases": [
            "Jiboy",
            "Jiboy Juego",
            "Honesto Juego",
            "Juego, Honesto Jr, Martinez",
        ],
        "department": FAMILY,
        "status": ACTIVE,
        "attendance": DEFAULT_ATTENDANCE.copy(),
        "sort_order": 14,
    },

    "FAM015": {
        "display_name": "Riza",
        "official_name": "Riza Gabriela Bonifacio",
        "aliases": [
            "Riza",
            "Riza Gabriela",
            "Riza Bonifacio",
        ],
        "department": FAMILY,
        "status": ACTIVE,
        "attendance": DEFAULT_ATTENDANCE.copy(),
        "sort_order": 15,
    },

    "FAM016": {
        "display_name": "Lavinia",
        "official_name": "Lavinia Arances Harris",
        "aliases": [
            "Lavinia",
            "Lavina",
            "Lavina Arances",
            "Lavina Harris",
            "Inia",
        ],
        "department": FAMILY,
        "status": ACTIVE,
        "attendance": DEFAULT_ATTENDANCE.copy(),
        "sort_order": 16,
    },

    "FAM017": {
        "display_name": "Iven",
        "official_name": "Iven Axel Harris",
        "aliases": [
            "Iven",
            "Axel",
            "Iven Harris",
            "Iven Axel Harris",
        ],
        "department": FAMILY,
        "status": ACTIVE,
        "attendance": DEFAULT_ATTENDANCE.copy(),
        "sort_order": 17,
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