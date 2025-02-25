import mysql.connector
import speech_recognition as sr
import pyttsx3

# Admin credentials (for demo purposes)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# Initialize text-to-speech engine for admin panel (if using voice mode)
tts_engine = pyttsx3.init()

# Global variable for admin mode selection (voice or text)
voice_mode = False  # Default is text mode

def speak(text):
    """Speak or print text based on the selected mode."""
    if voice_mode:
        print(f"Admin Bot: {text}")
        tts_engine.say(text)
        tts_engine.runAndWait()
    else:
        print(f"Admin Bot: {text}")

def listen():
    """Capture voice input and convert it to text."""
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
    """Get user input using voice or text."""
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

def admin_login():
    """Prompt for admin credentials and validate them."""
    username = get_input("Enter admin username:")
    password = get_input("Enter admin password:")
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        speak("Admin login successful!")
        return True
    else:
        speak("Invalid admin credentials.")
        return False

def admin_menu(cursor):
    """Display admin options for viewing users and searching SIM card counts."""
    speak("Welcome to the admin panel.")
    while True:
        speak("Say or type 'show users', 'search sims', or 'exit admin'.")
        command = listen() if voice_mode else input("Enter admin command: ").strip().lower()
        if not command:
            continue
        if "show users" in command:
            cursor.execute("SELECT * FROM users")
            users = cursor.fetchall()
            if users:
                speak("Here are all the users:")
                for user in users:
                    speak(f"User ID {user[0]}, Name: {user[1]}, Phone: {user[2]}, Plan ID: {user[3]}")
            else:
                speak("No users found.")
        elif "search sims" in command:
            name = get_input("Enter the user's name:")
            phone = get_input("Enter the user's phone number:")
            cursor.execute("SELECT COUNT(*) FROM users WHERE name = %s AND phone = %s", (name, phone))
            sim_count = cursor.fetchone()[0]
            speak(f"{name} with phone {phone} has {sim_count} SIM card(s).")
        elif "exit admin" in command:
            speak("Exiting admin panel.")
            break
        else:
            speak("Unknown admin command.")

def main():
    """Main function for the admin panel."""
    global voice_mode
    print("Admin Panel: Do you want to use voice mode or text mode?")
    mode = input("Choose mode (voice/text): ").strip().lower()
    if mode == "voice":
        voice_mode = True
        speak("Voice mode activated!")
    else:
        voice_mode = False
        print("Text mode activated!")

    db = connect_to_db()
    cursor = db.cursor()
    if admin_login():
        admin_menu(cursor)
    cursor.close()
    db.close()

if __name__ == "__main__":
    main()
