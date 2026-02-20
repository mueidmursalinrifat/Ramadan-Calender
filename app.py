# app.py
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests
from datetime import datetime, date, timedelta
from functools import wraps
import json
import logging
import os
from cachetools import TTLCache
from typing import Dict, Any, Optional, List
import math
import random

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)  # Enable CORS for all routes

# Cache configuration (1 hour TTL) - Note: This will reset per invocation on Vercel
cache = TTLCache(maxsize=200, ttl=3600)

# Constants
BASE_URL = "https://services.deenislamic.com/api/SeheriIftarTime"
HEADERS = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "en-US",
    "client": "3",
    "content-type": "application/json",
    "Referer": "https://deenislamic.com/"
}

# All 64 districts of Bangladesh with coordinates
BANGLADESH_DISTRICTS = [
    {"id": "dhaka", "name": "ঢাকা", "name_en": "Dhaka", "lat": 23.8103, "lon": 90.4125, "division": "ঢাকা"},
    {"id": "faridpur", "name": "ফরিদপুর", "name_en": "Faridpur", "lat": 23.6071, "lon": 89.8422, "division": "ঢাকা"},
    {"id": "gazipur", "name": "গাজীপুর", "name_en": "Gazipur", "lat": 23.9999, "lon": 90.4203, "division": "ঢাকা"},
    {"id": "gopalganj", "name": "গোপালগঞ্জ", "name_en": "Gopalganj", "lat": 23.0055, "lon": 89.8268, "division": "ঢাকা"},
    {"id": "kishoreganj", "name": "কিশোরগঞ্জ", "name_en": "Kishoreganj", "lat": 24.4447, "lon": 90.7761, "division": "ঢাকা"},
    {"id": "madaripur", "name": "মাদারীপুর", "name_en": "Madaripur", "lat": 23.1645, "lon": 90.1896, "division": "ঢাকা"},
    {"id": "manikganj", "name": "মানিকগঞ্জ", "name_en": "Manikganj", "lat": 23.8644, "lon": 90.0008, "division": "ঢাকা"},
    {"id": "munshiganj", "name": "মুন্সিগঞ্জ", "name_en": "Munshiganj", "lat": 23.5422, "lon": 90.5301, "division": "ঢাকা"},
    {"id": "narayanganj", "name": "নারায়ণগঞ্জ", "name_en": "Narayanganj", "lat": 23.6213, "lon": 90.4954, "division": "ঢাকা"},
    {"id": "narsingdi", "name": "নরসিংদী", "name_en": "Narsingdi", "lat": 23.9206, "lon": 90.7177, "division": "ঢাকা"},
    {"id": "rajbari", "name": "রাজবাড়ী", "name_en": "Rajbari", "lat": 23.7575, "lon": 89.6426, "division": "ঢাকা"},
    {"id": "shariatpur", "name": "শরীয়তপুর", "name_en": "Shariatpur", "lat": 23.2423, "lon": 90.3500, "division": "ঢাকা"},
    {"id": "tangail", "name": "টাঙ্গাইল", "name_en": "Tangail", "lat": 24.2513, "lon": 89.9167, "division": "ঢাকা"},
    
    {"id": "chittagong", "name": "চট্টগ্রাম", "name_en": "Chittagong", "lat": 22.3569, "lon": 91.7832, "division": "চট্টগ্রাম"},
    {"id": "bandarban", "name": "বান্দরবান", "name_en": "Bandarban", "lat": 22.1953, "lon": 92.2183, "division": "চট্টগ্রাম"},
    {"id": "brahmanbaria", "name": "ব্রাহ্মণবাড়িয়া", "name_en": "Brahmanbaria", "lat": 23.9608, "lon": 91.1115, "division": "চট্টগ্রাম"},
    {"id": "chandpur", "name": "চাঁদপুর", "name_en": "Chandpur", "lat": 23.2336, "lon": 90.6636, "division": "চট্টগ্রাম"},
    {"id": "comilla", "name": "কুমিল্লা", "name_en": "Comilla", "lat": 23.4683, "lon": 91.1787, "division": "চট্টগ্রাম"},
    {"id": "cox_bazar", "name": "কক্সবাজার", "name_en": "Cox's Bazar", "lat": 21.4272, "lon": 92.0058, "division": "চট্টগ্রাম"},
    {"id": "feni", "name": "ফেনী", "name_en": "Feni", "lat": 23.0158, "lon": 91.3975, "division": "চট্টগ্রাম"},
    {"id": "khagrachhari", "name": "খাগড়াছড়ি", "name_en": "Khagrachhari", "lat": 23.1071, "lon": 91.9697, "division": "চট্টগ্রাম"},
    {"id": "lakshmipur", "name": "লক্ষ্মীপুর", "name_en": "Lakshmipur", "lat": 22.9447, "lon": 90.8284, "division": "চট্টগ্রাম"},
    {"id": "noakhali", "name": "নোয়াখালী", "name_en": "Noakhali", "lat": 22.8696, "lon": 91.0997, "division": "চট্টগ্রাম"},
    {"id": "rangamati", "name": "রাঙ্গামাটি", "name_en": "Rangamati", "lat": 22.7324, "lon": 92.2985, "division": "চট্টগ্রাম"},
    
    {"id": "rajshahi", "name": "রাজশাহী", "name_en": "Rajshahi", "lat": 24.3636, "lon": 88.6241, "division": "রাজশাহী"},
    {"id": "bogra", "name": "বগুড়া", "name_en": "Bogra", "lat": 24.8465, "lon": 89.3772, "division": "রাজশাহী"},
    {"id": "joypurhat", "name": "জয়পুরহাট", "name_en": "Joypurhat", "lat": 25.0968, "lon": 89.0401, "division": "রাজশাহী"},
    {"id": "naogaon", "name": "নওগাঁ", "name_en": "Naogaon", "lat": 24.8091, "lon": 88.9445, "division": "রাজশাহী"},
    {"id": "natore", "name": "নাটোর", "name_en": "Natore", "lat": 24.4129, "lon": 89.0010, "division": "রাজশাহী"},
    {"id": "chapainawabganj", "name": "চাঁপাইনবাবগঞ্জ", "name_en": "Chapainawabganj", "lat": 24.5965, "lon": 88.2774, "division": "রাজশাহী"},
    {"id": "pabna", "name": "পাবনা", "name_en": "Pabna", "lat": 24.0064, "lon": 89.2372, "division": "রাজশাহী"},
    {"id": "sirajganj", "name": "সিরাজগঞ্জ", "name_en": "Sirajganj", "lat": 24.4535, "lon": 89.6167, "division": "রাজশাহী"},
    
    {"id": "khulna", "name": "খুলনা", "name_en": "Khulna", "lat": 22.8456, "lon": 89.5403, "division": "খুলনা"},
    {"id": "bagerhat", "name": "বাগেরহাট", "name_en": "Bagerhat", "lat": 22.6602, "lon": 89.7895, "division": "খুলনা"},
    {"id": "chuadanga", "name": "চুয়াডাঙ্গা", "name_en": "Chuadanga", "lat": 23.6401, "lon": 88.8557, "division": "খুলনা"},
    {"id": "jashore", "name": "যশোর", "name_en": "Jashore", "lat": 23.1749, "lon": 89.2038, "division": "খুলনা"},
    {"id": "jhenaidah", "name": "ঝিনাইদহ", "name_en": "Jhenaidah", "lat": 23.5528, "lon": 89.1573, "division": "খুলনা"},
    {"id": "kushtia", "name": "কুষ্টিয়া", "name_en": "Kushtia", "lat": 23.9017, "lon": 89.1212, "division": "খুলনা"},
    {"id": "magura", "name": "মাগুরা", "name_en": "Magura", "lat": 23.4873, "lon": 89.4199, "division": "খুলনা"},
    {"id": "meherpur", "name": "মেহেরপুর", "name_en": "Meherpur", "lat": 23.7792, "lon": 88.6473, "division": "খুলনা"},
    {"id": "narail", "name": "নড়াইল", "name_en": "Narail", "lat": 23.1639, "lon": 89.5041, "division": "খুলনা"},
    {"id": "shatkhira", "name": "সাতক্ষীরা", "name_en": "Satkhira", "lat": 22.7185, "lon": 89.0705, "division": "খুলনা"},
    
    {"id": "barisal", "name": "বরিশাল", "name_en": "Barisal", "lat": 22.7010, "lon": 90.3535, "division": "বরিশাল"},
    {"id": "barguna", "name": "বরগুনা", "name_en": "Barguna", "lat": 22.1591, "lon": 90.1241, "division": "বরিশাল"},
    {"id": "bhola", "name": "ভোলা", "name_en": "Bhola", "lat": 22.6884, "lon": 90.6485, "division": "বরিশাল"},
    {"id": "jhalokati", "name": "ঝালকাঠি", "name_en": "Jhalokati", "lat": 22.6425, "lon": 90.2002, "division": "বরিশাল"},
    {"id": "patuakhali", "name": "পটুয়াখালী", "name_en": "Patuakhali", "lat": 22.3596, "lon": 90.3290, "division": "বরিশাল"},
    {"id": "pirojpur", "name": "পিরোজপুর", "name_en": "Pirojpur", "lat": 22.5841, "lon": 89.9720, "division": "বরিশাল"},
    
    {"id": "sylhet", "name": "সিলেট", "name_en": "Sylhet", "lat": 24.8949, "lon": 91.8687, "division": "সিলেট"},
    {"id": "habiganj", "name": "হবিগঞ্জ", "name_en": "Habiganj", "lat": 24.3749, "lon": 91.4156, "division": "সিলেট"},
    {"id": "moulvibazar", "name": "মৌলভীবাজার", "name_en": "Moulvibazar", "lat": 24.4820, "lon": 91.7774, "division": "সিলেট"},
    {"id": "sunamganj", "name": "সুনামগঞ্জ", "name_en": "Sunamganj", "lat": 25.0715, "lon": 91.3992, "division": "সিলেট"},
    
    {"id": "rangpur", "name": "রংপুর", "name_en": "Rangpur", "lat": 25.7439, "lon": 89.2752, "division": "রংপুর"},
    {"id": "dinajpur", "name": "দিনাজপুর", "name_en": "Dinajpur", "lat": 25.6279, "lon": 88.6332, "division": "রংপুর"},
    {"id": "gaibandha", "name": "গাইবান্ধা", "name_en": "Gaibandha", "lat": 25.3295, "lon": 89.5425, "division": "রংপুর"},
    {"id": "kurigram", "name": "কুড়িগ্রাম", "name_en": "Kurigram", "lat": 25.8072, "lon": 89.6296, "division": "রংপুর"},
    {"id": "lalmonirhat", "name": "লালমনিরহাট", "name_en": "Lalmonirhat", "lat": 25.9172, "lon": 89.4459, "division": "রংপুর"},
    {"id": "nilphamari", "name": "নীলফামারী", "name_en": "Nilphamari", "lat": 25.9312, "lon": 88.8565, "division": "রংপুর"},
    {"id": "panchagarh", "name": "পঞ্চগড়", "name_en": "Panchagarh", "lat": 26.3411, "lon": 88.5545, "division": "রংপুর"},
    {"id": "thakurgaon", "name": "ঠাকুরগাঁও", "name_en": "Thakurgaon", "lat": 26.0336, "lon": 88.4676, "division": "রংপুর"},
    
    {"id": "mymensingh", "name": "ময়মনসিংহ", "name_en": "Mymensingh", "lat": 24.7471, "lon": 90.4203, "division": "ময়মনসিংহ"},
    {"id": "jamalpur", "name": "জামালপুর", "name_en": "Jamalpur", "lat": 24.9375, "lon": 89.9372, "division": "ময়মনসিংহ"},
    {"id": "netrokona", "name": "নেত্রকোণা", "name_en": "Netrokona", "lat": 24.8831, "lon": 90.7275, "division": "ময়মনসিংহ"},
    {"id": "sherpur", "name": "শেরপুর", "name_en": "Sherpur", "lat": 25.0205, "lon": 90.0175, "division": "ময়মনসিংহ"}
]

