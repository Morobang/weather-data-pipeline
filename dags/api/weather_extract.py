import requests
import json
import time
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional

# ============================================================
# LOGGING
# Airflow captures this properly unlike print statements
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(levelname)s — %(message)s"
)
log = logging.getLogger(__name__)

# ============================================================
# CONFIG FROM ENVIRONMENT
# Values come from .env — never hardcoded
# ============================================================
TIMEZONE      = os.getenv("WEATHER_TIMEZONE",      "Africa/Johannesburg")
FORECAST_DAYS = int(os.getenv("WEATHER_FORECAST_DAYS", "1"))
API_BASE_URL  = os.getenv("WEATHER_API_BASE_URL",  "https://api.open-meteo.com/v1/forecast")
DATA_DIR      = os.getenv("DATA_OUTPUT_DIR",        "data")

# ============================================================
# ALL 257 SA MUNICIPALITIES — 9 PROVINCES
# ============================================================
MUNICIPALITIES = [
    # ==================== EASTERN CAPE (38) ====================
    {"name": "Buffalo City",            "province": "Eastern Cape", "type": "Metropolitan", "lat": -32.9833, "lon": 27.8667},
    {"name": "Nelson Mandela Bay",      "province": "Eastern Cape", "type": "Metropolitan", "lat": -33.9581, "lon": 25.6000},
    {"name": "Alfred Nzo",              "province": "Eastern Cape", "type": "District",     "lat": -30.6500, "lon": 28.8833},
    {"name": "Amathole",                "province": "Eastern Cape", "type": "District",     "lat": -32.5667, "lon": 27.3667},
    {"name": "Chris Hani",              "province": "Eastern Cape", "type": "District",     "lat": -31.8833, "lon": 26.8833},
    {"name": "Joe Gqabi",               "province": "Eastern Cape", "type": "District",     "lat": -30.6667, "lon": 27.5000},
    {"name": "O.R. Tambo",              "province": "Eastern Cape", "type": "District",     "lat": -31.5667, "lon": 28.7833},
    {"name": "Sarah Baartman",          "province": "Eastern Cape", "type": "District",     "lat": -33.3000, "lon": 26.5000},
    {"name": "Thembisile Hani",         "province": "Eastern Cape", "type": "District",     "lat": -31.4167, "lon": 28.7000},
    {"name": "Amahlathi",               "province": "Eastern Cape", "type": "Local",        "lat": -32.7000, "lon": 27.3167},
    {"name": "Blue Crane Route",        "province": "Eastern Cape", "type": "Local",        "lat": -33.0000, "lon": 26.0000},
    {"name": "Dr Beyers Naude",         "province": "Eastern Cape", "type": "Local",        "lat": -31.8833, "lon": 26.8833},
    {"name": "Elundini",                "province": "Eastern Cape", "type": "Local",        "lat": -30.8667, "lon": 28.4000},
    {"name": "Emalahleni",              "province": "Eastern Cape", "type": "Local",        "lat": -31.9167, "lon": 27.0333},
    {"name": "Engcobo",                 "province": "Eastern Cape", "type": "Local",        "lat": -31.6667, "lon": 28.0000},
    {"name": "Enoch Mgijima",           "province": "Eastern Cape", "type": "Local",        "lat": -31.9000, "lon": 26.8833},
    {"name": "Great Kei",               "province": "Eastern Cape", "type": "Local",        "lat": -32.7500, "lon": 28.2500},
    {"name": "Ingquza Hill",            "province": "Eastern Cape", "type": "Local",        "lat": -30.9500, "lon": 29.4500},
    {"name": "Intsika Yethu",           "province": "Eastern Cape", "type": "Local",        "lat": -31.7500, "lon": 28.0000},
    {"name": "Inxuba Yethemba",         "province": "Eastern Cape", "type": "Local",        "lat": -32.0000, "lon": 26.5000},
    {"name": "King Sabata Dalindyebo",  "province": "Eastern Cape", "type": "Local",        "lat": -31.5887, "lon": 28.7840},
    {"name": "Kouga",                   "province": "Eastern Cape", "type": "Local",        "lat": -33.7500, "lon": 25.4000},
    {"name": "Kou-Kamma",               "province": "Eastern Cape", "type": "Local",        "lat": -33.7500, "lon": 24.5000},
    {"name": "Makana",                  "province": "Eastern Cape", "type": "Local",        "lat": -33.3167, "lon": 26.5167},
    {"name": "Matatiele",               "province": "Eastern Cape", "type": "Local",        "lat": -30.3333, "lon": 28.8333},
    {"name": "Mbhashe",                 "province": "Eastern Cape", "type": "Local",        "lat": -32.2500, "lon": 28.5000},
    {"name": "Mhlontlo",                "province": "Eastern Cape", "type": "Local",        "lat": -31.3333, "lon": 29.0000},
    {"name": "Mnquma",                  "province": "Eastern Cape", "type": "Local",        "lat": -32.5000, "lon": 28.0000},
    {"name": "Ndlambe",                 "province": "Eastern Cape", "type": "Local",        "lat": -33.5500, "lon": 27.0000},
    {"name": "Ngqushwa",                "province": "Eastern Cape", "type": "Local",        "lat": -33.3000, "lon": 27.2000},
    {"name": "Ntabankulu",              "province": "Eastern Cape", "type": "Local",        "lat": -30.9500, "lon": 29.3000},
    {"name": "Nyandeni",                "province": "Eastern Cape", "type": "Local",        "lat": -31.3667, "lon": 28.8500},
    {"name": "Port St Johns",           "province": "Eastern Cape", "type": "Local",        "lat": -31.6333, "lon": 29.5333},
    {"name": "Raymond Mhlaba",          "province": "Eastern Cape", "type": "Local",        "lat": -32.7833, "lon": 27.0167},
    {"name": "Sakhisizwe",              "province": "Eastern Cape", "type": "Local",        "lat": -31.3667, "lon": 27.9000},
    {"name": "Senqu",                   "province": "Eastern Cape", "type": "Local",        "lat": -30.6667, "lon": 27.5000},
    {"name": "Sundays River Valley",    "province": "Eastern Cape", "type": "Local",        "lat": -33.5000, "lon": 25.5000},
    {"name": "Umzimvubu",               "province": "Eastern Cape", "type": "Local",        "lat": -30.6667, "lon": 29.5000},

    # ==================== FREE STATE (23) ====================
    {"name": "Mangaung",                "province": "Free State",   "type": "Metropolitan", "lat": -29.0852, "lon": 26.1596},
    {"name": "Fezile Dabi",             "province": "Free State",   "type": "District",     "lat": -26.9333, "lon": 27.8667},
    {"name": "Lejweleputswa",           "province": "Free State",   "type": "District",     "lat": -27.9833, "lon": 26.7333},
    {"name": "Thabo Mofutsanyana",      "province": "Free State",   "type": "District",     "lat": -28.5333, "lon": 28.8833},
    {"name": "Xhariep",                 "province": "Free State",   "type": "District",     "lat": -29.5000, "lon": 26.0000},
    {"name": "Dihlabeng",               "province": "Free State",   "type": "Local",        "lat": -28.3333, "lon": 28.5000},
    {"name": "Kopanong",                "province": "Free State",   "type": "Local",        "lat": -30.0000, "lon": 26.0000},
    {"name": "Letsemeng",               "province": "Free State",   "type": "Local",        "lat": -29.5000, "lon": 25.5000},
    {"name": "Mafube",                  "province": "Free State",   "type": "Local",        "lat": -27.0667, "lon": 28.4500},
    {"name": "Maluti-a-Phofung",        "province": "Free State",   "type": "Local",        "lat": -28.5333, "lon": 28.8833},
    {"name": "Mantsopa",                "province": "Free State",   "type": "Local",        "lat": -29.1167, "lon": 27.1667},
    {"name": "Masilonyana",             "province": "Free State",   "type": "Local",        "lat": -28.0000, "lon": 26.6667},
    {"name": "Matjhabeng",              "province": "Free State",   "type": "Local",        "lat": -27.9833, "lon": 26.7333},
    {"name": "Metsimaholo",             "province": "Free State",   "type": "Local",        "lat": -26.9333, "lon": 27.8667},
    {"name": "Mohokare",                "province": "Free State",   "type": "Local",        "lat": -30.2000, "lon": 27.5000},
    {"name": "Moqhaka",                 "province": "Free State",   "type": "Local",        "lat": -27.0000, "lon": 27.4833},
    {"name": "Nala",                    "province": "Free State",   "type": "Local",        "lat": -28.0000, "lon": 26.7000},
    {"name": "Ngwathe",                 "province": "Free State",   "type": "Local",        "lat": -27.0333, "lon": 28.0000},
    {"name": "Nketoana",                "province": "Free State",   "type": "Local",        "lat": -27.7167, "lon": 28.6167},
    {"name": "Phumelela",               "province": "Free State",   "type": "Local",        "lat": -27.0000, "lon": 29.5000},
    {"name": "Setsoto",                 "province": "Free State",   "type": "Local",        "lat": -28.5000, "lon": 27.5000},
    {"name": "Tokologo",                "province": "Free State",   "type": "Local",        "lat": -28.0000, "lon": 25.5000},
    {"name": "Tswelopele",              "province": "Free State",   "type": "Local",        "lat": -27.8000, "lon": 26.3000},

    # ==================== GAUTENG (11) ====================
    {"name": "City of Ekurhuleni",      "province": "Gauteng",      "type": "Metropolitan", "lat": -26.3592, "lon": 28.1456},
    {"name": "City of Johannesburg",    "province": "Gauteng",      "type": "Metropolitan", "lat": -26.2041, "lon": 28.0473},
    {"name": "City of Tshwane",         "province": "Gauteng",      "type": "Metropolitan", "lat": -25.7479, "lon": 28.2293},
    {"name": "Sedibeng",                "province": "Gauteng",      "type": "District",     "lat": -26.6667, "lon": 28.0000},
    {"name": "West Rand",               "province": "Gauteng",      "type": "District",     "lat": -26.2500, "lon": 27.5000},
    {"name": "Emfuleni",                "province": "Gauteng",      "type": "Local",        "lat": -26.7000, "lon": 27.8000},
    {"name": "Lesedi",                  "province": "Gauteng",      "type": "Local",        "lat": -26.5000, "lon": 28.5000},
    {"name": "Merafong",                "province": "Gauteng",      "type": "Local",        "lat": -26.3667, "lon": 27.6667},
    {"name": "Midvaal",                 "province": "Gauteng",      "type": "Local",        "lat": -26.5000, "lon": 28.0000},
    {"name": "Mogale City",             "province": "Gauteng",      "type": "Local",        "lat": -26.0000, "lon": 27.6667},
    {"name": "Rand West City",          "province": "Gauteng",      "type": "Local",        "lat": -26.2500, "lon": 27.5000},

    # ==================== KWAZULU-NATAL (54) ====================
    {"name": "eThekwini",               "province": "KwaZulu-Natal","type": "Metropolitan", "lat": -29.8587, "lon": 31.0218},
    {"name": "Amajuba",                 "province": "KwaZulu-Natal","type": "District",     "lat": -27.7559, "lon": 29.9318},
    {"name": "Harry Gwala",             "province": "KwaZulu-Natal","type": "District",     "lat": -30.0000, "lon": 29.5000},
    {"name": "iLembe",                  "province": "KwaZulu-Natal","type": "District",     "lat": -29.5000, "lon": 31.0000},
    {"name": "King Cetshwayo",          "province": "KwaZulu-Natal","type": "District",     "lat": -28.7831, "lon": 32.0382},
    {"name": "Ugu",                     "province": "KwaZulu-Natal","type": "District",     "lat": -30.3333, "lon": 30.3333},
    {"name": "uMgungundlovu",           "province": "KwaZulu-Natal","type": "District",     "lat": -29.6006, "lon": 30.3794},
    {"name": "uMkhanyakude",            "province": "KwaZulu-Natal","type": "District",     "lat": -27.5000, "lon": 32.0000},
    {"name": "uMzinyathi",              "province": "KwaZulu-Natal","type": "District",     "lat": -28.5000, "lon": 30.5000},
    {"name": "uThukela",                "province": "KwaZulu-Natal","type": "District",     "lat": -28.5595, "lon": 29.7814},
    {"name": "Zululand",                "province": "KwaZulu-Natal","type": "District",     "lat": -28.0000, "lon": 31.0000},
    {"name": "AbaQulusi",               "province": "KwaZulu-Natal","type": "Local",        "lat": -27.7667, "lon": 30.8000},
    {"name": "Alfred Duma",             "province": "KwaZulu-Natal","type": "Local",        "lat": -28.5000, "lon": 29.5000},
    {"name": "Big 5 Hlabisa",           "province": "KwaZulu-Natal","type": "Local",        "lat": -27.8667, "lon": 32.0000},
    {"name": "Dannhauser",              "province": "KwaZulu-Natal","type": "Local",        "lat": -28.0000, "lon": 30.0000},
    {"name": "Dr Nkosazana Dlamini-Zuma","province": "KwaZulu-Natal","type": "Local",       "lat": -30.0000, "lon": 29.5000},
    {"name": "eDumbe",                  "province": "KwaZulu-Natal","type": "Local",        "lat": -27.5000, "lon": 30.5000},
    {"name": "eMadlangeni",             "province": "KwaZulu-Natal","type": "Local",        "lat": -27.5000, "lon": 30.5000},
    {"name": "Endumeni",                "province": "KwaZulu-Natal","type": "Local",        "lat": -28.1167, "lon": 30.2000},
    {"name": "Greater Kokstad",         "province": "KwaZulu-Natal","type": "Local",        "lat": -30.5500, "lon": 29.4167},
    {"name": "Impendle",                "province": "KwaZulu-Natal","type": "Local",        "lat": -29.6000, "lon": 29.8667},
    {"name": "Inkosi Langalibalele",    "province": "KwaZulu-Natal","type": "Local",        "lat": -28.5000, "lon": 29.5000},
    {"name": "Jozini",                  "province": "KwaZulu-Natal","type": "Local",        "lat": -27.4333, "lon": 32.0667},
    {"name": "KwaDukuza",               "province": "KwaZulu-Natal","type": "Local",        "lat": -29.3333, "lon": 31.2500},
    {"name": "Mandeni",                 "province": "KwaZulu-Natal","type": "Local",        "lat": -29.1500, "lon": 31.4167},
    {"name": "Maphumulo",               "province": "KwaZulu-Natal","type": "Local",        "lat": -29.4167, "lon": 30.5000},
    {"name": "Mkhambathini",            "province": "KwaZulu-Natal","type": "Local",        "lat": -29.6667, "lon": 30.4167},
    {"name": "Mpofana",                 "province": "KwaZulu-Natal","type": "Local",        "lat": -29.0667, "lon": 29.9167},
    {"name": "Msunduzi",                "province": "KwaZulu-Natal","type": "Local",        "lat": -29.6006, "lon": 30.3794},
    {"name": "Mthonjaneni",             "province": "KwaZulu-Natal","type": "Local",        "lat": -28.6833, "lon": 31.3500},
    {"name": "Mtubatuba",               "province": "KwaZulu-Natal","type": "Local",        "lat": -28.4167, "lon": 32.1833},
    {"name": "Ndwedwe",                 "province": "KwaZulu-Natal","type": "Local",        "lat": -29.5167, "lon": 30.9333},
    {"name": "Newcastle",               "province": "KwaZulu-Natal","type": "Local",        "lat": -27.7559, "lon": 29.9318},
    {"name": "Nkandla",                 "province": "KwaZulu-Natal","type": "Local",        "lat": -28.6167, "lon": 31.1000},
    {"name": "Nongoma",                 "province": "KwaZulu-Natal","type": "Local",        "lat": -27.8833, "lon": 31.6500},
    {"name": "Nquthu",                  "province": "KwaZulu-Natal","type": "Local",        "lat": -27.7667, "lon": 30.4667},
    {"name": "Okhahlamba",              "province": "KwaZulu-Natal","type": "Local",        "lat": -28.7000, "lon": 29.4000},
    {"name": "Ray Nkonyeni",            "province": "KwaZulu-Natal","type": "Local",        "lat": -30.5000, "lon": 30.0000},
    {"name": "Richmond",                "province": "KwaZulu-Natal","type": "Local",        "lat": -29.8667, "lon": 30.2667},
    {"name": "Ubuhlebezwe",             "province": "KwaZulu-Natal","type": "Local",        "lat": -30.0000, "lon": 29.5000},
    {"name": "Umdoni",                  "province": "KwaZulu-Natal","type": "Local",        "lat": -30.3333, "lon": 30.5000},
    {"name": "uMfolozi",                "province": "KwaZulu-Natal","type": "Local",        "lat": -28.0000, "lon": 32.0000},
    {"name": "Umhlabuyalingana",        "province": "KwaZulu-Natal","type": "Local",        "lat": -27.0000, "lon": 32.0000},
    {"name": "uMlalazi",                "province": "KwaZulu-Natal","type": "Local",        "lat": -28.7000, "lon": 31.8000},
    {"name": "uMngeni",                 "province": "KwaZulu-Natal","type": "Local",        "lat": -29.4667, "lon": 30.2167},
    {"name": "uMshwathi",               "province": "KwaZulu-Natal","type": "Local",        "lat": -29.4167, "lon": 30.3333},
    {"name": "uMsinga",                 "province": "KwaZulu-Natal","type": "Local",        "lat": -28.6000, "lon": 30.1667},
    {"name": "Umuziwabantu",            "province": "KwaZulu-Natal","type": "Local",        "lat": -30.1667, "lon": 30.0000},
    {"name": "Umvoti",                  "province": "KwaZulu-Natal","type": "Local",        "lat": -29.0833, "lon": 30.6667},
    {"name": "Umzimkhulu",              "province": "KwaZulu-Natal","type": "Local",        "lat": -30.2000, "lon": 29.5000},
    {"name": "Umzumbe",                 "province": "KwaZulu-Natal","type": "Local",        "lat": -30.4000, "lon": 30.4000},
    {"name": "uPhongolo",               "province": "KwaZulu-Natal","type": "Local",        "lat": -27.4167, "lon": 31.6667},
    {"name": "Ulundi",                  "province": "KwaZulu-Natal","type": "Local",        "lat": -28.3167, "lon": 31.4167},
    {"name": "uMhlathuze",              "province": "KwaZulu-Natal","type": "Local",        "lat": -28.7831, "lon": 32.0382},

    # ==================== LIMPOPO (26) ====================
    {"name": "Capricorn",               "province": "Limpopo",      "type": "District",     "lat": -23.9045, "lon": 29.4689},
    {"name": "Mopani",                  "province": "Limpopo",      "type": "District",     "lat": -23.6667, "lon": 30.3333},
    {"name": "Sekhukhune",              "province": "Limpopo",      "type": "District",     "lat": -24.5000, "lon": 29.5000},
    {"name": "Vhembe",                  "province": "Limpopo",      "type": "District",     "lat": -22.9561, "lon": 30.4794},
    {"name": "Waterberg",               "province": "Limpopo",      "type": "District",     "lat": -24.0000, "lon": 28.0000},
    {"name": "Ba-Phalaborwa",           "province": "Limpopo",      "type": "Local",        "lat": -23.9500, "lon": 31.1500},
    {"name": "Bela-Bela",               "province": "Limpopo",      "type": "Local",        "lat": -24.8833, "lon": 28.2833},
    {"name": "Blouberg",                "province": "Limpopo",      "type": "Local",        "lat": -23.0333, "lon": 29.0000},
    {"name": "Elias Motsoaledi",        "province": "Limpopo",      "type": "Local",        "lat": -25.0000, "lon": 29.0000},
    {"name": "Ephraim Mogale",          "province": "Limpopo",      "type": "Local",        "lat": -25.0000, "lon": 30.0000},
    {"name": "Fetakgomo Tubatse",       "province": "Limpopo",      "type": "Local",        "lat": -24.5000, "lon": 29.5000},
    {"name": "Greater Giyani",          "province": "Limpopo",      "type": "Local",        "lat": -23.3167, "lon": 30.7000},
    {"name": "Greater Letaba",          "province": "Limpopo",      "type": "Local",        "lat": -23.5000, "lon": 30.5000},
    {"name": "Greater Tzaneen",         "province": "Limpopo",      "type": "Local",        "lat": -23.8305, "lon": 30.1644},
    {"name": "Lepelle-Nkumpi",          "province": "Limpopo",      "type": "Local",        "lat": -24.1667, "lon": 29.5000},
    {"name": "Lephalale",               "province": "Limpopo",      "type": "Local",        "lat": -23.6667, "lon": 27.7500},
    {"name": "Makhado",                 "province": "Limpopo",      "type": "Local",        "lat": -23.0000, "lon": 30.0000},
    {"name": "Makhuduthamaga",          "province": "Limpopo",      "type": "Local",        "lat": -24.5000, "lon": 29.5000},
    {"name": "Maruleng",                "province": "Limpopo",      "type": "Local",        "lat": -24.3333, "lon": 30.5000},
    {"name": "Modimolle-Mookgophong",   "province": "Limpopo",      "type": "Local",        "lat": -24.7000, "lon": 28.4000},
    {"name": "Mogalakwena",             "province": "Limpopo",      "type": "Local",        "lat": -23.5000, "lon": 28.5000},
    {"name": "Molemole",                "province": "Limpopo",      "type": "Local",        "lat": -23.5000, "lon": 29.0000},
    {"name": "Musina",                  "province": "Limpopo",      "type": "Local",        "lat": -22.3500, "lon": 30.0333},
    {"name": "Polokwane",               "province": "Limpopo",      "type": "Local",        "lat": -23.9045, "lon": 29.4689},
    {"name": "Thabazimbi",              "province": "Limpopo",      "type": "Local",        "lat": -24.6000, "lon": 27.4000},
    {"name": "Thulamela",               "province": "Limpopo",      "type": "Local",        "lat": -22.9561, "lon": 30.4794},

    # ==================== MPUMALANGA (20) ====================
    {"name": "Ehlanzeni",               "province": "Mpumalanga",   "type": "District",     "lat": -25.4653, "lon": 30.9856},
    {"name": "Gert Sibande",            "province": "Mpumalanga",   "type": "District",     "lat": -26.5000, "lon": 29.0000},
    {"name": "Nkangala",                "province": "Mpumalanga",   "type": "District",     "lat": -25.8744, "lon": 29.2403},
    {"name": "Bushbuckridge",           "province": "Mpumalanga",   "type": "Local",        "lat": -24.8333, "lon": 31.0833},
    {"name": "Chief Albert Luthuli",    "province": "Mpumalanga",   "type": "Local",        "lat": -26.5000, "lon": 29.0000},
    {"name": "City of Mbombela",        "province": "Mpumalanga",   "type": "Local",        "lat": -25.4653, "lon": 30.9856},
    {"name": "Dipaleseng",              "province": "Mpumalanga",   "type": "Local",        "lat": -26.5000, "lon": 28.5000},
    {"name": "Dr JS Moroka",            "province": "Mpumalanga",   "type": "Local",        "lat": -25.5000, "lon": 28.5000},
    {"name": "Emakhazeni",              "province": "Mpumalanga",   "type": "Local",        "lat": -25.5000, "lon": 30.5000},
    {"name": "Emalahleni",              "province": "Mpumalanga",   "type": "Local",        "lat": -25.8744, "lon": 29.2403},
    {"name": "Govan Mbeki",             "province": "Mpumalanga",   "type": "Local",        "lat": -26.5000, "lon": 29.0000},
    {"name": "Lekwa",                   "province": "Mpumalanga",   "type": "Local",        "lat": -26.8000, "lon": 29.0000},
    {"name": "Mkhondo",                 "province": "Mpumalanga",   "type": "Local",        "lat": -27.0000, "lon": 30.5000},
    {"name": "Msukaligwa",              "province": "Mpumalanga",   "type": "Local",        "lat": -26.5000, "lon": 29.5000},
    {"name": "Nkomazi",                 "province": "Mpumalanga",   "type": "Local",        "lat": -25.5000, "lon": 31.5000},
    {"name": "Pixley ka Seme",          "province": "Mpumalanga",   "type": "Local",        "lat": -27.0000, "lon": 28.5000},
    {"name": "Steve Tshwete",           "province": "Mpumalanga",   "type": "Local",        "lat": -25.5000, "lon": 29.5000},
    {"name": "Thaba Chweu",             "province": "Mpumalanga",   "type": "Local",        "lat": -25.0000, "lon": 30.5000},
    {"name": "Thembisile Hani",         "province": "Mpumalanga",   "type": "Local",        "lat": -25.5000, "lon": 28.5000},
    {"name": "Victor Khanye",           "province": "Mpumalanga",   "type": "Local",        "lat": -26.0000, "lon": 28.5000},

    # ==================== NORTH WEST (21) ====================
    {"name": "Bojanala Platinum",       "province": "North West",   "type": "District",     "lat": -25.6672, "lon": 27.2423},
    {"name": "Dr Kenneth Kaunda",       "province": "North West",   "type": "District",     "lat": -26.8676, "lon": 26.6517},
    {"name": "Dr Ruth Segomotsi Mompati","province": "North West",  "type": "District",     "lat": -26.0000, "lon": 24.0000},
    {"name": "Ngaka Modiri Molema",     "province": "North West",   "type": "District",     "lat": -25.8503, "lon": 25.6442},
    {"name": "City of Matlosana",       "province": "North West",   "type": "Local",        "lat": -26.8676, "lon": 26.6517},
    {"name": "Ditsobotla",              "province": "North West",   "type": "Local",        "lat": -26.0000, "lon": 25.5000},
    {"name": "Greater Taung",           "province": "North West",   "type": "Local",        "lat": -27.5000, "lon": 24.5000},
    {"name": "Kagisano-Molopo",         "province": "North West",   "type": "Local",        "lat": -26.0000, "lon": 24.0000},
    {"name": "Kgetlengrivier",          "province": "North West",   "type": "Local",        "lat": -26.0000, "lon": 27.0000},
    {"name": "Lekwa-Teemane",           "province": "North West",   "type": "Local",        "lat": -27.0000, "lon": 25.0000},
    {"name": "Madibeng",                "province": "North West",   "type": "Local",        "lat": -25.5000, "lon": 27.5000},
    {"name": "Mahikeng",                "province": "North West",   "type": "Local",        "lat": -25.8503, "lon": 25.6442},
    {"name": "Mamusa",                  "province": "North West",   "type": "Local",        "lat": -27.0000, "lon": 24.5000},
    {"name": "Maquassi Hills",          "province": "North West",   "type": "Local",        "lat": -27.0000, "lon": 26.0000},
    {"name": "Moretele",                "province": "North West",   "type": "Local",        "lat": -25.5000, "lon": 28.0000},
    {"name": "Moses Kotane",            "province": "North West",   "type": "Local",        "lat": -25.5000, "lon": 27.0000},
    {"name": "Naledi",                  "province": "North West",   "type": "Local",        "lat": -26.0000, "lon": 24.5000},
    {"name": "Ramotshere Moiloa",       "province": "North West",   "type": "Local",        "lat": -25.5000, "lon": 26.0000},
    {"name": "Ratlou",                  "province": "North West",   "type": "Local",        "lat": -25.5000, "lon": 25.5000},
    {"name": "Rustenburg",              "province": "North West",   "type": "Local",        "lat": -25.6672, "lon": 27.2423},
    {"name": "Tswaing",                 "province": "North West",   "type": "Local",        "lat": -27.0000, "lon": 25.5000},

    # ==================== NORTHERN CAPE (31) ====================
    {"name": "Frances Baard",           "province": "Northern Cape","type": "District",     "lat": -28.7282, "lon": 24.7499},
    {"name": "John Taolo Gaetsewe",     "province": "Northern Cape","type": "District",     "lat": -27.5000, "lon": 24.0000},
    {"name": "Namakwa",                 "province": "Northern Cape","type": "District",     "lat": -29.6639, "lon": 17.8864},
    {"name": "Pixley ka Seme NC",       "province": "Northern Cape","type": "District",     "lat": -30.0000, "lon": 24.0000},
    {"name": "ZF Mgcawu",               "province": "Northern Cape","type": "District",     "lat": -28.4478, "lon": 21.2561},
    {"name": "Kheis",                   "province": "Northern Cape","type": "Local",        "lat": -29.0000, "lon": 21.0000},
    {"name": "Dawid Kruiper",           "province": "Northern Cape","type": "Local",        "lat": -28.4478, "lon": 21.2561},
    {"name": "Dikgatlong",              "province": "Northern Cape","type": "Local",        "lat": -28.5000, "lon": 24.5000},
    {"name": "Emthanjeni",              "province": "Northern Cape","type": "Local",        "lat": -30.5000, "lon": 24.0000},
    {"name": "Gamagara",                "province": "Northern Cape","type": "Local",        "lat": -27.5000, "lon": 24.0000},
    {"name": "Ga-Segonyana",            "province": "Northern Cape","type": "Local",        "lat": -27.5000, "lon": 24.0000},
    {"name": "Hantam",                  "province": "Northern Cape","type": "Local",        "lat": -31.0000, "lon": 20.0000},
    {"name": "Joe Morolong",            "province": "Northern Cape","type": "Local",        "lat": -27.5000, "lon": 24.0000},
    {"name": "Kai Garib",               "province": "Northern Cape","type": "Local",        "lat": -28.5000, "lon": 21.0000},
    {"name": "Kamiesberg",              "province": "Northern Cape","type": "Local",        "lat": -30.0000, "lon": 18.0000},
    {"name": "Kareeberg",               "province": "Northern Cape","type": "Local",        "lat": -30.5000, "lon": 22.0000},
    {"name": "Karoo Hoogland",          "province": "Northern Cape","type": "Local",        "lat": -31.0000, "lon": 20.0000},
    {"name": "Kgatelopele",             "province": "Northern Cape","type": "Local",        "lat": -28.5000, "lon": 24.0000},
    {"name": "Khai-Ma",                 "province": "Northern Cape","type": "Local",        "lat": -29.5000, "lon": 19.0000},
    {"name": "Magareng",                "province": "Northern Cape","type": "Local",        "lat": -28.5000, "lon": 24.5000},
    {"name": "Nama Khoi",               "province": "Northern Cape","type": "Local",        "lat": -29.5000, "lon": 18.0000},
    {"name": "Phokwane",                "province": "Northern Cape","type": "Local",        "lat": -28.0000, "lon": 24.5000},
    {"name": "Renosterberg",            "province": "Northern Cape","type": "Local",        "lat": -30.0000, "lon": 25.0000},
    {"name": "Richtersveld",            "province": "Northern Cape","type": "Local",        "lat": -28.5000, "lon": 17.0000},
    {"name": "Siyancuma",               "province": "Northern Cape","type": "Local",        "lat": -29.0000, "lon": 23.0000},
    {"name": "Siyathemba",              "province": "Northern Cape","type": "Local",        "lat": -29.5000, "lon": 24.0000},
    {"name": "Sol Plaatje",             "province": "Northern Cape","type": "Local",        "lat": -28.7282, "lon": 24.7499},
    {"name": "Thembelihle",             "province": "Northern Cape","type": "Local",        "lat": -29.5000, "lon": 25.0000},
    {"name": "Tsantsabane",             "province": "Northern Cape","type": "Local",        "lat": -28.0000, "lon": 24.0000},
    {"name": "Ubuntu",                  "province": "Northern Cape","type": "Local",        "lat": -31.0000, "lon": 23.0000},
    {"name": "Umsobomvu",               "province": "Northern Cape","type": "Local",        "lat": -30.5000, "lon": 25.0000},

    # ==================== WESTERN CAPE (30) ====================
    {"name": "City of Cape Town",       "province": "Western Cape", "type": "Metropolitan", "lat": -33.9249, "lon": 18.4241},
    {"name": "Cape Winelands",          "province": "Western Cape", "type": "District",     "lat": -33.7249, "lon": 18.9560},
    {"name": "Central Karoo",           "province": "Western Cape", "type": "District",     "lat": -33.0000, "lon": 22.0000},
    {"name": "Garden Route",            "province": "Western Cape", "type": "District",     "lat": -33.9646, "lon": 22.4617},
    {"name": "Overberg",                "province": "Western Cape", "type": "District",     "lat": -34.4187, "lon": 19.2345},
    {"name": "West Coast",              "province": "Western Cape", "type": "District",     "lat": -33.0000, "lon": 18.0000},
    {"name": "Beaufort West",           "province": "Western Cape", "type": "Local",        "lat": -32.3500, "lon": 22.5833},
    {"name": "Bergrivier",              "province": "Western Cape", "type": "Local",        "lat": -32.5000, "lon": 18.5000},
    {"name": "Bitou",                   "province": "Western Cape", "type": "Local",        "lat": -34.0357, "lon": 23.0487},
    {"name": "Breede Valley",           "province": "Western Cape", "type": "Local",        "lat": -33.5000, "lon": 19.5000},
    {"name": "Cape Agulhas",            "province": "Western Cape", "type": "Local",        "lat": -34.8333, "lon": 20.0000},
    {"name": "Cederberg",               "province": "Western Cape", "type": "Local",        "lat": -32.5000, "lon": 19.0000},
    {"name": "Drakenstein",             "province": "Western Cape", "type": "Local",        "lat": -33.5000, "lon": 19.0000},
    {"name": "George",                  "province": "Western Cape", "type": "Local",        "lat": -33.9646, "lon": 22.4617},
    {"name": "Hessequa",                "province": "Western Cape", "type": "Local",        "lat": -34.0000, "lon": 21.0000},
    {"name": "Kannaland",               "province": "Western Cape", "type": "Local",        "lat": -33.5000, "lon": 21.5000},
    {"name": "Knysna",                  "province": "Western Cape", "type": "Local",        "lat": -34.0357, "lon": 23.0487},
    {"name": "Laingsburg",              "province": "Western Cape", "type": "Local",        "lat": -33.2000, "lon": 20.8667},
    {"name": "Langeberg",               "province": "Western Cape", "type": "Local",        "lat": -33.5000, "lon": 20.0000},
    {"name": "Matzikama",               "province": "Western Cape", "type": "Local",        "lat": -31.5000, "lon": 18.5000},
    {"name": "Mossel Bay",              "province": "Western Cape", "type": "Local",        "lat": -34.1833, "lon": 22.1333},
    {"name": "Oudtshoorn",              "province": "Western Cape", "type": "Local",        "lat": -33.5833, "lon": 22.2000},
    {"name": "Overstrand",              "province": "Western Cape", "type": "Local",        "lat": -34.4187, "lon": 19.2345},
    {"name": "Prince Albert",           "province": "Western Cape", "type": "Local",        "lat": -33.2333, "lon": 22.0333},
    {"name": "Saldanha Bay",            "province": "Western Cape", "type": "Local",        "lat": -33.0000, "lon": 18.0000},
    {"name": "Stellenbosch",            "province": "Western Cape", "type": "Local",        "lat": -33.9321, "lon": 18.8602},
    {"name": "Swartland",               "province": "Western Cape", "type": "Local",        "lat": -33.5000, "lon": 18.5000},
    {"name": "Swellendam",              "province": "Western Cape", "type": "Local",        "lat": -34.0333, "lon": 20.4333},
    {"name": "Theewaterskloof",         "province": "Western Cape", "type": "Local",        "lat": -34.0000, "lon": 19.5000},
    {"name": "Witzenberg",              "province": "Western Cape", "type": "Local",        "lat": -33.5000, "lon": 19.5000},
]


