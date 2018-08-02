import uuid
from datetime import *
import random
import os
import sys
import time

def read_base_corpus(base_corpus_file):
    f = open(base_corpus_file, 'r')
    lines = f.readlines()
    f.close()
    return lines

def read_date_corpus(date_corpus_file):
    f = open(date_corpus_file, 'r')
    lines = f.readlines()
    f.close()
    return lines


def suffix(d):
    return 'th' if 11<=d<=13 else {1:'st',2:'nd',3:'rd'}.get(d%10, 'th')

def custom_strftime(format, t):
    return t.strftime(format).replace('{S}', str(t.day) + suffix(t.day))


def generate_date():
    year = random.choice(range(1899, 2019))
    month = random.choice(range(1,13))
    day = random.choice(range(1,29))
    date1 =  date(year, month, day)
    return date1

def generate_random_string():
    x = uuid.uuid4().hex[:10]
    return ' '.join(list(x))

def expand_base_corpus(lines, base_corpus_file):
    f = open(base_corpus_file, 'w').close()
    f = open(base_corpus_file, 'w')
    print("File size : ", len(lines))
    for line in lines:
        words = line.split()
        random_id = generate_random_string()
        words[-1] = random_id
        new_line = " ".join(words)
        f.write(new_line + "\n")
        f.write(line)
    f.close()

def expand_date_corpus(lines, date_corpus_file):
    fd = open(date_corpus_file, 'w').close()
    fd = open(date_corpus_file, 'w')
    for line in lines:
        i = 0
        while i != 1000:
            words = line.split()
            date = generate_date()
            new_date = custom_strftime('%B {S}, %Y', date)
            words[-1] = new_date
            new_line = ' '.join(words)
            fd.write(new_line + "\n")
            i = i + 1
    fd.close()


def main():
    # generate_random_string()
    # for i in range(9):
    #     lines = read_base_corpus('/Users/chrismathew/Desktop/Azure_STT/')
    #     expand_corpus(lines, '/Users/chrismathew/Desktop/')
    if sys.argv[1] == 'd':
        print('hi')
        lines = read_date_corpus('/Users/chrismathew/Desktop/Azure_STT/language_data/date_corpus.txt')
        expand_date_corpus(lines, '/Users/chrismathew/Desktop/Azure_STT/language_data/date_corpus.txt')
    elif sys.argv[1] is 'b':
        print('dick')
        pass
    print('fuckl')




if __name__ == '__main__':
    main()
