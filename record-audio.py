import sounddevice as sd
import soundfile as sf
import numpy as np
from datetime import datetime

def record_speaker_audio(duration=5, sample_rate=44100):
    """
    Record system audio output in chunks of specified duration using MacBook Pro Microphone.
    """
    # List all available devices first
    print("\nAvailable audio devices:")
    print(sd.query_devices())
    
    try:
        # Find MacBook Pro Microphone
        devices = sd.query_devices()
        device_id = None
        for i, device in enumerate(devices):
            if "MacBook Pro Microphone" in device['name']:
                device_id = i
                break
        
        if device_id is None:
            raise ValueError("MacBook Pro Microphone not found")
            
        device_info = sd.query_devices(device_id)
        print(f"\nRecording from device: {device_info['name']}")
        
        while True:
            # Record audio chunk
            recording = sd.rec(
                int(duration * sample_rate),
                samplerate=sample_rate,
                channels=1,  # Microphone typically has 1 channel
                dtype=np.float32,
                device=device_id
            )
            
            # Wait for the recording to complete
            sd.wait()
            
            # Generate timestamp for filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"mic_recording_{timestamp}.wav"
            
            # Save the audio chunk
            sf.write(filename, recording, sample_rate)
            print(f"Saved chunk: {filename}")
            
    except KeyboardInterrupt:
        print("\nRecording stopped by user")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        print("\nAvailable devices:")
        print(sd.query_devices())

if __name__ == "__main__":
    print("Recording speaker output. Press Ctrl+C to stop.")
    record_speaker_audio()