# ============================================================
# FETCH WEATHER FOR A SINGLE MUNICIPALITY
# ============================================================
def fetch_weather(municipality: dict, retries: int = 3) -> Optional[dict]:
    url = API_BASE_URL
    params = {
        "latitude":  municipality["lat"],
        "longitude": municipality["lon"],
        "hourly": [
            "temperature_2m",
            "precipitation",
            "windspeed_10m",
            "relativehumidity_2m",
            "cloudcover",
            "visibility",
            "uv_index",
            "surface_pressure",
        ],
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "windspeed_10m_max",
            "sunrise",
            "sunset",
            "daylight_duration",
            "weathercode",
        ],
        "timezone":      TIMEZONE,
        "forecast_days": FORECAST_DAYS,
    }

    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            return {
                "municipality": municipality["name"],
                "province":     municipality["province"],
                "type":         municipality["type"],
                "lat":          municipality["lat"],
                "lon":          municipality["lon"],
                "fetched_at":   datetime.now().isoformat(),
                "data":         response.json(),
            }
        except requests.exceptions.Timeout:
            log.warning(f"Timeout on attempt {attempt}/{retries} for {municipality['name']} — retrying...")
            time.sleep(2 ** attempt)
        except requests.exceptions.RequestException as e:
            log.error(f"Error on attempt {attempt}/{retries} for {municipality['name']}: {e}")
            time.sleep(2)

    log.error(f"FAILED after {retries} attempts — skipping {municipality['name']}")
    return None


