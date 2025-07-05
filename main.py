import argparse
import argostranslate.package
import argostranslate.translate
from subtitle_manager import parse
import ffmpeg
import uuid
from pydub import AudioSegment
from tts_manager import tts, get_voices
from audio_manager import get_pitch, is_same_speaker
import os
import json


def burn_audio(audio_filename=None, video_source=None, video_filename=None):
	if not audio_filename or not video_source or not video_filename:
		raise ValueError("audio_filename, video_source, and video_filename must all be provided")

	video_in = ffmpeg.input(video_source)
	audio_in = ffmpeg.input(audio_filename)

	# Combine streams without manual -map, keep video codec, encode audio as AAC
	ffmpeg.output(
		video_in['v'], audio_in['a'],
		video_filename,
		vcodec='copy',
		acodec='aac',
		strict='experimental'
	).overwrite_output().run()








def reconstruct_audio(audio=None, tts_file_map=None):	
	if audio is None:
		print(-1, "You must provide an AudioSegment object to use as a base")
		return -1
	
	if tts_file_map is None:
		print(-1, "You must provide a tts file map, which has names of tts output files along with timestamps they belong in")
		return -1
	
	print("Reconstruction called")
	for i in range(len(tts_file_map)):
		item = tts_file_map[i]
		filename = list(item.keys())[0]
		timing = item[filename]

		tts_audio = AudioSegment.from_wav(filename)
		start = timing['start']
		stop = timing['stop']

		audio = audio[:start] + tts_audio + audio[stop:]

	return audio


def is_voice_unique(file=None, characters=None):

	if file == None:
		print(-1, "You must provide with a file to compare")

	if characters == None:
		print(-1, "You must provide with a list of unique audio files to compare to")
	for i in range(len(characters)):
		if is_same_speaker(characters[i], file):
			return i
	
	return True

def get_best_voice_from_voices(voices=None, pitch=None):
	if voices == None:
		print(-1, "You must provide a list of dictionaries of voices and pitches")
	
	if pitch == None:
		print(-1, "You must provide a target pitch")
	
	winner_pitch = 0
	winner_index = None
	for i in range(len(voices)):
		if abs(pitch - winner_pitch) > abs(voices[i]["pitch"]):
			#print("Found a new winner with a pitch of", voices[i]["pitch"], "and the target is", pitch)
			winner_pitch = voices[i]["pitch"]
			winner_index = i
		else:
			#print("This pitch", voices[i]["pitch"], "is less close than", winner_pitch)
			pass
	
	return winner_index

def extract_audio(video_path):
	audio_path = str(uuid.uuid4()) + ".wav"
	ffmpeg.input(video_path).output(
		audio_path,	
		format='wav',
		acodec='pcm_s16le',  # WAV codec
		ar='16000',           # sample rate: 16kHz
		ac=1,                 # mono channel
		vn=None               # disable video
	).run(overwrite_output=True, quiet=True)
	
	print("Trying to load:", audio_path)
	print("Size:", os.path.getsize(audio_path), "bytes")
	
	audio = AudioSegment.from_file(audio_path)
	os.remove(audio_path)	

	return audio

def install_package(from_code, to_code):
	argostranslate.package.update_package_index()
	available_packages = argostranslate.package.get_available_packages()

	for package in available_packages:
		if package.from_code == from_code and package.to_code == to_code:
			print(f"Installing translation package: {from_code} -> {to_code}")
			downloaded_path = package.download()
			argostranslate.package.install_from_path(downloaded_path)
			# Refresh languages after install
			argostranslate.translate.load_installed_languages()
			return

	print(f"No package found for {from_code} -> {to_code}")

