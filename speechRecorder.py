import pyaudio
import wave


class SpeechRecorder:
    def __init__(self):
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 16000
        self.chunk = 256
        self.record_seconds = 10
        self.output_filename = 'audio/recording.wav'
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.frames = []

    def start(self):
        self.stream = self.audio.open(format=self.format,
                                      channels=self.channels,
                                      rate=self.rate,
                                      input=True,
                                      frames_per_buffer=self.chunk)

        print('\nRecording...', end=' ')

        for i in range(int(self.rate / self.chunk * self.record_seconds)):
            data = self.stream.read(self.chunk)
            self.frames.append(data)

        print('Done!')

        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()
        self.save()

        return self.output_filename


    def save(self):
        wave_file = wave.open(self.output_filename, 'wb')

        wave_file.setnchannels(self.channels)
        wave_file.setsampwidth(self.audio.get_sample_size(self.format))
        wave_file.setframerate(self.rate)
        wave_file.writeframes(b''.join(self.frames))

        wave_file.close()