# ============================================================
# SAVE ALL RECORDS TO JSON
# ============================================================
def save_to_json(records: list) -> str:
    output_dir = Path(DATA_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    filename  = f"weather_municipalities_{datetime.now().strftime('%Y-%m-%d')}.json"
    filepath  = output_dir / filename
    with open(filepath, "w") as f:
        json.dump(records, f, indent=2)
    log.info(f"Saved {len(records)} municipality records to {filepath}")
    return str(filepath)


# ============================================================
# SUMMARY
# ============================================================
def print_summary(records: list, total: int) -> None:
    successful = len(records)
    type_counts     = {}
    province_counts = {}
    for r in records:
        type_counts[r["type"]]         = type_counts.get(r["type"], 0) + 1
        province_counts[r["province"]] = province_counts.get(r["province"], 0) + 1

    log.info("=" * 60)
    log.info("EXTRACTION SUMMARY")
    log.info(f"Total:      {total}")
    log.info(f"Success:    {successful}")
    log.info(f"Failed:     {total - successful}")
    log.info(f"Rate:       {successful/total*100:.1f}%")
    log.info("--- By Type ---")
    for k, v in sorted(type_counts.items()):
        log.info(f"  {k}: {v}")
    log.info("--- By Province ---")
    for k, v in sorted(province_counts.items()):
        log.info(f"  {k}: {v}")
    log.info("=" * 60)


# ============================================================
# MAIN — called by Airflow DAG or directly
# ============================================================
def extract_all_municipalities(sample_size: Optional[int] = None) -> str:
    targets = MUNICIPALITIES[:sample_size] if sample_size else MUNICIPALITIES
    log.info(f"Starting extraction — {len(targets)} municipalities")

    records = []
    failed  = []

    for idx, municipality in enumerate(targets, 1):
        log.info(f"[{idx}/{len(targets)}] {municipality['name']} ({municipality['province']}, {municipality['type']})")
        record = fetch_weather(municipality)
        if record:
            records.append(record)
            log.info(f"  Done — {len(record['data']['hourly']['time'])} hourly readings")
        else:
            failed.append(municipality["name"])

        if idx < len(targets):
            time.sleep(0.5)

    print_summary(records, len(targets))

    if failed:
        log.warning(f"Skipped: {', '.join(failed)}")

    return save_to_json(records)

# ============================================================
# HISTORICAL BACKFILL
# Hits the Open-Meteo archive API
# Goes back as far as you want — we default to 90 days
# ============================================================

def fetch_historical_weather(municipality: dict, start_date: str, end_date: str, retries: int = 3) -> Optional[dict]:
    """
    Fetch historical weather data for a single municipality.
    Uses the Open-Meteo archive API instead of forecast API.

    Args:
        municipality: Dictionary with name, province, type, lat, lon
        start_date:   YYYY-MM-DD format
        end_date:     YYYY-MM-DD format
        retries:      Number of retry attempts on failure

    Returns:
        Dictionary with historical weather data or None if failed
    """
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude":   municipality["lat"],
        "longitude":  municipality["lon"],
        "start_date": start_date,
        "end_date":   end_date,
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "windspeed_10m_max",
            "sunrise",
            "sunset",
            "daylight_duration",
            "weathercode",
        ],
        "hourly": [
            "temperature_2m",
            "precipitation",
            "windspeed_10m",
            "relativehumidity_2m",
            "cloudcover",
            "visibility",
            "uv_index",
            "surface_pressure",
        ],
        "timezone": TIMEZONE,
    }

    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, params=params, timeout=60)
            response.raise_for_status()
            return {
                "municipality": municipality["name"],
                "province":     municipality["province"],
                "type":         municipality["type"],
                "lat":          municipality["lat"],
                "lon":          municipality["lon"],
                "fetched_at":   datetime.now().isoformat(),
                "start_date":   start_date,
                "end_date":     end_date,
                "data":         response.json(),
            }
        except requests.exceptions.Timeout:
            log.warning(f"Timeout on attempt {attempt}/{retries} for {municipality['name']} — retrying...")
            time.sleep(2 ** attempt)
        except requests.exceptions.RequestException as e:
            log.error(f"Error on attempt {attempt}/{retries} for {municipality['name']}: {e}")
            time.sleep(2)

    log.error(f"FAILED after {retries} attempts — skipping {municipality['name']}")
    return None


