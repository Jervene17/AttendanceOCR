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
# Departments
FAMILY = "FAMILY"
CAREER_MALES = "CAREER MALES"
CAREER_FEMALES = "CAREER FEMALES"
CAMPUS_FEMALES = "CAMPUS FEMALES"
JS = "JS"
OPM = "OPM"
LLC = "LLC"
LVC = "LVC"

# Status
ACTIVE = "ACTIVE"
INACTIVE = "INACTIVE"
NEWCOMER = "NEWCOMER"

# Attendance modes
ONLINE = "ONLINE"
ONSITE = "ONSITE"
BOTH = "BOTH"

DEFAULT_ATTENDANCE = {
    "sunday": BOTH,
    "wednesday": BOTH,
    "predawn": BOTH,
}

def attendance(sunday=None, wednesday=None, predawn=None):
    result = DEFAULT_ATTENDANCE.copy()
    if sunday is not None:
        result["sunday"] = sunday
    if wednesday is not None:
        result["wednesday"] = wednesday
    if predawn is not None:
        result["predawn"] = predawn
    return result

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
        # =================================================
    # CAREER MALES
    # =================================================

    "CM001": {
        "display_name": "Jabs",
        "official_name": "Edgardo Magdua Jr.",
        "aliases": [
            "Jabs",
            "Edgardo",
            "Jabs Magdua",
            "Edgardo Magdua Jr",
            "D Jabs",
            "D.Jabs",
        ],
        "department": CAREER_MALES,
        "status": ACTIVE,
        "attendance": DEFAULT_ATTENDANCE.copy(),
        "sort_order": 1,
    },

    "CM002": {
        "display_name": "Xander",
        "official_name": "Alex Astucia",
        "aliases": [
            "Xander",
            "Alex",
            "Alex Astucia",
        ],
        "department": CAREER_MALES,
        "status": ACTIVE,
        "attendance": DEFAULT_ATTENDANCE.copy(),
        "sort_order": 2,
    },

    "CM003": {
        "display_name": "Franz",
        "official_name": "Franz Javier Jr.",
        "aliases": [
            "Franz",
            "Franz Javier",
            "Franz Javier Jr",
            "Franz Jr",
        ],
        "department": CAREER_MALES,
        "status": ACTIVE,
        "attendance": DEFAULT_ATTENDANCE.copy(),
        "sort_order": 3,
    },

    "CM004": {
        "display_name": "Daniel",
        "official_name": "Daniel Ezekiel Inson",
        "aliases": [
            "Daniel",
            "Daniel Inson",
            "Daniel Ezekiel",
            "Daniel Ezekiel Inson",
            "MCareer_Daniel Ezekiel",
        ],
        "department": CAREER_MALES,
        "status": ACTIVE,
        "attendance": DEFAULT_ATTENDANCE.copy(),
        "sort_order": 4,
    },

    "CM005": {
        "display_name": "Venancio",
        "official_name": "Venancio Jimenez III",
        "aliases": [
            "Ven",
            "Venancio",
            "Venancio Jimenez",
            "Venancio Jimenez III",
        ],
        "department": CAREER_MALES,
        "status": ACTIVE,
        "attendance": DEFAULT_ATTENDANCE.copy(),
        "sort_order": 5,
    },

    "CM006": {
        "display_name": "Gideon",
        "official_name": "Gideon Alidon",
        "aliases": [
            "Gideon",
            "Gideon Alidon",
        ],
        "department": CAREER_MALES,
        "status": ACTIVE,
        "attendance": DEFAULT_ATTENDANCE.copy(),
        "sort_order": 6,
    },
           # =================================================
    # CAREER FEMALES
    # =================================================

    "CrF001": {
        "display_name": "Shaja",
        "official_name": "Shaja Alcantara",
        "aliases": [
            "Shaja",
            "Shaja Alcantara",
        ],
        "department": CAREER_FEMALES,
        "status": ACTIVE,
        "attendance": DEFAULT_ATTENDANCE.copy(),
        "sort_order": 1,
    },

    "CrF002": {
        "display_name": "Grace",
        "official_name": "Grace Leguarda",
        "aliases": [
            "Grace",
            "Grace Leguarda",
            "Atty Grace",
        ],
        "department": CAREER_FEMALES,
        "status": ACTIVE,
        "attendance": DEFAULT_ATTENDANCE.copy(),
        "sort_order": 2,
    },

    "CrF003": {
        "display_name": "Daryl",
        "official_name": "Daryl Mitzi Evangelista",
        "aliases": [
            "Daryl",
            "Daryl Evangelista",
            "Daryl Mitzi Evangelista",
        ],
        "department": CAREER_FEMALES,
        "status": ACTIVE,
        "attendance": DEFAULT_ATTENDANCE.copy(),
        "sort_order": 3,
    },

    "CrF004": {
        "display_name": "Clarice",
        "official_name": "Clarice",
        "aliases": [
            "Clarice",
        ],
        "department": CAREER_FEMALES,
        "status": ACTIVE,
        "attendance": attendance(
            sunday=ONLINE,
            wednesday=ONLINE,
            predawn=ONLINE,
        ),
        "sort_order": 4,
    },

    "CrF005": {
        "display_name": "Aliza",
        "official_name": "Aliza Manuel",
        "aliases": [
            "Aliza",
            "Aliza Manuel",
        ],
        "department": CAREER_FEMALES,
        "status": ACTIVE,
        "attendance": attendance(
            sunday=ONLINE,
            wednesday=ONLINE,
            predawn=ONLINE,
        ),
        "sort_order": 5,
    },

    "CrF006": {
        "display_name": "Anica",
        "official_name": "Anica Astucia",
        "aliases": [
            "Anica",
            "Anica Astucia",
        ],
        "department": CAREER_FEMALES,
        "status": ACTIVE,
        "attendance": DEFAULT_ATTENDANCE.copy(),
        "sort_order": 6,
    },

    "CrF007": {
        "display_name": "Mel",
        "official_name": "Melanie Vaflor",
        "aliases": [
            "Mel",
            "Melanie",
            "Melanie Vaflor",
            "D Mel",
            "D.Mel",
            "DMel",
        ],
        "department": CAREER_FEMALES,
        "status": ACTIVE,
        "attendance": DEFAULT_ATTENDANCE.copy(),
        "sort_order": 7,
    },

    "CrF008": {
        "display_name": "Andrea",
        "official_name": "Andrea Bonifacio",
        "aliases": [
            "Andrea",
            "Andrea Bonifacio",
        ],
        "department": CAREER_FEMALES,
        "status": ACTIVE,
        "attendance": DEFAULT_ATTENDANCE.copy(),
        "sort_order": 8,
    },

    "CrF009": {
        "display_name": "Angel",
        "official_name": "Angel Galez",
        "aliases": [
            "Angel",
            "Angel Galez",
        ],
        "department": CAREER_FEMALES,
        "status": ACTIVE,
        "attendance": DEFAULT_ATTENDANCE.copy(),
        "sort_order": 9,
    },

    "CrF010": {
        "display_name": "M Rose",
        "official_name": "Rosemarie",
        "aliases": [
            "Rose",
            "Rosemarie",
            "Philippines_Rosemarie",
            "M Rose",
            "MRose",
            "M.Rose",
        ],
        "department": CAREER_FEMALES,
        "status": ACTIVE,
        "attendance": DEFAULT_ATTENDANCE.copy(),
        "sort_order": 10,
    },
        "CF011": {
        "display_name": "Vicky",
        "official_name": "Vicky Leguarda",
        "aliases": [
            "Vicky",
            "Vicky Leguarda",
        ],
        "department": CAREER_FEMALES,
        "status": ACTIVE,
        "attendance": DEFAULT_ATTENDANCE.copy(),
        "sort_order": 11,
    },

    "CrF012": {
        "display_name": "Donna",
        "official_name": "Donna Velasquez",
        "aliases": [
            "Donna",
            "Donna Velasquez",
        ],
        "department": CAREER_FEMALES,
        "status": ACTIVE,
        "attendance": attendance(
            sunday=ONLINE,
            wednesday=ONLINE,
            predawn=ONLINE,
        ),
        "sort_order": 12,
    },

    "CrF013": {
        "display_name": "D Rue",
        "official_name": "Rubilyn Narra",
        "aliases": [
            "D Rue",
            "Rue",
            "Rue Narra",
            "Rubilyn Narra",
        ],
        "department": CAREER_FEMALES,
        "status": ACTIVE,
        "attendance": DEFAULT_ATTENDANCE.copy(),
        "sort_order": 13,
    },

    "CrF014": {
        "display_name": "PP Bam",
        "official_name": "Gene Ann Ladaga",
        "aliases": [
            "PP Bam",
            "Bambi",
            "Bambi Ladaga",
            "Gene Ann Ladaga",
        ],
        "department": CAREER_FEMALES,
        "status": ACTIVE,
        "attendance": DEFAULT_ATTENDANCE.copy(),
        "sort_order": 14,
    },

    "CrF015": {
        "display_name": "Zhandra",
        "official_name": "Zhandra Tam",
        "aliases": [
            "Zhandra",
            "Zhandra Tam",
        ],
        "department": CAREER_FEMALES,
        "status": ACTIVE,
        "attendance": attendance(
            sunday=ONLINE,
            wednesday=ONLINE,
            predawn=ONLINE,
        ),
        "sort_order": 15,
    },

    "CrF016": {
        "display_name": "Trina",
        "official_name": "Trina Yabut",
        "aliases": [
            "Trina",
            "Trina Yabut",
            "T.Yabut",
        ],
        "department": CAREER_FEMALES,
        "status": ACTIVE,
        "attendance": DEFAULT_ATTENDANCE.copy(),
        "sort_order": 16,
    },

    "CrF017": {
        "display_name": "Dr Kristine",
        "official_name": "Kristine",
        "aliases": [
            "Dr Kristine",
            "Kristine",
        ],
        "department": CAREER_FEMALES,
        "status": INACTIVE,
        "attendance": attendance(
            sunday=ONLINE,
            wednesday=ONLINE,
            predawn=ONLINE,
        ),
        "sort_order": 17,
    },

    "CrF018": {
        "display_name": "Milca",
        "official_name": "Milca Angeles",
        "aliases": [
            "Milca",
            "Milca Angeles",
        ],
        "department": CAREER_FEMALES,
        "status": ACTIVE,
        "attendance": DEFAULT_ATTENDANCE.copy(),
        "sort_order": 18,
    },

    "CrF019": {
        "display_name": "Nelissa",
        "official_name": "Nelissa",
        "aliases": [
            "Nelissa",
        ],
        "department": CAREER_FEMALES,
        "status": ACTIVE,
        "attendance": attendance(
            sunday=ONLINE,
            wednesday=ONLINE,
            predawn=ONLINE,
        ),
        "sort_order": 19,
    },

    "CrF020": {
        "display_name": "Reisa",
        "official_name": "Reisa Gonzaga",
        "aliases": [
            "Reisa",
            "Reisa Gonzaga",
        ],
        "department": CAREER_FEMALES,
        "status": ACTIVE,
        "attendance": attendance(
            sunday=ONLINE,
            wednesday=ONLINE,
            predawn=ONLINE,
        ),
        "sort_order": 20,
    },
    "CrF021": {
        "display_name": "M Ju Nara",
        "official_name": "Krist Anonuevo",
        "aliases": [
            "M Ju Nara",
            "Ju Nara",
            "Krist Anonuevo",
            "HQ Junara",
        ],
        "department": CAREER_FEMALES,
        "status": ACTIVE,
        "attendance": DEFAULT_ATTENDANCE.copy(),
        "sort_order": 21,
    },

    "CrF022": {
        "display_name": "MA",
        "official_name": "Azzel Lao",
        "aliases": [
            "MA",
            "Azzel",
            "Azzel Lao",
            "Philippines Azzel",
        ],
        "department": CAREER_FEMALES,
        "status": ACTIVE,
        "attendance": DEFAULT_ATTENDANCE.copy(),
        "sort_order": 22,
    },

    "CrF023": {
        "display_name": "M Sarah",
        "official_name": "Sarah Alidon",
        "aliases": [
            "M Sarah",
            "Sarah",
            "Sarah Alidon",
            "M Sa",
            "M.Sa",
            "MSa",
        ],
        "department": CAREER_FEMALES,
        "status": ACTIVE,
        "attendance": DEFAULT_ATTENDANCE.copy(),
        "sort_order": 23,
    },
    "CrF024": {
        "display_name": "Joan",
        "official_name": "Joannes Alonsagay",
        "aliases": [
            "Joannes",
            "Joannes Alonsagay",
            "Annes Alonsagay",
            "Joannes Resurreccion",
            "Joannes Resurreccion Alonsagay",
        ],
        "department": CAREER_FEMALES,
        "status": ACTIVE,
        "attendance": DEFAULT_ATTENDANCE.copy(),
        "sort_order": 24,
    },
    # =================================================
    # CAMPUS FEMALES
    # =================================================

    "CAMP001": {
        "display_name": "Divine",
        "official_name": "Divine Hernandez",
        "aliases": [
            "Divine",
            "Divine Hernandez",
        ],
        "department": CAMPUS_FEMALES,
        "status": ACTIVE,
        "attendance": DEFAULT_ATTENDANCE.copy(),
        "sort_order": 1,
    },

    "CAMP002": {
        "display_name": "Marinell",
        "official_name": "Marinell Almero",
        "aliases": [
            "Marinell",
            "Marinell Almero",
        ],
        "department": CAMPUS_FEMALES,
        "status": ACTIVE,
        "attendance": DEFAULT_ATTENDANCE.copy(),
        "sort_order": 2,
    },
    # =================================================
    # JS
    # =================================================

    "JS001": {
        "display_name": "MCor",
        "official_name": "Corazon Lualhati",
        "aliases": [
            "MCor",
            "M Cor",
            "M.Cor",
            "Cor",
            "Corazon Lualhati",
            "Cor Lualhati"
        ],
        "department": JS,
        "status": ACTIVE,
        "attendance": DEFAULT_ATTENDANCE.copy(),
        "sort_order": 1,
    },

    "JS002": {
        "display_name": "Tita Merlita",
        "official_name": "Merlita Alidon",
        "aliases": [
            "Tita Merlita",
            "Merlita",
            "Merlita Alidon",
        ],
        "department": JS,
        "status": ACTIVE,
        "attendance": DEFAULT_ATTENDANCE.copy(),
        "sort_order": 2,
    },

    "JS003": {
        "display_name": "Grace",
        "official_name": "Grace Givera",
        "aliases": [
            "Grace",
            "Grace Givera",
            "Megumi",
            "Megumi Givera",
        ],
        "department": JS,
        "status": ACTIVE,
        "attendance": attendance(
            sunday=ONLINE,
            wednesday=ONLINE,
            predawn=ONLINE,
        ),
        "sort_order": 3,
    },

    "JS004": {
        "display_name": "Emeru",
        "official_name": "Emercedita Hiramatsu",
        "aliases": [
            "Emeru",
            "Emercedita Hiramatsu",
        ],
        "department": JS,
        "status": ACTIVE,
        "attendance": attendance(
            sunday=ONLINE,
            wednesday=ONLINE,
            predawn=ONLINE,
        ),
        "sort_order": 4,
    },

    "JS005": {
        "display_name": "Michelle",
        "official_name": "Michelle Bautista",
        "aliases": [
            "Michelle",
            "Michelle Bautista",
            "Mitch Bautista",
        ],
        "department": JS,
        "status": ACTIVE,
        "attendance": DEFAULT_ATTENDANCE.copy(),
        "sort_order": 5,
    },

    "JS006": {
        "display_name": "Edilyn",
        "official_name": "Edilyn",
        "aliases": [
            "Edilyn",
        ],
        "department": JS,
        "status": ACTIVE,
        "attendance": DEFAULT_ATTENDANCE.copy(),
        "sort_order": 6,
    },

    "JS007": {
        "display_name": "Raquel",
        "official_name": "Raquel",
        "aliases": [
            "Raquel",
        ],
        "department": JS,
        "status": ACTIVE,
        "attendance": DEFAULT_ATTENDANCE.copy(),
        "sort_order": 7,
    },

    "JS008": {
        "display_name": "Florelyn",
        "official_name": "Florelyn",
        "aliases": [
            "Florelyn",
        ],
        "department": JS,
        "status": ACTIVE,
        "attendance": DEFAULT_ATTENDANCE.copy(),
        "sort_order": 8,
    },
    # =================================================
    # OVERSEAS FILIPINO MEMBERS
    # =================================================

    "OPM001": {
        "display_name": "Cheyserr",
        "official_name": "Cheyserr Lamayra",
        "aliases": [
            "Cheyserr",
            "Cheyserr Lamayra",
        ],
        "department": OPM,
        "status": ACTIVE,
        "attendance": attendance(
            sunday=ONLINE,
            wednesday=ONLINE,
            predawn=ONLINE,
        ),
        "sort_order": 1,
    },

    "OPM002": {
        "display_name": "John Carlo",
        "official_name": "John Carlo Balmes Rucero",
        "aliases": [
            "John Carlo",
            "John Carlo Balmes Rucero",
            "John Carlo Rucero",
            "JC Lucero",
        ],
        "department": OPM,
        "status": ACTIVE,
        "attendance": attendance(
            sunday=ONLINE,
            wednesday=ONLINE,
            predawn=ONLINE,
        ),
        "sort_order": 2,
    },

    "OPM003": {
        "display_name": "M Saeyoung",
        "official_name": "Jeong Saeyoung",
        "aliases": [
            "M Saeyoung",
            "Saeyoung",
            "Jeong Saeyoung",
            "정새영",
            "정새영 Edelweiss",
            "Edelweiss",
        ],
        "department": OPM,
        "status": ACTIVE,
        "attendance": attendance(
            sunday=ONLINE,
            wednesday=ONLINE,
            predawn=ONLINE,
        ),
        "sort_order": 3,
    },

    "OPM004": {
        "display_name": "Miae",
        "official_name": "Miae Park",
        "aliases": [
            "Miae",
            "Miae Park",
        ],
        "department": OPM,
        "status": ACTIVE,
        "attendance": attendance(
            sunday=ONLINE,
            wednesday=ONLINE,
            predawn=ONLINE,
        ),
        "sort_order": 4,
    },

    "OPM005": {
        "display_name": "Andrew",
        "official_name": "Andrew Dela Cruz",
        "aliases": [
            "Andrew",
            "Andrew Dela Cruz",
        ],
        "department": OPM,
        "status": ACTIVE,
        "attendance": attendance(
            sunday=ONLINE,
            wednesday=ONLINE,
            predawn=ONLINE,
        ),
        "sort_order": 5,
    },

    "OPM006": {
        "display_name": "Cherry",
        "official_name": "Cherry Na",
        "aliases": [
            "Cherry",
            "체리 나",
            "Cherry Na",
        ],
        "department": OPM,
        "status": ACTIVE,
        "attendance": attendance(
            sunday=ONLINE,
            wednesday=ONLINE,
            predawn=ONLINE,
        ),
        "sort_order": 6,
    },
    # =================================================
    # LORD'S LOVE CHURCH
    # =================================================

    "LLC001": {
        "display_name": "LLC",
        "official_name": "Philippines LLC",
        "aliases": [
            "LLC",
            "Philippines LLC",
        ],
        "department": LLC,
        "status": ACTIVE,
        "attendance": attendance(
            sunday=ONLINE,
            wednesday=ONLINE,
            predawn=ONLINE,
        ),
        "sort_order": 1,
    },

    "LLC002": {
        "display_name": "Therese",
        "official_name": "Therese Marie Po",
        "aliases": [
            "Therese",
            "Therese Marie Po",
        ],
        "department": LLC,
        "status": ACTIVE,
        "attendance": attendance(
            sunday=ONLINE,
            wednesday=ONLINE,
            predawn=ONLINE,
        ),
        "sort_order": 2,
    },

    "LLC003": {
        "display_name": "Ria",
        "official_name": "Ria",
        "aliases": [
            "Ria",
            "LLC Ria",
        ],
        "department": LLC,
        "status": ACTIVE,
        "attendance": attendance(
            sunday=ONLINE,
            wednesday=ONLINE,
            predawn=ONLINE,
        ),
        "sort_order": 3,
    },

    "LLC004": {
        "display_name": "Irene",
        "official_name": "Irene Fe G. Vicerra",
        "aliases": [
            "Irene",
            "VICERRA, Irene Fe G.",
            "Irene Fe G. Vicerra",
        ],
        "department": LLC,
        "status": ACTIVE,
        "attendance": attendance(
            sunday=ONLINE,
            wednesday=ONLINE,
            predawn=ONLINE,
        ),
        "sort_order": 4,
    },

    "LLC005": {
        "display_name": "Daisy",
        "official_name": "Rose Daisy Jane T. Lemu",
        "aliases": [
            "Daisy",
            "LEMU, Rose Daisy Jane T.",
            "Rose Daisy Jane T. Lemu",
        ],
        "department": LLC,
        "status": ACTIVE,
        "attendance": attendance(
            sunday=ONLINE,
            wednesday=ONLINE,
            predawn=ONLINE,
        ),
        "sort_order": 5,
    },

    "LLC006": {
        "display_name": "Shaina",
        "official_name": "Shaina Fatima Inson",
        "aliases": [
            "Shaina",
            "Shaina Fatima Inson",
        ],
        "department": LLC,
        "status": ACTIVE,
        "attendance": attendance(
            sunday=ONLINE,
            wednesday=ONLINE,
            predawn=ONLINE,
        ),
        "sort_order": 6,
    },
    # =================================================
    # LORD'S VICTORY CHURCH
    # =================================================

    "LVC001": {
        "display_name": "Cynthia",
        "official_name": "Cynthia Aquino",
        "aliases": [
            "Cynthia",
            "Cynthia Aquino",
        ],
        "department": LVC,
        "status": ACTIVE,
        "attendance": attendance(
            sunday=ONLINE,
            wednesday=ONLINE,
            predawn=ONLINE,
        ),
        "sort_order": 1,
    },

    "LVC002": {
        "display_name": "Kezia",
        "official_name": "Kezia Aquino",
        "aliases": [
            "Kezia",
            "Kezia Aquino",
        ],
        "department": LVC,
        "status": NEWCOMER,
        "attendance": attendance(
            sunday=ONLINE,
            wednesday=ONLINE,
            predawn=ONLINE,
        ),
        "sort_order": 2,
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