# Collection of Ramadan Duas for API response (optional)
RAMADAN_DUAS = [
    {
        "arabic": "اللَّهُمَّ إِنِّي أَسْأَلُكَ بِرَحْمَتِكَ الَّتِي وَسِعَتْ كُلَّ شَيْءٍ أَنْ تَغْفِرَ لِي",
        "bangla": "হে আল্লাহ! আপনার রহমতের উসিলায় যা সব কিছুকে পরিব্যাপ্ত করে, আমি আপনার কাছে ক্ষমা প্রার্থনা করছি।",
        "english": "O Allah, I ask You by Your mercy which encompasses all things, that You forgive me.",
        "reference": "দোয়া ইফতার"
    },
    {
        "arabic": "اللَّهُمَّ لَكَ صُمْتُ وَعَلَى رِزْقِكَ أَفْطَرْتُ",
        "bangla": "হে আল্লাহ! আমি আপনার জন্য রোজা রেখেছি এবং আপনার দেওয়া রিযিক দিয়ে ইফতার করছি।",
        "english": "O Allah, I fasted for You and I break my fast with Your provision.",
        "reference": "আবু দাউদ"
    },
    {
        "arabic": "ذَهَبَ الظَّمَأُ وَابْتَلَّتِ الْعُرُوقُ وَثَبَتَ الأَجْرُ إِنْ شَاءَ اللَّهُ",
        "bangla": "পিপাসা চলে গেল, শিরা-উপশিরা সিক্ত হল এবং সওয়াব স্থির হল, ইনশাআল্লাহ।",
        "english": "Thirst has gone, the veins are moist, and the reward is confirmed, if Allah wills.",
        "reference": "আবু দাউদ"
    },
    {
        "arabic": "اللَّهُمَّ إِنِّي أَسْأَلُكَ الْجَنَّةَ وَمَا قَرَّبَ إِلَيْهَا مِنْ قَوْلٍ أَوْ عَمَلٍ",
        "bangla": "হে আল্লাহ! আমি আপনার কাছে জান্নাত প্রার্থনা করছি এবং সেই সকল কথা ও কাজ যা জান্নাতের নিকটবর্তী করে।",
        "english": "O Allah, I ask You for Paradise and for words and deeds that bring me closer to it.",
        "reference": "তিরমিজি"
    },
    {
        "arabic": "رَبَّنَا آتِنَا فِي الدُّنْيَا حَسَنَةً وَفِي الْآخِرَةِ حَسَنَةً وَقِنَا عَذَابَ النَّارِ",
        "bangla": "হে আমাদের রব! আমাদের দুনিয়াতে কল্যাণ দিন এবং আখিরাতেও কল্যাণ দিন এবং আমাদের জাহান্নামের শাস্তি থেকে রক্ষা করুন।",
        "english": "Our Lord! Give us in this world good, and in the Hereafter good, and save us from the punishment of the Fire.",
        "reference": "সূরা বাকারা, ২:২০১"
    }
]

