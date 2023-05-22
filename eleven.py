import requests

voicesURL = 'https://api.elevenlabs.io/v1/voices'
ttsURL = 'https://api.elevenlabs.io/v1/text-to-speech/'
elevenkey = ''
# get key from elevenkey.txt
with open('keys/elevenkey.txt', 'r+') as f:
    elevenkey = f.readline().strip()

# Returns a string on success, False on failure
def request_voice_list() -> str | bool:
    headers = {
        'Content-Type': 'application/json',
        'xi-api-key': elevenkey
    }
    response = requests.get(voicesURL, headers=headers)
    if response.ok:
        return response.json()['voices']
    else:
        print('Error: ' + response.text)
        return False

# Returns a string on success, False on failure
def tts(voiceID, text, filepath) -> str | bool:
    print("Fetching tts...")
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        'xi-api-key': elevenkey
    }
    data = {
        "text": text,
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0
        }
    }
    response = requests.post(ttsURL + voiceID, headers=headers, json=data)
    if response.ok:
        filepath = filepath + '.mp3'
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        print("File created! (?) " + filepath)
        return filepath
    else:
        print('Error: ' + response.text)
        return False
    # if response.ok:
    #     print("Response OK! Writing to file " + filename + ".mp3...")
    #     with open(filename + '.mp3', 'wb') as file:
    #         file.write(response.content)
    #         print('File saved successfully.')
    # else:
    #     print('Error: ' + response.text)
# voices = request_voice_list()
# for voice in voices:
#     print(f"{voice['voice_id']}: {voice['name']}")


voices = {
    "Rachel": "21m00Tcm4TlvDq8ikWAM",
    "Domi": "AZnzlk1XvdvUeBnXmlld",
    "Bella": "EXAVITQu4vr4xnSDxMaL",
    "Antoni": "ErXwobaYiN019PkySvjV",
    "Elli": "MF3mGyEYCl7XYWbV9V6O",
    "Josh": "TxGEqnHWrfWFTfGW9XjX",
    "Arnold": "VR6AewLTigWG4xSOukaG",
    "Adam": "pNInz6obpgDQGcFmaJgB",
    "Sam": "yoZ06aMxZJJ28mfd3POQ",
    "kiwi historio": "5Yi1qKBaQH9k2LxPy9U5",
    "Luddy": "GhsUqu2Ut3upfgNa579f",
    "Explano": "gg15OiMVm7XQFCA9VB58"
}

def generate_test_list():
    for voice in voices.items():
        tts(voice[1], "Hello! This is a test.", "audio/" + voice[0])


# Async below

# Returns a string on success, False on failure
async def async_request_voice_list(session) -> str | bool:
    headers = {
        'Content-Type': 'application/json',
        'xi-api-key': elevenkey
    }
    # response = requests.get(voicesURL, headers=headers)
    async with session.get(voicesURL, headers=headers) as response:
        if response.ok:
            return (await response.json())['voices']
        else:
            print('Error: ' + await response.text())
            return False

# Returns a string on success, False on failure
async def async_tts(session, voiceID, text, filepath) -> str | bool:
    print("Fetching tts...")
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        'xi-api-key': elevenkey
    }
    data = {
        "text": text,
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0
        }
    }
    async with session.post(ttsURL + voiceID, headers=headers, json=data) as response:
        if response.ok:
            filepath = filepath + '.mp3'
            with open(filepath, 'wb') as f:
                async for chunk in response.content.iter_chunked(4096):
                    f.write(chunk)
            print("File created! (?) " + filepath)
            return filepath
        else:
            print('TTS Error: ' + await response.text())
            return False


# Quick test

# import aiohttp
# import asyncio
# async def main():
#     async with aiohttp.ClientSession() as session:
#         await async_tts(session, voices["Antoni"], "Hello! This is not a test, funny guy.", "audio/test_download")

# if __name__ == "__main__":
#     import asyncio
#     asyncio.run(main())