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

#该代码 qwen AI 辅助编写，#qwen AI 辅助封装，AI辅助生成：qwen3
try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False


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
        "audio/webm": "webm",  # 添加 WebM 支持
        "audio/x-webm": "webm",
    }

    _EXT_TO_FORMAT = {
        "wav": "wav",
        "pcm": "pcm",
        "mp3": "mp3",
        "mpeg": "mp3",
        "mpga": "mp3",
        "amr": "amr",
        "m4a": "m4a",
        "webm": "webm",  # 添加 WebM 扩展名支持
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
    def _convert_webm_to_pcm(webm_content: bytes) -> bytes:
        """Convert WebM audio to 16kHz mono 16-bit PCM (raw data, no WAV header).
        
        Args:
            webm_content: WebM audio bytes
            
        Returns:
            Raw PCM bytes (16kHz, mono, 16-bit little-endian, no header)
        """
        if not PYDUB_AVAILABLE:
            raise ImportError(
                "pydub is required for WebM conversion. "
                "Install it with: pip install pydub"
            )
        
        try:
            # Load WebM audio
            audio = AudioSegment.from_file(io.BytesIO(webm_content), format="webm")
            
            print(f"[STT] Original WebM: rate={audio.frame_rate}Hz, channels={audio.channels}, duration={len(audio)}ms, sample_width={audio.sample_width}")
            
            # Convert to 16kHz mono 16-bit
            audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
            
            # Get raw PCM data and ensure little-endian
            pcm_data = audio.raw_data
            
            # Verify and fix byte order if needed (ensure little-endian)
            # pydub returns little-endian by default, but let's be safe
            if audio.sample_width == 2:
                # Convert to numpy to verify/fix byte order and normalize volume
                pcm_array = np.frombuffer(pcm_data, dtype='<i2')  # little-endian int16
                
                # Normalize volume to avoid too quiet audio
                max_val = np.max(np.abs(pcm_array))
                if max_val > 0 and max_val < 10000:  # If too quiet, amplify
                    amplification = 15000.0 / max_val
                    pcm_array = (pcm_array * amplification).astype(np.int16)
                    print(f"[STT] Audio amplified by {amplification:.2f}x (max was {max_val})")
                
                pcm_data = pcm_array.tobytes()
            
            print(f"[STT] Converted PCM: duration={len(audio)}ms, size={len(pcm_data)} bytes, sample_width={audio.sample_width}")
            print(f"[STT] PCM data preview (first 20 bytes): {pcm_data[:20].hex()}")
            
            return pcm_data
        except Exception as e:
            import traceback
            print(f"[STT] WebM conversion failed: {e}")
            print(traceback.format_exc())
            raise ValueError(f"Failed to convert WebM to PCM: {str(e)}")

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

        # WebM 文件需要转换为 PCM
        if audio_format == "webm":
            try:
                print(f"[STT] Converting WebM to PCM...")
                normalized_content = self._convert_webm_to_pcm(file_content)
                audio_format = "pcm"
                actual_rate = 16000
                actual_channel = 1
                print(f"[STT] WebM conversion successful, size: {len(normalized_content)} bytes")
                print(f"[STT] Format: {audio_format}, Rate: {actual_rate}, Channel: {actual_channel}")
            except Exception as e:
                print(f"[STT] WebM conversion failed: {e}")
                raise BaiduSpeechToTextError(
                    400, 
                    f"WebM conversion failed: {str(e)}",
                    {"error": "webm_conversion_failed"}
                )
        # WAV 文件经常带有实际的采样率/声道；将它们标准化为 16k 单声道 PCM 以用于百度。
        elif audio_format == "wav":
            try:
                normalized_content, actual_rate, actual_channel = self._normalize_wav_to_pcm16_mono(file_content)
                audio_format = "pcm"
                print(f"[STT] WAV conversion successful, format: {audio_format}, rate: {actual_rate}, channel: {actual_channel}")
            except Exception:
                # 如果转换失败，回退到原始 WAV 负载。
                wav_rate, wav_channel = self._try_read_wav_meta(file_content)
                if wav_rate:
                    actual_rate = wav_rate
                if wav_channel:
                    actual_channel = wav_channel
                print(f"[STT] Using original WAV, rate: {actual_rate}, channel: {actual_channel}")

        body = {
            "format": audio_format,
            "rate": actual_rate,
            "channel": actual_channel,
            "cuid": cuid,
            "token": access_token,
            "speech": base64.b64encode(normalized_content).decode("utf-8"),
            "len": len(normalized_content),
        }

        # 打印请求参数用于调试
        print(f"[STT] Request params: format={audio_format}, rate={actual_rate}, channel={actual_channel}, len={len(normalized_content)}")
        print(f"[STT] Base64 length: {len(body['speech'])} chars")
        
        # 检查音频数据是否有效
        if len(normalized_content) < 1000:
            print(f"[STT] WARNING: Audio data too small ({len(normalized_content)} bytes), may cause quality error")
        
        # 验证 PCM 数据大小是否符合预期
        expected_size = (actual_rate * actual_channel * 2)  # 每秒字节数 = 采样率 * 声道数 * 2字节(16-bit)
        duration_seconds = len(normalized_content) / expected_size if expected_size > 0 else 0
        print(f"[STT] Estimated duration: {duration_seconds:.2f} seconds")
        
        if duration_seconds < 0.5:
            print(f"[STT] WARNING: Audio duration too short ({duration_seconds:.2f}s), minimum recommended is 1s")

        req = urllib_request.Request(
            url=self.STT_URL,
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )

        try:
            with urllib_request.urlopen(req, timeout=self.timeout) as resp:
                payload = self._parse_json(resp.read().decode("utf-8"))
                print(f"[STT] Baidu API response: {json.dumps(payload, ensure_ascii=False)}")
        except urllib_error.HTTPError as exc:
            detail = self._parse_json(exc.read().decode("utf-8") if exc.fp else "")
            print(f"[STT] HTTP Error: {exc.code}, detail: {detail}")
            raise BaiduSpeechToTextError(exc.code, "baidu stt request failed", detail) from exc
        except urllib_error.URLError as exc:
            print(f"[STT] URL Error: {exc}")
            raise BaiduSpeechToTextError(502, "baidu stt upstream unavailable", str(exc)) from exc

        if isinstance(payload, dict) and payload.get("err_no") == 0:
            result = payload.get("result")
            if isinstance(result, list) and result:
                return str(result[0])
            return ""

        # 打印错误详情
        err_no = payload.get("err_no") if isinstance(payload, dict) else "unknown"
        err_msg = payload.get("err_msg") if isinstance(payload, dict) else "unknown"
        print(f"[STT] Recognition failed: err_no={err_no}, err_msg={err_msg}")
        
        raise BaiduSpeechToTextError(400, "baidu stt request failed", payload)