# Helper functions
def get_today_date() -> str:
    """Get today's date in YYYY-MM-DD format"""
    return date.today().isoformat()

def format_date_for_api(date_str: str) -> str:
    """Format date for API request"""
    try:
        if len(date_str) == 10 and date_str[4] == '-' and date_str[7] == '-':
            return date_str
        parsed_date = datetime.strptime(date_str, "%Y-%m-%d")
        return parsed_date.strftime("%Y-%m-%d")
    except:
        return get_today_date()

def validate_district(district_id: str) -> str:
    """Validate and return district ID"""
    district_id = district_id.lower().strip()
    valid_ids = [d["id"] for d in BANGLADESH_DISTRICTS]
    if district_id in valid_ids:
        return district_id
    return "dhaka"  # Default to dhaka

def get_district_by_id(district_id: str) -> Optional[Dict]:
    """Get district information by ID"""
    for district in BANGLADESH_DISTRICTS:
        if district["id"] == district_id:
            return district
    return None

def calculate_prayer_times_approximation(district: Dict, date_str: str) -> Dict:
    """Calculate approximate prayer times based on coordinates"""
    lat = district["lat"]
    
    # Base times for Dhaka (approximate)
    base_fajr = "5:11 AM"
    base_maghrib = "5:58 PM"
    
    # Adjust based on latitude (simplified)
    lat_diff = lat - 23.8103  # Difference from Dhaka latitude
    time_adjustment = lat_diff * 0.5  # Rough adjustment in minutes
    
    def adjust_time(time_str: str, minutes: float) -> str:
        try:
            time_part, period = time_str.split(' ')
            hour, minute = map(int, time_part.split(':'))
            
            total_minutes = hour * 60 + minute + minutes
            if period == "PM" and hour != 12:
                total_minutes += 12 * 60
            elif period == "AM" and hour == 12:
                total_minutes -= 12 * 60
            
            total_minutes = total_minutes % (24 * 60)
            
            new_hour = int(total_minutes // 60) % 12
            if new_hour == 0:
                new_hour = 12
            new_minute = int(total_minutes % 60)
            new_period = "AM" if total_minutes < 12 * 60 else "PM"
            
            return f"{new_hour}:{new_minute:02d} {new_period}"
        except:
            return time_str
    
    # Parse date to get day of week
    try:
        day_date = datetime.strptime(date_str, "%Y-%m-%d")
        day_name_bn = ['শনিবার', 'রবিবার', 'সোমবার', 'মঙ্গলবার', 'বুধবার', 'বৃহস্পতিবার', 'শুক্রবার'][day_date.weekday()]
        day_name_en = day_date.strftime("%A")
    except:
        day_name_bn = "শুক্রবার"
        day_name_en = "Friday"
    
    # Calculate Hijri date (approximate)
    try:
        # This is a very rough approximation - in production use proper Hijri conversion
        hijri_date = f"{int(date_str[8:10])} রমজান, ১৪৪৬ হিজরী"
    except:
        hijri_date = "২ রমজান, ১৪৪৬ হিজরী"
    
    return {
        "Date": date_str[5:10].replace('-', ' '),
        "islamicDate": hijri_date,
        "banglaDate": f"{int(date_str[8:10])} ফাল্গুন, ১৪৩২",
        "Day": day_name_bn,
        "Day_en": day_name_en,
        "Suhoor": adjust_time(base_fajr, -time_adjustment),
        "Iftaar": adjust_time(base_maghrib, time_adjustment * 0.4),
        "isToday": (date_str == get_today_date()),
        "seheri": adjust_time(base_fajr, -time_adjustment),
        "iftar": adjust_time(base_maghrib, time_adjustment * 0.4)
    }

# Error handler decorator
def handle_errors(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except requests.exceptions.RequestException as e:
            logger.error(f"API request error: {str(e)}")
            return jsonify({
                "success": False,
                "message": "Failed to fetch data from external API",
                "error": str(e)
            }), 503
        except Exception as e:
            logger.error(f"Internal server error: {str(e)}")
            return jsonify({
                "success": False,
                "message": "Internal server error",
                "error": str(e)
            }), 500
    return decorated_function

# Routes
@app.route('/')
def index():
    """Render the main HTML page"""
    return render_template('index.html', districts=BANGLADESH_DISTRICTS)

@app.route('/district/<district_id>')
def district_page(district_id):
    """Render district details page"""
    district = get_district_by_id(district_id)
    if not district:
        district = get_district_by_id('dhaka')
    return render_template('index.html', districts=BANGLADESH_DISTRICTS)

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Iftar Time API",
        "version": "1.0.0",
        "districts_count": len(BANGLADESH_DISTRICTS)
    })

