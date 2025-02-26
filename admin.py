import mysql.connector
import speech_recognition as sr
import pyttsx3
import matplotlib.pyplot as plt

# Admin credentials (for demonstration purposes)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# Initialize text-to-speech engine
tts_engine = pyttsx3.init()

# Global variable for admin mode selection (voice or text)
voice_mode = False  # Default: text mode

def speak(text):
    """Output text via TTS if voice mode is enabled, otherwise print it."""
    if voice_mode:
        print(f"Admin Bot: {text}")
        tts_engine.say(text)
        tts_engine.runAndWait()
    else:
        print(f"Admin Bot: {text}")

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
            password="admin",
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

def calculate_monthly_revenue(cursor):
    """
    Calculate total monthly revenue by summing up the prices for all active SIM cards.
    """
    query = """
        SELECT SUM(plans.price) AS total_revenue
        FROM users
        JOIN plans ON users.plan_id = plans.id;
    """
    cursor.execute(query)
    result = cursor.fetchone()
    total_revenue = result[0] if result[0] is not None else 0
    return total_revenue

def plot_revenue_by_plan(cursor):
    """
    Retrieve revenue data by plan and plot a bar chart.
    """
    query = """
        SELECT plans.name, COUNT(users.id) AS sim_count, plans.price, (COUNT(users.id) * plans.price) AS revenue
        FROM users
        JOIN plans ON users.plan_id = plans.id
        GROUP BY plans.id, plans.name, plans.price;
    """
    cursor.execute(query)
    results = cursor.fetchall()
    if results:
        plan_names = [row[0] for row in results]
        revenues = [row[3] for row in results]
        plt.figure(figsize=(10, 6))
        plt.bar(plan_names, revenues, color='skyblue')
        plt.xlabel("Plan")
        plt.ylabel("Revenue ($)")
        plt.title("Monthly Revenue by Plan")
        plt.show()
    else:
        speak("No data available to plot.")

def add_new_plan(cursor, db):
    """
    Prompt admin for new plan details and insert the plan into the database.
    """
    plan_name = get_input("Enter the new plan name:")
    price_input = get_input("Enter the plan price:")
    try:
        price = float(price_input)
    except ValueError:
        speak("Invalid price. Please try again.")
        return

    try:
        cursor.execute("INSERT INTO plans (name, price) VALUES (%s, %s)", (plan_name, price))
        db.commit()
        speak("Plan added successfully!")
    except mysql.connector.Error as err:
        speak(f"Error adding plan: {err}")

def admin_menu(cursor, db):
    """Display admin options for various database operations."""
    speak("Welcome to the admin panel.")
    while True:
        speak("Say or type 'show users', 'search sims', 'show revenue', 'show revenue chart', 'add plan', or 'exit admin'.")
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
        elif "show revenue" in command:
            revenue = calculate_monthly_revenue(cursor)
            speak(f"The total monthly revenue is ${revenue:.2f}")
        elif "show revenue chart" in command:
            plot_revenue_by_plan(cursor)
        elif "add plan" in command:
            add_new_plan(cursor, db)
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
        admin_menu(cursor, db)
    cursor.close()
    db.close()

if __name__ == "__main__":
    main()