def main_parser(subs=None, audio=None, tts_lang=None, video_path=None, save_file=True, index=0, voices=get_voices(), characters=[], tts_file_map=[]):
	print("Main video parser called")
	for i in range(index, len(subs)):
		#print(f"Characters list: \n {characters} \n")
		#print(f"Voices list: \n {voices} \n")
		start = subs[i]["timestamps"]["start"]
		stop = subs[i]["timestamps"]["stop"]
		segment = audio[start:stop]
		segment_file = "segment_" + str(i) + ".wav"
		segment.export(segment_file, format="wav")
		print(f"Segment file created: {segment_file}")
		segment_pitch = get_pitch(segment_file)
		print(f"Segment pitch: {segment_pitch}")
		elapsed = (stop - start) / 1000
		tts_output_file = "tts_output_" + str(i) + ".wav"
		if elapsed > 0.5:
			print("Segment is long enough, proceeding")
			is_voice_unique_output = is_voice_unique(file=segment_file, characters=characters)  
			print(f"Voice is unique (int means no): {is_voice_unique_output}")
			if is_voice_unique_output == True:
				characters.append(segment_file)
				print(f"Appended {segment_file} to characters, because it is unique from all other charactors in list")
				voice_to_use = get_best_voice_from_voices(voices=voices, pitch=get_pitch(segment_file))
			else:
				voice_to_use = is_voice_unique_output
				voices.pop(voice_to_use)
	
			tts(
				text=subs[i]["text"], 
				output_file=tts_output_file, 
				lang=tts_lang, 
				speaker_index=voice_to_use
			)
			
			tts_file_map.append({tts_output_file:subs[i]["timestamps"]})	
		else:
			print("Segment too short, skipping and deleteing")

		#print(f"tts_file_map : \n {tts_file_map} \n")	

		if save_file:
			print("Saving progress")
			
			save_dict = {
				"subs" : subs,
				"index" : i,
				"video" : video_path,
				"voices" : voices,
				"tts_file_map" : tts_file_map,
				"tts_lang" : tts_lang,
				"characters" : characters	
			}
		
			with open(f'savefile_{video_path}.json', 'w') as f:
				json.dump(save_dict, f)	
		
			print("Progress saved.")	
	
	print("Done dubbing, removing segment files")	
	for file in os.listdir():
		if "segment_" in file:
			print(f"Removing {file}")
			os.remove(file)
			
	audio_dubbed = reconstruct_audio(audio=audio, tts_file_map=tts_file_map)
	audio_dubbed.export("dubbed_audio.wav", format="wav")	
	
	#input() # acts like a pause for debug
		
	print(f"Burnring audio into dubbed_{video_path}")	
	burn_audio(video_source=video_path, audio_filename="dubbed_audio.wav", video_filename=f"dubbed_{video_path}")

	print("Deleteing dubbed_audio.wav")	
	os.remove("dubbed_audio.wav")
	
	print("Deleting TTS output files")	
	for file in os.listdir():
		if "tts_output_" in file:
			print(f"Removing {file}")
			os.remove(file)

	print("Done")

def main():
	parser = argparse.ArgumentParser(description="Replace subtitle lines with TTS in a video")
	parser.add_argument("-v", "--video", default=None, help="Path to the input video file")
	parser.add_argument("-s", "--subtitles", default=None, help="Path to the subtitle (.srt) file")
	parser.add_argument("--from_lang", default="en", help="Source language code (default: en)")
	parser.add_argument("--to_lang", default="es", help="Target language code (default: es)")
	parser.add_argument( "--save_file", default=None, help="Add a save file to continue without restarting")
	parser.add_argument("--create_save_file", action='store_true', default=False, help="Pass this to create a save file while generating TTS (defaule: False)")	
	args = parser.parse_args()
	video_path = args.video
	subtitles_path = args.subtitles
	from_code = args.from_lang
	to_code = args.to_lang
	
	if not args.save_file and not (args.video and args.subtitles):
		parser.error("Either --save_file or video and subtitles must be provided.")	
	
	if args.save_file:
		if not os.path.exists(args.save_file):
			print("Save file doesnt exist")
			return -1 
		
		print("Save file found, loading")
		with open(args.save_file, 'r') as f:
			save_dict = json.load(f)
			main_parser(
				save_file=args.create_save_file,
				subs=save_dict["subs"], 
				audio=extract_audio(save_dict["video"]), 
				video_path=save_dict["video"], 
				index=save_dict["index"], 
				characters=save_dict["characters"], 
				voices=save_dict["voices"], 
				tts_file_map=save_dict["tts_file_map"], 
				tts_lang=save_dict["tts_lang"]
			)

	print(f"Input video: {video_path}")
	print(f"Subtitle file: {subtitles_path}")
	print(f"Translating from {from_code} to {to_code}")

	install_package(from_code, to_code)

	# Parse subtitles (placeholder)

	print("Parsing and translating subtitles")
	subs = parse(file=subtitles_path, from_lang=from_code, to_lang=to_code)
	
	print("Extracting audio")
	audio = extract_audio(video_path=video_path)
	
	main_parser(save_file=args.create_save_file, subs=subs, audio=audio, tts_lang=to_code, video_path=video_path)	
	
if __name__ == "__main__":
	main()
	#pass