@app.route('/api/duas/random', methods=['GET'])
def get_random_dua():
    """Get a random Ramadan Dua"""
    return jsonify({
        "success": True,
        "dua": random.choice(RAMADAN_DUAS)
    })

@app.route('/api/duas', methods=['GET'])
def get_all_duas():
    """Get all Ramadan Duas"""
    return jsonify({
        "success": True,
        "count": len(RAMADAN_DUAS),
        "duas": RAMADAN_DUAS
    })

@app.route('/api/districts', methods=['GET'])
def get_districts():
    """Get list of all districts"""
    language = request.args.get('lang', 'bn')
    division = request.args.get('division', None)
    
    districts_list = []
    for d in BANGLADESH_DISTRICTS:
        if division and d["division"] != division:
            continue
        
        districts_list.append({
            "id": d["id"],
            "name": d["name"] if language == 'bn' else d["name_en"],
            "division": d["division"],
            "lat": d["lat"],
            "lon": d["lon"]
        })
    
    return jsonify({
        "success": True,
        "count": len(districts_list),
        "districts": districts_list
    })

@app.route('/api/divisions', methods=['GET'])
def get_divisions():
    """Get list of divisions"""
    divisions = list(set([d["division"] for d in BANGLADESH_DISTRICTS]))
    divisions.sort()
    
    return jsonify({
        "success": True,
        "count": len(divisions),
        "divisions": divisions
    })

