import os
import threading
import time
import wave
from datetime import datetime

import numpy as np
import pyaudio
import soundcard as sc
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# Update audio recording configuration
CHUNK = 1024
FORMAT = pyaudio.paFloat32  # This can be removed since we're using soundcard
CHANNELS = 2
RATE = 44100
RECORD_SECONDS = 5
RECORDINGS_DIR = "meeting_recordings"


# Selenium Setup
def join_google_meet(meet_url):
    try:
        print("Setting up Chrome options...")
        options = webdriver.ChromeOptions()

        # Basic Chrome options
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        # Set basic preferences
        prefs = {
            "profile.default_content_setting_values.media_stream_mic": 1,  # 1:allow, 2:block
            "profile.default_content_setting_values.media_stream_camera": 2,  # 1:allow, 2:block
            "profile.default_content_setting_values.notifications": 2,
            "browser.custom_chrome_frame": True,
        }
        options.add_experimental_option("prefs", prefs)
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )

        print("Launching Chrome browser...")
        driver = webdriver.Chrome(options=options)
        driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        # First sign into Google
        print("Navigating to Google sign-in page...")
        driver.get("https://accounts.google.com/signin")
        wait = WebDriverWait(driver, 30)

        # Enter email
        print("Waiting for email input field...")
        email_input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']"))
        )
        print("Entering email address...")
        email_input.send_keys("londonfounderhouse@gmail.com")
        time.sleep(2)  # Wait a bit before hitting enter
        print("Submitting email...")
        email_input.send_keys(Keys.RETURN)

        # Wait and enter password
        print("Waiting for password input field...")
        time.sleep(3)  # Give more time for the password page to load
        password_input = wait.until(EC.presence_of_element_located((By.NAME, "Passwd")))
        print("Entering password...")
        password_input.send_keys("UnicornsOnly_999")
        time.sleep(2)  # Wait a bit before hitting enter
        print("Submitting password...")
        password_input.send_keys(Keys.RETURN)

        print("Waiting for login to complete...")
        time.sleep(5)

        # Now join the meeting
        print(f"Navigating to Google Meet URL: {meet_url}")
        driver.get(meet_url)
        time.sleep(2)  # Wait for initial load

        # Continue with joining the meeting
        join_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'Join now')]"))
        )
        join_button.click()

        print("Bot waiting to be admitted to the meeting...")

        # After joining the meeting, start recording
        print("Creating recording thread...")
        stop_recording = threading.Event()
        recording_thread = threading.Thread(target=record_audio, args=(stop_recording,))
        print("Starting recording thread...")
        recording_thread.start()
        print("Recording thread started successfully")

        # Store the recording control in the driver object
        driver.stop_recording = stop_recording
        driver.recording_thread = recording_thread

        return driver
    except Exception as e:
        print(f"Error in join_google_meet: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        if "driver" in locals():
            print("Closing browser due to error...")
            driver.quit()
        return None


def get_timestamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def save_audio_chunk(frames, chunk_number):
    try:
        if not os.path.exists(RECORDINGS_DIR):
            print(f"Creating directory: {RECORDINGS_DIR}")
            os.makedirs(RECORDINGS_DIR)

        filename = os.path.join(RECORDINGS_DIR, f"meeting_chunk_{get_timestamp()}.wav")
        print(f"Attempting to save file: {filename}")

        # Convert float32 array to int16 for WAV file
        wav_data = (frames * 32767).astype(np.int16)

        with wave.open(filename, "wb") as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(2)  # 2 bytes for int16
            wf.setframerate(RATE)
            wf.writeframes(wav_data.tobytes())

        print(f"Successfully saved chunk {chunk_number} to {filename}")
    except Exception as e:
        print(f"Error saving audio chunk: {str(e)}")


def record_audio(stop_event):
    try:
        # Get default system speakers for loopback recording
        speakers = sc.default_speaker()
        print(f"\nRecording from system speakers: {speakers.name}")

        chunk_number = 1
        print("Started recording...")

        # Create a recorder for loopback recording from the speakers
        with speakers.recorder(samplerate=RATE) as mic:
            while not stop_event.is_set():
                print(f"Recording chunk {chunk_number}...")
                # Record directly without intermediate frames list
                data = mic.record(numframes=int(RATE * RECORD_SECONDS))
                if data is not None and len(data) > 0:
                    print(f"Chunk {chunk_number} recorded, saving...")
                    save_audio_chunk(data, chunk_number)
                    chunk_number += 1

        print("Recording stopped")

    except Exception as e:
        print(f"Error in record_audio: {str(e)}")
        print(f"Error type: {type(e).__name__}")


if __name__ == "__main__":
    # Create recordings directory at startup
    if not os.path.exists(RECORDINGS_DIR):
        print(f"Creating recordings directory: {RECORDINGS_DIR}")
        os.makedirs(RECORDINGS_DIR)

    meet_url = "https://meet.google.com/hwi-ehah-ota"

    try:
        print("Starting meeting bot...")
        driver = join_google_meet(meet_url)

        if driver:
            print("Successfully joined meeting. Recording will be saved in chunks.")
            print(f"Recordings will be saved to: {os.path.abspath(RECORDINGS_DIR)}")
            print("Press Ctrl+C to stop recording and exit.")

            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nReceived stop signal. Cleaning up...")

    except Exception as e:
        print(f"An error occurred in main: {str(e)}")

    finally:
        if "driver" in locals() and driver:
            if hasattr(driver, "stop_recording"):
                print("Stopping audio recording...")
                driver.stop_recording.set()
                print("Waiting for recording thread to finish...")
                driver.recording_thread.join()
            print("Closing browser...")
            driver.quit()
