from typing import Annotated, Literal
import httpx
import ormsgpack
from pydantic import BaseModel, conint
import pygame
import os
import threading
import uuid  
import tkinter as tk  
from tkinter import scrolledtext  

DONGXUELIAN = '97fd95a426b44ff2a6731c97b9924824'
DINGZHEN = '54a5170264694bfc8e9ad98df7bd89c3'
GAOYUANHAO = 'f9930dde631741e3ab46904d76e718cd'
BUTCHER = 'f2d3c3f6cf4f4b49bfd52335c2761138'
SUNXIAOCHUAN = 'e80ea225770f42f79d50aa98be3cedfc'
YONGCHUTAFEI = 'e1cfccf59a1c4492b5f51c7c62a8abd2'
MANBO = 'c30c92c9a27d4a8f9b80ba21ca58245d'
ZHOUJIELUN = '1512d05841734931bf905d0520c272b1'
ADXUEJIE = '7f92f8afb8ec43bf81429cc1c9199cb1'
QIHAINANAMI = 'a7725771e0974eb5a9b044ba357f6e13'
# ServeReferenceAudio and ServeTTSRequest remain unchanged
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
    refernce_id = DONGXUELIAN
    request = ServeTTSRequest(
        text=text,
        reference_id= refernce_id,
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
                    "authorization": "Bearer e750df17a2bd4710aa1f890105782790",
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


def create_gui():
    def submit_text(event=None):
        text = text_input.get("1.0", tk.END).strip()  # 获取文本框中的内容
        if text:
            output_box.insert(tk.END, f"Processing: {text}\n")
            start_audio_thread(text)
            text_input.delete("1.0", tk.END)  # 清空输入框

    root = tk.Tk()
    root.title("Text to Speech Processor")
    root.geometry("500x400")

    text_input = scrolledtext.ScrolledText(root, height=5, wrap=tk.WORD)
    text_input.pack(pady=10)
    
    text_input.bind("<Return>", submit_text)

    output_box = scrolledtext.ScrolledText(root, height=10, wrap=tk.WORD, state=tk.DISABLED)
    output_box.pack(pady=10)

    output_box.config(state=tk.NORMAL)

    root.mainloop()


if __name__ == "__main__":
    create_gui()
