import argostranslate.package
import argostranslate.translate
import time
import srt
import os
import re

def translate_text(text=None, from_lang=None, to_lang=None):
	if not text:
		return -1, "You must provide with input text"
	if not from_lang or not to_lang:
		return text
	# Make sure installed languages are loaded
	argostranslate.translate.load_installed_languages()

	# Translate the text
	translated = argostranslate.translate.translate(text, from_lang, to_lang)
	return translated


def parse(file=None, from_lang=None, to_lang=None):
	if file == None:
		return -1, "Error: no subtitle file provided"

	if not os.path.exists(file):
		return -1, "Error: this subtitle file doesn't exist"
	
	with open(file, "r", encoding="utf-8") as f:
		srt_content = f.read()

	subtitles = list(srt.parse(srt_content))
	subs_as_dicts = []

	for i in range(len(subtitles)):
		time.sleep(0.001)
		sub = subtitles[i]
		clean_text = re.sub(r'\[.*?\]', '', sub.content)
		clean_text = re.sub(r'[\r\n]', '', clean_text)
		clean_text = clean_text.strip()

		if clean_text == '':
			continue

		subs_as_dicts.append({
			"text": translate_text(text=clean_text, from_lang=from_lang, to_lang=to_lang),
			"timestamps": {
				"start": int(sub.start.total_seconds() * 1000),
				"stop": int(sub.end.total_seconds() * 1000)
			}
		})

	return subs_as_dicts

