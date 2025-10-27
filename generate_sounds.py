import os
import numpy as np
#from scipy.io import wavfile
import audioread
import re
import librosa
import soundfile as sf

from psynet.asset import S3Storage
#asset_storage = S3Storage("sigspace-bucket", "sigspace-experiment")  # Comment out S3 for local development

# Constants
SAMPLE_RATE = 22050
BASE_STEPS = 16  # matches drum_machine.html internal resolution
STEP_TIME = 0.125  # 125ms per 16th note (120 BPM) - matches drum_machine.html STEP_TIME

def load_sample(filename):
    data, sample_rate = librosa.load(f'static/audio/{filename}.mp3', sr=None)  # audioread.audio_open(f'static/audio/{filename}.mp3')
    return data

def create_silence(duration):
    """Create a silent audio segment."""
    return np.zeros(int(duration * SAMPLE_RATE))

def generate_pattern_audio(pattern, grid_size, kit_type):
    """Generate audio for a specific pattern."""
    # Load the base samples
    hihat = load_sample('hihat')
    snare = load_sample('snare')
    kick = load_sample('kick')
    
    # Calculate timing based on grid size
    factor = BASE_STEPS / grid_size  # How many 16th notes per grid step
    beat_duration = STEP_TIME * factor  # Duration of each grid step
    
    # Calculate total duration
    total_duration = grid_size * beat_duration
    total_samples = int(total_duration * SAMPLE_RATE)
    
    # Calculate samples per beat
    samples_per_beat = int(beat_duration * SAMPLE_RATE)
    
    # Create empty audio array
    audio = np.zeros(total_samples)
    
    # Parse the pattern and determine which drums to use
    patterns = {}  # Initialize patterns dictionary
    
    if kit_type == 'snare+kick':
        snare_pattern, kick_pattern = pattern.split('_')
        patterns = {'snare': snare_pattern, 'kick': kick_pattern}
    elif kit_type == 'hihat+snare+kick':
        hihat_pattern, snare_pattern, kick_pattern = pattern.split('_')
        patterns = {'hihat': hihat_pattern, 'snare': snare_pattern, 'kick': kick_pattern}
    elif kit_type == 'kick':
        patterns = {'kick': pattern}
    else:
        # Fallback: try to parse the pattern as individual components
        pattern_parts = pattern.split('_')
        if len(pattern_parts) >= 2:
            patterns = {'kick': pattern_parts[0], 'snare': pattern_parts[1]}
        elif len(pattern_parts) == 1:
            patterns = {'kick': pattern_parts[0]}
        else:
            raise ValueError(f"Invalid pattern format: {pattern}")

    
    # Add each beat to the audio
    for i in range(grid_size):
        # Calculate position in the audio array
        pos = int(i * beat_duration * SAMPLE_RATE)

        # Add each drum hit with full sample length
        if 'hihat' in patterns and i < len(patterns['hihat']) and patterns['hihat'][i] == '1':
            # Add hihat sample, but don't exceed the audio array bounds
            end_pos = min(pos + len(hihat), len(audio))
            audio[pos:end_pos] += hihat[:end_pos - pos]
            
        if 'snare' in patterns and i < len(patterns['snare']) and patterns['snare'][i] == '1':
            # Add snare sample, but don't exceed the audio array bounds
            end_pos = min(pos + len(snare), len(audio))
            audio[pos:end_pos] += snare[:end_pos - pos]
            
        if 'kick' in patterns and i < len(patterns['kick']) and patterns['kick'][i] == '1':
            # Add kick sample, but don't exceed the audio array bounds
            end_pos = min(pos + len(kick), len(audio))
            audio[pos:end_pos] += kick[:end_pos - pos]
    
    # Normalize audio
    if np.max(np.abs(audio)) > 0:
        audio = audio / np.max(np.abs(audio))
    
    return audio

def generate_audio_file(pattern, grid_size, kit_type, output_dir='static/generated_sounds'):
    """Generate a single audio file from a rhythm pattern."""
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Generate the audio
    audio = generate_pattern_audio(pattern, grid_size, kit_type)

    # Create filename based on kit type
    if kit_type == 'snare+kick':
        snare_pattern, kick_pattern  = pattern.split('_')
        filename = f"grid{grid_size}_snare{snare_pattern}_kick{kick_pattern}.mp3"
    elif kit_type == 'hihat+snare+kick':
        hihat_pattern, snare_pattern, kick_pattern = pattern.split('_')
        filename = f"grid{grid_size}_hihat{hihat_pattern}_snare{snare_pattern}_kick{kick_pattern}.mp3"
    
    # Full path for the file
    full_path = os.path.join(output_dir, filename)

    # Save the audio file
    #wavfile.write(full_path, SAMPLE_RATE, (audio * 32767).astype(np.int16))
    #print(f'Saved audio file to: {full_path}')
    sf.write(full_path, audio, SAMPLE_RATE, format='MP3')
    
    # Return the path relative to the static directory for web access
    return os.path.join('generated_sounds', filename)


def parse_and_generate_audio(director_sound_str):
    """
    Parse a rhythm pattern string like 'hihat_1100_snare_0000_kick_0000' and generate the corresponding audio.
    
    Args:
        director_sound_str (str): Pattern in format 'hihat_[01]+_snare_[01]+_kick_[01]+'
    
    Returns:
        str: Path to the generated audio file
    """

    # Remove trailing underscore if present (drum machine outputs with trailing underscore)
    if director_sound_str.endswith('_'):
        director_sound_str = director_sound_str[:-1]

    # Extract patterns
    patterns = {}
    for drum in ['hihat', 'snare', 'kick']:
        pattern_match = re.search(f'{drum}_([01]+)', director_sound_str)
        if pattern_match:
            patterns[drum] = pattern_match.group(1)

    # Determine grid size from the first pattern
    if not patterns:
        raise ValueError("No valid patterns found in the input string")
    
    grid_size = len(next(iter(patterns.values())))

    # Determine kit type based on which patterns are present
    if 'hihat' in patterns:
        kit_type = 'hihat+snare+kick'
        pattern = f"{patterns['hihat']}_{patterns['snare']}_{patterns['kick']}"
    elif 'snare' in patterns:
        kit_type = 'snare+kick'
        pattern = f"{patterns['snare']}_{patterns['kick']}"
    else:
        kit_type = 'kick'
        pattern = patterns['kick']
    
    # Generate the audio file
    return generate_audio_file(pattern, grid_size, kit_type)
