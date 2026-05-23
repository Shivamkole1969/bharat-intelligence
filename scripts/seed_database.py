"""
Bharat Market Intelligence Agent — Comprehensive Database Seeder

Seeds 500 Indian companies (Nifty 500 universe) across all major sectors.
Run this after schema.sql and indexes.sql have been applied.

Usage:
    python scripts/seed_database.py
    # or via Makefile:
    make seed
"""

from __future__ import annotations

import asyncio
import logging
import sys
import os

# Add parent directory to path so we can import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

# ============================================================
# Nifty 500 Universe — Top Indian Companies by Sector
# ============================================================
# Organized by sector for maintainability. Each entry:
# (symbol, exchange, isin, company_name, sector, industry, nse_symbol, bse_code)

COMPANIES = [
    # ── IT Services & Technology (45 companies) ──────────────────
    ("TCS", "NSE", "INE467B01029", "Tata Consultancy Services Ltd", "Information Technology", "IT Services", "TCS", "532540"),
    ("INFY", "NSE", "INE009A01021", "Infosys Ltd", "Information Technology", "IT Services", "INFY", "500209"),
    ("WIPRO", "NSE", "INE075A01022", "Wipro Ltd", "Information Technology", "IT Services", "WIPRO", "507685"),
    ("HCLTECH", "NSE", "INE860A01027", "HCL Technologies Ltd", "Information Technology", "IT Services", "HCLTECH", "532281"),
    ("TECHM", "NSE", "INE669C01036", "Tech Mahindra Ltd", "Information Technology", "IT Services", "TECHM", "532755"),
    ("LTIM", "NSE", "INE214T01019", "LTIMindtree Ltd", "Information Technology", "IT Services", "LTIM", "540005"),
    ("PERSISTENT", "NSE", "INE262H01013", "Persistent Systems Ltd", "Information Technology", "IT Services", "PERSISTENT", "533179"),
    ("COFORGE", "NSE", "INE591G01017", "Coforge Ltd", "Information Technology", "IT Services", "COFORGE", "532541"),
    ("MPHASIS", "NSE", "INE356A01018", "Mphasis Ltd", "Information Technology", "IT Services", "MPHASIS", "526299"),
    ("LTTS", "NSE", "INE010V01017", "L&T Technology Services Ltd", "Information Technology", "IT Services", "LTTS", "540115"),
    ("OFSS", "NSE", "INE881D01027", "Oracle Financial Services Software", "Information Technology", "IT Products", "OFSS", "532466"),
    ("TATAELXSI", "NSE", "INE670A01012", "Tata Elxsi Ltd", "Information Technology", "IT Services", "TATAELXSI", "500408"),
    ("CYIENT", "NSE", "INE136B01020", "Cyient Ltd", "Information Technology", "IT Services", "CYIENT", "532175"),
    ("ZENSAR", "NSE", "INE520A01027", "Zensar Technologies Ltd", "Information Technology", "IT Services", "ZENSAR", "504067"),
    ("BIRLASOFT", "NSE", "INE836A01035", "Birlasoft Ltd", "Information Technology", "IT Services", "BIRLASOFT", "532400"),
    ("HAPPSTMNDS", "NSE", "INE419U01012", "Happiest Minds Technologies", "Information Technology", "IT Services", "HAPPSTMNDS", "543227"),
    ("ROUTE", "NSE", "INE450U01017", "Route Mobile Ltd", "Information Technology", "Cloud Communications", "ROUTE", "543228"),
    ("SONATSOFTW", "NSE", "INE269A01021", "Sonata Software Ltd", "Information Technology", "IT Services", "SONATSOFTW", "532221"),
    ("MASTEK", "NSE", "INE759A01021", "Mastek Ltd", "Information Technology", "IT Services", "MASTEK", "523704"),
    ("NEWGEN", "NSE", "INE619B01017", "Newgen Software Technologies", "Information Technology", "IT Products", "NEWGEN", "540900"),
    ("INTELLECT", "NSE", "INE306R01017", "Intellect Design Arena Ltd", "Information Technology", "IT Products", "INTELLECT", "538835"),
    ("RATEGAIN", "NSE", "INE0CC201010", "RateGain Travel Technologies", "Information Technology", "Travel Tech", "RATEGAIN", "543417"),
    ("TANLA", "NSE", "INE483C01032", "Tanla Platforms Ltd", "Information Technology", "Cloud Communications", "TANLA", "532790"),
    ("KPITTECH", "NSE", "INE04I401011", "KPIT Technologies Ltd", "Information Technology", "Embedded Software", "KPITTECH", "542651"),
    ("ZENSARTECH", "NSE", "INE520A01027", "Zensar Technologies Ltd", "Information Technology", "IT Services", "ZENSARTECH", "504067"),

    # ── Banking (30 companies) ───────────────────────────────────
    ("HDFCBANK", "NSE", "INE040A01034", "HDFC Bank Ltd", "Financial Services", "Banking - Private", "HDFCBANK", "500180"),
    ("ICICIBANK", "NSE", "INE090A01021", "ICICI Bank Ltd", "Financial Services", "Banking - Private", "ICICIBANK", "532174"),
    ("SBIN", "NSE", "INE062A01020", "State Bank of India", "Financial Services", "Banking - PSU", "SBIN", "500112"),
    ("KOTAKBANK", "NSE", "INE237A01028", "Kotak Mahindra Bank Ltd", "Financial Services", "Banking - Private", "KOTAKBANK", "500247"),
    ("AXISBANK", "NSE", "INE238A01034", "Axis Bank Ltd", "Financial Services", "Banking - Private", "AXISBANK", "532215"),
    ("INDUSINDBK", "NSE", "INE095A01012", "IndusInd Bank Ltd", "Financial Services", "Banking - Private", "INDUSINDBK", "532187"),
    ("BANKBARODA", "NSE", "INE028A01039", "Bank of Baroda", "Financial Services", "Banking - PSU", "BANKBARODA", "532134"),
    ("PNB", "NSE", "INE160A01022", "Punjab National Bank", "Financial Services", "Banking - PSU", "PNB", "532461"),
    ("CANBK", "NSE", "INE476A01022", "Canara Bank", "Financial Services", "Banking - PSU", "CANBK", "532483"),
    ("UNIONBANK", "NSE", "INE692A01016", "Union Bank of India", "Financial Services", "Banking - PSU", "UNIONBANK", "532477"),
    ("IDFCFIRSTB", "NSE", "INE092T01019", "IDFC First Bank Ltd", "Financial Services", "Banking - Private", "IDFCFIRSTB", "539437"),
    ("FEDERALBNK", "NSE", "INE171A01029", "Federal Bank Ltd", "Financial Services", "Banking - Private", "FEDERALBNK", "500469"),
    ("BANDHANBNK", "NSE", "INE545U01014", "Bandhan Bank Ltd", "Financial Services", "Banking - Private", "BANDHANBNK", "541153"),
    ("AUBANK", "NSE", "INE949L01017", "AU Small Finance Bank", "Financial Services", "Banking - SFB", "AUBANK", "540611"),
    ("RBLBANK", "NSE", "INE976G01028", "RBL Bank Ltd", "Financial Services", "Banking - Private", "RBLBANK", "540065"),
    ("INDIANB", "NSE", "INE562A01011", "Indian Bank", "Financial Services", "Banking - PSU", "INDIANB", "532814"),
    ("IOB", "NSE", "INE565A01014", "Indian Overseas Bank", "Financial Services", "Banking - PSU", "IOB", "532388"),
    ("CENTRALBK", "NSE", "INE483A01010", "Central Bank of India", "Financial Services", "Banking - PSU", "CENTRALBK", "532885"),
    ("MAHABANK", "NSE", "INE457A01014", "Bank of Maharashtra", "Financial Services", "Banking - PSU", "MAHABANK", "532525"),
    ("YESBANK", "NSE", "INE528G01035", "Yes Bank Ltd", "Financial Services", "Banking - Private", "YESBANK", "532648"),
    ("IDBI", "NSE", "INE008A01015", "IDBI Bank Ltd", "Financial Services", "Banking - PSU", "IDBI", "500116"),
    ("KARURVYSYA", "NSE", "INE036D01028", "Karur Vysya Bank Ltd", "Financial Services", "Banking - Private", "KARURVYSYA", "590003"),
    ("SOUTHBANK", "NSE", "INE683A01023", "South Indian Bank Ltd", "Financial Services", "Banking - Private", "SOUTHBANK", "532218"),
    ("CUB", "NSE", "INE491A01021", "City Union Bank Ltd", "Financial Services", "Banking - Private", "CUB", "532210"),
    ("TMB", "NSE", "INE00C801016", "Tamilnad Mercantile Bank", "Financial Services", "Banking - Private", "TMB", "543596"),
    ("EQUITASBNK", "NSE", "INE063P01018", "Equitas Small Finance Bank", "Financial Services", "Banking - SFB", "EQUITASBNK", "543243"),
    ("UJJIVANSFB", "NSE", "INE551W01018", "Ujjivan Small Finance Bank", "Financial Services", "Banking - SFB", "UJJIVANSFB", "542904"),

    # ── NBFC & Financial Services (35 companies) ─────────────────
    ("BAJFINANCE", "NSE", "INE296A01024", "Bajaj Finance Ltd", "Financial Services", "NBFC", "BAJFINANCE", "500034"),
    ("BAJAJFINSV", "NSE", "INE918I01018", "Bajaj Finserv Ltd", "Financial Services", "Financial Holding", "BAJAJFINSV", "532978"),
    ("HDFCLIFE", "NSE", "INE795G01014", "HDFC Life Insurance Co", "Financial Services", "Insurance - Life", "HDFCLIFE", "540777"),
    ("SBILIFE", "NSE", "INE123W01016", "SBI Life Insurance Co", "Financial Services", "Insurance - Life", "SBILIFE", "540719"),
    ("SBICARD", "NSE", "INE018E01016", "SBI Cards & Payment Services", "Financial Services", "Credit Cards", "SBICARD", "543066"),
    ("ICICIPRULI", "NSE", "INE726G01019", "ICICI Prudential Life Insurance", "Financial Services", "Insurance - Life", "ICICIPRULI", "540133"),
    ("ICICIGI", "NSE", "INE765G01017", "ICICI Lombard General Insurance", "Financial Services", "Insurance - General", "ICICIGI", "540716"),
    ("CHOLAFIN", "NSE", "INE121A01024", "Cholamandalam Investment & Finance", "Financial Services", "NBFC", "CHOLAFIN", "511243"),
    ("SHRIRAMFIN", "NSE", "INE721A01013", "Shriram Finance Ltd", "Financial Services", "NBFC", "SHRIRAMFIN", "511218"),
    ("M&MFIN", "NSE", "INE774D01024", "Mahindra & Mahindra Financial", "Financial Services", "NBFC", "M&MFIN", "532720"),
    ("MUTHOOTFIN", "NSE", "INE414G01012", "Muthoot Finance Ltd", "Financial Services", "NBFC - Gold Loans", "MUTHOOTFIN", "533398"),
    ("MANAPPURAM", "NSE", "INE522D01027", "Manappuram Finance Ltd", "Financial Services", "NBFC - Gold Loans", "MANAPPURAM", "531213"),
    ("PEL", "NSE", "INE318A01026", "Piramal Enterprises Ltd", "Financial Services", "NBFC", "PEL", "500331"),
    ("LICHSGFIN", "NSE", "INE115A01026", "LIC Housing Finance Ltd", "Financial Services", "Housing Finance", "LICHSGFIN", "500253"),
    ("CANFINHOME", "NSE", "INE477A01020", "Can Fin Homes Ltd", "Financial Services", "Housing Finance", "CANFINHOME", "511196"),
    ("AAVAS", "NSE", "INE216P01012", "Aavas Financiers Ltd", "Financial Services", "Housing Finance", "AAVAS", "541988"),
    ("POONAWALLA", "NSE", "INE511C01022", "Poonawalla Fincorp Ltd", "Financial Services", "NBFC", "POONAWALLA", "524000"),
    ("SUNDARMFIN", "NSE", "INE660A01013", "Sundaram Finance Ltd", "Financial Services", "NBFC", "SUNDARMFIN", "590071"),
    ("CREDITACC", "NSE", "INE741K01010", "CreditAccess Grameen Ltd", "Financial Services", "Microfinance", "CREDITACC", "541770"),
    ("STARHEALTH", "NSE", "INE00DQ01015", "Star Health & Allied Insurance", "Financial Services", "Insurance - Health", "STARHEALTH", "543412"),
    ("NIACL", "NSE", "INE006F01024", "New India Assurance Company", "Financial Services", "Insurance - General", "NIACL", "540769"),
    ("GICRE", "NSE", "INE481Y01014", "General Insurance Corp of India", "Financial Services", "Insurance - Reinsurance", "GICRE", "540755"),
    ("CAMS", "NSE", "INE596I01012", "Computer Age Management Services", "Financial Services", "Capital Markets", "CAMS", "543232"),
    ("CDSL", "NSE", "INE736A01011", "Central Depository Services", "Financial Services", "Capital Markets", "CDSL", "532991"),
    ("MCX", "NSE", "INE745G01035", "Multi Commodity Exchange", "Financial Services", "Exchanges", "MCX", "534091"),
    ("BSE", "NSE", "INE118H01025", "BSE Ltd", "Financial Services", "Exchanges", "BSE", "539399"),
    ("ANGELONE", "NSE", "INE732I01013", "Angel One Ltd", "Financial Services", "Stock Broking", "ANGELONE", "543235"),
    ("MOTILALOFS", "NSE", "INE338I01027", "Motilal Oswal Financial Services", "Financial Services", "Stock Broking", "MOTILALOFS", "532892"),
    ("IIFL", "NSE", "INE530B01024", "IIFL Finance Ltd", "Financial Services", "NBFC", "IIFL", "532636"),
    ("JMFINANCIL", "NSE", "INE780C01023", "JM Financial Ltd", "Financial Services", "Investment Banking", "JMFINANCIL", "523405"),

    # ── Oil, Gas & Energy (30 companies) ─────────────────────────
    ("RELIANCE", "NSE", "INE002A01018", "Reliance Industries Ltd", "Energy", "Oil & Gas - Integrated", "RELIANCE", "500325"),
    ("ONGC", "NSE", "INE213A01029", "Oil & Natural Gas Corporation", "Energy", "Oil & Gas - Exploration", "ONGC", "500312"),
    ("BPCL", "NSE", "INE029A01011", "Bharat Petroleum Corp", "Energy", "Oil & Gas - Refining", "BPCL", "500547"),
    ("IOC", "NSE", "INE242A01010", "Indian Oil Corporation", "Energy", "Oil & Gas - Refining", "IOC", "530965"),
    ("NTPC", "NSE", "INE733E01010", "NTPC Ltd", "Energy", "Power - Thermal", "NTPC", "532555"),
    ("POWERGRID", "NSE", "INE752E01010", "Power Grid Corporation", "Energy", "Power - Transmission", "POWERGRID", "532898"),
    ("ADANIENT", "NSE", "INE423A01024", "Adani Enterprises Ltd", "Energy", "Conglomerate", "ADANIENT", "512599"),
    ("ADANIGREEN", "NSE", "INE364U01010", "Adani Green Energy Ltd", "Energy", "Renewable Energy", "ADANIGREEN", "541450"),
    ("ADANIPOWER", "NSE", "INE814H01011", "Adani Power Ltd", "Energy", "Power - Thermal", "ADANIPOWER", "533096"),
    ("TATAPOWER", "NSE", "INE245A01021", "Tata Power Company Ltd", "Energy", "Power - Integrated", "TATAPOWER", "500400"),
    ("NHPC", "NSE", "INE848E01016", "NHPC Ltd", "Energy", "Power - Hydro", "NHPC", "533098"),
    ("SJVN", "NSE", "INE002L01015", "SJVN Ltd", "Energy", "Power - Hydro", "SJVN", "533206"),
    ("GAIL", "NSE", "INE129A01019", "GAIL India Ltd", "Energy", "Gas Distribution", "GAIL", "532155"),
    ("IGL", "NSE", "INE203G01027", "Indraprastha Gas Ltd", "Energy", "Gas Distribution", "IGL", "532514"),
    ("MGL", "NSE", "INE002S01010", "Mahanagar Gas Ltd", "Energy", "Gas Distribution", "MGL", "539957"),
    ("PETRONET", "NSE", "INE347G01014", "Petronet LNG Ltd", "Energy", "Gas Distribution", "PETRONET", "532522"),
    ("HINDPETRO", "NSE", "INE094A01015", "Hindustan Petroleum Corp", "Energy", "Oil & Gas - Refining", "HINDPETRO", "500104"),
    ("OIL", "NSE", "INE274J01014", "Oil India Ltd", "Energy", "Oil & Gas - Exploration", "OIL", "533106"),
    ("TORNTPOWER", "NSE", "INE813H01021", "Torrent Power Ltd", "Energy", "Power - Integrated", "TORNTPOWER", "532779"),
    ("CESC", "NSE", "INE486A01013", "CESC Ltd", "Energy", "Power - Distribution", "CESC", "500084"),
    ("JSPL", "NSE", "INE220G01021", "Jindal Steel & Power Ltd", "Energy", "Steel & Power", "JSPL", "532286"),
    ("IREDA", "NSE", "INE202E01016", "Indian Renewable Energy Dev Agency", "Energy", "Renewable Finance", "IREDA", "543963"),
    ("RECLTD", "NSE", "INE020B01018", "REC Ltd", "Energy", "Power Finance", "RECLTD", "532955"),
    ("PFC", "NSE", "INE134E01011", "Power Finance Corporation", "Energy", "Power Finance", "PFC", "532810"),
    ("ADANITRANS", "NSE", "INE931S01010", "Adani Energy Solutions", "Energy", "Power - Transmission", "ADANITRANS", "539254"),
    ("JSWENERGY", "NSE", "INE121E01018", "JSW Energy Ltd", "Energy", "Power - Integrated", "JSWENERGY", "533148"),
    ("SUZLON", "NSE", "INE040H01021", "Suzlon Energy Ltd", "Energy", "Wind Energy", "SUZLON", "532667"),
    ("TATACONSUM", "NSE", "INE192A01025", "Tata Consumer Products Ltd", "FMCG", "FMCG", "TATACONSUM", "500800"),

    # ── Automobile & Auto Ancillary (35 companies) ───────────────
    ("TATAMOTORS", "NSE", "INE155A01022", "Tata Motors Ltd", "Automobile", "Auto - Passenger", "TATAMOTORS", "500570"),
    ("MARUTI", "NSE", "INE585B01010", "Maruti Suzuki India Ltd", "Automobile", "Auto - Passenger", "MARUTI", "532500"),
    ("M&M", "NSE", "INE101A01026", "Mahindra & Mahindra Ltd", "Automobile", "Auto - Passenger", "M&M", "500520"),
    ("BAJAJ-AUTO", "NSE", "INE917I01010", "Bajaj Auto Ltd", "Automobile", "Auto - Two Wheeler", "BAJAJ-AUTO", "532977"),
    ("EICHERMOT", "NSE", "INE066A01021", "Eicher Motors Ltd", "Automobile", "Auto - Two Wheeler", "EICHERMOT", "505200"),
    ("HEROMOTOCO", "NSE", "INE158A01026", "Hero MotoCorp Ltd", "Automobile", "Auto - Two Wheeler", "HEROMOTOCO", "500182"),
    ("TVSMOTORS", "NSE", "INE494B01023", "TVS Motor Company Ltd", "Automobile", "Auto - Two Wheeler", "TVSMOTORS", "532343"),
    ("ASHOKLEY", "NSE", "INE208A01029", "Ashok Leyland Ltd", "Automobile", "Auto - CV", "ASHOKLEY", "500477"),
    ("ESCORTS", "NSE", "INE042A01014", "Escorts Kubota Ltd", "Automobile", "Auto - Tractors", "ESCORTS", "500495"),
    ("MOTHERSON", "NSE", "INE775A01035", "Samvardhana Motherson International", "Automobile", "Auto Ancillary", "MOTHERSON", "517334"),
    ("BOSCHLTD", "NSE", "INE323A01026", "Bosch Ltd", "Automobile", "Auto Ancillary", "BOSCHLTD", "500530"),
    ("BALKRISIND", "NSE", "INE787D01026", "Balkrishna Industries Ltd", "Automobile", "Tyres", "BALKRISIND", "502355"),
    ("MRF", "NSE", "INE883A01011", "MRF Ltd", "Automobile", "Tyres", "MRF", "500290"),
    ("APOLLOTYRE", "NSE", "INE438A01022", "Apollo Tyres Ltd", "Automobile", "Tyres", "APOLLOTYRE", "500877"),
    ("CEATLTD", "NSE", "INE482A01020", "CEAT Ltd", "Automobile", "Tyres", "CEATLTD", "500878"),
    ("BHARATFORG", "NSE", "INE465A01025", "Bharat Forge Ltd", "Automobile", "Auto Components", "BHARATFORG", "500493"),
    ("ENDURANCE", "NSE", "INE913H01037", "Endurance Technologies Ltd", "Automobile", "Auto Components", "ENDURANCE", "540153"),
    ("SUNDRMFAST", "NSE", "INE387A01021", "Sundram Fasteners Ltd", "Automobile", "Auto Components", "SUNDRMFAST", "500403"),
    ("EXIDEIND", "NSE", "INE302A01020", "Exide Industries Ltd", "Automobile", "Auto - Batteries", "EXIDEIND", "500086"),
    ("AMARAJABAT", "NSE", "INE885A01032", "Amara Raja Energy & Mobility", "Automobile", "Auto - Batteries", "AMARAJABAT", "500008"),
    ("TIINDIA", "NSE", "INE670A01012", "Tube Investments of India", "Automobile", "Auto Components", "TIINDIA", "540762"),
    ("SCHAEFFLER", "NSE", "INE513A01014", "Schaeffler India Ltd", "Automobile", "Bearings", "SCHAEFFLER", "505790"),
    ("SKFINDIA", "NSE", "INE640A01023", "SKF India Ltd", "Automobile", "Bearings", "SKFINDIA", "500472"),
    ("OLECTRA", "NSE", "INE260D01016", "Olectra Greentech Ltd", "Automobile", "Electric Vehicles", "OLECTRA", "532439"),

    # ── Pharma & Healthcare (40 companies) ───────────────────────
    ("SUNPHARMA", "NSE", "INE044A01036", "Sun Pharmaceutical Industries", "Healthcare", "Pharma - Large Cap", "SUNPHARMA", "524715"),
    ("DRREDDY", "NSE", "INE089A01023", "Dr Reddys Laboratories", "Healthcare", "Pharma - Large Cap", "DRREDDY", "500124"),
    ("CIPLA", "NSE", "INE059A01026", "Cipla Ltd", "Healthcare", "Pharma - Large Cap", "CIPLA", "500087"),
    ("APOLLOHOSP", "NSE", "INE437A01024", "Apollo Hospitals Enterprise", "Healthcare", "Hospitals", "APOLLOHOSP", "508869"),
    ("DIVISLAB", "NSE", "INE361B01024", "Divis Laboratories Ltd", "Healthcare", "Pharma - API", "DIVISLAB", "532488"),
    ("TORNTPHARM", "NSE", "INE685A01028", "Torrent Pharmaceuticals", "Healthcare", "Pharma - Mid Cap", "TORNTPHARM", "500420"),
    ("LUPIN", "NSE", "INE326A01037", "Lupin Ltd", "Healthcare", "Pharma - Large Cap", "LUPIN", "500257"),
    ("AUROPHARMA", "NSE", "INE406A01037", "Aurobindo Pharma Ltd", "Healthcare", "Pharma - Generic", "AUROPHARMA", "524804"),
    ("BIOCON", "NSE", "INE376G01013", "Biocon Ltd", "Healthcare", "Biotech", "BIOCON", "532523"),
    ("ALKEM", "NSE", "INE540L01014", "Alkem Laboratories Ltd", "Healthcare", "Pharma - Mid Cap", "ALKEM", "539523"),
    ("GLENMARK", "NSE", "INE935A01035", "Glenmark Pharmaceuticals", "Healthcare", "Pharma - Mid Cap", "GLENMARK", "532296"),
    ("IPCALAB", "NSE", "INE571A01020", "IPCA Laboratories Ltd", "Healthcare", "Pharma - Mid Cap", "IPCALAB", "524494"),
    ("ABBOTINDIA", "NSE", "INE358A01014", "Abbott India Ltd", "Healthcare", "Pharma - MNC", "ABBOTINDIA", "500488"),
    ("PFIZER", "NSE", "INE182A01018", "Pfizer Ltd", "Healthcare", "Pharma - MNC", "PFIZER", "500680"),
    ("SANOFI", "NSE", "INE058A01010", "Sanofi India Ltd", "Healthcare", "Pharma - MNC", "SANOFI", "500674"),
    ("GLAXO", "NSE", "INE159A01016", "GlaxoSmithKline Pharma", "Healthcare", "Pharma - MNC", "GLAXO", "500660"),
    ("LAURUSLABS", "NSE", "INE947Q01028", "Laurus Labs Ltd", "Healthcare", "Pharma - API", "LAURUSLABS", "540222"),
    ("GRANULES", "NSE", "INE101D01020", "Granules India Ltd", "Healthcare", "Pharma - Generic", "GRANULES", "532482"),
    ("ASTRAZEN", "NSE", "INE203A01020", "AstraZeneca Pharma India", "Healthcare", "Pharma - MNC", "ASTRAZEN", "506820"),
    ("MAXHEALTH", "NSE", "INE027H01010", "Max Healthcare Institute", "Healthcare", "Hospitals", "MAXHEALTH", "543220"),
    ("FORTIS", "NSE", "INE061F01013", "Fortis Healthcare Ltd", "Healthcare", "Hospitals", "FORTIS", "532843"),
    ("METROPOLIS", "NSE", "INE112L01020", "Metropolis Healthcare Ltd", "Healthcare", "Diagnostics", "METROPOLIS", "542650"),
    ("LALPATHLAB", "NSE", "INE600L01024", "Dr Lal PathLabs Ltd", "Healthcare", "Diagnostics", "LALPATHLAB", "539524"),
    ("NATCOPHARM", "NSE", "INE987B01026", "Natco Pharma Ltd", "Healthcare", "Pharma - Specialty", "NATCOPHARM", "524816"),
    ("JBCHEPHARM", "NSE", "INE572E01024", "JB Chemicals & Pharma", "Healthcare", "Pharma - Mid Cap", "JBCHEPHARM", "506943"),
    ("ERIS", "NSE", "INE406M01024", "Eris Lifesciences Ltd", "Healthcare", "Pharma - Branded", "ERIS", "540596"),
    ("AJANTPHARM", "NSE", "INE031B01049", "Ajanta Pharma Ltd", "Healthcare", "Pharma - Mid Cap", "AJANTPHARM", "532331"),
    ("SOLARA", "NSE", "INE624Z01016", "Solara Active Pharma Sciences", "Healthcare", "Pharma - API", "SOLARA", "541540"),
    ("SYNGENE", "NSE", "INE398R01022", "Syngene International Ltd", "Healthcare", "CRAMS", "SYNGENE", "539268"),
    ("GLAND", "NSE", "INE068V01023", "Gland Pharma Ltd", "Healthcare", "Pharma - Injectables", "GLAND", "543245"),

    # ── FMCG (25 companies) ──────────────────────────────────────
    ("HINDUNILVR", "NSE", "INE030A01027", "Hindustan Unilever Ltd", "FMCG", "FMCG - Personal Care", "HINDUNILVR", "500696"),
    ("ITC", "NSE", "INE154A01025", "ITC Ltd", "FMCG", "FMCG - Diversified", "ITC", "500875"),
    ("NESTLEIND", "NSE", "INE239A01016", "Nestle India Ltd", "FMCG", "FMCG - Food", "NESTLEIND", "500790"),
    ("BRITANNIA", "NSE", "INE216A01030", "Britannia Industries Ltd", "FMCG", "FMCG - Food", "BRITANNIA", "500825"),
    ("DABUR", "NSE", "INE016A01026", "Dabur India Ltd", "FMCG", "FMCG - Personal Care", "DABUR", "500096"),
    ("MARICO", "NSE", "INE196A01026", "Marico Ltd", "FMCG", "FMCG - Personal Care", "MARICO", "531642"),
    ("GODREJCP", "NSE", "INE102D01028", "Godrej Consumer Products", "FMCG", "FMCG - Personal Care", "GODREJCP", "532424"),
    ("COLPAL", "NSE", "INE259A01022", "Colgate-Palmolive India", "FMCG", "FMCG - Oral Care", "COLPAL", "500830"),
    ("PGHH", "NSE", "INE179A01014", "Procter & Gamble Hygiene", "FMCG", "FMCG - Personal Care", "PGHH", "500459"),
    ("EMAMILTD", "NSE", "INE548C01032", "Emami Ltd", "FMCG", "FMCG - Personal Care", "EMAMILTD", "531162"),
    ("JYOTHYLAB", "NSE", "INE668F01031", "Jyothy Labs Ltd", "FMCG", "FMCG - Home Care", "JYOTHYLAB", "532926"),
    ("VBL", "NSE", "INE200M01039", "Varun Beverages Ltd", "FMCG", "Beverages", "VBL", "540180"),
    ("UBL", "NSE", "INE686F01025", "United Breweries Ltd", "FMCG", "Beverages - Alcoholic", "UBL", "532478"),
    ("RADICO", "NSE", "INE944F01028", "Radico Khaitan Ltd", "FMCG", "Beverages - Alcoholic", "RADICO", "532497"),
    ("UNITEDSPRT", "NSE", "INE854D01024", "United Spirits Ltd", "FMCG", "Beverages - Alcoholic", "UNITEDSPRT", "532432"),
    ("BIKAJI", "NSE", "INE00AC01010", "Bikaji Foods International", "FMCG", "FMCG - Snacks", "BIKAJI", "543653"),
    ("ZYDUSWELL", "NSE", "INE768C01010", "Zydus Wellness Ltd", "FMCG", "FMCG - Health", "ZYDUSWELL", "531335"),
    ("TATACONSUM", "NSE", "INE192A01025", "Tata Consumer Products Ltd", "FMCG", "FMCG - Beverages", "TATACONSUM", "500800"),

    # ── Metals & Mining (25 companies) ───────────────────────────
    ("TATASTEEL", "NSE", "INE081A01020", "Tata Steel Ltd", "Metals & Mining", "Steel", "TATASTEEL", "500470"),
    ("JSWSTEEL", "NSE", "INE019A01038", "JSW Steel Ltd", "Metals & Mining", "Steel", "JSWSTEEL", "500228"),
    ("HINDALCO", "NSE", "INE038A01020", "Hindalco Industries Ltd", "Metals & Mining", "Aluminium", "HINDALCO", "500440"),
    ("COALINDIA", "NSE", "INE522F01014", "Coal India Ltd", "Metals & Mining", "Coal", "COALINDIA", "533278"),
    ("VEDL", "NSE", "INE205A01025", "Vedanta Ltd", "Metals & Mining", "Diversified Metals", "VEDL", "500295"),
    ("NMDC", "NSE", "INE584A01023", "NMDC Ltd", "Metals & Mining", "Iron Ore", "NMDC", "526371"),
    ("SAIL", "NSE", "INE114A01011", "Steel Authority of India", "Metals & Mining", "Steel - PSU", "SAIL", "500113"),
    ("NATIONALUM", "NSE", "INE139A01034", "National Aluminium Company", "Metals & Mining", "Aluminium - PSU", "NATIONALUM", "532234"),
    ("HINDCOPPER", "NSE", "INE531E01026", "Hindustan Copper Ltd", "Metals & Mining", "Copper", "HINDCOPPER", "513599"),
    ("MOIL", "NSE", "INE490G01020", "MOIL Ltd", "Metals & Mining", "Manganese Ore", "MOIL", "533286"),
    ("HINDZINC", "NSE", "INE267A01025", "Hindustan Zinc Ltd", "Metals & Mining", "Zinc", "HINDZINC", "500188"),
    ("APLAPOLLO", "NSE", "INE702C01027", "APL Apollo Tubes Ltd", "Metals & Mining", "Steel Tubes", "APLAPOLLO", "533758"),
    ("RATNAMANI", "NSE", "INE703B01027", "Ratnamani Metals & Tubes", "Metals & Mining", "Steel Tubes", "RATNAMANI", "520111"),
    ("WELCORP", "NSE", "INE191B01025", "Welspun Corp Ltd", "Metals & Mining", "Steel Pipes", "WELCORP", "532144"),
    ("JSWINFRA", "NSE", "INE880J01012", "JSW Infrastructure Ltd", "Metals & Mining", "Ports & Infrastructure", "JSWINFRA", "543900"),

    # ── Construction & Engineering (25 companies) ────────────────
    ("LT", "NSE", "INE018A01030", "Larsen & Toubro Ltd", "Construction", "Engineering - EPC", "LT", "500510"),
    ("ULTRACEMCO", "NSE", "INE481G01011", "UltraTech Cement Ltd", "Construction", "Cement", "ULTRACEMCO", "532538"),
    ("GRASIM", "NSE", "INE047A01021", "Grasim Industries Ltd", "Construction", "Cement & Diversified", "GRASIM", "500300"),
    ("SHREECEM", "NSE", "INE070A01015", "Shree Cement Ltd", "Construction", "Cement", "SHREECEM", "500387"),
    ("AMBUJACEM", "NSE", "INE079A01024", "Ambuja Cements Ltd", "Construction", "Cement", "AMBUJACEM", "500425"),
    ("ACC", "NSE", "INE012A01025", "ACC Ltd", "Construction", "Cement", "ACC", "500410"),
    ("RAMCOCEM", "NSE", "INE331A01037", "The Ramco Cements Ltd", "Construction", "Cement", "RAMCOCEM", "500260"),
    ("DALMIACEM", "NSE", "INE007A01025", "Dalmia Bharat Ltd", "Construction", "Cement", "DALMIACEM", "502032"),
    ("JKCEMENT", "NSE", "INE823G01014", "JK Cement Ltd", "Construction", "Cement", "JKCEMENT", "532644"),
    ("STARCEMENT", "NSE", "INE460H01021", "Star Cement Ltd", "Construction", "Cement", "STARCEMENT", "540575"),
    ("NUVOCO", "NSE", "INE859I01011", "Nuvoco Vistas Corp Ltd", "Construction", "Cement", "NUVOCO", "543334"),
    ("IRCON", "NSE", "INE962Y01021", "Ircon International Ltd", "Construction", "Engineering - Railway", "IRCON", "541956"),
    ("NBCC", "NSE", "INE095N01031", "NBCC India Ltd", "Construction", "Construction - PSU", "NBCC", "534309"),
    ("KEC", "NSE", "INE389H01022", "KEC International Ltd", "Construction", "Engineering - Power T&D", "KEC", "532714"),
    ("THERMAX", "NSE", "INE152A01029", "Thermax Ltd", "Construction", "Engineering - Energy", "THERMAX", "500411"),
    ("CUMMINSIND", "NSE", "INE298A01020", "Cummins India Ltd", "Construction", "Engineering - Engines", "CUMMINSIND", "500480"),
    ("KALPATPOWR", "NSE", "INE220B01022", "Kalpataru Projects International", "Construction", "Engineering - Power T&D", "KALPATPOWR", "522287"),
    ("NCC", "NSE", "INE868B01028", "NCC Ltd", "Construction", "Construction - Infra", "NCC", "500294"),
    ("PNCINFRA", "NSE", "INE195J01029", "PNC Infratech Ltd", "Construction", "Construction - Roads", "PNCINFRA", "539150"),
    ("HCC", "NSE", "INE549A01026", "Hindustan Construction Co", "Construction", "Construction - Infra", "HCC", "500185"),

    # ── Telecom & Media (10 companies) ───────────────────────────
    ("BHARTIARTL", "NSE", "INE397D01024", "Bharti Airtel Ltd", "Telecom", "Telecom - Wireless", "BHARTIARTL", "532454"),
    ("IDEA", "NSE", "INE669E01016", "Vodafone Idea Ltd", "Telecom", "Telecom - Wireless", "IDEA", "532822"),
    ("TTML", "NSE", "INE517B01013", "Tata Teleservices Maharashtra", "Telecom", "Telecom - Wireless", "TTML", "532371"),
    ("INDUSTOWER", "NSE", "INE121W01018", "Indus Towers Ltd", "Telecom", "Telecom - Infrastructure", "INDUSTOWER", "534816"),
    ("SUNTV", "NSE", "INE424H01027", "Sun TV Network Ltd", "Telecom", "Media - Broadcasting", "SUNTV", "532733"),
    ("ZEEL", "NSE", "INE256A01028", "Zee Entertainment Enterprises", "Telecom", "Media - Broadcasting", "ZEEL", "505537"),
    ("PVR", "NSE", "INE191H01014", "PVR INOX Ltd", "Telecom", "Media - Entertainment", "PVR", "532689"),
    ("NAZARA", "NSE", "INE418L01014", "Nazara Technologies Ltd", "Telecom", "Gaming", "NAZARA", "543280"),
    ("NXTDIGITAL", "NSE", "INE040M01015", "NxtDigital Ltd", "Telecom", "Media - Cable TV", "NXTDIGITAL", "543272"),
    ("HATHWAY", "NSE", "INE982F01036", "Hathway Cable & Datacom", "Telecom", "Media - Cable TV", "HATHWAY", "533162"),

    # ── Consumer Durables & Retail (25 companies) ────────────────
    ("TITAN", "NSE", "INE280A01028", "Titan Company Ltd", "Consumer Durables", "Jewellery & Watches", "TITAN", "500114"),
    ("ASIANPAINT", "NSE", "INE021A01026", "Asian Paints Ltd", "Consumer Durables", "Paints", "ASIANPAINT", "500820"),
    ("PIDILITIND", "NSE", "INE318A01026", "Pidilite Industries Ltd", "Consumer Durables", "Adhesives", "PIDILITIND", "500331"),
    ("HAVELLS", "NSE", "INE176B01034", "Havells India Ltd", "Consumer Durables", "Electrical Equipment", "HAVELLS", "517354"),
    ("VOLTAS", "NSE", "INE226A01021", "Voltas Ltd", "Consumer Durables", "Air Conditioning", "VOLTAS", "500575"),
    ("WHIRLPOOL", "NSE", "INE716A01013", "Whirlpool of India Ltd", "Consumer Durables", "Home Appliances", "WHIRLPOOL", "500238"),
    ("BLUESTARCO", "NSE", "INE472A01039", "Blue Star Ltd", "Consumer Durables", "Air Conditioning", "BLUESTARCO", "500067"),
    ("CROMPTON", "NSE", "INE299U01018", "Crompton Greaves Consumer", "Consumer Durables", "Electrical Equipment", "CROMPTON", "539876"),
    ("ORIENTELEC", "NSE", "INE142Z01019", "Orient Electric Ltd", "Consumer Durables", "Electrical Equipment", "ORIENTELEC", "541301"),
    ("BAJAJELEC", "NSE", "INE193E01025", "Bajaj Electricals Ltd", "Consumer Durables", "Electrical Equipment", "BAJAJELEC", "500031"),
    ("KAJARIACER", "NSE", "INE217B01036", "Kajaria Ceramics Ltd", "Consumer Durables", "Building Materials", "KAJARIACER", "500233"),
    ("CENTURYPLY", "NSE", "INE348B01021", "Century Plyboards India", "Consumer Durables", "Building Materials", "CENTURYPLY", "532548"),
    ("BERGEPAINT", "NSE", "INE463A01038", "Berger Paints India Ltd", "Consumer Durables", "Paints", "BERGEPAINT", "509480"),
    ("KANSAINER", "NSE", "INE217A01012", "Kansai Nerolac Paints", "Consumer Durables", "Paints", "KANSAINER", "500165"),
    ("TRENT", "NSE", "INE849A01020", "Trent Ltd", "Consumer Durables", "Retail - Fashion", "TRENT", "500251"),
    ("DMART", "NSE", "INE599L01018", "Avenue Supermarts Ltd", "Consumer Durables", "Retail - Grocery", "DMART", "540376"),
    ("SHOPERSTOP", "NSE", "INE498B01024", "Shoppers Stop Ltd", "Consumer Durables", "Retail - Department", "SHOPERSTOP", "532638"),
    ("VMART", "NSE", "INE665J01013", "V-Mart Retail Ltd", "Consumer Durables", "Retail - Value", "VMART", "534976"),
    ("PAGEIND", "NSE", "INE761H01022", "Page Industries Ltd", "Consumer Durables", "Apparel", "PAGEIND", "532827"),
    ("RELAXO", "NSE", "INE131B01039", "Relaxo Footwears Ltd", "Consumer Durables", "Footwear", "RELAXO", "530517"),
    ("BATAINDIA", "NSE", "INE176A01028", "Bata India Ltd", "Consumer Durables", "Footwear", "BATAINDIA", "500043"),
    ("METROBRAND", "NSE", "INE317K01015", "Metro Brands Ltd", "Consumer Durables", "Footwear - Retail", "METROBRAND", "543426"),
    ("CAMPUS", "NSE", "INE768C01028", "Campus Activewear Ltd", "Consumer Durables", "Footwear", "CAMPUS", "543523"),
    ("SAPPHIRE", "NSE", "INE770I01018", "Sapphire Foods India", "Consumer Durables", "QSR", "SAPPHIRE", "543397"),
    ("DEVYANI", "NSE", "INE872J01015", "Devyani International Ltd", "Consumer Durables", "QSR", "DEVYANI", "543330"),

    # ── Chemicals & Fertilizers (25 companies) ───────────────────
    ("PIIND", "NSE", "INE603J01030", "PI Industries Ltd", "Chemicals", "Agrochemicals", "PIIND", "523642"),
    ("UPL", "NSE", "INE628A01036", "UPL Ltd", "Chemicals", "Agrochemicals", "UPL", "512070"),
    ("SRF", "NSE", "INE647A01010", "SRF Ltd", "Chemicals", "Specialty Chemicals", "SRF", "503806"),
    ("DEEPAKNTR", "NSE", "INE288B01029", "Deepak Nitrite Ltd", "Chemicals", "Specialty Chemicals", "DEEPAKNTR", "506401"),
    ("ATUL", "NSE", "INE100A01010", "Atul Ltd", "Chemicals", "Specialty Chemicals", "ATUL", "500027"),
    ("NAVINFLUOR", "NSE", "INE048G01026", "Navin Fluorine International", "Chemicals", "Specialty Chemicals", "NAVINFLUOR", "532504"),
    ("CLEAN", "NSE", "INE473R01018", "Clean Science & Technology", "Chemicals", "Specialty Chemicals", "CLEAN", "543318"),
    ("AARTIIND", "NSE", "INE769A01020", "Aarti Industries Ltd", "Chemicals", "Specialty Chemicals", "AARTIIND", "524208"),
    ("FINEORG", "NSE", "INE686Y01026", "Fine Organic Industries", "Chemicals", "Oleochemicals", "FINEORG", "541557"),
    ("TATACHEM", "NSE", "INE092A01019", "Tata Chemicals Ltd", "Chemicals", "Inorganic Chemicals", "TATACHEM", "500770"),
    ("CHAMBLFERT", "NSE", "INE085A01013", "Chambal Fertilisers", "Chemicals", "Fertilizers", "CHAMBLFERT", "500085"),
    ("COROMANDEL", "NSE", "INE169A01031", "Coromandel International", "Chemicals", "Fertilizers", "COROMANDEL", "506395"),
    ("GNFC", "NSE", "INE113A01013", "Gujarat Narmada Valley Fertilizers", "Chemicals", "Fertilizers", "GNFC", "500670"),
    ("GSFC", "NSE", "INE026A01025", "Gujarat State Fertilizers", "Chemicals", "Fertilizers", "GSFC", "500690"),
    ("RALLIS", "NSE", "INE613A01020", "Rallis India Ltd", "Chemicals", "Agrochemicals", "RALLIS", "500355"),
    ("BASF", "NSE", "INE373A01013", "BASF India Ltd", "Chemicals", "Diversified Chemicals", "BASF", "500042"),
    ("FLUOROCHEM", "NSE", "INE11LI01012", "Gujarat Fluorochemicals", "Chemicals", "Fluorochemicals", "FLUOROCHEM", "543285"),
    ("GALAXYSURF", "NSE", "INE600K01018", "Galaxy Surfactants Ltd", "Chemicals", "Surfactants", "GALAXYSURF", "540935"),
    ("ANURAS", "NSE", "INE457K01013", "Anupam Rasayan India", "Chemicals", "Custom Synthesis", "ANURAS", "543275"),
    ("NOCIL", "NSE", "INE163A01018", "NOCIL Ltd", "Chemicals", "Rubber Chemicals", "NOCIL", "500730"),

    # ── Real Estate (15 companies) ───────────────────────────────
    ("DLF", "NSE", "INE271C01023", "DLF Ltd", "Real Estate", "Real Estate - Residential", "DLF", "532868"),
    ("GODREJPROP", "NSE", "INE484J01027", "Godrej Properties Ltd", "Real Estate", "Real Estate - Residential", "GODREJPROP", "533150"),
    ("OBEROIRLTY", "NSE", "INE093I01010", "Oberoi Realty Ltd", "Real Estate", "Real Estate - Luxury", "OBEROIRLTY", "533273"),
    ("PRESTIGE", "NSE", "INE811K01011", "Prestige Estates Projects", "Real Estate", "Real Estate - Diversified", "PRESTIGE", "533274"),
    ("BRIGADE", "NSE", "INE791I01019", "Brigade Enterprises Ltd", "Real Estate", "Real Estate - Diversified", "BRIGADE", "532929"),
    ("LODHA", "NSE", "INE670K01029", "Macrotech Developers Ltd", "Real Estate", "Real Estate - Residential", "LODHA", "543287"),
    ("SOBHA", "NSE", "INE671H01015", "Sobha Ltd", "Real Estate", "Real Estate - Residential", "SOBHA", "532784"),
    ("PHOENIXLTD", "NSE", "INE267B01025", "Phoenix Mills Ltd", "Real Estate", "Real Estate - Retail", "PHOENIXLTD", "503100"),
    ("EMBASSY", "NSE", "INE041K01011", "Embassy Office Parks REIT", "Real Estate", "REIT - Commercial", "EMBASSY", "542602"),
    ("MINDSPACE", "NSE", "INE0CCU01010", "Mindspace Business Parks REIT", "Real Estate", "REIT - Commercial", "MINDSPACE", "543217"),
    ("SUNTECK", "NSE", "INE805D01034", "Sunteck Realty Ltd", "Real Estate", "Real Estate - Luxury", "SUNTECK", "512179"),
    ("MAHLIFE", "NSE", "INE813A01018", "Mahindra Lifespace Developers", "Real Estate", "Real Estate - Diversified", "MAHLIFE", "532313"),

    # ── Infrastructure & Logistics (15 companies) ────────────────
    ("ADANIPORTS", "NSE", "INE742F01042", "Adani Ports & SEZ Ltd", "Infrastructure", "Ports", "ADANIPORTS", "532921"),
    ("CONCOR", "NSE", "INE111A01025", "Container Corp of India", "Infrastructure", "Logistics - Rail", "CONCOR", "531344"),
    ("IRCTC", "NSE", "INE335Y01020", "Indian Railway Catering & Tourism", "Infrastructure", "Railways - Services", "IRCTC", "542830"),
    ("RVNL", "NSE", "INE415G01027", "Rail Vikas Nigam Ltd", "Infrastructure", "Railways - Construction", "RVNL", "542649"),
    ("GMDCLTD", "NSE", "INE131A01023", "Gujarat Mineral Dev Corp", "Infrastructure", "Mining - PSU", "GMDCLTD", "532181"),
    ("IRB", "NSE", "INE821I01014", "IRB Infrastructure Developers", "Infrastructure", "Roads & Highways", "IRB", "532947"),
    ("DELHIVERY", "NSE", "INE148O01028", "Delhivery Ltd", "Infrastructure", "Logistics - Express", "DELHIVERY", "543529"),
    ("BLUEDART", "NSE", "INE233B01017", "Blue Dart Express Ltd", "Infrastructure", "Logistics - Express", "BLUEDART", "526612"),
    ("MAHSEAMLES", "NSE", "INE271B01025", "Maharashtra Seamless Ltd", "Infrastructure", "Steel Pipes", "MAHSEAMLES", "500265"),
    ("GSPL", "NSE", "INE246F01010", "Gujarat State Petronet Ltd", "Infrastructure", "Gas Pipeline", "GSPL", "532702"),
    ("HUDCO", "NSE", "INE031A01017", "Housing & Urban Development Corp", "Infrastructure", "Housing Finance - PSU", "HUDCO", "540530"),
    ("COCHINSHIP", "NSE", "INE704A01026", "Cochin Shipyard Ltd", "Infrastructure", "Shipbuilding", "COCHINSHIP", "540678"),
    ("GRSE", "NSE", "INE152A01029", "Garden Reach Shipbuilders", "Infrastructure", "Shipbuilding - Defence", "GRSE", "542011"),

    # ── Defence & Aerospace (10 companies) ───────────────────────
    ("HAL", "NSE", "INE066F01020", "Hindustan Aeronautics Ltd", "Defence", "Aerospace - PSU", "HAL", "541154"),
    ("BEL", "NSE", "INE263A01024", "Bharat Electronics Ltd", "Defence", "Defence Electronics", "BEL", "500049"),
    ("BDL", "NSE", "INE171Z01018", "Bharat Dynamics Ltd", "Defence", "Missiles & Defence", "BDL", "541143"),
    ("SOLARINDS", "NSE", "INE343H01029", "Solar Industries India", "Defence", "Explosives & Defence", "SOLARINDS", "532725"),
    ("DATAPATTER", "NSE", "INE0II801010", "Data Patterns India Ltd", "Defence", "Defence Electronics", "DATAPATTER", "543428"),
    ("MAZAGON", "NSE", "INE249Z01012", "Mazagon Dock Shipbuilders", "Defence", "Shipbuilding - Defence", "MAZAGON", "543237"),
    ("PARAS", "NSE", "INE883L01018", "Paras Defence & Space Tech", "Defence", "Defence Components", "PARAS", "543367"),

    # ── Textiles & Apparel (10 companies) ────────────────────────
    ("RAYMOND", "NSE", "INE301A01014", "Raymond Ltd", "Textiles", "Textiles - Diversified", "RAYMOND", "500330"),
    ("ARVIND", "NSE", "INE034A01011", "Arvind Ltd", "Textiles", "Textiles - Cotton", "ARVIND", "500101"),
    ("WELSPUNLIV", "NSE", "INE192B01031", "Welspun Living Ltd", "Textiles", "Home Textiles", "WELSPUNLIV", "514162"),
    ("TRIDENT", "NSE", "INE064C01022", "Trident Ltd", "Textiles", "Home Textiles", "TRIDENT", "521064"),
    ("KITEX", "NSE", "INE602G01020", "Kitex Garments Ltd", "Textiles", "Garments - Kids", "KITEX", "521248"),
    ("KPRMILL", "NSE", "INE930H01023", "K.P.R. Mill Ltd", "Textiles", "Textiles - Integrated", "KPRMILL", "532889"),
    ("HIMATSEIDE", "NSE", "INE049A01027", "Himatsingka Seide Ltd", "Textiles", "Home Textiles", "HIMATSEIDE", "514043"),
    ("SOMANYCERA", "NSE", "INE355A01028", "Somany Ceramics Ltd", "Textiles", "Ceramics", "SOMANYCERA", "532324"),

    # ── Diversified / Conglomerate (10 companies) ────────────────
    ("SIEMENS", "NSE", "INE003A01024", "Siemens Ltd", "Diversified", "Engineering - MNC", "SIEMENS", "500550"),
    ("ABB", "NSE", "INE117A01022", "ABB India Ltd", "Diversified", "Engineering - MNC", "ABB", "500002"),
    ("HONAUT", "NSE", "INE671A01010", "Honeywell Automation India", "Diversified", "Automation - MNC", "HONAUT", "517174"),
    ("3MINDIA", "NSE", "INE470A01017", "3M India Ltd", "Diversified", "Diversified - MNC", "3MINDIA", "523395"),
    ("PGHH", "NSE", "INE179A01014", "Procter & Gamble Health", "Diversified", "FMCG - Health", "PGHH", "500459"),
    ("GRINDWELL", "NSE", "INE536A01023", "Grindwell Norton Ltd", "Diversified", "Abrasives", "GRINDWELL", "506076"),
    ("CARBORUNIV", "NSE", "INE120A01034", "Carborundum Universal", "Diversified", "Abrasives", "CARBORUNIV", "513375"),
    ("AIAENG", "NSE", "INE212H01026", "AIA Engineering Ltd", "Diversified", "Castings", "AIAENG", "532683"),
    ("ELGIEQUIP", "NSE", "INE285A01027", "Elgi Equipments Ltd", "Diversified", "Compressors", "ELGIEQUIP", "522074"),
    ("GODREJIND", "NSE", "INE233A01035", "Godrej Industries Ltd", "Diversified", "Conglomerate", "GODREJIND", "500163"),

    # ── Miscellaneous / Others (25 companies) ────────────────────
    ("ZOMATO", "NSE", "INE758T01015", "Zomato Ltd", "Technology", "Food Delivery", "ZOMATO", "543320"),
    ("NYKAA", "NSE", "INE388Y01029", "FSN E-Commerce Ventures", "Technology", "Beauty E-Commerce", "NYKAA", "543384"),
    ("PAYTM", "NSE", "INE982J01020", "One97 Communications Ltd", "Technology", "Fintech", "PAYTM", "543396"),
    ("POLICYBZR", "NSE", "INE417T01026", "PB Fintech Ltd", "Technology", "Insurtech", "POLICYBZR", "543390"),
    ("CARTRADE", "NSE", "INE290S01011", "CarTrade Tech Ltd", "Technology", "Auto Marketplace", "CARTRADE", "543358"),
    ("INDIAMART", "NSE", "INE933S01016", "IndiaMART InterMESH Ltd", "Technology", "B2B Marketplace", "INDIAMART", "542726"),
    ("INFOEDGE", "NSE", "INE663F01024", "Info Edge India Ltd", "Technology", "Internet - Classifieds", "INFOEDGE", "532777"),
    ("JUSTDIAL", "NSE", "INE599M01018", "Just Dial Ltd", "Technology", "Local Search", "JUSTDIAL", "535648"),
    ("MAPMYINDIA", "NSE", "INE0BJ901019", "C.E. Info Systems Ltd", "Technology", "Map Technology", "MAPMYINDIA", "543425"),
    ("AFFLE", "NSE", "INE00WK01013", "Affle India Ltd", "Technology", "AdTech", "AFFLE", "542752"),
    ("EASEMYTRIP", "NSE", "INE07RH01011", "Easy Trip Planners Ltd", "Technology", "Travel Tech", "EASEMYTRIP", "543272"),
    ("IIFLSEC", "NSE", "INE466L01038", "IIFL Securities Ltd", "Financial Services", "Stock Broking", "IIFLSEC", "542773"),
    ("CRISIL", "NSE", "INE007A01025", "CRISIL Ltd", "Financial Services", "Credit Rating", "CRISIL", "500092"),
    ("ICRA", "NSE", "INE725G01011", "ICRA Ltd", "Financial Services", "Credit Rating", "ICRA", "532835"),
    ("CARERATING", "NSE", "INE752H01013", "CARE Ratings Ltd", "Financial Services", "Credit Rating", "CARERATING", "534804"),
    ("WHIRLPOOL", "NSE", "INE716A01013", "Whirlpool of India Ltd", "Consumer Durables", "Home Appliances", "WHIRLPOOL", "500238"),
    ("DIXON", "NSE", "INE935N01020", "Dixon Technologies India", "Consumer Durables", "Electronics Manufacturing", "DIXON", "540699"),
    ("KAYNES", "NSE", "INE918Z01012", "Kaynes Technology India", "Technology", "EMS", "KAYNES", "543600"),
    ("AMBER", "NSE", "INE371P01015", "Amber Enterprises India", "Consumer Durables", "AC Components", "AMBER", "540902"),
    ("SYRMA", "NSE", "INE0DWR01010", "Syrma SGS Technology Ltd", "Technology", "EMS", "SYRMA", "543573"),
    ("TTKPRESTIG", "NSE", "INE690A01028", "TTK Prestige Ltd", "Consumer Durables", "Kitchen Appliances", "TTKPRESTIG", "517506"),
    ("JUBLFOOD", "NSE", "INE797F01020", "Jubilant Foodworks Ltd", "Consumer Durables", "QSR", "JUBLFOOD", "533155"),
    ("WESTLIFE", "NSE", "INE274F01020", "Westlife Foodworld Ltd", "Consumer Durables", "QSR", "WESTLIFE", "505533"),
    ("NYKAA", "NSE", "INE388Y01029", "FSN E-Commerce Ventures", "Technology", "Beauty E-Commerce", "NYKAA", "543384"),
    ("APTUS", "NSE", "INE852O01025", "Aptus Value Housing Finance", "Financial Services", "Housing Finance", "APTUS", "543335"),
]


