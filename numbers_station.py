#!/usr/bin/env python3

import argparse
import contextlib
import glob
import io
import random
import sys
import wave

import ffmpeg


STEREO_BITRATE = 64000


def parse_command_line():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-o", "--output", required=True, help="Output filename. Specify '-' for stdout."
    )
    parser.add_argument(
        "--samples-glob", required=True, help="Glob pattern for selecting sample files."
    )
    parser.add_argument(
        "--silence",
        type=float,
        default=0,
        help="Seconds of silence to add between samples. Defaults to %(default)s.",
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=4,
        help="Number of samples to use. Defaults to %(default)s.",
    )
    parser.add_argument(
        "--opus", action="store_true", help="Encode output with OPUS and mux to OGG."
    )
    return parser.parse_args()


def generate_silence(channels, sampwidth, framerate, duration):
    samples_in_channel = int(framerate * duration)
    bytes_in_channel = samples_in_channel * sampwidth
    total_bytes = bytes_in_channel * channels

    return b"\x00" * total_bytes


def concatenate_wavs(output, *wavs, silence_duration=0):
    with wave.open(wavs[0], mode="rb") as wav_name:
        channels, sampwidth, framerate = wav_name.getparams()[:3]

    for wav_name in wavs:
        with wave.open(wav_name, mode="rb") as wav:
            if wav.getparams()[:3] != (channels, sampwidth, framerate):
                raise ValueError("Parameters mismatch in '{}'".format(wav_name))

    silence = generate_silence(channels, sampwidth, framerate, silence_duration)

    with wave.open(output, mode="wb") as out_wav:
        out_wav.setnchannels(channels)
        out_wav.setsampwidth(sampwidth)
        out_wav.setframerate(framerate)

        for index, wav_name in enumerate(wavs):
            with wave.open(wav_name, mode="rb") as in_wav:
                frames = in_wav.readframes(in_wav.getnframes())
                out_wav.writeframes(frames)
                if index != len(wavs) - 1:
                    out_wav.writeframes(silence)


def get_wave_info(data):
    with io.BytesIO(data) as stream:
        with wave.open(stream, mode="rb") as wav:
            return wav.getparams()


@contextlib.contextmanager
def file_or_stdout(filename):
    if filename == "-":
        yield sys.stdout.buffer
        return

    with open(filename, mode="wb") as outfile:
        yield outfile


def main():
    args = parse_command_line()

    sample_filenames = glob.glob(args.samples_glob, recursive=True)

    chosen_samples = random.choices(sample_filenames, k=args.samples)

    with io.BytesIO() as outstream:
        concatenate_wavs(outstream, *chosen_samples, silence_duration=args.silence)
        result = outstream.getvalue()

    if not args.opus:
        with file_or_stdout(args.output) as outfile:
            outfile.write(result)
        return

    bitrate = STEREO_BITRATE * (get_wave_info(result).nchannels // 2)
    if bitrate < STEREO_BITRATE:
        bitrate = STEREO_BITRATE

    (
        ffmpeg
        .input("pipe:")
        .output(
            args.output,
            acodec="libopus",
            audio_bitrate=bitrate,
            vbr="on",
            compression_level=10,
            format="ogg",
        )
        .overwrite_output()
        .run(input=result)
    )


if __name__ == "__main__":
    sys.exit(main())