def save_historical_to_json(records: list, start_date: str, end_date: str) -> str:
    """
    Save historical records to a JSON file.
    """
    output_dir = Path(DATA_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"weather_historical_{start_date}_to_{end_date}.json"
    filepath = output_dir / filename
    with open(filepath, "w") as f:
        json.dump(records, f, indent=2)
    log.info(f"Saved {len(records)} municipality records to {filepath}")
    return str(filepath)


def backfill_historical(days: int = 90, sample_size: Optional[int] = None) -> str:
    """
    Fetch historical weather data for all municipalities.
    Called once on first pipeline run to seed the warehouse with history.

    Args:
        days:        How many days back to fetch (default 90)
        sample_size: If provided, only fetch this many municipalities (for testing)

    Returns:
        Path to the saved JSON file
    """
    end_date   = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    targets = MUNICIPALITIES[:sample_size] if sample_size else MUNICIPALITIES
    log.info(f"Starting backfill — {len(targets)} municipalities — {start_date} to {end_date}")

    records = []
    failed  = []

    for idx, municipality in enumerate(targets, 1):
        log.info(f"[{idx}/{len(targets)}] {municipality['name']} ({municipality['province']}, {municipality['type']})")
        record = fetch_historical_weather(municipality, start_date, end_date)
        if record:
            records.append(record)
            daily_count  = len(record["data"]["daily"]["time"])
            hourly_count = len(record["data"]["hourly"]["time"])
            log.info(f"  Done — {daily_count} daily readings, {hourly_count} hourly readings")
        else:
            failed.append(municipality["name"])

        if idx < len(targets):
            time.sleep(0.5)

    print_summary(records, len(targets))

    if failed:
        log.warning(f"Skipped: {', '.join(failed)}")

    return save_historical_to_json(records, start_date, end_date)

# ============================================================
# ENTRY POINT — local testing only
# ============================================================
if __name__ == "__main__":
    sample_mode = "--sample" in sys.argv
    path = extract_all_municipalities(sample_size=10 if sample_mode else None)
    log.info(f"Output: {path}")