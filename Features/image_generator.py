import asyncio
from random import randint
from PIL import Image
import requests
from dotenv import get_key
import os
from TextToSpeech.Fast_DF_TTS import speak

API_URL = "https://router.huggingface.co/hf-inference/models/runwayml/stable-diffusion-v1-5"

headers = {
    "Authorization": f"Bearer {get_key('.env', 'HuggingFaceAPIKey')}",
    "Content-Type": "application/json"
}

if not os.path.exists("image_storage"):
    os.makedirs("image_storage")


async def query(payload):
    response = await asyncio.to_thread(
        requests.post,
        API_URL,
        headers=headers,
        json=payload
    )

    print("Status Code:", response.status_code)

    if response.status_code != 200:
        print("Error Response:", response.text)
        return None

    # Check if response is actually image
    if "image" not in response.headers.get("content-type", ""):
        print("Not an image! Response was:", response.text)
        return None

    return response.content


async def generate_images(prompt: str):
    tasks = []

    for i in range(4):
        seed = randint(0, 1000000)

        payload = {
            "inputs": f"{prompt}, ultra high detail, 4k, seed={seed}"
        }

        tasks.append(asyncio.create_task(query(payload)))

    responses = await asyncio.gather(*tasks)

    for i, content in enumerate(responses):
        if content:
            with open(f"Data/{prompt.replace(' ', '_')}{i+1}.jpg", "wb") as f:
                f.write(content)

    return True


def GenerateImages(prompt: str):
    asyncio.run(generate_images(prompt))
    speak("Boss, the task is complete. Your image has been successfully created.")
