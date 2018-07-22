#!/usr/bin/env python3

import argparse
import os
import sys

from google.cloud import texttospeech


def parse_command_line():
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--output-dir", required=True)
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--end", type=int, default=100)
    parser.add_argument("--language-code", default="en-US")
    parser.add_argument("--voice", default="en-US-Wavenet-E")
    return parser.parse_args()


def synthesize_audio(text, language_code, voice):
    """Synthesizes speech from the input string of text."""
    client = texttospeech.TextToSpeechClient()

    input_text = texttospeech.types.SynthesisInput(text=text)

    voice = texttospeech.types.VoiceSelectionParams(
        language_code=language_code,
        name=voice)

    audio_config = texttospeech.types.AudioConfig(
        audio_encoding=texttospeech.enums.AudioEncoding.LINEAR16)

    response = client.synthesize_speech(input_text, voice, audio_config)

    return response.audio_content


def main():
    args = parse_command_line()

    os.makedirs(args.output_dir)

    for number in range(args.start, args.end + 1):
        audio = synthesize_audio(str(number), args.language_code, args.voice)
        filename = os.path.join(args.output_dir, "{}.wav".format(number))
        with open(filename, mode="wb") as outfile:
            outfile.write(audio)
        print('Audio content written to file "{}"'.format(filename))


if __name__ == "__main__":
    sys.exit(main())