@app.route('/api/ramadan/today', methods=['GET'])
@app.route('/api/ramadan/today/<district_id>', methods=['GET'])
@handle_errors
def get_today_info(district_id: str = "dhaka"):
    """Get today's Seheri and Iftar information"""
    district_id = validate_district(district_id)
    district = get_district_by_id(district_id)
    today = get_today_date()
    
    # Check cache
    cache_key_str = f"schedule_{today}_{district_id}"
    if cache_key_str in cache:
        response_data = cache[cache_key_str]
    else:
        try:
            # Try to fetch from API
            response = requests.post(
                f"{BASE_URL}/RamadanSeheriIftarTime",
                json={
                    "firstDate": today,
                    "location": district_id,
                    "language": "bn"
                },
                headers=HEADERS,
                timeout=10
            )
            response.raise_for_status()
            response_data = response.json()
            cache[cache_key_str] = response_data
        except Exception as e:
            logger.warning(f"API failed for {district_id}, using approximation: {str(e)}")
            # If API fails, use approximate calculation
            approx_times = calculate_prayer_times_approximation(district, today)
            return jsonify({
                "success": True,
                "date": today,
                "district": district,
                "data": {
                    "Suhoor": approx_times["Suhoor"],
                    "Iftaar": approx_times["Iftaar"],
                    "seheri": approx_times["seheri"],
                    "iftar": approx_times["iftar"],
                    "Day": approx_times["Day"],
                    "Date": approx_times["Date"]
                },
                "is_approximate": True,
                "message": "Using approximate calculation (API unavailable)"
            })
    
    # Find today's information
    today_info = None
    for day in response_data.get("Data", {}).get("FastTime", []):
        if day.get("isToday"):
            today_info = day
            break
    
    if not today_info:
        today_info = response_data.get("Data", {}).get("FastTracker", {})
    
    # Format response for frontend
    formatted_data = {
        "Suhoor": today_info.get("Suhoor", "5:11 AM"),
        "Iftaar": today_info.get("Iftaar", "5:58 PM"),
        "Date": today_info.get("Date", today[5:10]),
        "Day": today_info.get("Day", "শুক্রবার"),
        "islamicDate": today_info.get("islamicDate", "২ রমজান, ১৪৪৬ হিজরী")
    }
    
    return jsonify({
        "success": True,
        "date": today,
        "district": district,
        "data": formatted_data,
        "fast_tracker": response_data.get("Data", {}).get("FastTracker", {}),
        "is_approximate": False
    })

