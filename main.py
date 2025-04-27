import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from gtts import gTTS
import speech_recognition as sr
from playsound import playsound
from deep_translator import GoogleTranslator
from pydub import AudioSegment
import sqlite3
import hashlib
import asyncio
import edge_tts
import random
import string
import webbrowser

# Set paths for ffmpeg
AudioSegment.converter = r"C:\Users\karni\Downloads\ffmpeg-7.1.1-essentials_build\ffmpeg-7.1.1-essentials_build\bin\ffmpeg.exe"
AudioSegment.ffprobe = r"C:\Users\karni\Downloads\ffmpeg-7.1.1-essentials_build\ffmpeg-7.1.1-essentials_build\bin\ffprobe.exe"

# --- Language and Voice Mappings ---
language_voice_map = {
    "hi": {"Female": "hi-IN-SwaraNeural", "Male": "hi-IN-MadhurNeural"},
    "en": {"Female": "en-US-JennyNeural", "Male": "en-US-GuyNeural"},
    "es": {"Female": "es-ES-ElviraNeural", "Male": "es-ES-AlvaroNeural"},
    "fr": {"Female": "fr-FR-DeniseNeural", "Male": "fr-FR-HenriNeural"},
    "de": {"Female": "de-DE-KatjaNeural", "Male": "de-DE-ConradNeural"},
    "ja": {"Female": "ja-JP-NanamiNeural", "Male": "ja-JP-KeitaNeural"},
    "zh-CN": {"Female": "zh-CN-XiaoxiaoNeural", "Male": "zh-CN-YunxiNeural"},
    "bn": {"Female": "bn-IN-TanishaaNeural", "Male": "bn-IN-TanishNeural"},
    "ta": {"Female": "ta-IN-PallaviNeural", "Male": "ta-IN-ValluvarNeural"},
    "te": {"Female": "te-IN-ShrutiNeural", "Male": "te-IN-MohanNeural"},
    "kn": {"Female": "kn-IN-SapnaNeural", "Male": "kn-IN-GaganNeural"},
    "gu": {"Female": "gu-IN-DhwaniNeural", "Male": "gu-IN-NiranjanNeural"},
    "pa": {"Female": "pa-IN-HarmeetNeural", "Male": "pa-IN-BaldevNeural"},
    "ko": {"Female": "ko-KR-SunHiNeural", "Male": "ko-KR-InJoonNeural"},
    "ru": {"Female": "ru-RU-SvetlanaNeural", "Male": "ru-RU-DmitryNeural"},
}

