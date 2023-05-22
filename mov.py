from moviepy.editor import *
import moviepy.video.fx.all as vfx

def add_static_image_to_audio(image_path, audio_path):
    """Create and save a video file to `output_path` after 
    combining a static image that is located in `image_path` 
    with an audio file in `audio_path`"""
    # create the audio clip object
    audio_clip = AudioFileClip(audio_path)
    # create the image clip object
    image_clip = ImageClip(image_path)
    # use set_audio method from image clip to combine the audio with the image
    video_clip = image_clip.set_audio(audio_clip)
    # specify the duration of the new clip to be the duration of the audio clip
    video_clip.duration = audio_clip.duration
    # set the FPS to 1
    video_clip.fps = 5
    # write the resuling video clip
    # video_clip.write_videofile(output_path)
    # return video file
    return video_clip

# ia_tuple = (image_file_name, audio_file_name)
def ia_tuple_to_clip(ia_tuple):
    return add_static_image_to_audio(ia_tuple[0], ia_tuple[1])

def ia_tuple_arr_to_videoclip(ia_tuple_array, output_path):
    clip_array = []
    for ia_tuple in ia_tuple_array:
        clip_array.append(ia_tuple_to_clip(ia_tuple))
    return concatenate_videoclips(clip_array, method='compose')


def generate_n_ia_tuples(n):
    ia_tuple_array = []
    for i in range(n):
        ia_tuple_array.append((f"www/images/{i+1}.jpg", f"www/audio/{i+1}.wav"))
    return ia_tuple_array

def overlay_on_bg(clip, bg_num):
    bg = VideoFileClip("bg/bg" + str(bg_num) +  "_pp.mp4")
    new_clip = CompositeVideoClip([bg, clip.set_position("center")])
    return new_clip.subclip(0, clip.duration)

def overlay_captions(script, clip):
    pass

# output = overlay_on_bg(VideoFileClip("output/1-sneeze.mp4"), 1)
# output.write_videofile("output.mp4")