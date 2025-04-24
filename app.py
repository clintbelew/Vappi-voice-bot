import os
import logging
import requests
from flask import Flask, request, jsonify, send_file
from dotenv import load_dotenv
import tempfile
import io
from pytz import timezone as pytz_timezone
from datetime import datetime

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('vappi')

# Initialize Flask app
app = Flask(__name__)

# Environment variables
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')
ELEVENLABS_VOICE_ID = os.getenv('ELEVENLABS_VOICE_ID')
GHL_API_KEY = os.getenv('GHL_API_KEY')
GHL_LOCATION_ID = os.getenv('GHL_LOCATION_ID')
GHL_CALENDAR_ID = os.getenv('GHL_CALENDAR_ID')

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({"status": "healthy", "service": "VAPPI Voice Bot Backend"})

@app.route('/voice', methods=['POST'])
def generate_voice():
    """
    Generate voice audio from text using ElevenLabs API
    
    Expects JSON with:
    {
        "text": "Text to convert to speech"
    }
    
    Returns audio file (MP3)
    """
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            logger.error("Invalid request: missing 'text' field")
            return jsonify({"error": "Missing 'text' field"}), 400
            
        text = data['text']
        logger.info(f"Voice generation request received: {text[:50]}...")
        
        if not ELEVENLABS_API_KEY:
            logger.error("ELEVENLABS_API_KEY not configured")
            return jsonify({"error": "ElevenLabs API key not configured"}), 500
            
        if not ELEVENLABS_VOICE_ID:
            logger.error("ELEVENLABS_VOICE_ID not configured")
            return jsonify({"error": "ElevenLabs voice ID not configured"}), 500
        
        # Call ElevenLabs API
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": ELEVENLABS_API_KEY
        }
        payload = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.5
            }
        }
        
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            logger.info("Voice successfully generated")
            # Create a temporary file to store the audio
            audio_data = io.BytesIO(response.content)
            audio_data.seek(0)
            return send_file(
                audio_data,
                mimetype="audio/mpeg",
                as_attachment=True,
                download_name="voice.mp3"
            )
        else:
            logger.error(f"ElevenLabs API error: {response.status_code} - {response.text}")
            return jsonify({
                "error": "Failed to generate voice",
                "details": response.text
            }), response.status_code
            
    except Exception as e:
        logger.error(f"Voice generation error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/book', methods=['POST'])
def book_appointment():
    """
    Book an appointment in GoHighLevel
    
    Expects JSON with:
    {
        "name": "Client Name",
        "phone": "1234567890",
        "email": "client@example.com",
        "selectedSlot": "2023-04-25T14:00:00"  # ISO format datetime string
    }
    
    Returns success or error JSON
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'phone', 'email', 'selectedSlot']
        for field in required_fields:
            if field not in data:
                logger.error(f"Invalid request: missing '{field}' field")
                return jsonify({"error": f"Missing '{field}' field"}), 400
        
        logger.info(f"Booking request received for {data['name']}")
        
        # Default to Central Time (America/Chicago)
        central = pytz_timezone("America/Chicago")
        
        # Parse and localize the selectedSlot to Central Time
        try:
            appointment_time = central.localize(datetime.fromisoformat(data['selectedSlot']))
            logger.info(f"Appointment time parsed and localized: {appointment_time.isoformat()}")
        except Exception as e:
            logger.error(f"Invalid datetime format: {str(e)}")
            return jsonify({"error": f"Invalid datetime format: {str(e)}"}), 400
        
        if not all([GHL_API_KEY, GHL_LOCATION_ID, GHL_CALENDAR_ID]):
            logger.error("GoHighLevel API configuration incomplete")
            return jsonify({"error": "GoHighLevel API configuration incomplete"}), 500
        
        # First, create or update contact in GoHighLevel
        contact_url = "https://rest.gohighlevel.com/v1/contacts/"
        contact_headers = {
            "Authorization": f"Bearer {GHL_API_KEY}",
            "Content-Type": "application/json"
        }
        contact_payload = {
            "email": data['email'],
            "phone": data['phone'],
            "firstName": data['name'].split(' ')[0],
            "lastName": " ".join(data['name'].split(' ')[1:]) if len(data['name'].split(' ')) > 1 else "",
            "locationId": GHL_LOCATION_ID
        }
        
        contact_response = requests.post(contact_url, json=contact_payload, headers=contact_headers)
        
        if contact_response.status_code not in [200, 201]:
            logger.error(f"GoHighLevel contact creation error: {contact_response.status_code} - {contact_response.text}")
            return jsonify({
                "error": "Failed to create contact",
                "details": contact_response.text
            }), 500
        
        contact_data = contact_response.json()
        contact_id = contact_data.get('id') or contact_data.get('contact', {}).get('id')
        
        if not contact_id:
            logger.error("Failed to get contact ID from GoHighLevel response")
            return jsonify({"error": "Failed to get contact ID"}), 500
        
        # Now book the appointment
        calendar_url = f"https://rest.gohighlevel.com/v1/appointments/"
        calendar_payload = {
            "calendarId": GHL_CALENDAR_ID,
            "contactId": contact_id,
            "startTime": appointment_time.isoformat(),
            "title": f"Appointment with {data['name']}",
            "description": "Appointment booked via VAPPI Voice Bot",
            "locationId": GHL_LOCATION_ID
        }
        
        calendar_response = requests.post(calendar_url, json=calendar_payload, headers=contact_headers)
        
        if calendar_response.status_code in [200, 201]:
            logger.info(f"Appointment successfully booked for {data['name']}")
            return jsonify({
                "success": True,
                "message": "Appointment booked successfully",
                "scheduled_time": appointment_time.isoformat(),
                "appointment": calendar_response.json()
            })
        else:
            logger.error(f"GoHighLevel appointment booking error: {calendar_response.status_code} - {calendar_response.text}")
            return jsonify({
                "error": "Failed to book appointment",
                "details": calendar_response.text
            }), 500
            
    except Exception as e:
        logger.error(f"Appointment booking error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Get port from environment variable or use default
    port = int(os.getenv('PORT') or os.getenv('RAILWAY_PORT') or 5000)
    logger.info(f"Starting VAPPI Voice Bot Backend on port {port}")
    app.run(host='0.0.0.0', port=port)