# --- User Authentication ---
def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS translations (
                    translation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    input_text TEXT,
                    output_text TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id))''')

    conn.commit()
    conn.close()
def store_translation(user_id, input_text, output_text):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("INSERT INTO translations (user_id, input_text, output_text) VALUES (?, ?, ?)",
              (user_id, input_text, output_text))
    conn.commit()
    conn.close()
def fetch_translation_history(user_id):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT input_text, output_text FROM translations WHERE user_id = ?", (user_id,))
    translations = c.fetchall()
    conn.close()
    print(f"Translations: {translations}")
    return translations
def show_translation_history(user_id):
    translations = fetch_translation_history(user_id)
    if not translations:
        messagebox.showinfo("History", "No translation history found.")
        return

    history_window = tk.Toplevel()
    history_window.title("Translation History")

    for idx, (input_text, output_text) in enumerate(translations):
        tk.Label(history_window, text=f"Translation {idx + 1}").pack(pady=5)
        tk.Label(history_window, text=f"Input: {input_text}").pack(pady=5)
        tk.Label(history_window, text=f"Output: {output_text}").pack(pady=5)

    history_window.mainloop()



    
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user():
    username = reg_username_entry.get()
    password = reg_password_entry.get()
    if username and password:
        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hash_password(password)))
            conn.commit()
            messagebox.showinfo("Success", "Registration successful!")
            register_window.destroy()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Username already exists!")
        conn.close()
    else:
        messagebox.showerror("Error", "Please fill all fields.")

def login_user():
    username = login_username_entry.get()
    password = login_password_entry.get()
    if username and password:
        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, hash_password(password)))
        result = c.fetchone()
        conn.close()
        if result:
            user_id, username, _ = result
            print(f"User ID: {user_id}")
            messagebox.showinfo("Success", "Login successful!")
            login_window.destroy()
            launch_main_app(user_id,username)
        else:
            messagebox.showerror("Error", "Invalid username or password.")
    else:
        messagebox.showerror("Error", "Please fill all fields.")

# --- Windows ---
def show_login():
    global login_window, login_username_entry, login_password_entry
    login_window = tk.Tk()
    login_window.geometry("350x250")
    login_window.title("Login")

    tk.Label(login_window, text="Username:").pack(pady=5)
    login_username_entry = tk.Entry(login_window)
    login_username_entry.pack()

    tk.Label(login_window, text="Password:").pack(pady=5)
    login_password_entry = tk.Entry(login_window, show="*")
    login_password_entry.pack()

    tk.Button(login_window, text="Login", command=login_user).pack(pady=10)
    tk.Button(login_window, text="Register", command=show_register).pack()

    login_window.mainloop()

def show_register():
    global register_window, reg_username_entry, reg_password_entry
    register_window = tk.Toplevel()
    register_window.geometry("350x250")
    register_window.title("Register")

    tk.Label(register_window, text="Username:").pack(pady=5)
    reg_username_entry = tk.Entry(register_window)
    reg_username_entry.pack()

    tk.Label(register_window, text="Password:").pack(pady=5)
    reg_password_entry = tk.Entry(register_window, show="*")
    reg_password_entry.pack()

    tk.Button(register_window, text="Register", command=register_user).pack(pady=10)

def launch_main_app(user_id,username):
    global win, gender_var, input_lang, output_lang,current_user_id
    current_user_id = user_id
    win = tk.Tk()
    win.geometry("750x600")
    win.title(f"Real-Time Voice Translator - User: {username}")

    try:
        icon = tk.PhotoImage(file="icon.png")
        win.iconphoto(False, icon)
    except Exception:
        pass

    # Language setup
    global language_codes, language_names, file_path, keep_running
    language_codes = {
        "English": "en",
        "Hindi": "hi",
        "Bengali": "bn",
        "Spanish": "es",
        "Chinese (Simplified)": "zh-CN",
        "Russian": "ru",
        "Japanese": "ja",
        "Korean": "ko",
        "German": "de",
        "French": "fr",
        "Tamil": "ta",
        "Telugu": "te",
        "Kannada": "kn",
        "Gujarati": "gu",
        "Punjabi": "pa"
    }
    language_names = list(language_codes.keys())
    file_path = ""
    keep_running = False
    gender_var = tk.StringVar(value="Default")

    # Functions inside main
    def upload_audio_file():
        global file_path
        file_path = filedialog.askopenfilename(filetypes=[("Audio Files", ".wav .mp3 .m4a")])
        if file_path:
            convert_audio_if_needed()

    def convert_audio_if_needed():
        global file_path
        if file_path.endswith(".mp3") or file_path.endswith(".m4a"):
            try:
                ext = file_path.split(".")[-1]
                audio = AudioSegment.from_file(file_path, format=ext)
                new_file = file_path.replace(f".{ext}", "_converted.wav")
                audio.export(new_file, format="wav")
                file_path = new_file
            except Exception as e:
                output_text.insert(tk.END, f"Conversion Error: {e}\n")

    def process_audio_file():
        global file_path
        if not file_path:
            output_text.insert(tk.END, "No audio file uploaded!\n")
            return
        recognizer = sr.Recognizer()
        try:
            with sr.AudioFile(file_path) as source:
                audio_data = recognizer.record(source)
                recognized_text = recognizer.recognize_google(audio_data)
                input_text.delete("1.0", tk.END)  # Clear previous
                output_text.delete("1.0", tk.END)
                input_text.insert(tk.END, recognized_text + "\n")

                translated = GoogleTranslator(source="auto", target=language_codes.get(output_lang.get(), "en")).translate(recognized_text)
                output_text.insert(tk.END, translated + "\n")
                store_translation(current_user_id, recognized_text, translated)

                speak(translated)
                file_path = ""  # Clear path after processing

        except Exception as e:
            output_text.insert(tk.END, f"Processing Error: {e}\n")

    async def speak_edge(text):
        try:
            lang_code = language_codes.get(output_lang.get(), "en")
            voices = language_voice_map.get(lang_code, language_voice_map["en"])
            voice = voices.get(gender_var.get(), voices["Female"])

            random_suffix = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
            filename = f"output_{random_suffix}.mp3"

            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(filename)

            playsound(filename)

            # Now safe to delete
            os.remove(filename)

        except Exception as e:
            output_text.insert(tk.END, f"TTS Error: {e}\n")

    def speak(text):
        asyncio.run(speak_edge(text))

    def start_translation():
        global keep_running
        keep_running = True
        threading.Thread(target=listen_translate, daemon=True).start()

    def listen_translate():
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)  # Important!
            while keep_running:
                try:
                    output_text.insert(tk.END, "Listening...\n")
                    audio = recognizer.listen(source, timeout=5)
                    recognized = recognizer.recognize_google(audio)
                    
                    input_text.delete("1.0", tk.END)
                    output_text.delete("1.0", tk.END)

                    input_text.insert(tk.END, recognized + "\n")

                    translated = GoogleTranslator(source="auto", target=language_codes.get(output_lang.get(), "en")).translate(recognized)
                    output_text.insert(tk.END, translated + "\n")
                    store_translation(current_user_id, recognized, translated)

                    speak(translated)

                    if recognized.lower() in ["exit", "stop"]:
                        break

                except sr.WaitTimeoutError:
                    output_text.insert(tk.END, "Listening timed out. No speech detected.\n")
                except sr.UnknownValueError:
                    output_text.insert(tk.END, "Could not understand audio.\n")
                except Exception as e:
                    output_text.insert(tk.END, f"Error: {e}\n")


    def stop_translation():
        global keep_running
        keep_running = False

    def open_about():
        webbrowser.open("https://github.com/SamirPaulb/real-time-voice-translator")

    # GUI
    tk.Label(win, text="Recognized Text").pack()
    input_text = tk.Text(win, height=5)
    input_text.pack()

    tk.Label(win, text="Translated Text").pack()
    output_text = tk.Text(win, height=5)
    output_text.pack()

    tk.Label(win, text="Input Language").pack()
    input_lang = ttk.Combobox(win, values=language_names)
    input_lang.set("English")
    input_lang.pack()

    tk.Label(win, text="Output Language").pack()
    output_lang = ttk.Combobox(win, values=language_names)
    output_lang.set("English")
    output_lang.pack()

    tk.Label(win, text="Voice Gender").pack()
    gender_combo = ttk.Combobox(win, textvariable=gender_var, values=["Default", "Female", "Male"])
    gender_combo.pack()

    tk.Button(win, text="Start Listening", command=start_translation).pack(pady=5)
    tk.Button(win, text="Stop Listening", command=stop_translation).pack(pady=5)
    tk.Button(win, text="Upload Audio", command=upload_audio_file).pack(pady=5)
    tk.Button(win, text="Translate Uploaded File", command=process_audio_file).pack(pady=5)
    tk.Button(win, text="About Project", command=open_about).pack(pady=5)
    tk.Button(win, text="View Translation History", command=lambda: show_translation_history(user_id)).pack(pady=5)
    win.mainloop()

# --- Start ---
if __name__ == "__main__":
    init_db()
    show_login()
