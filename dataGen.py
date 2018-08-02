import pymedia.audio.acodec as acodec
import pymedia.muxer as muxer
from gtts import gTTS
import os

def read_text_file(file_name):
    f = open(file_name, 'r')
    lines = f.readlines()
    f.close()
    return lines

def generate_audio_files(text_lines):
    i = 1
    for line in text_lines:
        tts = gTTS(text = line, lang='en')
        tts.save("audio/dobby_audio_" + str(i) + ".wav")
        i = i + 1



def main():
    lines = read_text_file('/Users/chrismathew/Desktop/work_test/language_data/dobby_language.txt')
    generate_audio_files(lines)

if __name__ == '__main__':
    main()