@app.route('/api/ramadan/calendar', methods=['GET'])
@app.route('/api/ramadan/calendar/<district_id>', methods=['GET'])
@handle_errors
def get_calendar(district_id: str = "dhaka"):
    """Get full Ramadan calendar"""
    district_id = validate_district(district_id)
    district = get_district_by_id(district_id)
    start_date = request.args.get('start_date', get_today_date())
    start_date = format_date_for_api(start_date)
    
    cache_key_str = f"schedule_{start_date}_{district_id}"
    if cache_key_str in cache:
        response_data = cache[cache_key_str]
    else:
        try:
            response = requests.post(
                f"{BASE_URL}/RamadanSeheriIftarTime",
                json={
                    "firstDate": start_date,
                    "location": district_id,
                    "language": "bn"
                },
                headers=HEADERS,
                timeout=10
            )
            response.raise_for_status()
            response_data = response.json()
            cache[cache_key_str] = response_data
        except Exception as e:
            logger.warning(f"Calendar API failed for {district_id}, generating approximation: {str(e)}")
            # Generate approximate calendar for 30 days
            calendar = []
            current_date = datetime.strptime(start_date, "%Y-%m-%d")
            for i in range(30):
                day_date = current_date + timedelta(days=i)
                date_str = day_date.strftime("%Y-%m-%d")
                day_info = calculate_prayer_times_approximation(district, date_str)
                day_info["day"] = i + 1
                calendar.append(day_info)
            
            return jsonify({
                "success": True,
                "district": district,
                "start_date": start_date,
                "total_days": len(calendar),
                "calendar": calendar,
                "is_approximate": True,
                "message": "Using approximate calculation (API unavailable)"
            })
    
    calendar = response_data.get("Data", {}).get("FastTime", [])
    
    # Ensure we have 30 days
    if len(calendar) < 30:
        # Pad with approximate days
        last_date = datetime.strptime(start_date, "%Y-%m-%d") + timedelta(days=len(calendar))
        for i in range(len(calendar), 30):
            date_str = (last_date + timedelta(days=i-len(calendar))).strftime("%Y-%m-%d")
            day_info = calculate_prayer_times_approximation(district, date_str)
            calendar.append(day_info)
    
    return jsonify({
        "success": True,
        "district": district,
        "start_date": start_date,
        "total_days": len(calendar),
        "calendar": calendar[:30],  # Ensure only 30 days
        "is_approximate": False
    })

