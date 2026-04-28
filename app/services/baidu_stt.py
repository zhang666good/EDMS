from __future__ import annotations

import base64
import io
import json
import os
import wave
from dataclasses import dataclass
from typing import Any, Optional
from urllib import error as urllib_error
from urllib import parse as urllib_parse
from urllib import request as urllib_request

import numpy as np
from scipy import signal


@dataclass
class BaiduSpeechToTextError(Exception):
    """Raised when Baidu STT API returns an error or cannot be reached."""

    status_code: int
    message: str
    detail: Any = None


class BaiduSpeechToTextClient:
    """Client wrapper for Baidu speech-to-text REST APIs."""

    TOKEN_URL = "https://aip.baidubce.com/oauth/2.0/token"
    STT_URL = "https://vop.baidu.com/server_api"

    _MIME_TO_FORMAT = {
        "audio/wav": "wav",
        "audio/x-wav": "wav",
        "audio/wave": "wav",
        "audio/pcm": "pcm",
        "audio/L16": "pcm",
        "audio/mp3": "mp3",
        "audio/mpeg": "mp3",
        "audio/mpga": "mp3",
        "audio/amr": "amr",
        "audio/m4a": "m4a",
        "audio/x-m4a": "m4a",
    }

    _EXT_TO_FORMAT = {
        "wav": "wav",
        "pcm": "pcm",
        "mp3": "mp3",
        "mpeg": "mp3",
        "mpga": "mp3",
        "amr": "amr",
        "m4a": "m4a",
    }

    def __init__(
            self,
            api_key: str,
            secret_key: str,
            *,
            timeout: int = 30,
            default_rate: int = 16000,
            default_channel: int = 1,
    ) -> None:
        self.api_key = api_key
        self.secret_key = secret_key
        self.timeout = timeout
        self.default_rate = default_rate
        self.default_channel = default_channel

    @staticmethod
    def _parse_json(text: str) -> Any:
        if not text:
            return None
        try:
            return json.loads(text)
        except Exception:
            return {"raw": text}

    def _detect_format(self, file_name: str, content_type: Optional[str]) -> str:
        if content_type:
            normalized_content_type = content_type.strip().split(";", 1)[0].strip().lower()
            if normalized_content_type in self._MIME_TO_FORMAT:
                return self._MIME_TO_FORMAT[normalized_content_type]

        _, ext = os.path.splitext(file_name.lower())
        ext = ext.lstrip(".")
        if ext in self._EXT_TO_FORMAT:
            return self._EXT_TO_FORMAT[ext]
        return "pcm"

    @staticmethod
    def _try_read_wav_meta(file_content: bytes) -> tuple[Optional[int], Optional[int], Optional[int]]:
        try:
            with wave.open(io.BytesIO(file_content), "rb") as wav_obj:
                return wav_obj.getframerate(), wav_obj.getnchannels(), wav_obj.getsampwidth()
        except Exception:
            return None, None, None

    @staticmethod
    def _normalize_wav_to_pcm16_mono(file_content: bytes) -> tuple[bytes, int, int]:
        """Convert WAV bytes to 16kHz mono 16-bit PCM bytes."""

        with wave.open(io.BytesIO(file_content), "rb") as wav_obj:
            if wav_obj.getcomptype() != "NONE":
                raise ValueError("unsupported wav compression type")

            framerate = wav_obj.getframerate()
            nchannels = wav_obj.getnchannels()
            sampwidth = wav_obj.getsampwidth()
            raw_frames = wav_obj.readframes(wav_obj.getnframes())

        if nchannels not in (1, 2):
            raise ValueError(f"unsupported wav channel count: {nchannels}")
        if sampwidth not in (1, 2, 4):
            raise ValueError(f"unsupported wav sample width: {sampwidth}")

        # Convert raw bytes to numpy array based on sample width
        if sampwidth == 1:
            dtype = np.uint8
            audio_data = np.frombuffer(raw_frames, dtype=dtype).astype(np.float64)
            audio_data = (audio_data - 128) / 128.0  # Normalize to [-1, 1]
        elif sampwidth == 2:
            dtype = np.int16
            audio_data = np.frombuffer(raw_frames, dtype=dtype).astype(np.float64)
            audio_data = audio_data / 32768.0  # Normalize to [-1, 1]
        else:  # sampwidth == 4
            dtype = np.int32
            audio_data = np.frombuffer(raw_frames, dtype=dtype).astype(np.float64)
            audio_data = audio_data / 2147483648.0  # Normalize to [-1, 1]

        # Convert stereo to mono
        if nchannels == 2:
            audio_data = audio_data.reshape(-1, 2).mean(axis=1)

        # Resample to 16kHz if needed
        target_rate = 16000
        if framerate != target_rate:
            num_samples = int(len(audio_data) * target_rate / framerate)
            audio_data = signal.resample(audio_data, num_samples)
            framerate = target_rate

        # Convert back to 16-bit PCM
        audio_data = np.clip(audio_data, -1.0, 1.0)
        pcm_data = (audio_data * 32767.0).astype(np.int16)

        return pcm_data.tobytes(), framerate, 1

    def get_access_token(self) -> str:
        params = {
            "grant_type": "client_credentials",
            "client_id": self.api_key,
            "client_secret": self.secret_key,
        }
        url = f"{self.TOKEN_URL}?{urllib_parse.urlencode(params)}"
        req = urllib_request.Request(url=url, method="POST")

        try:
            with urllib_request.urlopen(req, timeout=self.timeout) as resp:
                payload = self._parse_json(resp.read().decode("utf-8"))
        except urllib_error.HTTPError as exc:
            detail = self._parse_json(exc.read().decode("utf-8") if exc.fp else "")
            raise BaiduSpeechToTextError(exc.code, "baidu token request failed", detail) from exc
        except urllib_error.URLError as exc:
            raise BaiduSpeechToTextError(502, "baidu token upstream unavailable", str(exc)) from exc

        token = payload.get("access_token") if isinstance(payload, dict) else None
        if not token:
            raise BaiduSpeechToTextError(401, "baidu token not found", payload)
        return str(token)

    def recognize(
            self,
            *,
            file_name: str,
            file_content: bytes,
            cuid: str,
            content_type: Optional[str] = None,
            rate: Optional[int] = None,
            channel: Optional[int] = None,
    ) -> str:
        access_token = self.get_access_token()
        audio_format = self._detect_format(file_name, content_type)

        actual_rate = rate or self.default_rate
        actual_channel = channel or self.default_channel
        normalized_content = file_content

        # WAV files often carry real sample rate/channel; normalize them to 16k mono PCM for Baidu.
        if audio_format == "wav":
            try:
                normalized_content, actual_rate, actual_channel = self._normalize_wav_to_pcm16_mono(file_content)
                audio_format = "pcm"
            except Exception:
                # Fall back to original WAV payload if conversion fails.
                wav_rate, wav_channel = self._try_read_wav_meta(file_content)
                if wav_rate:
                    actual_rate = wav_rate
                if wav_channel:
                    actual_channel = wav_channel

        body = {
            "format": audio_format,
            "rate": actual_rate,
            "channel": actual_channel,
            "cuid": cuid,
            "token": access_token,
            "speech": base64.b64encode(normalized_content).decode("utf-8"),
            "len": len(normalized_content),
        }

        req = urllib_request.Request(
            url=self.STT_URL,
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )

        try:
            with urllib_request.urlopen(req, timeout=self.timeout) as resp:
                payload = self._parse_json(resp.read().decode("utf-8"))
        except urllib_error.HTTPError as exc:
            detail = self._parse_json(exc.read().decode("utf-8") if exc.fp else "")
            raise BaiduSpeechToTextError(exc.code, "baidu stt request failed", detail) from exc
        except urllib_error.URLError as exc:
            raise BaiduSpeechToTextError(502, "baidu stt upstream unavailable", str(exc)) from exc

        if isinstance(payload, dict) and payload.get("err_no") == 0:
            result = payload.get("result")
            if isinstance(result, list) and result:
                return str(result[0])
            return ""

        raise BaiduSpeechToTextError(400, "baidu stt request failed", payload)

