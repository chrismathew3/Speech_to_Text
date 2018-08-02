import os
import sys
import json
import uuid
import asyncio
import requests
import platform
import websockets

import utils
from speechRecorder import SpeechRecorder

endpoints_ws = {'interactive':'wss://westus.stt.speech.microsoft.com/speech/recognition/interactive/cognitiveservices/v1?cid=3513552d-299d-4592-a646-4caa737f221c',
                'conversation':'wss://westus.stt.speech.microsoft.com/speech/recognition/conversation/cognitiveservices/v1?cid=3513552d-299d-4592-a646-4caa737f221c',
                'dictation':'wss://westus.stt.speech.microsoft.com/speech/recognition/dictation/cognitiveservices/v1?cid=3513552d-299d-4592-a646-4caa737f221c'
                }

class SpeechClient:

    def __init__(self):
        self.sub_key = 'e081fbf02ad142749dde190704eb360e'
        self.api_key = 'evsfWXvspGDzyUI69JFthcqKpwGxxuDh99wWREAbeKs='
        self.uuid = str(uuid.uuid4()).replace('-', '')
        self.connection_id = str(uuid.uuid4()).replace('-', '')
        self.request_id = str(uuid.uuid4()).replace('-', '')
        self.auth_token = utils.obtain_auth_token(self.sub_key)
        self.acoustical_mode = 'Universal'
        self.region = 'westus'
        self.chunk_size = 8192
        self.turns = 0
        self.language = None
        self.response_format = 'simple'
        self.recognition_mode = None
        self.endpoint_url = None
        self.num_turns = 0
        self.is_ongoing_turn = False
        self.cur_hypothesis = ''
        self.phrase = ''
        self.received_messages = []
        self.metrics = []
        self.ws = None

    def setup(self, lang, recognition):
        self.language = str(lang)
        self.recognition_mode = str(recognition)

    async def connectAPI(self):
        endpoint = endpoints_ws[self.recognition_mode]
        url = endpoint
        headers = {
            'Authorization': 'Bearer ' + self.auth_token,
            'X-ConnectionId': self.connection_id
        }

        self.metrics.append({
            'Name': 'Connection',
            'Id': self.connection_id,
            'Start': utils.generate_timestamp()
        })

        try:
            self.ws = await websockets.client.connect(url, extra_headers=headers)
        except websockets.exceptions.InvalidHandshake as err:
            print('Handshake error: {0}'.format(err))
            return

        self.metrics[-1]['End'] = utils.generate_timestamp()
        await self.sendSpeechConfig()

    async def sendSpeechConfig(self):
        context = {
            'system': {
                'version': '5.4'
            },
            'os': {
                'platform': platform.system(),
                'name': platform.system() + ' ' + platform.version(),
                'version': platform.version()
            },
            'device': {
                'manufacturer': 'SpeechSample',
                'model': 'SpeechSample',
                'version': '1.0.00000'
            }
        }
        payload = {'context': context}

        msg = 'Path: speech.config\r\n'
        msg += 'Content-Type: application/json; charset=utf-8\r\n'
        msg += 'X-Timestamp: ' + utils.generate_timestamp() + '\r\n'
        msg += '\r\n' + json.dumps(payload, indent=2)

        await self.ws.send(msg)

    async def speechToText(self, audio_file_path):
        sending_task = asyncio.ensure_future(self.sendAudio(audio_file_path))
        receiving_task = asyncio.ensure_future(self.processResponse())

        await asyncio.wait(
            [sending_task, receiving_task],
            return_when=asyncio.ALL_COMPLETED,
        )

        return self.phrase

    async def sendAudio(self, audio_file_path):
        with open(audio_file_path, 'rb') as f_audio:
            num_chunks = 0
            while True:
                audio_chunk = f_audio.read(self.chunk_size)
                if not audio_chunk:
                    break
                num_chunks += 1

                msg = b'Path: audio\r\n'
                msg += b'Content-Type: audio/x-wav\r\n'
                msg += b'X-RequestId: ' + bytearray(self.request_id, 'ascii') + b'\r\n'
                msg += b'X-Timestamp: ' + bytearray(utils.generate_timestamp(), 'ascii') + b'\r\n'
                msg = len(msg).to_bytes(2, byteorder='big') + msg
                msg += b'\r\n' + audio_chunk

                try:
                    await self.ws.send(msg)
                except websockets.exceptions.ConnectionClosed as e:
                    print('Connection closed: {0}'.format(e))
                    return

    async def sendTelemetry(self, is_first_turn=False):
        payload = {
            'ReceivedMessages': self.received_messages
        }
        if is_first_turn:
            payload['Metrics'] = self.metrics

        msg = 'Path: telemetry\r\n'
        msg += 'Content-Type: application/json; charset=utf-8\r\n'
        msg += 'X-RequestId: ' + self.request_id + '\r\n'
        msg += 'X-Timestamp: ' + utils.generate_timestamp() + '\r\n'
        msg += '\r\n' + json.dumps(payload, indent=2)

        try:
            await self.ws.send(msg)
        except websockets.exceptions.ConnectionClosed as e:
            print('Connection closed: {0}'.format(e))
            return


    async def processResponse(self):
        while True:
            try:
                response = await self.ws.recv()
            except websockets.exceptions.ConnectionClosed as e:
                print('Connection closed: {0}'.format(e))
                return

            response_path = utils.parse_header_value(response, 'Path')
            if response_path is None:
                print('Error: invalid response header.')
                return

            self.recordTelemetry(response_path)

            if response_path == 'turn.start':
                self.is_ongoing_turn = True
                self.num_turns += 1
            elif response_path == 'speech.startDetected':
                pass
            elif response_path == 'speech.hypothesis':
                response_dict = utils.parse_body_json(response)
                if response_dict is None:
                    print('Error: no body found in the response.')
                    return
                if 'Text' not in response_dict:
                    print('Error: unexpected response header.')
                    return
                self.cur_hypothesis = response_dict['Text']
                print('Current hypothesis: ' + self.cur_hypothesis)
            elif response_path == 'speech.phrase':
                response_dict = utils.parse_body_json(response)
                if response_dict is None:
                    print('Error: no body found in the response.')
                    return
                if 'RecognitionStatus' not in response_dict:
                    print('Error: unexpected response header.')
                    return
                if response_dict['RecognitionStatus'] == 'Success':
                    if self.response_format == 'simple':
                        if 'DisplayText' not in response_dict:
                            print('Error: unexpected response header.')
                            return
                        self.phrase = response_dict['DisplayText']
                    else:
                        print('Error: unexpected response format.')
                        return
            elif response_path == 'speech.endDetected':
                pass
            elif response_path == 'turn.end':
                self.is_ongoing_turn = False
                break
            else:
                print('Error: unexpected response type (Path header).')
                return

        await self.sendTelemetry(is_first_turn=(self.num_turns == 1))

    def recordTelemetry(self, response_path):
        if response_path not in [next(iter(msg.keys())) for msg in self.received_messages]:
            self.received_messages.append({
                response_path: utils.generate_timestamp()
            })
        else:
            for i, msg in enumerate(self.received_messages):
                if next(iter(msg.keys())) == response_path:
                    if not isinstance(msg[response_path], list):
                        self.received_messages[i][response_path] = [msg[response_path]]
                    self.received_messages[i][response_path].append(utils.generate_timestamp())
                    break

    async def disconnect(self):
        await self.ws.close()
def main():
    if len(sys.argv) < 3:
        print('Please, provide the following arguments, and try again:')
        print('\t-> Language (e.g. en-US)') #1
        print('\t-> Recognition mode [interactive/conversation/dictation]') #2
        exit()

    client = SpeechClient()
    client.setup(sys.argv[1], sys.argv[2])

    print("Okay now speak.\n")

    rec = SpeechRecorder()
    audio_file_path = rec.start()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(client.connectAPI())
    output = loop.run_until_complete(client.speechToText(audio_file_path))

    if output != '':
        print('\n>> Recognized phrase: ' + output + '\n')
    else:
        print('\n>> Sorry, we were unable to recognize the utterance.\n')

    loop.run_until_complete(client.disconnect())
    loop.close()

if __name__ == '__main__':
    main()
