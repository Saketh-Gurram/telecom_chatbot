import mysql.connector
import speech_recognition as sr
import pyttsx3
from groq import Groq

# Hardcoded GroqCloud API key (use environment variables in production)
GROQCLOUD_API_KEY = "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"

# Initialize GroqCloud client
client = Groq(api_key=GROQCLOUD_API_KEY)

# Initialize text-to-speech engine
tts_engine = pyttsx3.init()

# Global variable for mode selection
voice_mode = False  # Default is text mode

def speak(text):
    """Output text via TTS if voice mode is enabled, otherwise print it."""
    if voice_mode:
        print(f"Bot: {text}")
        tts_engine.say(text)
        tts_engine.runAndWait()
    else:
        print(f"Bot: {text}")

def listen():
    """Capture and return voice input as text."""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        speak("Listening...")
        recognizer.adjust_for_ambient_noise(source)
        try:
            audio = recognizer.listen(source)
            command = recognizer.recognize_google(audio)
            print(f"You: {command}")
            return command.lower()
        except sr.UnknownValueError:
            speak("Sorry, I didn't catch that. Please try again.")
            return None
        except sr.RequestError:
            speak("Speech recognition service is unavailable.")
            return None

def get_input(prompt):
    """Get input from the user based on the selected mode."""
    speak(prompt)
    return listen() if voice_mode else input(f"{prompt} ").strip()

def connect_to_db():
    """Connect to the telecom database."""
    try:
        return mysql.connector.connect(
            host="localhost",
            user="root",       
            password="saketh",  
            database="telecom"
        )
    except mysql.connector.Error as err:
        speak(f"Database connection error: {err}")
        exit()

def show_plans(cursor):
    """Retrieve and display telecom plans from the database."""
    cursor.execute("SELECT * FROM plans")
    plans = cursor.fetchall()
    if plans:
        speak("Here are the available plans:")
        for plan in plans:
            speak(f"Plan ID {plan[0]}, {plan[1]}, priced at {plan[2]} dollars.")
    else:
        speak("No plans found.")

def get_user_details():
    """Collect user registration details."""
    name = get_input("What is your name?")
    if not name:
        return None, None, None

    phone = get_input("What is your phone number?")
    if not phone:
        return None, None, None

    plan_id = get_input("Which plan ID do you want to choose?")
    if not plan_id or not plan_id.isdigit():
        speak("Invalid plan ID. Please try again later.")
        return None, None, None

    return name, phone, int(plan_id)

def save_user_details(cursor, db, name, phone, plan_id):
    """Save the user's details into the database after checking SIM card limit."""
    try:
        # Check if the user already has 2 SIM cards (using name and phone as identifiers)
        cursor.execute("SELECT COUNT(*) FROM users WHERE name = %s AND phone = %s", (name, phone))
        sim_count = cursor.fetchone()[0]
        if sim_count >= 2:
            speak("Sorry, you already have the maximum of 2 SIM cards. Cannot add another.")
            return
    except mysql.connector.Error as err:
        speak(f"Error checking existing SIM cards: {err}")
        return

    try:
        cursor.execute(
            "INSERT INTO users (name, phone, plan_id) VALUES (%s, %s, %s)",
            (name, phone, plan_id)
        )
        db.commit()
        speak("Your details have been saved successfully!")
    except mysql.connector.Error as err:
        speak(f"Error saving details: {err}")

def get_usage_details():
    """Prompt user for usage details for plan recommendation."""
    data_usage = get_input("How much data do you use per month in gigabytes?")
    call_minutes = get_input("How many call minutes do you use per month?")
    texts = get_input("How many text messages do you send per month?")
    return data_usage, call_minutes, texts

def get_plan_recommendation(usage_details):
    """Request a plan recommendation from GroqCloud based on usage."""
    message = (
        f"My monthly usage is {usage_details[0]}GB of data, "
        f"{usage_details[1]} call minutes, and {usage_details[2]} texts. "
        "Based on this, which telecom plan is best for me?"
    )
    speak("Processing your request, please wait...")
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": message}],
        model="llama-3.3-70b-versatile"
    )
    recommendation = chat_completion.choices[0].message.content
    speak("Here is my recommendation:")
    speak(recommendation)
    return recommendation

def main():
    """Main function to choose mode and run the chatbot."""
    global voice_mode
    
    # Mode selection at startup
    print("Welcome! Do you want to use voice mode or text mode?")
    mode = input("Choose mode (voice/text): ").strip().lower()
    if mode == "voice":
        voice_mode = True
        speak("Voice mode activated!")
    else:
        voice_mode = False
        print("Text mode activated!")
    
    # Connect to database
    db = connect_to_db()
    cursor = db.cursor()

    # Chatbot main loop
    while True:
        if voice_mode:
            speak("Say: 'show plans', 'enter details', 'get recommendation', or 'exit'.")
            command = listen()
        else:
            command = input("Enter command (show plans, enter details, get recommendation, exit): ").strip().lower()
        
        if not command:
            continue

        if "show plans" in command:
            show_plans(cursor)
        elif "enter details" in command:
            name, phone, plan_id = get_user_details()
            if name and phone and plan_id:
                save_user_details(cursor, db, name, phone, plan_id)
        elif "get recommendation" in command:
            usage_details = get_usage_details()
            get_plan_recommendation(usage_details)
        elif "exit" in command:
            speak("Exiting. Have a great day!")
            break
        else:
            speak("Sorry, I didn't understand. Please try again.")

    cursor.close()
    db.close()

if __name__ == "__main__":
    main()
