import aiohttp
import gpt
import eleven
import moviepy.editor as mov

import json

image_path = 'images/'
audio_path = 'audio/'
output_path = 'output/'

current_eleven_requests = 0 # max 3 concurrent
max_concurrent_eleven_requests = 3
current_gpt_requests = 0 # max 10? concurrent
max_concurrent_gpt_requests = 3
current_dalle_requests = 0 # max 10? concurrent
max_concurrent_dalle_requests = 3

prompts = {}
try:
    with open('prompts.json', 'r') as f:
        prompts = json.load(f)
except FileNotFoundError:
    print("File not found error: prompts.json")
except json.JSONDecodeError:
    print("JSON parse error: prompts.json")

async def wait_for_eleven_concurrency():
    while current_eleven_requests >= max_concurrent_eleven_requests:
        await asyncio.sleep(1)
    return

async def wait_for_gpt_concurrency():
    while current_gpt_requests >= max_concurrent_gpt_requests:
        await asyncio.sleep(1)
    return

async def wait_for_dalle_concurrency():
    while current_dalle_requests >= max_concurrent_dalle_requests:
        await asyncio.sleep(1)
    return

async def concurrent_tts(session, voiceID, text, filepath):
    global current_eleven_requests
    await wait_for_eleven_concurrency()
    current_eleven_requests += 1
    result = await eleven.async_tts(session, voiceID, text, filepath)
    current_eleven_requests -= 1
    return result

async def concurrent_dalle(session, prompt, filepath):
    global current_dalle_requests
    await wait_for_dalle_concurrency()
    current_dalle_requests += 1
    result = await gpt.async_dalle(session, prompt, filepath)
    current_dalle_requests -= 1
    return result

async def concurrent_gpt(session, prompt):
    global current_gpt_requests
    await wait_for_gpt_concurrency()
    current_gpt_requests += 1
    result = await gpt.async_gpt(session, prompt)
    current_gpt_requests -= 1
    return result

class Segment:
    def __init__(self, index, name):
        self.name = name
        self.index = index;
        self.image_list: list[str] = []
        self.text_list: list[str] = []
        self.audio_list: list[str] = []
        self.image_version = -1
        self.text_version = -1
        self.audio_version = -1
        self.session = None
    
    async def init(self, session, text):
        self.session = session
        self.text_list.append(text)
        self.text_version = 0
        await asyncio.gather(self.new_image(), self.new_audio())
        # await self.new_image()
        # await self.new_audio()
    
    def path(self, ver):
        return self.name + "_" + str(ver)
    
    def change_image_version(self, new_version):
        if 0 <= new_version < len(self.image_list):
            self.image_version = new_version
            return self.image_list[new_version]
        return False

    def change_text_version(self, new_version):
        if 0 <= new_version < len(self.text_list):
            self.text_version = new_version
            return self.text_list[new_version]
        return False
    
    def change_audio_version(self, new_version):
        if 0 <= new_version < len(self.audio_list):
            self.audio_version = new_version
            return self.audio_list[new_version]
        return False

    # Can return false!
    def get_current_image(self):
        if self.image_version < 0:
            return False
        return self.image_list[self.image_version]
    
    def get_current_text(self):
        return self.text_list[self.text_version]
    
    def get_current_audio(self):
        return self.audio_list[self.audio_version]
    
    async def new_image(self, image_prompt=None):
        new_version = len(self.image_list)
        image_prompt = image_prompt or await concurrent_gpt(self.session, prompts['get_image_description'] + self.get_current_text())
        image_prompt = image_prompt or self.get_current_text()
        image_filepath = await concurrent_dalle(self.session, image_prompt, image_path + self.path(new_version))
        if type(image_filepath) == str:
            self.image_list.append(image_filepath)
            self.image_version = new_version
            return image_filepath
        else:
            return False
        
    async def new_audio(self, audio_prompt=None):
        new_version = len(self.audio_list)
        audio_prompt = audio_prompt or self.get_current_text()
        audio_filepath = await concurrent_tts(self.session, eleven.voices['Antoni'], audio_prompt, audio_path + self.path(new_version))
        if type(audio_filepath) == str:
            self.audio_list.append(audio_filepath)
            self.audio_version = new_version
            return audio_filepath
        else:
            return False
    
    async def new_text(self, script=None, text_prompt=None):
        new_version = len(self.text_list)
        if text_prompt is None:
            text_prompt = prompts['regenerate_sentence'][0]
            text_prompt += script
            text_prompt += prompts['regenerate_sentence'][1]
            text_prompt += self.get_current_text()
            text_prompt += prompts['regenerate_sentence'][2]
        text = await concurrent_gpt(self.session, text_prompt)
        if type(text) == str:
            self.text_list.append(text)
            self.text_version = new_version
            return text
        else:
            return False
        
    def get_snapshot(self, iv=None, tv=None, av=None):
        iv = iv or self.image_version
        tv = tv or self.text_version
        av = av or self.audio_version
        return {
            "image": self.image_list[iv],
            "text": self.text_list[tv],
            "audio": self.audio_list[av]
        }
    
    def jsonify(self):
        return_object = {
            "index": self.index,
            "images": {
                "list": self.image_list,
                "current_version": self.image_version
            },
            "text": {
                "list": self.text_list,
                "current_version": self.text_version
            },
            "audio": {
                "list": self.audio_list,
                "current_version": self.audio_version
            }
        }
        return return_object
        
        

