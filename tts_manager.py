from torch.serialization import add_safe_globals
from TTS.tts.models.xtts import XttsAudioConfig  # <-- important: import this exact class
from TTS.api import TTS
import os
import uuid
import librosa
import soundfile as sf
import math



# Register the class globally, once per program run
add_safe_globals([XttsAudioConfig])

tts_model = TTS("tts_models/multilingual/multi-dataset/xtts_v2")

final_output_file = None

def change_pitch(file=None, output_file=None, pitch=1.0):
	if file is None:
		return -1, "You must provide an input file"

	if output_file is None:
		return -1, "You must provide an output file path"

	if not os.path.exists(file):
		return -1, "The input file does not exist"

	y, sr = librosa.load(file, sr=None)

	# Convert pitch factor to semitones
	semitones = 12 * math.log2(pitch)

	# Use keyword arguments (required in librosa >= 1.0)
	y_shifted = librosa.effects.pitch_shift(y=y, sr=sr, n_steps=semitones)

	sf.write(output_file, y_shifted, sr)

	return 0, f"Pitch-shifted audio saved to {output_file}"

def tts(text=None, output_file=None, lang=None, pitch=None, speaker_index=0):
	
	if text == None:
		return -1, "You must provide text to generate speech with"
	
	if output_file == None:
		return -1, "You must provide with an output file path"
	
	if lang == None:
		return -1, "You must provide with a language"	
	#tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
	
#	print(tts_model.speakers)  # List available speakers (voices)
	if pitch != None:	
		final_output_file = output_file
		output_file = str(uuid.uuid4()) + ".wav"
			
	tts_model.tts_to_file(
		text=text,
		speaker=tts_model.speakers[speaker_index],  # pick one speaker
		file_path=output_file,
		language=lang
	)
	
	if pitch != None:
		ref_pitch = 146
		pitch_factor = pitch / ref_pitch
		change_pitch(file=output_file, output_file=final_output_file, pitch=pitch_factor)	
		os.remove(output_file)


def get_speakers():
	return tts_model.speakers
#import asyncio
#import edge_tts
#
#async def list_voices_backend():
#	voices = await edge_tts.list_voices()
#	return voices
#
#def list_voices():	
#	voices = asyncio.run(list_voices_backend())
#	for i in range(len(voices)):
#		del voices[i]["Name"], voices[i]["SuggestedCodec"], voices[i]["Status"], voices[i]["FriendlyName"], voices[i]["VoiceTag"]
#	return voices
