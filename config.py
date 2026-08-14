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
MILKY_WAY_SS = "Milky Way and SS"

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

# =====================================================
# Retro Submission Organizers
# =====================================================
# User IDs allowed to initiate retro submissions (including
# Sunday retro, which bypasses the department-checker flow).
ORGANIZER_IDS = [
    515714808, 
    503493798,
]
USER_GROUP_MAP = {
    503493798: "FAMILY",
    485107813: "CAREER MALES",
    7681981308: "CAREER FEMALES",
    2016438287: "CAMPUS FEMALES",
    544095264: "JS",
    515714808: "MILKY WAY and SS",
}

# =====================================================
# Checker Display Names
# =====================================================

USER_NAMES = {
    503493798: "Fatima",
    485107813: "Jabs",
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
        "M Jhay",
        "Dcns Frances",
        "Shayne",
        "Eldress Issa",
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
        "M Rose",
        "Vicky",
        "Donna",
        "D Rue",
        "PP Bam",
        "Zhandra",
        "Trina",
        "Dr Kristine",
        "Milca",
        "Joannes",
        "M Ju Nara",
        "M Sarah",
        "M Azzel",
        "P Auda",
        "Reisa",
        "Nelissa",
        "MCor",
    ],

    "CAMPUS FEMALES": [
        "Divine",
        "Marinell",
    ],

    "JS": [
        "Tita Merlita",
        "Grace - Japan",
        "Emeru",
        "Michelle",
        "Edilyn",
        "Raquel",
        "Florelyn",
    ],

    "OPM": [
        "John Carlo",
        "Cherry",
        "Miae",
        "Cheyserr",
        "M Saeyoung",
        "Alma Joy",
    ],

    "Newcomers": [
        "NC RD",
        "Kezia Aquino",
        "NC HM",
    ],

    "LLC": [
        "Leah Jean",
        "Therese",
        "Shaina",
        "Daisy",
        "Ria",
        "Irene",
    ],

    "LVC": [
        "Cynthia Aquino",
        "Diane",
        "Kezia",
        "Glory",
    ],

    "Milky Way and SS": [
        "Victor",
        "Eve",
        "Vanna",
        "Gia",
        "Am Am",
        "Nikko",
        "Glenda",
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
            "Fatima Venturina",
            "Fatima Berliene Venturina",
            "D.Fatima",
            "DFatima",
            "D Fatima",
            "BF_Fatima",
            "Fatima",
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
            "Evangelyn Dolom",
            "Vangie Dolom",
            "Evangelyn",
            "Vangie",
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
            "Shayne Ericka",
            "Shayne Ombao",
            "Shayne Ericka Ombao",
            "Shayne Dalde",
            "Shayne",
        ],
        "department": FAMILY,
        "status": ACTIVE,
        "attendance": DEFAULT_ATTENDANCE.copy(),
        "sort_order": 5,
    },

    "FAM006": {
        "display_name": "Eldress Issa",
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
            "E.Issa",
            "E Issa",
            "EIssa",
            "Marissa Liponhay",
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
            "Hannah Zotomayor",
            "Hannah Sanz",
            "Hannah",
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
            "DIan",
            "Jhong",
            "Ian Liponhay",
            "Jhong Liponhay",
            "Dcn Jhong",
            "Dcn Ian",
            "D Ian",
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
            "MJervene",
            "Jervene Venturina",
            "M Jervene",
            "M.Jervene",
            "Philippines_Jervene Venturina",
            "Jervene Venturina_Philippines",
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
            "Jessie Dalde",
            "D.Jessie",
            "DJessie",
            "D Jessie",
            "Dalde Jessie Jr",
            "Jessie Dalde Jr",
            "Jesse",
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
            "Almen Dolom",
            "Almen",
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
            "Fernan Zotomayor",
            "Fernan",
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
            "Jiboy Juego",
            "Honesto Juego",
            "Juego, Honesto Jr, Martinez",
            "Jiboy",
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
            "Riza Gabriela",
            "Riza Bonifacio",
            "Philippines_Riza (wmd)",
            "Philippines_Riza",
            "Riza",
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
            "Lavinia Arances",
            "Lavinia Harris",
            "Inia",
            "Lavinia A Harris",
            "Lavinia",
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
            "Axel",
            "Iven Harris",
            "Iven Axel Harris",
            "Iven",
        ],
        "department": FAMILY,
        "status": ACTIVE,
        "attendance": DEFAULT_ATTENDANCE.copy(),
        "sort_order": 17,
    },

    "FAM018": {
        "display_name": "M Jhay",
        "official_name": "Jonathan Santos",
        "aliases": [
            "Jonathan",
            "Jhay",
            "Jonathan Santos",
            "Jhay Santos",
            "NLP Jonathan Santos",
            "Mjhay",
            "M Jhay",
        ],
        "department": FAMILY,
        "status": ACTIVE,
        "attendance": DEFAULT_ATTENDANCE.copy(),
        "sort_order": 18,
    },
        # =================================================
    # CAREER MALES
    # =================================================

    "CM001": {
        "display_name": "Jabs",
        "official_name": "Edgardo Magdua Jr.",
        "aliases": [
            "Edgardo",
            "Jabs Magdua",
            "Edgardo Magdua Jr",
            "D Jabs",
            "D.Jabs",
            "DJabs",
            "Jabs",
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
            "Xander Astucia",
            "Alex",
            "Alex Astucia",
            "Xander",
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
            "Franz Javier",
            "Franz Javier Jr",
            "Franz Jr",
            "Franz",
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
            "Daniel Inson",
            "Daniel Ezekiel",
            "Daniel Ezekiel Inson",
            "MCareer_Daniel Ezekiel",
            "Daniel",
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
            "Venancio Jimenez",
            "Venancio Jimenez III",
            "Venancio Jimenez IILI",
            "Venancio Jimenez ILI",
            "Venancio Jimenez IIL",
            "Venancio",
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
            "Gideon Mangahas Alidon",
            "Gideon Alidon",
            "Gideon",
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
            "Shaja Lei",
            "Shaja Alcantara",
            "Shaja",
            
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
            "Grace Leguarda",
            "Atty Grace",
            "Leguarda, Grace B",
            "Leguarda, Grace",
            "Grace",
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
            "Daryl Evangelista",
            "Daryl Mitzi Evangelista",
            "Daryl",
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
            "Clarice A",
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
            "Aliza M",
            "Aliza Manuel",
            "Aliza",
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
            "Anica A",
            "Anica Astucia",
            "Anica",
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
            "Melanie",
            "Melanie Vaflor",
            "D Mel",
            "D.Mel",
            "DMel",
            "Mel",
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
            "Andrea B",
            "Andrea Bonifacio",
            "Andrea",
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
            "Angel G",
            "Angel Galez",
            "Angel",
            "Ma Angelica Galez",
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
            "Rosemarie Juanatas",
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
            "Vicky L",
            "Vicky Leguarda",
            "Vicky",
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
            "Donna V",
            "Donna Velasquez",
            "Donna",
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
            "D Rue Narra",
            "Rue",
            "Rue Narra",
            "Rubilyn Narra",
            "RA Narra",
            "D Rue",
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
            "PP Bambi",
            "Bambi",
            "Bambi Ladaga",
            "Gene Ann Ladaga",
            "PP Bam",
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
            "Zhandra T",
            "Zhandra Tam",
            "Zhandra",
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
            "Trina Y",
            "Trina Yabut",
            "T.Yabut",
            "Trina",
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
            "Doc Kristine",
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
            "Milca A",
            "Milca Angeles",
            "Milca",
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
            "MJu",
            "Ju Nara",
            "Krist Anonuevo",
            "HQ Junara",
            "M Ju",
            "HQ_Junara",
        ],
        "department": CAREER_FEMALES,
        "status": ACTIVE,
        "attendance": DEFAULT_ATTENDANCE.copy(),
        "sort_order": 21,
    },

    "CrF022": {
        "display_name": "M Azzel",
        "official_name": "Azzel Lao",
        "aliases": [
            "MA",
            "Ling Long",
            "Azzel Lao",
            "Philippines Azzel",
            "Azzel",
            "Philippines_Azzel",
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
            "Sarah A",
            "Sarah Alidon",
            "M Sa",
            "M.Sa",
            "MSa",
            "Sarah",
        ],
        "department": CAREER_FEMALES,
        "status": ACTIVE,
        "attendance": DEFAULT_ATTENDANCE.copy(),
        "sort_order": 23,
    },
    "CrF024": {
        "display_name": "Joannes",
        "official_name": "Joannes Alonsagay",
        "aliases": [
            "Joan",
            "Joannes Alonsagay",
            "Annes Alonsagay",
            "Joannes Resurreccion",
            "Joannes Resurreccion Alonsagay",
            "Joannes",
            "Pres Joan",
        ],
        "department": CAREER_FEMALES,
        "status": ACTIVE,
        "attendance": DEFAULT_ATTENDANCE.copy(),
        "sort_order": 24,
    },

    "CrF025": {
        "display_name": "P Auda",
        "official_name": "Auda Atienza",
        "aliases": [
            "Auda",
            "Auda Love",
            "Auda Atienza",
            "Auda Allison Atienza",
            "Allison Atienza",
            "PA",
            "P.Auda",
            "P Auda",
        ],
        "department": CAREER_FEMALES,
        "status": ACTIVE,
        "attendance": DEFAULT_ATTENDANCE.copy(),
        "sort_order": 25,
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
            "Cor L",
            "M Cor",
            "M.Cor",
            "Cor",
            "Corazon Lualhati",
            "Cor Lualhati",
            "MCor",
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
            "Tita Merly",
            "Merlita",
            "Merlita Alidon",
            "Merly",
            "Merly Alidon",
            "Tita Merlita",
        ],
        "department": JS,
        "status": ACTIVE,
        "attendance": DEFAULT_ATTENDANCE.copy(),
        "sort_order": 2,
    },

    "JS003": {
        "display_name": "Grace - Japan",
        "official_name": "Grace Givera",
        "aliases": [
            "Grace",
            "Grace Givera",
            "Megumi",
            "Megumi Givera",
            "Megumi (Me)",
            "Megumi ME",
            "MEGUMI",
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
            "Emercedita Hiramatsu",
            "Emeru",
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
            "Michelle B",
            "Michelle Bautista",
            "Mitch Bautista",
            "Michelle",
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
    # Milky Way and SS
    # =================================================

    "MW001": {
        "display_name": "Victor",
        "official_name": "Victor Liponhay",
        "aliases": [
            "Victor",
            "Uno",
            "Victor Philip Liponhay",
            "Victor Liponhay",
        ],
        "department": MILKY_WAY_SS,
        "status": ACTIVE,
        "attendance": DEFAULT_ATTENDANCE.copy(),
        "sort_order": 1,
    },

    "MW002": {
        "display_name": "Eve",
        "official_name": "Eliana Given Venturina",
        "aliases": [
            "Eliana Given",
            "Eve Venturina",
            "Eliana Given D. Venturina",
            "Eve",
        ],
        "department": MILKY_WAY_SS,
        "status": ACTIVE,
        "attendance": DEFAULT_ATTENDANCE.copy(),
        "sort_order": 2,
    },

    "MW003": {
        "display_name": "Vanna",
        "official_name": "Vanna Amelie Dolom",
        "aliases": [
            "Vanna D",
            "Vanna Dolom",
            "Vanna Amelie Dolom",
            "Vanna",
        ],
        "department": MILKY_WAY_SS,
        "status": ACTIVE,
        "attendance": DEFAULT_ATTENDANCE.copy(),
        "sort_order": 3,
    },

    "MW004": {
            "display_name": "Gia",
            "official_name": "Aubrielle Gia Santos",
            "aliases": [
                "Bree",
                "Bree Bree",
                "Bree Bree Santos",
                "Bree Santos",
                "Gia Santos"
                "Gia",
            ],
            "department": MILKY_WAY_SS,
            "status": ACTIVE,
            "attendance": DEFAULT_ATTENDANCE.copy(),
            "sort_order": 4,
    },
    
    "MW005": {
                "display_name": "Am Am",
                "official_name": "Audrielle Megan Zotomayor",
                "aliases": [
                    "Audrielle Megan",
                    "Am Am Zotomayor",
                    "Audrielle,"
                    "Am Am",
                ],
                "department": MILKY_WAY_SS,
                "status": ACTIVE,
                "attendance": DEFAULT_ATTENDANCE.copy(),
                "sort_order": 5,
    },

    "SS001": {
                    "display_name": "Nikko",
                    "official_name": "Nikko Leguarda",
                    "aliases": [
                        "Nikko L",
                        "Nikko Leguarda",
                        "Nikko",
                    ],
                    "department": MILKY_WAY_SS,
                    "status": ACTIVE,
                    "attendance": DEFAULT_ATTENDANCE.copy(),
                    "sort_order": 6,
        },

    "SS002": {
                        "display_name": "Glenda",
                        "official_name": "Glenda Leguarda",
                        "aliases": [
                            "Glenda",
                            "Glenda Leguarda",
                        ],
                        "department": MILKY_WAY_SS,
                        "status": ACTIVE,
                        "attendance": DEFAULT_ATTENDANCE.copy(),
                        "sort_order": 7,
            },
        

    # =================================================
    # OVERSEAS FILIPINO MEMBERS
    # =================================================

    "OPM001": {
        "display_name": "Cheyserr",
        "official_name": "Cheyserr Lamayra",
        "aliases": [
            "Cheyserr L",
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
            "John Carlo R",
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
            "M. Saeyoung",
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
            "Miae P",
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
            "Andrew DC",
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
            "Cherry N",
            "체리 나",
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
    "OPM007": {
        "display_name": "Alma Joy",
        "official_name": "Alma Joy",
        "aliases": [
            "Alma J",
            "Alma Joy",
        ],
        "department": OPM,
        "status": ACTIVE,
        "attendance": attendance(
            sunday=ONLINE,
            wednesday=ONLINE,
            predawn=ONLINE,
        ),
        "sort_order": 7,
    },
    # =================================================
    # LORD'S LOVE CHURCH
    # =================================================

    "LLC001": {
        "display_name": "Leah Jean",
        "official_name": "Leah Jean Inson",
        "aliases": [
            "Leah",
            "Leah Jean Inson",
            "Leah Inson",
            "LEAH JEAN INSON",
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
            "Therese P",
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
            "Ria LLC",
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
            "Irene V",
            "VICERRA, Irene Fe G.",
            "Irene Fe G. Vicerra",
            "Irene",
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
            "Daisy Lemu",
            "LEMU, Rose Daisy Jane T.",
            "Rose Daisy Jane T. Lemu",
            "Daisy",
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
            "Shaina I",
            "Shaina Fatima Inson",
            "Shaina",
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

    "LVC003": {
            "display_name": "Diane",
            "official_name": "Diane Infante",
            "aliases": [
                "Diane",
                "Diane Infante",
            ],
            "department": LVC,
            "status": ACTIVE,
            "attendance": attendance(
                sunday=ONLINE,
                wednesday=ONLINE,
                predawn=ONLINE,
            ),
            "sort_order": 3,
        },

    "LVC003": {
                "display_name": "Glory",
                "official_name": "Glory Tangarorang",
                "aliases": [
                    "Glory",
                    "Glory Tangarorang",
                ],
                "department": LVC,
                "status": ACTIVE,
                "attendance": attendance(
                    sunday=ONLINE,
                    wednesday=ONLINE,
                    predawn=ONLINE,
                ),
                "sort_order": 3,
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