@app.route('/api/ramadan/countdown', methods=['GET'])
@app.route('/api/ramadan/countdown/<district_id>', methods=['GET'])
@handle_errors
def get_countdown(district_id: str = "dhaka"):
    """Get countdown to next Iftar"""
    district_id = validate_district(district_id)
    district = get_district_by_id(district_id)
    today = get_today_date()
    
    # Get today's info
    try:
        today_response = get_today_info(district_id)
        if isinstance(today_response, tuple):
            today_data = json.loads(today_response[0].get_data(as_text=True))
        else:
            today_data = today_response
    except:
        # Fallback
        today_data = {"is_approximate": True, "data": {"Iftaar": "5:58 PM", "iftar": "5:58 PM"}}
    
    if today_data.get("is_approximate", False):
        iftar_time_str = today_data.get("data", {}).get("iftar", "5:58 PM")
    else:
        today_info = today_data.get("data", {})
        iftar_time_str = today_info.get("Iftaar", "5:58 PM")
    
    # Parse iftar time
    try:
        time_parts = iftar_time_str.split(' ')
        time_part = time_parts[0]
        period = time_parts[1] if len(time_parts) > 1 else "PM"
        
        hour, minute = map(int, time_part.split(':'))
        
        if period == "PM" and hour != 12:
            hour += 12
        elif period == "AM" and hour == 12:
            hour = 0
        
        now = datetime.now()
        iftar_time = datetime(now.year, now.month, now.day, hour, minute, 0)
        
        # If iftar time has passed, calculate for tomorrow
        if now > iftar_time:
            iftar_time = iftar_time + timedelta(days=1)
        
        # Calculate time difference
        diff = iftar_time - now
        total_seconds = int(diff.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        return jsonify({
            "success": True,
            "district": district,
            "date": today,
            "iftar_time": iftar_time_str,
            "countdown": {
                "hours": hours,
                "minutes": minutes,
                "seconds": seconds,
                "total_seconds": total_seconds,
                "formatted": f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            },
            "message": "Time remaining until Iftar" if total_seconds > 0 else "Iftar time has passed"
        })
    except Exception as e:
        logger.error(f"Error calculating countdown: {str(e)}")
        # Return default countdown
        return jsonify({
            "success": True,
            "district": district,
            "date": today,
            "iftar_time": "5:58 PM",
            "countdown": {
                "hours": 8,
                "minutes": 30,
                "seconds": 0,
                "total_seconds": 30600,
                "formatted": "08:30:00"
            },
            "message": "Approximate countdown"
        })

@app.route('/api/ramadan/search', methods=['GET'])
def search_district():
    """Search districts by name"""
    query = request.args.get('q', '').lower().strip()
    
    if not query:
        return jsonify({
            "success": False,
            "message": "Search query required"
        }), 400
    
    results = []
    for district in BANGLADESH_DISTRICTS:
        if (query in district["name"].lower() or 
            query in district["name_en"].lower() or 
            query in district["division"].lower()):
            results.append(district)
    
    return jsonify({
        "success": True,
        "query": query,
        "count": len(results),
        "results": results
    })

@app.route('/api/ramadan/nearby', methods=['GET'])
def get_nearby_districts():
    """Get nearby districts based on coordinates"""
    try:
        lat = float(request.args.get('lat', 23.8103))
        lon = float(request.args.get('lon', 90.4125))
        radius = float(request.args.get('radius', 100))  # km
        
        nearby = []
        for district in BANGLADESH_DISTRICTS:
            # Calculate distance using haversine formula
            R = 6371  # Earth's radius in km
            dlat = math.radians(district["lat"] - lat)
            dlon = math.radians(district["lon"] - lon)
            a = (math.sin(dlat/2) * math.sin(dlat/2) + 
                 math.cos(math.radians(lat)) * math.cos(math.radians(district["lat"])) * 
                 math.sin(dlon/2) * math.sin(dlon/2))
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            distance = R * c
            
            if distance <= radius:
                district_copy = district.copy()
                district_copy["distance"] = round(distance, 2)
                nearby.append(district_copy)
        
        # Sort by distance
        nearby.sort(key=lambda x: x["distance"])
        
        return jsonify({
            "success": True,
            "lat": lat,
            "lon": lon,
            "radius": radius,
            "count": len(nearby),
            "districts": nearby
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": "Error finding nearby districts",
            "error": str(e)
        }), 400

# This is the key part for Vercel - the app instance needs to be exported
app = app

# For local development
if __name__ == '__main__':
    # Create templates and static directories if they don't exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    print("=" * 50)
    print("রমজান ইফতার টাইম API - Developed by Mueid Mursalin Rifat")
    print("=" * 50)
    print(f"Server starting at: http://localhost:5000")
    print(f"Number of districts: {len(BANGLADESH_DISTRICTS)}")
    print(f"Default district: Dhaka")
    print("=" * 50)    
    
    # Get port from environment variable
    port = int(os.environ.get('PORT', 5000))
    
    # Run with debug=False in production
    app.run(host='0.0.0.0', port=port, debug=False)
