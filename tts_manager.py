from TTS.api import TTS
from audio_manager import get_pitch
import os
import uuid
import librosa
import soundfile as sf
import math
import json

tts_model = TTS("tts_models/multilingual/multi-dataset/xtts_v2")

final_output_file = None

def tts(text=None, output_file=None, lang=None, pitch=None, speaker_index=5, max_duration=None):
	if text is None:
		return -1, "You must provide text to generate speech with"	
			
	if output_file is None:
		return -1, "You must provide with an output file path"
	
	if lang is None:
		return -1, "You must provide with a language"
	
	global final_output_file
	final_output_file = None

	# Use temp file if pitch or max_duration is specified
	use_temp = (pitch is not None) or (max_duration is not None)
	
	if use_temp:
		final_output_file = output_file
		temp_file = str(uuid.uuid4()) + ".wav"
	else:
		temp_file = output_file
	
	# Generate TTS audio to temp_file
	tts_model.tts_to_file(
		text=text,
		speaker=tts_model.speakers[speaker_index],
		file_path=temp_file,
		language=lang
	)
	
	# Load audio
	y, sr = librosa.load(temp_file, sr=None)
	
	# Speed up if max_duration given and audio too long
	if max_duration is not None:
		curr_duration = librosa.get_duration(y=y, sr=sr)
		if curr_duration > max_duration:
			speed_factor = curr_duration / max_duration
			max_speed = 1.5
			speed_factor = min(speed_factor, max_speed)
			y = librosa.effects.time_stretch(y, rate=speed_factor)

	# Apply pitch shift if pitch given
	if pitch is not None:
		ref_pitch = 146
		pitch_factor = pitch / ref_pitch
		semitones = 12 * math.log2(pitch_factor)
		y = librosa.effects.pitch_shift(y=y, sr=sr, n_steps=semitones)
	
	# Save final output
	sf.write(final_output_file if use_temp else output_file, y, sr)
	
	# Remove temp file if used
	if use_temp and os.path.exists(temp_file):
		os.remove(temp_file)
	
	return 0, f"TTS audio generated and saved to {final_output_file if use_temp else output_file}"


def get_voices():
	if os.path.exists("voices.json"):
		with open("voices.json", "r") as f:
			voices_list = json.load(f) 
			return voices_list
		
	speakers = tts_model.speakers
	voices_list = []
	for i in range(len(speakers)):
		audio_clip = str(uuid.uuid4()) + ".wav" 
		tts(text="Hello, World", speaker_index=i, lang="en", output_file=audio_clip)
		pitch = get_pitch(file=audio_clip)
		name = speakers[i]
		cell = {"name" : name, "pitch" : pitch}
		voices_list.append(cell)
		os.remove(audio_clip)	

	return voices_list
