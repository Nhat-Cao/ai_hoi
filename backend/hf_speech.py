"""
Hugging Face Speech Services - Free alternatives to Azure Speech
Uses open-source models from Hugging Face for speech-to-text and text-to-speech
"""

import os
import tempfile
from gtts import gTTS
import io
import soundfile as sf
import librosa
import numpy as np
from scipy.signal import wiener, butter, filtfilt

# Lazy loading for heavy models
_stt_pipeline = None

def get_speech_to_text_pipeline():
    """
    Get or initialize the speech-to-text pipeline
    Using OpenAI's Whisper model from Hugging Face
    """
    global _stt_pipeline
    if _stt_pipeline is None:
        print("🔄 Loading Whisper model for speech-to-text...")
        from transformers import pipeline
        import torch
        
        # Use Whisper large-v3 model for BEST Vietnamese accuracy
        # This is the most accurate model for Vietnamese transcription
        _stt_pipeline = pipeline(
            "automatic-speech-recognition",
            model="openai/whisper-large-v3",
            device=0 if torch.cuda.is_available() else -1,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
        )
        print("✅ Whisper large-v3 model loaded (best accuracy)")
    return _stt_pipeline

def transcribe_audio(audio_path: str, language: str = "vi") -> str:
    """
    Transcribe audio file to text using Whisper
    
    Args:
        audio_path: Path to audio file
        language: Language code (default: "vi" for Vietnamese)
    
    Returns:
        Transcribed text
    """
    try:
        pipe = get_speech_to_text_pipeline()
        
        print(f"📁 Processing audio file: {audio_path}")
        print(f"📊 Original file size: {os.path.getsize(audio_path)} bytes")
        
        # Load and preprocess audio for better quality
        print("🔧 Preprocessing audio...")
        audio, sr = librosa.load(audio_path, sr=16000)  # Whisper works best at 16kHz
        
        print(f"📊 Original audio stats: min={np.min(audio):.4f}, max={np.max(audio):.4f}, mean={np.mean(np.abs(audio)):.4f}")
        
        # Remove silence from beginning and end FIRST
        audio, _ = librosa.effects.trim(audio, top_db=30)  # More aggressive trimming
        
        # Apply spectral gating for noise reduction
        print("🔇 Applying noise reduction...")
        
        # Normalize before processing
        audio = librosa.util.normalize(audio)
        
        # Apply Wiener filter for noise reduction
        audio = wiener(audio, mysize=5)
        
        # High-pass filter to remove low-frequency noise (below 80 Hz)
        b, a = butter(5, 80 / (sr / 2), btype='high')
        audio = filtfilt(b, a, audio)
        
        # Normalize again after filtering
        audio = librosa.util.normalize(audio)
        
        # Check if audio is too quiet
        rms = np.sqrt(np.mean(audio**2))
        print(f"📈 RMS level: {rms:.4f}")
        
        if rms < 0.01:
            print("⚠️ Audio is very quiet (possibly silence or noise only)")
            print("❌ No clear speech detected")
            return "Không phát hiện được giọng nói rõ ràng. Vui lòng thử lại và nói to hơn."
        
        # Apply gentle compression to make speech more consistent
        if np.max(np.abs(audio)) > 0:
            audio = np.sign(audio) * np.power(np.abs(audio), 0.8)  # Soft compression
            audio = librosa.util.normalize(audio)
        
        print(f"✅ Preprocessed audio: {len(audio)/sr:.2f} seconds, RMS: {rms:.4f}")
        print(f"📊 Processed audio stats: min={np.min(audio):.4f}, max={np.max(audio):.4f}, mean={np.mean(np.abs(audio)):.4f}")
        
        # Save preprocessed audio to temporary file
        temp_fd, temp_audio_path = tempfile.mkstemp(suffix='.wav')
        os.close(temp_fd)  # Close file descriptor
        sf.write(temp_audio_path, audio, sr)
        print(f"💾 Saved preprocessed audio to: {temp_audio_path}")
        
        # Transcribe with optimized parameters for Vietnamese
        print("🎯 Starting transcription...")
        
        result = pipe(
            temp_audio_path,
            generate_kwargs={
                "language": "vietnamese",  # Explicit Vietnamese
                "task": "transcribe",
                "temperature": 0.0,  # More deterministic output
                "no_repeat_ngram_size": 3,  # Reduce repetition
                "num_beams": 10,  # Increased from 5 for better accuracy
                "compression_ratio_threshold": 1.35,  # Detect and reject bad outputs
                "logprob_threshold": -1.0,  # Filter low-probability outputs
            },
            chunk_length_s=30,
            stride_length_s=5,  # Overlap for better context
            return_timestamps=False
        )
        
        # Clean up temporary file
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)
        
        text = result["text"].strip()
        print(f"✅ Transcribed: {text}")
        return text
    
    except Exception as e:
        print(f"❌ Transcription error: {e}")
        import traceback
        traceback.print_exc()
        raise

def text_to_speech_gtts(text: str, language: str = "vi") -> bytes:
    """
    Convert text to speech using gTTS (Google Text-to-Speech)
    Completely free, no API key required
    
    Args:
        text: Text to convert to speech
        language: Language code (default: "vi" for Vietnamese)
    
    Returns:
        Audio bytes (MP3 format)
    """
    try:
        print(f"🔊 Converting to speech: {text[:50]}...")
        
        # Create gTTS object
        tts = gTTS(text=text, lang=language, slow=False)
        
        # Save to bytes
        audio_bytes = io.BytesIO()
        tts.write_to_fp(audio_bytes)
        audio_bytes.seek(0)
        
        print("✅ Text-to-speech conversion successful")
        return audio_bytes.read()
    
    except Exception as e:
        print(f"❌ Text-to-speech error: {e}")
        raise