class Sequence:
    def __init__(self, project_name):
        self.name = project_name
        self.segments: list[Segment] = []
        self.session = aiohttp.ClientSession()
    
    async def open_session(self):
        self.session = await self.session.__aenter__()
    
    async def close_session(self):
        await self.session.close()
    
    def seg_name(self, segment_number):
        return self.name + "_" + str(segment_number)
    
    async def generate_script_from_subject(self, subject=None):
        prompt = prompts['script_prompt']
        if subject is not None: prompt += "\nWrite the script about " + subject
        return await gpt.async_gpt(self.session, prompt)

    async def generate_sequence_from_subject(self, subject=None):
        script = await self.generate_script_from_subject(subject)
        if type(script) == bool: return False
        return await self.generate_sequence(script)
    
    # Warning: Resets sequence before generating
    async def generate_sequence(self, script: str):
        self.segments = []
        line_number = 0
        coroutines = []
        for line in script.splitlines():
            if line in ['', '\n']: continue
            seg = Segment(line_number, self.seg_name(line_number))
            coroutines.append(seg.init(self.session, line))
            self.add_segment(seg)
            line_number += 1
        await asyncio.gather(*coroutines)
    
    def reindex_segments(self):
        for (i, seg) in enumerate(self.segments):
            seg.index = i
    
    def add_segment(self, segment):
        self.segments.append(segment)
        self.reindex_segments()
     
    def insert_segment(self, segment, index):
        self.segments.insert(index, segment)
        self.reindex_segments()
        
        
    async def generate_insert_segment(self, index):
        script = self.compile_script()
        text_prompt = ''
        if not (0 <= index < len(self.segments)): return False
        elif index == 0:    # beginning
            text_prompt = prompts['generate_sentence_at_beginning'][0]
            text_prompt += script
            text_prompt = prompts['generate_sentence_at_beginning'][1]
        elif index == len(self.segments)-1:    # end
            text_prompt = prompts['generate_sentence_at_end'][0]
            text_prompt += script
            text_prompt = prompts['generate_sentence_at_end'][1]
        else:   # between
            text_prompt = prompts['generate_sentence_between'][0]
            text_prompt += script
            text_prompt += prompts['generate_sentence_between'][1]
            text_prompt += self.segments[index-1].get_current_text()
            text_prompt += prompts['generate_sentence_between'][2]
            text_prompt += self.segments[index+1].get_current_text()
            text_prompt += prompts['generate_sentence_between'][3]
        seg = Segment(index, self.seg_name(index))
        await seg.init(self.session, text_prompt)
        self.insert_segment(seg, index);
    
    def remove_segment(self, index):
        self.segments.pop(index)
    
    def get_segment(self, index):
        return self.segments[index]

    def compile_script(self):
        script = ''
        for seg in self.segments:
            script += seg.get_current_text()
            script += '\n'
        return script
    
    # Future advanced option: "compile audio"
    #   - Generates audio from the compiled script
    #   - Uses some library to get timestamped captions for the audio
    #   - Cuts the audio up into segments based on the timestamps
    #   - Generates the exported video with the cut pieces of audio matched to the images
    # This would make the audio sound more matural, but it would be a lot more work
    def export_video(self, filepath):
        clips = []
        seg_count = 0
        for seg in self.segments:
            audio_clip = mov.AudioFileClip(seg.get_current_audio())
            image_path = seg.get_current_image()
            if image_path is False:
                if seg_count == 0:
                    image_clip = mov.ColorClip(size=(1024, 1024), color=(0, 0, 0))
                else:
                    image_path = self.segments[seg_count-1].get_current_image()
                    image_clip = mov.ImageClip(image_path)
            else:
                image_clip = mov.ImageClip(image_path)
            video_clip = image_clip.set_audio(audio_clip)
            video_clip.duration = audio_clip.duration
            video_clip.fps = 5
            clips.append(video_clip)
            seg_count += 1
        final_clip = mov.concatenate_videoclips(clips, method='compose')
        final_clip.write_videofile(output_path + filepath + ".mp4")
        return output_path + filepath + ".mp4"

async def main():
    seq = Sequence("seq-test");
    await seq.open_session()
    await seq.generate_sequence_from_subject("lettuce")
    seq.export_video("seq-test")
    await seq.close_session()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())