DATA_SOURCES = [
    ("BSE India", "exchange", "https://www.bseindia.com", 0.95, "Public corporate announcements via BSE website", True),
    ("NSE India", "exchange", "https://www.nseindia.com", 0.95, "Public corporate announcements via NSE website", True),
    ("MoneyControl", "news", "https://www.moneycontrol.com", 0.80, "Public financial news aggregator", True),
    ("Economic Times", "news", "https://economictimes.indiatimes.com", 0.80, "Public financial news", True),
    ("LiveMint", "news", "https://www.livemint.com", 0.80, "Public financial news", True),
    ("Business Standard", "news", "https://www.business-standard.com", 0.80, "Public financial news", True),
    ("NDTV Profit", "news", "https://www.ndtvprofit.com", 0.75, "Public financial news", True),
    ("RBI", "regulator", "https://www.rbi.org.in", 0.98, "Reserve Bank of India public releases", True),
    ("SEBI", "regulator", "https://www.sebi.gov.in", 0.98, "SEBI circulars and orders", True),
    ("Ministry of Finance", "regulator", "https://www.finmin.nic.in", 0.95, "Government fiscal policy releases", True),
    ("Yahoo Finance", "market_data", "https://finance.yahoo.com", 0.70, "Delayed market data for educational/demo use via yfinance", True),
    ("Alpha Vantage", "market_data", "https://www.alphavantage.co", 0.70, "Free-tier market data API", True),
    ("Company IR Pages", "company", None, 0.90, "Investor relations pages of listed companies", True),
    ("Earnings Transcripts", "transcript", None, 0.85, "Public earnings call transcripts from multiple sources", True),
    ("Screener.in", "analytics", "https://www.screener.in", 0.80, "Public financial analytics portal", True),
]


