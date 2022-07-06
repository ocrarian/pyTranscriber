import multiprocessing
from os import name
from pathlib import Path
from platform import uname
from sys import path
from time import sleep

# Append cli to path

path.insert(0, str(Path(__file__).parent.parent.parent / "autosub_cli"))

from autosub_cli.autosub.api_wit_ai import WITAiAPI
from autosub_cli.autosub.auditok_utils import auditok_gen_speech_regions
from autosub_cli.autosub.cmdline_utils import convert_wav
from autosub_cli.autosub.constants import (
    DEFAULT_AUDIO_CVT_CMD,
    DEFAULT_AUDIO_SPLT_CMD,
    DEFAULT_CONCURRENCY,
    DEFAULT_SUBTITLES_FORMAT,
    WIT_AI_API_URL,
)
from autosub_cli.autosub.core import list_to_sub_str
from autosub_cli.autosub.ffmpeg_utils import SplitIntoAudioPiece
from pytranscriber.util.util import MyUtil

api_url = f"https://{WIT_AI_API_URL}"
api_key = ""

# TODO add settings
# TODO add other languages support


class Ctr_Autosub:
    cancel = False

    @staticmethod
    def init():
        Ctr_Autosub.cancel = False

    @staticmethod
    def is_operation_canceled():
        return Ctr_Autosub.cancel

    @staticmethod
    def output_progress(listener_progress, str_task, progress_percent):
        # only update progress if not requested to cancel
        if not Ctr_Autosub.cancel:
            listener_progress(str_task, progress_percent)

    @staticmethod
    def cancel_operation():
        Ctr_Autosub.cancel = True

        while Ctr_Autosub.step == 0:
            sleep(0.1)

        # the first step involves ffmpeg and cannot be stopped safely
        if Ctr_Autosub.step == 1:
            # close wait for threads to finish their work first
            Ctr_Autosub.pool.close()
            Ctr_Autosub.pool.join()

        else:
            # terminates the threads immediately
            Ctr_Autosub.pool.terminate()
            Ctr_Autosub.pool.join()

    @staticmethod
    def generate_subtitles(  # pylint: disable=too-many-locals,too-many-arguments
        source_path,
        src_language,
        listener_progress,
        output=None,
        concurrency=DEFAULT_CONCURRENCY,
        # subtitle_file_format=DEFAULT_SUBTITLES_FORMAT,
    ):

        # windows not support forkserver... only spawn
        if name != "nt" and "Darwin" in uname():
            # necessary for running on MacOS
            # method can be set only once, otherwise crash
            # from python 3.8 above the default for macos is spawn and not fork
            if "spawn" != multiprocessing.get_start_method(allow_none=True):
                multiprocessing.set_start_method("spawn")
        Ctr_Autosub.cancel = False
        Ctr_Autosub.step = 0
        # Given an input audio/video file, generate subtitles in the specified language and format.
        Ctr_Autosub.output_progress(
            listener_progress, "Step 1 of 4: Converting input file to wav ", 1
        )
        audio_wav = convert_wav(
            input_=source_path,
            conversion_cmd=DEFAULT_AUDIO_CVT_CMD,
        )
        regions = auditok_gen_speech_regions(
            audio_wav=audio_wav, mode=0
        )  # mode=0 => autosub's args.auditok_mode
        if not regions:
            return
        converter = SplitIntoAudioPiece(
            source_path=source_path,
            output=output,
            is_keep=False,
            cmd=DEFAULT_AUDIO_SPLT_CMD.replace("-vn", "-vn -c:a pcm_s16le -f s16le")
            .replace("[channel]", "1")
            .replace("[sample_rate]", "8000"),
            suffix=".pcm",
        )  # TODO allow more values
        recognizer = WITAiAPI(api_url=api_url, api_key=api_key)
        transcripts = []
        try:
            if Ctr_Autosub.cancel:
                return -1
            str_task_1 = "Step 2 of 4: Recognizing speech regions "
            len_regions = len(regions)
            audio_fragments = []
            Ctr_Autosub.pool = multiprocessing.Pool(concurrency)
            for i, audio_fragment in enumerate(
                Ctr_Autosub.pool.imap(converter, regions)
            ):
                Ctr_Autosub.step = 1
                if audio_fragment:
                    audio_fragments.append(audio_fragment)
                progress_percent = MyUtil.percentage(i, len_regions)
                Ctr_Autosub.output_progress(
                    listener_progress, str_task_1, progress_percent
                )
            if not audio_fragments:
                return
            if Ctr_Autosub.cancel:
                return -1
            else:
                Ctr_Autosub.pool.close()
                Ctr_Autosub.pool.join()

            str_task_2 = "Step 3 of 4: Performing speech recognition "
            Ctr_Autosub.pool = multiprocessing.Pool(concurrency)
            for i, transcript in enumerate(
                Ctr_Autosub.pool.imap(recognizer, audio_fragments)
            ):
                Ctr_Autosub.step = 2
                transcripts.append(transcript)
                progress_percent = MyUtil.percentage(i, len_regions)
                Ctr_Autosub.output_progress(
                    listener_progress, str_task_2, progress_percent
                )

            if Ctr_Autosub.cancel:
                return -1
            else:
                Ctr_Autosub.pool.close()
                Ctr_Autosub.pool.join()

        except KeyboardInterrupt:
            Ctr_Autosub.pbar.finish()
            Ctr_Autosub.pool.terminate()
            Ctr_Autosub.pool.join()
            raise

        timed_subtitles = [
            (region, text) for region, text in zip(regions, transcripts) if text
        ]
        subtitle = list_to_sub_str(timed_subtitles)
        output.write_bytes(subtitle.encode("utf-8"))

        if Ctr_Autosub.cancel:
            return -1
        else:
            Ctr_Autosub.pool.close()
            Ctr_Autosub.pool.join()

        return output
