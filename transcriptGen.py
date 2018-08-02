def read_text_file(file_name, transcript_name):
    #Open corpus
    f = open(file_name, 'r')
    lines = f.readlines()
    #Create new
    t = open(transcript_name, 'w')
    i = 1
    for line in lines:
        t.write("dobby_audio_" + str(i) + ".wav" + "\t" + line)
        i = i + 1
    f.close()
    t.close()

def main():
    read_text_file('language_data/dobby_language.txt', 'language_data/transcription.tsv')

if __name__ == '__main__':
    main()
