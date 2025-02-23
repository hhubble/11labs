import asyncio
import io
import logging
import os
import time
from pathlib import Path

import numpy as np
import pyaudio
from pydub import AudioSegment
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from utils.action_handling import ActionHandler
from utils.agent import Agent
from utils.logging_config import setup_logging
from utils.STT_utils import AudioTranscriptionHandler
from utils.TTS_utils import handle_audio_output, handle_audio_to_microphone, stream_to_elevenlabs

# Initialize logging
setup_logging(log_file=Path("logs/meeting_agent.log"), log_level="INFO")
logger = logging.getLogger(__name__)


class MeetingAgent:
    def __init__(self):
        logger.info("Initializing MeetingAgent with audio configuration...")
        # Audio configuration
        self.CHUNK = 4096
        self.FORMAT = pyaudio.paFloat32
        self.CHANNELS = 1
        self.RATE = 16000

        logger.debug(f"Audio config - CHUNK: {self.CHUNK}, FORMAT: {self.FORMAT}, CHANNELS: {self.CHANNELS}, RATE: {self.RATE}")

        # Initialize audio components
        logger.info("Initializing audio components...")
        self.p = pyaudio.PyAudio()
        self.transcription_handler = AudioTranscriptionHandler()
        self.function_caller = Agent()
        self.action_handler = ActionHandler()
        self.driver = None

        logger.info("MeetingAgent initialization completed successfully")

    def setup_chrome(self):
        """Configure and return ChromeDriver with appropriate options"""
        logger.info("Setting up Chrome driver with custom options...")
        options = webdriver.ChromeOptions()

        # Basic Chrome options
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        # Set preferences
        prefs = {
            "profile.default_content_setting_values.media_stream_mic": 1,
            "profile.default_content_setting_values.media_stream_camera": 2,
            "profile.default_content_setting_values.notifications": 2,
        }
        options.add_experimental_option("prefs", prefs)
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        logger.debug("Chrome preferences set: %s", prefs)
        logger.info("Chrome driver setup completed")
        return webdriver.Chrome(options=options)

    async def join_meeting(self, meet_url, email, password):
        """Join Google Meet meeting"""
        try:
            logger.info(f"Attempting to join meeting at URL: {meet_url}")
            logger.info(f"Logging in with email: {email}")
            self.driver = self.setup_chrome()
            wait = WebDriverWait(self.driver, 30)

            logger.info("Navigating to Google sign-in page...")
            self.driver.get("https://accounts.google.com/signin")

            logger.info("Entering email...")
            email_input = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']"))
            )
            email_input.send_keys(email)
            email_input.send_keys(Keys.RETURN)

            logger.info("Entering password...")
            time.sleep(3)
            password_input = wait.until(EC.presence_of_element_located((By.NAME, "Passwd")))
            password_input.send_keys(password)
            password_input.send_keys(Keys.RETURN)

            logger.info("Waiting for login completion...")
            time.sleep(3)

            logger.info(f"Navigating to meeting URL: {meet_url}")
            self.driver.get(meet_url)
            time.sleep(2)

            logger.info("Looking for 'Join now' button...")
            join_button = wait.until(
                EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'Join now')]"))
            )
            join_button.click()

            logger.info("Successfully joined meeting")
            return True

        except Exception as e:
            logger.error(f"Error joining meeting: {str(e)}", exc_info=True)
            if self.driver:
                logger.info("Closing Chrome driver due to error")
                self.driver.quit()
            return False

    def get_input_device(self):
        """Select appropriate audio input device"""
        logger.info("\nAvailable audio input devices:")
        input_device_index = None

        for i in range(self.p.get_device_count()):
            device_info = self.p.get_device_info_by_index(i)
            if device_info["maxInputChannels"] > 0:
                logger.info(f"Index {i}: {device_info['name']}")
                print(f"Index {i}: {device_info['name']}")

                # You might want to adjust this logic based on your preferred input device
                if input_device_index is None:
                    input_device_index = i

        return input_device_index

    async def process_audio(self):
        """Process audio input and handle commands"""
        logger.info("Starting audio processing...")
        input_device_index = self.get_input_device()
        logger.info(f"Selected input device index: {input_device_index}")

        # Add this variable at the start of the method
        previously_sent_context = ""

        try:
            logger.info("Opening audio stream...")
            stream = self.p.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                input_device_index=input_device_index,
                frames_per_buffer=self.CHUNK,
            )
            logger.info("Audio stream opened successfully")
            print("\nListening... (Press Ctrl+C to stop)")

            while True:
                try:
                    logger.debug("Reading audio chunk...")
                    data = stream.read(self.CHUNK, exception_on_overflow=False)
                    audio_data = np.frombuffer(data, dtype=np.float32)
                    audio_data_int16 = (audio_data * 32767).astype(np.int16)
                    audio_bytes = audio_data_int16.tobytes()

                    logger.debug("Processing audio chunk through transcription handler...")
                    is_active, context = await self.transcription_handler.process_audio_chunk(
                        audio_bytes
                    )
                    logger.debug(f"Transcription result: {context}")
                    
                    # Only process if we have context and it's different from the previous one
                    if context and context.strip() != previously_sent_context.strip():
                        logger.info(f"New transcription detected: {context}")
                        previously_sent_context = context

                        logger.info("Calling LLM for response...")
                        response_dict = await self.function_caller.call_llm(context, ["haz@pally.com", "wylansford@gmail.com"])
                        response = response_dict.get("response")
                        taking_action = response_dict.get("taking_action")
                        more_info_required = response_dict.get("more_info_required")
                        
                        logger.info(f"LLM Response: {response}")
                        logger.debug(f"Taking action: {taking_action}, More info required: {more_info_required}")

                        if response:
                            logger.info("Generating audio response...")
                            audio_data = await stream_to_elevenlabs(response)
                            logger.info("Playing audio response...")
                            await handle_audio_output(audio_data, output_mode="speak")

                        print(f"\n💬 Response: {response}")

                        logger.debug("Resetting listening state...")
                        self.transcription_handler.reset_listening_state()

                    await asyncio.sleep(0.01)

                except IOError as e:
                    logger.error(f"IOError during audio processing: {str(e)}", exc_info=True)
                    break

        except KeyboardInterrupt:
            logger.info("Keyboard interrupt detected, stopping audio capture...")
        finally:
            logger.info("Closing audio stream...")
            stream.stop_stream()
            stream.close()

    async def cleanup(self):
        """Cleanup resources"""
        logger.info("Starting cleanup process...")
        try:
            logger.info("Closing transcription handler...")
            await self.transcription_handler.close()
            if self.p:
                logger.info("Terminating PyAudio...")
                self.p.terminate()
            if self.driver:
                logger.info("Closing Chrome driver...")
                self.driver.quit()
            logger.info("Cleanup completed successfully")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}", exc_info=True)


async def main():
    logger.info("Starting main process...")
    agent = MeetingAgent()
    try:
        meet_url = "https://meet.google.com/fbb-gsfv-osg?authuser=0"
        email = "elevenlabsagent@gmail.com"
        password = os.environ.get("GOOGLE_PASSWORD")
        
        logger.info("Attempting to join meeting...")
        if await agent.join_meeting(meet_url, email, password):
            logger.info("Successfully joined meeting, starting audio processing...")
            await agent.process_audio()
        else:
            logger.error("Failed to join meeting")
    except Exception as e:
        logger.exception("Critical error in main process")
    finally:
        logger.info("Starting cleanup process...")
        await agent.cleanup()


import litellm

# async def generate_email_summary(transcript, action_items):
#     litellm.completion(
#         model="groq/llama-3.3-70b-versatile",
#         messages=[{"role": "user", "content": f"Summary: {summary}\nAction Items: {action_items}"}],
#     )


if __name__ == "__main__":
    print("\nStarting Meeting Agent...")
    print("Press Ctrl+C to stop\n")
    asyncio.run(main())
