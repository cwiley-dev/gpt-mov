import requests

gpturl = 'https://api.openai.com/v1/chat/completions'
dalleurl = 'https://api.openai.com/v1/images/generations'
openaikey = ''
# get key from openaikey.txt
with open('keys/openaikey.txt', 'r+') as f:
    openaikey = f.readline().strip()

models = ["gpt-3.5-turbo", "gpt-4", "gpt-4-32k"]
use_model = models[0]

# Makes a request to the OpenAI API
# Uses headers:
#   Authorization": "Bearer " + openaikey,
#   "Content-Type": "application/json"
# Returns a string on success, False on failure
def gpt(prompt) -> str | bool:
    headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + openaikey}
    request = {
        "model": use_model,
        "messages": [
            {
                "role": "system",
                "content": prompt
            }
        ]
    }
    print("Sending GPT request...")
    response = requests.post(gpturl, headers=headers, json=request)
    if response.ok:
        print("Got GPT response!")
        return response.json()['choices'][0]['message']['content']
    else:
        print('Error: ' + response.text)
        return False

# Returns a string on success, False on failure
def download_image(url, filename) -> str | bool:
    print("Downloading image...")
    response = requests.get(url)
    if response.ok:
        print("Response OK! Writing to file " + filename + "...")
        with open(filename, 'wb') as file:
            file.write(response.content)
            print('File saved successfully.')
        return filename
    else:
        print('Error: ' + response.text)
        return False

# Returns a string on success, False on failure
def dalle(prompt: str, filepath) -> str | bool:
    headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + openaikey}
    request = {
        "prompt": prompt,
        "n": 1,
        "size": "1024x1024" #256x256, 512x512, or 1024x1024
    }
    print(f"Getting DALL-E image from prompt: {prompt}")
    response = requests.post(dalleurl, headers=headers, json=request)
    if response.ok:
        url = response.json()["data"][0]['url']
        filepath = filepath + ".png"
        img_succ = download_image(url, filepath)
        return filepath if img_succ else False
    else:
        print('Error: ' + response.text)
        return False

# Async versions below

# Returns a string on success, False on failure
async def async_gpt(session, prompt) -> str | bool:
    headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + openaikey}
    request = {
        "model": use_model,
        "messages": [
            {
                "role": "system",
                "content": prompt
            }
        ]
    }
    print("Sending GPT request...")
    async with session.post(gpturl, headers=headers, json=request) as response:
        if response.ok:
            print("Got GPT response!")
            return (await response.json())['choices'][0]['message']['content']
        else:
            error = await response.text()
            # Recurse if failed due to external issue.
            if "That model is currently overloaded with other requests" in error["error"]["message"]:
                return await async_gpt(session, prompt)
            print('GPT Request Error: ' + await response.text())
            return False

# Returns a string on success, False on failure
async def async_download_image(session, url, filename) -> str | bool:
    print("Downloading image...")
    async with session.get(url) as response:
        if response.ok:
            print("Response OK! Writing to file " + filename + "...")
            with open(filename, 'wb') as file:
                file.write(await response.read())
                print('File saved successfully.')
            return filename
        else:
            print('Download Image Error: ' + await response.text())
            return False

# Returns a string on success, False on failure
async def async_dalle(session, prompt: str, filepath) -> str | bool:
    headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + openaikey}
    request = {
        "prompt": prompt,
        "n": 1,
        "size": "1024x1024" #256x256, 512x512, or 1024x1024
    }
    print(f"Getting DALL-E image from prompt: {prompt}")
    async with session.post(dalleurl, headers=headers, json=request) as response:
        if response.ok:
            url = (await response.json())["data"][0]['url']
            filepath = filepath + ".png"
            img_succ = await async_download_image(session, url, filepath)
            return filepath if img_succ else False
        else:
            print('DALL-E Request Error: ' + await response.text())
            return False