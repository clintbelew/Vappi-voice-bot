# VAPPI Voice Bot Backend

A clean starter repository for a voice bot backend called VAPPI, designed to be hosted on Railway.

## Features

1. **Voice Generation**
   - `/voice` endpoint that accepts POST requests with text
   - Returns ElevenLabs-generated audio (MP3)
   - Uses ELEVENLABS_API_KEY and voice ID from environment variables

2. **Appointment Booking**
   - `/book` endpoint that accepts POST requests with contact and appointment details
   - Creates a contact and books an appointment in GoHighLevel
   - Uses GHL API credentials from environment variables

3. **Environment Configuration**
   - Configured via `.env` file
   - Supports all required API keys and IDs

4. **Logging**
   - Comprehensive logging for requests, responses, and errors

## Setup

1. Clone this repository
2. Create a `.env` file based on `.env.example`
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Run the application:
   ```
   python app.py
   ```

## API Endpoints

### Health Check
```
GET /health
```
Returns a simple health check response to verify the service is running.

### Voice Generation
```
POST /voice
```
**Request Body:**
```json
{
    "text": "Text to convert to speech"
}
```
**Response:**
- Audio file (MP3) with the generated speech

### Appointment Booking
```
POST /book
```
**Request Body:**
```json
{
    "name": "Client Name",
    "phone": "1234567890",
    "email": "client@example.com",
    "datetime": "2023-04-25T14:00:00Z"
}
```
**Response:**
```json
{
    "success": true,
    "message": "Appointment booked successfully",
    "appointment": {
        // Appointment details from GoHighLevel
    }
}
```

## Deployment

This application is designed to be deployed on Railway. Railway will automatically:

1. Install dependencies from `requirements.txt`
2. Set the `RAILWAY_PORT` environment variable
3. Run the application

No additional configuration is needed for deployment beyond setting the required environment variables in the Railway dashboard.

## Environment Variables

| Variable | Description |
|----------|-------------|
| `ELEVENLABS_API_KEY` | API key for ElevenLabs TTS service |
| `ELEVENLABS_VOICE_ID` | Voice ID to use for speech generation |
| `GHL_API_KEY` | API key for GoHighLevel |
| `GHL_LOCATION_ID` | Location ID for GoHighLevel |
| `GHL_CALENDAR_ID` | Calendar ID for GoHighLevel |
| `PORT` | Port to run the server on (locally) |
| `RAILWAY_PORT` | Port set by Railway (automatically configured) |
