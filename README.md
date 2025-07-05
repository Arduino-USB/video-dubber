# Video Dudder Software Using TTS

A tool to dub videos using text-to-speech (TTS) from subtitle files, with optional save file support for stopping and resuming.

## Getting started 

Clone the repository: 

```bash
git clone https://github.com/Arduino-USB/video-dubber 
```
Change into the project directory: 

```bash
cd video-dubber
```
 Install the required Python packages: 
```bash
pip install -r requirements.txt 
```
Run the main script with your desired arguments:
```bash
 python main.py [ARGS] 
```
## Usage Examples 

Use a save file and keep updating it: 
``` bash
python main.py --save_file save_file_name.json --create_save_file
```

Dub a video without creating a save file: 
```bash
python main.py -v video.mp4 -s subtitles.srt 
```
Dub a video from scratch and create a save file: 
```bash
python main.py -v video.mp4 -s subtitles.srt --create_save_file
```
## About Save Files 

Save files allow you to stop and resume the dubbing process without starting over. This is especially handy for longer videos or if you need to pause your work. 

## Arguments Summary
	```bash 
	-v, --video: Input video file to dub.
	-s, --subtitles: Subtitle file to use for dubbing. 
	--save_file: Path to a JSON save file to load/save progress. 
	--create_save_file: Create or update the save file during dubbing.
	```
