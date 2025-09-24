import argparse
import argostranslate.package
import argostranslate.translate
from subtitle_manager import parse as subtitle_parse
import ffmpeg
import uuid
import random
from audio_manager import get_pitch
from pydub import AudioSegment
import machine
import os
import json
import string


def random_fldr(length=7):	
	return str().join(random.choices(string.ascii_letters + string.digits, k=length))


def install_package(from_code, to_code):
	argostranslate.package.update_package_index()
	available_packages = argostranslate.package.get_available_packages()

	for package in available_packages:
		if package.from_code == from_code and package.to_code == to_code:
			print(f"[stager] Installing translation package: {from_code} ==> {to_code}")
			downloaded_path = package.download()
			argostranslate.package.install_from_path(downloaded_path)
			# Refresh languages after install
			argostranslate.translate.load_installed_languages()
			return

	print(f"[stager] No package found for {from_code} -> {to_code}")


def main():
	parser = argparse.ArgumentParser(description="Replace subtitle lines with TTS in a video")
	parser.add_argument("-v", "--video", default=None, help="Path to the input video file")
	parser.add_argument("-s", "--subtitles", default=None, help="Path to the subtitle (.srt) file")
	parser.add_argument("--from_lang", default=None, help="Source language code")
	parser.add_argument("--to_lang", default=None, help="Target language code")
	parser.add_argument("--similarity", default=0.30, help="Number of similarity to be considered same speaker (default: 0.30) (may need to adjust per video)")
	parser.add_argument("-p", "--project", default=None, help="Project folder where everything will be or was saved ")
	parser.add_argument("--speakers", default=None, help="Number of known speakes in video file ")
	
	args = parser.parse_args()
	
	if args.project == None:
		print("[stager] Project folder not passed, creating")


		project = random_fldr()
		print(f"[stager] Project folder: {project}")	
		while os.path.exists(project):
			print("[stager] That path already exists, trying again")
			project = random_fldr()
		
		os.mkdir(project)
		print(f"[stager] {project} created")
		
	elif not os.path.exists(args.project):
		print("[stager] This project path doesn't exist, creating")	
		
		os.mkdir(args.project)

		project = args.project
	else:
		print(f"[stager] Found {args.project}")
		
		project = args.project


	if not (args.subtitles or args.video or args.to_lang or args.from_lang) and not os.path.exists(os.path.join(project, "metadata")):
		print("[stager] [ERROR] Metadata doesn't exist, and args not suffiecnt")	
		return -1

		
			
	if args.video and args.subtitles:	
		video_fullpath = os.path.abspath(args.video)
		subtitles_fullpath = os.path.abspath(args.subtitles)

	print(f"[stager] Changing into {project}")
	os.chdir(project)
	
	
	#Loading metadata
	if os.path.exists("metadata"):
		metadata = json.load(open("metadata", "r"))
	else:
		# Saving metadata	
		metadata = {
			"video" : video_fullpath,
			"subtitles_path" : subtitles_fullpath,
			"from_code" : args.from_lang,
			"to_code" : args.to_lang,
			"similarity" : args.similarity,
			"speakers" : args.speakers
		}
		
		json.dump(metadata, open("metadata", "w"))

	#Loading varibles	
	video_path = metadata["video"]
	subtitles_path = metadata["subtitles_path"]
	from_code = metadata["from_code"]	
	to_code = metadata["to_code"]
	similarity = metadata["similarity"]
	speakers = metadata["speakers"]
	
	print(f"[stager] [DEBUG] {metadata}")
	
	#Subtitle stage	

	if not os.path.exists("subtitles.parsed"):
		print("[stager] Could not find parsed subtitles, parsing")
		install_package(from_code, to_code)
		subs = subtitle_parse(file=subtitles_path, from_lang=from_code, to_lang=to_code)
		print("[stager] Parsed subtitles, saving")
		json.dump({"subs" : subs}, open("subtitles.parsed", "w"))
	else:
		print("[stager] Found subtitle parse file, loading")
		subs = json.load(open("subtitles.parsed"))["subs"]
	
	print("[stager] Subtitles loaded")
	
	audio = machine.extract_audio(video_path=video_path)	
	# Segment Stage
	if os.path.exists("stage0.output"):
		print("[stager] Found stage 0 segments, saving")
		segments = json.load(open("stage0.output", "r"))["segments"]
	else:
		print("[stager] Could not find stage 0 segments, running")
		segments = machine.segment_stage(audio=machine.extract_audio(video_path=video_path, clean=True), video_path=video_path, subs=subs)
	
	print("[stager] Got segment files list")
	


	# Voices Stage
	if os.path.exists("stage1.output"):
		print("[stager] Found stage 1 clusters, saving")
		clusters = json.load(open("stage1.output", "r"))["clusters"] 
	else:
		print("[stager] Could not find stage 1 clusters, running")
		clusters = machine.voices_stage(eps=similarity)
	
	print("[stager] Got clusters")
	
	#TTS generation stage

	if os.path.exists("stage2.output"):
		print("[stager] Found stage 2 tts map, saving")
		tts_map = json.load(open("stage2.output", "r"))["tts_map"]
	else:
		print("[stager] Could not find stage 2 output, checking for save")
		if os.path.exists("stage2.json"):
			print("[stager] Found stage2.json, loading")
			save_data = json.load(open("stage2.json", "r"))
			install_package(from_code, to_code)
			tts_map = machine.tts_stage(
				segment_files=segments, 
				subs=subs, 
				clusters=clusters, 
				tts_lang=save_data["tts_lang"], 
				index_i=save_data["index_i"], 
				index_j=save_data["index_j"], 
				voices=save_data["voices"], 
				tts_map=save_data["tts_map"]
			)
		
		else:
			print("[stager] No stage 2 json found, running")
			tts_map = machine.tts_stage(segment_files=segments, subs=subs, clusters=clusters, tts_lang=to_code)	

	print("[stager] Got tts map")
			
	if not os.path.exists("dubbed_audio.wav"):		
		audio = machine.extract_audio(video_path=video_path)
		print("[stager] Could not find dubbed audio, running stage 3 audio glue")
		combined_audio = machine.audio_stage(audio=audio, tts_file_map=tts_map)
	else:
		print("[stager] Found dubbed audio")
		
	print("[stager] Got dubbed audio")
		
	#def burn_audio_stage(audio_filename=None, video_source=None, video_filename=None
	
	if not os.path.exists(f"{video_path}_dubbed.mp4"):
		print("[stager] Could not find output video, creating")
		machine.burn_audio_stage(audio_filename="dubbed_audio.wav", video_source=video_path, video_filename=os.path.join(os.path.dirname(video_path), f"dubbed_{os.path.basename(video_path)}"))
	
	
	print("[stager] All done")
	
if __name__ == "__main__":
	main()
	#pass
