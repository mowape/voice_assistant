import os
import json
import subprocess
import pyttsx3 as s
import speech_recognition as sr
import requests
from datetime import datetime
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate

CACHE_FILE = "app_cache.json"
engine = s.init()

model = OllamaLLM(model='solar')
prompt_template = """ 
Answer the question below:
Question: {question}
Answer: 
"""
prompt = ChatPromptTemplate.from_template(prompt_template)

aliases = {
    "notepad": "notepad",
    "spotify": "spotify",
    "chrome": "chrome",
    "visual studio": "devenv",
    "word": "winword",
    "excel": "excel"
}

def speak(text):
    engine.say(text)
    engine.runAndWait()

def scan_for_apps():
    apps = {}
    drives = ['C:\\']
    search_extensions = ['.exe']

    specific_dirs = [
        'C:\\Program Files\\Microsoft Office\\root\\Office16'
    ]

    for directory in specific_dirs:
        for root, dirs, files in os.walk(directory):
            try:
                for file in files:
                    if any(file.endswith(ext) for ext in search_extensions):
                        app_name = file.replace(".exe", "").lower()
                        app_path = os.path.join(root, file)
                        apps[app_name] = app_path
                        print(f"Found {app_name}: {app_path}")
            except (PermissionError, OSError) as e:
                print(f"Skipping directory {root}: {str(e)}")

    for drive in drives:
        for root, dirs, files in os.walk(drive):
            try:
                for file in files:
                    if any(file.endswith(ext) for ext in search_extensions):
                        app_name = file.replace(".exe", "").lower()
                        app_path = os.path.join(root, file)
                        apps[app_name] = app_path
                        print(f"Found {app_name}: {app_path}")
            except (PermissionError, OSError) as e:
                print(f"Skipping directory {root}: {str(e)}")
    
    with open(CACHE_FILE, 'w') as cache_file:
        json.dump(apps, cache_file)
    
    return apps


def load_cached_apps():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as cache_file:
                data = cache_file.read().strip()
                if data:  # Check if the file is not empty
                    return json.loads(data)
                else:
                    print("Cache file is empty, rescanning for apps.")
                    return scan_for_apps()
        except (json.JSONDecodeError, ValueError):
            print("Invalid JSON format in cache file, rescanning for apps.")
            return scan_for_apps()
    return scan_for_apps()

def fetch_india_headlines():
    api_key = "475babbeefd68405eef81a2f62282bfe"
    url = f"https://gnews.io/api/v4/top-headlines?token={api_key}&country=in&lang=en&max=5"

    try:
        response = requests.get(url)
        data = response.json()

        if 'articles' in data and len(data['articles']) > 0:
            speak("Here are the top headlines:")
            for article in data['articles']:
                speak(article['title'])
                print(article['title'])
        else:
            print("No articles found in the response.")
            speak("I couldn't find any news articles at the moment.")
    
    except Exception as e:
        print(f"Error fetching news: {e}")
        speak("Sorry, there was an error fetching the news.")

def perform_task(command, apps):
    command = command.lower()

    if "open" in command:
        app_name = command.replace("open ", "").strip()
        
        if app_name in aliases:
            app_name = aliases[app_name]
        
        if app_name in apps:
            try:
                subprocess.Popen([apps[app_name]], shell=True)
                speak(f"Opening {app_name}")
            except Exception as e:
                speak(f"Error opening {app_name}: {str(e)}")
        else:
            speak(f"Sorry, I couldn't find {app_name}.")
    
    elif "close" in command:
        app_name = command.replace("close ", "").strip()
        if app_name in aliases:
            app_name = aliases[app_name]

        if app_name in apps:
            try:
                subprocess.Popen(["taskkill", "/f", "/im", f"{app_name}.exe"], shell=True)
                speak(f"Closing {app_name}")
            except Exception as e:
                speak(f"Error closing {app_name}: {str(e)}")
        else:
            speak(f"Sorry, I couldn't find {app_name}.exe.")

def tell_time():
    current_time = datetime.now().strftime("%H:%M")
    speak(f"The current time is {current_time}")
    print(f"The current time is {current_time}")

def question_handler(question):
    chain = prompt | model
    result = chain.invoke({"question": question})
    print(result)
    speak(result)

def listen_for_command():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        audio = recognizer.listen(source)
        try:
            command = recognizer.recognize_google(audio)
            print(f"You said: {command}")
            return command
        except sr.UnknownValueError:
            print("Sorry, I did not understand the audio.")
            speak("Sorry, I did not understand the audio.")
            return None
        except sr.RequestError:
            print("Sorry, there was an error with the request.")
            speak("Sorry, there was an error with the request.")
            return None
 
def main():
    apps = load_cached_apps()
    initial_greeting = True

    while True:
        if initial_greeting:
            speak("Hi, how may I assist you?")
            print("Hi, how may I assist you?")
            initial_greeting = False
        else:
            speak("Is there anything else I can help you with?")
            print("Is there anything else I can help you with?")

        user_input = listen_for_command()
        if user_input is None:
            continue

        if user_input.lower() in ["terminate", "exit"]:
            speak("Goodbye!")
            print("Goodbye!")
            break

        if "current time" in user_input.lower():
            tell_time()
            continue

        if any(keyword in user_input.lower() for keyword in ["open", "close"]):
            perform_task(user_input, apps)
            continue

        if "latest news" in user_input.lower() or "news" in user_input.lower():
            fetch_india_headlines()
            continue

        question_handler(user_input)

if __name__ == "__main__":
    main()