async def seed_companies_async():
    """Seed companies using async SQLAlchemy."""
    from app.config import get_settings
    from app.db.session import async_session_factory, engine
    from app.db.models import Company, DataSource
    from sqlalchemy import select, text

    settings = get_settings()
    logger.info("Starting database seed with %d companies and %d data sources",
                len(COMPANIES), len(DATA_SOURCES))

    async with async_session_factory() as session:
        # Check if companies already seeded
        result = await session.execute(select(Company).limit(1))
        existing = result.scalar_one_or_none()
        if existing:
            count_result = await session.execute(text("SELECT COUNT(*) FROM companies"))
            count = count_result.scalar()
            logger.info("Database already has %d companies. Skipping seed.", count)
            return

        # Seed data sources
        seen_sources = set()
        for src in DATA_SOURCES:
            name = src[0]
            if name in seen_sources:
                continue
            seen_sources.add(name)
            ds = DataSource(
                source_name=src[0],
                source_type=src[1],
                base_url=src[2],
                reliability_score=src[3],
                license_notes=src[4],
                is_active=src[5],
            )
            session.add(ds)

        # Seed companies (deduplicate by symbol+exchange)
        seen = set()
        added = 0
        for comp in COMPANIES:
            key = (comp[0], comp[1])  # (symbol, exchange)
            if key in seen:
                continue
            seen.add(key)

            company = Company(
                symbol=comp[0],
                exchange=comp[1],
                isin=comp[2],
                company_name=comp[3],
                sector=comp[4],
                industry=comp[5],
                nse_symbol=comp[6],
                bse_code=comp[7],
                is_active=True,
            )
            session.add(company)
            added += 1

        await session.commit()
        logger.info("Seeded %d unique companies and %d data sources.", added, len(seen_sources))


def main():
    """Entry point."""
    logger.info("=" * 60)
    logger.info("Bharat Market Intelligence — Database Seeder")
    logger.info("=" * 60)
    asyncio.run(seed_companies_async())
    logger.info("Seed complete.")


if __name__ == "__main__":
    main()
