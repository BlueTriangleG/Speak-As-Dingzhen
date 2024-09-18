from typing import Annotated, Literal
import httpx
import ormsgpack
from pydantic import BaseModel, conint
from pydub import AudioSegment
import pygame
import os
import threading
import uuid  


class ServeReferenceAudio(BaseModel):
    audio: bytes
    text: str


class ServeTTSRequest(BaseModel):
    text: str
    chunk_length: Annotated[int, conint(ge=100, le=300, strict=True)] = 200
    format: Literal["wav", "pcm", "mp3"] = "mp3"
    mp3_bitrate: Literal[64, 128, 192] = 128
    references: list[ServeReferenceAudio] = []
    reference_id: str | None = None
    normalize: bool = True
    latency: Literal["normal", "balanced"] = "normal"


def get_and_play_audio(text):
    request = ServeTTSRequest(
        text=text,
        reference_id='54a5170264694bfc8e9ad98df7bd89c3',
        references=[
            ServeReferenceAudio(
                audio=open("lengyue.wav", "rb").read(),
                text="Text in reference AUDIO",
            )
        ],
    )

    try:
        audio_file = f"{uuid.uuid4()}.mp3"
        with (
            httpx.Client() as client,
            open(audio_file, "wb") as f,
        ):
            with client.stream(
                "POST",
                "https://api.fish.audio/v1/tts",
                content=ormsgpack.packb(request, option=ormsgpack.OPT_SERIALIZE_PYDANTIC),
                headers={
                    "authorization": "Bearer <API_KEY>",
                    "content-type": "application/msgpack",
                },
                timeout=None,
            ) as response:
                if response.status_code != 200:
                    print(f"Error: Received status code {response.status_code}")
                    return
                for chunk in response.iter_bytes():
                    f.write(chunk)

        # Ensure the file exists and has content
        if not os.path.exists(audio_file) or os.path.getsize(audio_file) == 0:
            print("Error: The audio file was not created correctly or is empty.")
            return

        # Play the audio after writing
        play_audio(audio_file)
    
    except Exception as e:
        print(f"An error occurred: {e}")


def play_audio(file_path):
    try:
        # Initialize pygame mixer with specific parameters
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

        # Load and play the mp3 file using pygame
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()

        # Wait for the music to finish playing
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
    
    except Exception as e:
        print(f"An error occurred while playing the audio: {e}")
    finally:
        os.remove(file_path)  # Clean up the file after playback


def start_audio_thread(text):
    # Create a new thread for each audio request and start it
    threading.Thread(target=get_and_play_audio, args=(text,), daemon=True).start()


if __name__ == "__main__":
    while True:
        text = input("Enter text: ")
        try:
            # Start a new thread for each text input
            start_audio_thread(text)
        except Exception as e:
            print(f"An error occurred after submitting the audio request: {e}")
