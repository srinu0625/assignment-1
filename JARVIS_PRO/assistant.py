import os
import subprocess
import webbrowser
import datetime
import platform
import shutil

# -----------------------
# OUTPUT
# -----------------------
def speak(text):
    print("AI:", text)

def listen():
    return input("You: ").lower()

# -----------------------
# CORE FUNCTIONS
# -----------------------

def run_cmd(cmd):
    try:
        subprocess.run(cmd, shell=True)
    except:
        speak("Command failed")

def open_any_app(name):
    try:
        subprocess.Popen(name)
        speak(f"Opening {name}")
    except:
        speak("App not found")

def open_path(path):
    if os.path.exists(path):
        os.startfile(path)
    else:
        speak("Path not found")

def list_files(path):
    try:
        files = os.listdir(path)
        for f in files:
            print(f)
    except:
        speak("Cannot access folder")

def create_file(name):
    open(name, "w").close()
    speak("File created")

def delete_file(name):
    if os.path.exists(name):
        os.remove(name)
        speak("File deleted")
    else:
        speak("File not found")

def system_info():
    speak(platform.system())
    speak(platform.version())
    speak(platform.processor())

# -----------------------
# COMMAND ENGINE
# -----------------------

def handle_command(cmd):

    # TIME
    if "time" in cmd:
        speak(datetime.datetime.now().strftime("%I:%M %p"))

    elif "date" in cmd:
        speak(str(datetime.date.today()))

    # OPEN ANYTHING
    elif cmd.startswith("open "):
        target = cmd.replace("open ", "")

        if target.startswith("http"):
            webbrowser.open(target)
        else:
            open_any_app(target)

    # SEARCH
    elif "search" in cmd:
        query = cmd.replace("search", "")
        webbrowser.open(f"https://google.com/search?q={query}")

    # FILE OPERATIONS
    elif "list files" in cmd:
        list_files(os.getcwd())

    elif "create file" in cmd:
        name = cmd.replace("create file", "").strip()
        create_file(name)

    elif "delete file" in cmd:
        name = cmd.replace("delete file", "").strip()
        delete_file(name)

    elif "open folder" in cmd:
        path = cmd.replace("open folder", "").strip()
        open_path(path)

    # SYSTEM CONTROL
    elif "shutdown" in cmd:
        run_cmd("shutdown /s /t 5")

    elif "restart" in cmd:
        run_cmd("shutdown /r /t 5")

    elif "lock" in cmd:
        run_cmd("rundll32.exe user32.dll,LockWorkStation")

    # PROCESS CONTROL
    elif "list processes" in cmd:
        run_cmd("tasklist")

    elif "kill" in cmd:
        proc = cmd.replace("kill", "").strip()
        run_cmd(f"taskkill /f /im {proc}")

    # NETWORK
    elif "ip" in cmd:
        run_cmd("ipconfig")

    elif "wifi off" in cmd:
        run_cmd("netsh interface set interface Wi-Fi disable")

    elif "wifi on" in cmd:
        run_cmd("netsh interface set interface Wi-Fi enable")

    # SYSTEM INFO
    elif "system info" in cmd:
        system_info()

    # CLEAR SCREEN
    elif "clear" in cmd:
        os.system("cls")

    # EXIT
    elif cmd in ["exit", "quit"]:
        speak("Goodbye")
        return False

    else:
        speak("Unknown command")

    return True

# -----------------------
# MAIN LOOP
# -----------------------

speak("System Controller Ready")

running = True
while running:
    command = listen()
    running = handle_command(command)