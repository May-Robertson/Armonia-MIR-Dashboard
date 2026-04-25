import urllib.request
import json
import IPython
import librosa
import os
import subprocess
import numpy as np
import musicbrainzngs
from datetime import datetime
from thefuzz import fuzz
import matplotlib.pyplot as plt
import pandas as pd
import pyloudnorm as pyln

from dotenv import load_dotenv
load_dotenv()
#--------------------------------SEARCH FUNCTION--------------------------------

def deezer_search(artist_name, track_name, similarity_threshold=65):

    # Broad search - just use track name to get more results
    search_track_name = urllib.parse.quote(track_name.replace(" ", "+"))

    search_url = f"https://api.deezer.com/search/track/?q={search_track_name}"
    # https://api.deezer.com/search/track?q="good luck babe"
    try:
        track_search = urllib.request.urlopen(search_url).read().decode('utf-8')
        data = json.loads(track_search)
        matches = []

        for track_data in data["data"]:
            current_artist = track_data["artist"]["name"]
            current_track = track_data["title"]
            
            # Calculate multiple similarity scores
            artist_similarity = fuzz.token_sort_ratio(artist_name.lower(), current_artist.lower())
            track_similarity = fuzz.token_sort_ratio(track_name.lower(), current_track.lower())
            
            # Use the higher score between partial and token ratios
            artist_partial = fuzz.partial_ratio(artist_name.lower(), current_artist.lower())
            track_partial = fuzz.partial_ratio(track_name.lower(), current_track.lower())
            
            artist_score = max(artist_similarity, artist_partial)
            track_score = max(track_similarity, track_partial)
            
            total_score = (artist_score + track_score) / 2
            
            if total_score >= similarity_threshold:
                # Get the track ID
                track_id = track_data["id"]
                
                # Make a second API call to get full track details
                try:
                    track_details_url = f"https://api.deezer.com/track/{track_id}"
                    track_details_response = urllib.request.urlopen(track_details_url).read()
                    track_details = json.loads(track_details_response)
                    
                    # Get release date from track details or album
                    release_date = track_details.get("release_date", "")
                    
                    # If no release date at track level, check album
                    if not release_date and "album" in track_details:
                        release_date = track_details["album"].get("release_date", "")
                        
                except Exception as e:
                    print(f"Error fetching details for track {track_id}: {e}")
                    release_date = ""
                
                matches.append({
                    "track": current_track,
                    "artist": current_artist,
                    "album": track_data["album"]["title"],
                    "id": track_id,
                    "artist_score": artist_score,
                    "track_score": track_score,
                    "total_score": total_score,
                    "preview": track_data.get("preview", ""),
                    "duration": track_data["duration"],
                    "release_date": release_date,
                    "album_id": track_data["album"]["id"]
                })
    
        # Sort by total score
        matches.sort(key=lambda x: x["total_score"], reverse=True)
        return matches
        
    except Exception as e:
        print(f"Error searching Deezer: {e}")
        return []

# deezer_search(artist_name, track_name)
# deezer_search("A Tribe Called Quest", "Electric Relaxation")


def analyze_selected_track(output):
    # print("\nPlease enter number from 0-"+str(len(output)-1)+" to select a track for analysis!\n")
    print("output",output)
    # selection = int(input())
    # print("Performing Analysis On --> ",output[int(selection)])
    # print("ID = ",output[selection]['id'])
    track_id = str(output['id'])

    print("ACCESSING DEEZER API")
    contents = urllib.request.urlopen("https://api.deezer.com/track/"+track_id).read()
    data = json.loads(contents)
    print("DATA LOADED")

    track_url = "https://api.deezer.com/track/"+track_id
    preview_url = data["preview"]
    track_name = data["title_short"]
    artist_name = data["artist"]["name"]
    album_title = data["album"]["title"]
    release_date = data["release_date"]

    # with open('x_file.pkl', 'wb') as outf:
    #     pickle.dump([track_url, track_id, preview_url, track_name, artist_name,album_title, release_date], outf)

    print("\nTRACK INFO:")
    print("Track:",track_name,"\nArtist:",artist_name,"\nAlbum Title:", album_title,"\nRelease Date:",release_date)



    '''GET PREVIEW URL'''


    urllib.request.urlretrieve(preview_url, "audio_files/"+track_name+".mp3")



    print("subprocess.call")
    # convert mp3 to wav file
    subprocess.call(['ffmpeg','-y', '-i', 'audio_files/'+track_name+'.mp3',
                    'audio_files/'+track_name+'.wav'])
    
    

    # import required modules



    # wav conversion code
    from os import path
    from pydub import AudioSegment

    # assign files
    input_file = "audio_files/"+track_name+".mp3"
    output_file = "audio_files/"+track_name+".wav"

    # convert mp3 file to wav file
    print("AudioSegment.from_mp3")
    sound = AudioSegment.from_mp3(input_file)
    
    print("sound.export")
    sound.export(output_file, format="wav")

    print("os.remove")
    os.remove(input_file)

    return track_name




# class that uses the librosa library to analyze the key that an mp3 is in
# arguments:
#     waveform: an mp3 file loaded by librosa, ideally separated out from any percussive sources
#     sr: sampling rate of the mp3, which can be obtained when the file is read with librosa
#     tstart and tend: the range in seconds of the file to be analyzed; default to the beginning and end of file if not specified
class Tonal_Fragment(object):
    def __init__(self, waveform, sr, tstart=None, tend=None):
        self.waveform = waveform
        self.sr = sr
        self.tstart = tstart
        self.tend = tend
        
        if self.tstart is not None:
            self.tstart = librosa.time_to_samples(self.tstart, sr=self.sr)
        if self.tend is not None:
            self.tend = librosa.time_to_samples(self.tend, sr=self.sr)
        self.y_segment = self.waveform[self.tstart:self.tend]
        self.chromograph = librosa.feature.chroma_cqt(y=self.y_segment, sr=self.sr, bins_per_octave=24)
        
        # chroma_vals is the amount of each pitch class present in this time interval
        self.chroma_vals = []
        for i in range(12):
            self.chroma_vals.append(np.sum(self.chromograph[i]))
        pitches = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
        # dictionary relating pitch names to the associated intensity in the song
        self.keyfreqs = {pitches[i]: self.chroma_vals[i] for i in range(12)} 
        
        keys = [pitches[i] + ' major' for i in range(12)] + [pitches[i] + ' minor' for i in range(12)]

        # use of the Krumhansl-Schmuckler key-finding algorithm, which compares the chroma
        # data above to typical profiles of major and minor keys:
        maj_profile = [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
        min_profile = [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]

        # finds correlations between the amount of each pitch class in the time interval and the above profiles,
        # starting on each of the 12 pitches. then creates dict of the musical keys (major/minor) to the correlation
        self.min_key_corrs = []
        self.maj_key_corrs = []
        for i in range(12):
            key_test = [self.keyfreqs.get(pitches[(i + m)%12]) for m in range(12)]
            # correlation coefficients (strengths of correlation for each key)
            self.maj_key_corrs.append(round(np.corrcoef(maj_profile, key_test)[1,0], 3))
            self.min_key_corrs.append(round(np.corrcoef(min_profile, key_test)[1,0], 3))

        # names of all major and minor keys
        self.key_dict = {**{keys[i]: self.maj_key_corrs[i] for i in range(12)}, 
                         **{keys[i+12]: self.min_key_corrs[i] for i in range(12)}}
        
        # this attribute represents the key determined by the algorithm
        self.key = max(self.key_dict, key=self.key_dict.get)
        self.bestcorr = max(self.key_dict.values())
        
        # this attribute represents the second-best key determined by the algorithm,
        # if the correlation is close to that of the actual key determined
        self.altkey = None
        self.altbestcorr = None

        for key, corr in self.key_dict.items():
            if corr > self.bestcorr*0.9 and corr != self.bestcorr:
                self.altkey = key
                self.altbestcorr = corr
                
    # prints the relative prominence of each pitch class            
    def print_chroma(self):
        self.chroma_max = max(self.chroma_vals)
        for key, chrom in self.keyfreqs.items():
            print(key, '\t', f'{chrom/self.chroma_max:5.3f}')
                
    # prints the correlation coefficients associated with each major/minor key
    def corr_table(self):
        for key, corr in self.key_dict.items():
            print(key, '\t', f'{corr:6.3f}')
    
    # printout of the key determined by the algorithm; if another key is close, that key is mentioned
    def print_key(self):
        key = max(self.key_dict, key=self.key_dict.get)
        print("likely key: ", max(self.key_dict, key=self.key_dict.get), ", correlation: ", self.bestcorr, sep='')
        if self.altkey is not None:
                print("also possible: ", self.altkey, ", correlation: ", self.altbestcorr, sep='')
        return key
    
    # prints a chromagram of the file, showing the intensity of each pitch class over time
    def chromagram(self, title=None):
        C = librosa.feature.chroma_cqt(y=self.waveform, sr=self.sr, bins_per_octave=24)
        plt.figure(figsize=(12,4))
        librosa.display.specshow(C, sr=self.sr, x_axis='time', y_axis='chroma', vmin=0, vmax=1)
        if title is None:
            plt.title('Chromagram')
        else:
            plt.title(title)
        plt.colorbar()
        plt.tight_layout()
        plt.show()


# https://github.com/jackmcarthur/musical-key-finder/tree/master
def librosa_analysis(track_name):
    #--------------------------------LIBROSA ANALYSIS--------------------------------

    # input_file = sys.argv[1]
    IPython.display.Audio('audio_files/'+track_name+".wav")

    y, sr = librosa.load('audio_files/'+track_name+".wav", sr=None)

    y_harmonic, y_percussive = librosa.effects.hpss(y)

    print("FULL FILE")
    track = Tonal_Fragment(y_harmonic, sr)
    key = track.print_key()

    onset_env = librosa.onset.onset_strength(y=y, sr=sr, aggregate=np.median)
    tempo, beats = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr)

    return key, tempo


def get_loudness(track_name):
    
    y, sr = librosa.load('audio_files/'+track_name+".wav", sr=None)

    rms = librosa.feature.rms(y=y)
    rms_db = librosa.amplitude_to_db(rms, ref=1.0)  # ref=1.0 gives negative values
    loudness = float(np.mean(rms_db))
    
    y = y / np.max(np.abs(y))
    
    # spotify
    meter = pyln.Meter(sr) 
    loudness_normalized = meter.integrated_loudness(y)
    return round(loudness, 2),round(loudness_normalized, 2)

# based on Igor Vatolkin and Anil Nagathil paper
def get_valence(track_name):

    # load track
    y, sr = librosa.load('audio_files/'+track_name+".wav", sr=None)
    y_harmonic, y_percussive = librosa.effects.hpss(y)

    # RHYTHM COMPONENTS
    # --- TEMPO ---
    tempo, _ = librosa.beat.beat_track(y=y_percussive, sr=sr)
    tempo_norm = min(1.0, max(0.0, (float(tempo) - 40) / 160.0))

    # --- RHYTHM STRENGTH ---
    # mean strength of tempogram will give us average pulse strength
    onset_env = librosa.onset.onset_strength(y=y_percussive, sr=sr)
    tempogram = librosa.feature.tempogram(onset_envelope=onset_env, sr=sr)
    avg_pulse_str = np.mean(tempogram)
    # Normalize with expected range of 0 - 0.5
    pulse_norm = min(1.0, avg_pulse_str / 0.5)


    # HARMONIC COMPONENTS
    # --- CHROMA STABILITY ---
    # use standard deviation for this
    chroma = librosa.feature.chroma_cqt(y=y_harmonic, sr=sr)
    # std of the chromagram
    chroma_std = np.mean(np.std(chroma, axis=1))
    # normalize
    chroma_norm = min(1.0, chroma_std / 0.5)


    # --- TONAL CENTROID ---
    # based on chroma
    # This representation uses the method of 1 to project chroma features onto a 6-dimensional basis representing the perfect fifth, minor third, and major third each as two-dimensional coordinates.
    # tonnetz computes tonal centroid features
    tonnetz = librosa.feature.tonnetz(y=y_harmonic, sr=sr)
    # the mean of this is a good way to get a general sense of harmonic components
    tonnetz_complexity = np.mean(np.abs(tonnetz))
    tonnetz_norm = min(1.0, tonnetz_complexity / 0.2)

    #   valence weights from linear regression
    #   Tempo weight: -0.6838
    #   Pulse Clarity weight: -1.7406
    #   Chroma Stability weight: 1.9100
    #   Harmonic Brightness weight: -0.9237
    #   Intercept: 1.0522


    valence = tempo_norm * (-0.6838) + pulse_norm * (-1.7406) + chroma_norm * (1.9100) + tonnetz_norm * (-0.9237) + 1.0522
   
    # clamp
    final_valence = max(0.0, min(1.0, valence))
    
    return round(final_valence, 2)


def get_energy(track_name):
    y, sr = librosa.load('audio_files/'+track_name+".wav", sr=None)

    # --- LOUDNESS ---
    rms = librosa.feature.rms(y=y)
    rms_db = librosa.amplitude_to_db(rms, ref=1.0)
    loudness = float(np.mean(rms_db))

    # normalize using expected range of -60 to 0 dB
    loudness_norm = (loudness + 60)/60
    
    # --- ONSET RATE ---
    # onset is the beginning of a musical event (for example, a note)
    # higher onset rate definitely correlates somehow to energy
    onsets = librosa.onset.onset_detect(y=y, sr=sr)
    onset_rate = (len(onsets))/(len(y)/sr)
    # normalize with assumed range of 0 - 15 onsets per second
    onset_rate_norm = min(1.0, onset_rate / 15.0)
    
    
    # --- ENTROPY ---
    # entropy refers to how predictable the next event in a phrase is
    # can be used to approximate how varied/predictable the audio is
    D = np.abs(librosa.stft(y))**2
    D_norm = D / (np.sum(D, axis=0, keepdims=True) + 1e-10)
    spectral_entropy = -np.sum(D_norm * np.log2(D_norm + 1e-10), axis=0)
    
    # avg entropy normalized
    entropy_mean = np.mean(spectral_entropy)
    # normalize with expected range of 0 to 0
    entropy_norm = min(1.0, entropy_mean / 8.0)
    # print("NORM ",entropy_norm)


    # from lin_test.py
    # Loudness weight: 1.8200
    # Onset rate weight: 0.3425
    # Entropy weight: 2.7923
    # Tempo weight: -0.0936 #TEMPO REMOVED as its inclusion made results less accurate
    # Intercept: -2.2188
    # final_energy = loudness_norm * 1.82 + onset_rate_norm * 0.3425 + entropy_norm * 2.7923 + tempo_norm * -0.0936 - 2.2188
    energy = loudness_norm * 1.82 + onset_rate_norm * 0.3425 + entropy_norm * 2.7923 - 2.2188

    # clamp to 0-1
    final_energy = max(0.0, min(1.0, energy))
    return round(final_energy, 2)


def get_danceability(track_name, spotify_val=None):
    # Danceability describes how suitable a track is for 
    # dancing based on a combination of musical elements including 
    # tempo, rhythm stability, beat strength, and overall regularity. 
    energy = get_energy(track_name)
    valence = get_valence(track_name)

    danceability = energy * 0.4 + valence * 0.6
    final_danceability = max(0.0, min(1.0, danceability))
    return round(final_danceability, 2)


def export_saved_analyses_to_csv(saved_analyses_data, filename="saved_analyses.csv"):
    """
    Export saved analyses to a CSV file
    
    Args:
        saved_analyses_data: List of dictionaries containing analysis data
        filename: Output CSV filename
    """
    export_data = []
    
    for item in saved_analyses_data:
        track_info = item.get('track_info', {})
        analysis_data = item.get('analysis_data', {})
        
        row = {
            'Track Name': track_info.get('track', 'Unknown'),
            'Artist Name': track_info.get('artist', 'Unknown'),
            'Album Name': track_info.get('album', 'Unknown'),
            'Release Date': track_info.get('release_date', 'Unknown'),
            'Genre': analysis_data.get('genre', 'Unknown'),
            'Estimated Key': analysis_data.get('key', 'Unknown'),
            'Tempo (BPM)': analysis_data.get('tempo', 'Unknown'),
            'Energy': analysis_data.get('energy', 'Unknown'),
            'Valence': analysis_data.get('valence', 'Unknown'),
            'Loudness (dB)': analysis_data.get('loudness', 'Unknown'),
            'Loudness Normalized (LUFS)': analysis_data.get('loudness_norm', 'Unknown')
        }
        export_data.append(row)
    
    # Create DataFrame and save to CSV
    df = pd.DataFrame(export_data)
    df.to_csv(filename, index=False)
    print(f"Exported {len(export_data)} tracks to {filename}")
    return filename



def librosa_graphs(track_name):
    #--------------------------------LIBROSA ANALYSIS--------------------------------
    print('audio_files/'+track_name+".wav")
    # input_file = sys.argv[1]
    IPython.display.Audio('audio_files/'+track_name+".wav")

    y, sr = librosa.load('audio_files/'+track_name+".wav", sr=None)
    onset_env = librosa.onset.onset_strength(y=y, sr=sr, aggregate=np.median)
    tempo, beats = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr)
    chroma = librosa.feature.chroma_cens(y=y, sr=sr)

    # Compute the Chroma Short-Time Fourier Transform (chroma_stft)
    chromagram = librosa.feature.chroma_stft(y=y, sr=sr)
    # Calculate the mean chroma feature across time
    mean_chroma = np.mean(chromagram, axis=1)
    # Define the mapping of chroma features to keys
    chroma_to_key = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    # Find the key by selecting the maximum chroma feature
    estimated_key_index = np.argmax(mean_chroma)
    estimated_key = chroma_to_key[estimated_key_index]


    fig, ax = plt.subplots()
    librosa.display.waveshow(y, sr=sr, ax=ax)
    ax.set(title='Amplitude over time')
    plt.xlabel('Time(Seconds)')
    plt.ylabel('Amplitude')

    # plt.show();



    D = librosa.stft(y)
    S_db = librosa.amplitude_to_db(np.abs(D), ref=np.max)


    fig, ax = plt.subplots(nrows=2, ncols=1, sharex=True)

    #linear 
    img = librosa.display.specshow(D, y_axis='linear', x_axis='time', sr=sr, ax=ax[0],
                                    fmin=20, fmax=2000, hop_length=2048)
    
    ax[0].set(title='Linear-frequency power spectrum')
    ax[0].label_outer()
    ax[0].set_ylim([20, 2000])

    #log
    D = librosa.amplitude_to_db(np.abs(librosa.stft(y, hop_length=2048)), ref=np.max)

    librosa.display.specshow(D, y_axis='log', x_axis='time', sr=sr, ax=ax[1], 
                             hop_length=2048)
    

    ax[1].set(title='Log-frequency power spectrogram')
    ax[1].label_outer()
    fig.colorbar(img, ax=ax, format="%+2.f dB")
    plt.xlim(0, 30)

    print("SAVING 1st FILE")
    plt.savefig('figs/spectrograms.png')
    print("SAVED")
    # plt.show();


    chroma = librosa.feature.chroma_stft(y=y, sr=sr)

# chromagram = librosa.feature.chroma_stft(y=y, sr=sr)

    fig, ax = plt.subplots()
    img = librosa.display.specshow(chroma, y_axis='chroma', x_axis='time', ax=ax)
    ax.set(title='Chromagram')
    fig.colorbar(img, ax=ax)

    # plt.show()
    

    # ccov = np.cov(chroma)
    # fig, ax = plt.subplots()
    # img = librosa.display.specshow(ccov, y_axis='chroma', x_axis='chroma', ax=ax)
    # ax.set(title='Chroma covariance')
    # fig.colorbar(img, ax=ax)
    plt.savefig('figs/chromagram.png')

    # plt.show();

    # Print the detected key
    print("---Track Information---")
    # print(track_name)
    print("Detected Key:", estimated_key)
    print("Tempo: ", tempo)

    y_harmonic, y_percussive = librosa.effects.hpss(y)

    fig, ax = plt.subplots()
    librosa.display.waveshow(y_harmonic, sr=sr, ax=ax)
    ax.set(title='Amplitude over time for harmonic elements')
    plt.xlabel('Time (Seconds)')
    plt.ylabel('Amplitude')

    fig, ax = plt.subplots()
    librosa.display.waveshow(y_percussive, sr=sr, ax=ax)
    ax.set(title='Amplitude over time for percussive elements')
    plt.xlabel('Time (Seconds)')
    plt.ylabel('Amplitude')

    plt.savefig('figs/amp_over_time.png')
    # plt.show();
    print("return plt")
    return plt
    


# librosa_graphs("Hold On")




def musicbrainz_search(artist_name, track_name, album_title):
    """Search MusicBrainz for track releases and return data sorted by release date"""
    musicbrainzngs.set_useragent("ApplicationName", "0.1")
    releases = []
    
    try:
        result = musicbrainzngs.search_recordings(
            artist=artist_name, 
            recording=track_name, 
            release=album_title, 
            strict=True
        )
        
        for recording in result['recording-list']:
            # Check all releases for this recording
            for release in recording.get('release-list', []):
                if release['title'] == album_title:
                    releases.append(release)
        
        # Sort releases by date (oldest first)
        releases.sort(key=lambda x: parse_release_date(x.get('date', '0000')))
        
        return releases
        
    except Exception as e:
        print(f"Error searching MusicBrainz: {e}")
        return []
    
def parse_release_date(date_str):
    """Parse release date string for sorting"""
    if not date_str:
        return '9999-12-31'  # Put undated releases at the end
    
    # Handle various date formats
    parts = date_str.split('-')
    
    # Year only
    if len(parts) == 1:
        return f"{parts[0]}-12-31"  # End of year for sorting
    
    # Year-Month
    elif len(parts) == 2:
        # Get last day of month
        year, month = parts
        from datetime import datetime
        try:
            # Try to get last day of month
            if month == '02':
                last_day = '29' if int(year) % 4 == 0 else '28'
            elif month in ['04', '06', '09', '11']:
                last_day = '30'
            else:
                last_day = '31'
            return f"{year}-{month}-{last_day}"
        except:
            return f"{year}-{month}-31"
    
    # Full date
    else:
        return date_str

# def get_tags(artist_name, track_name, album_title):
#     """Search MusicBrainz for track releases and extract genre tags"""
#     musicbrainzngs.set_useragent("ApplicationName", "0.1")
#     releases = []
    
#     try:
#         result = musicbrainzngs.search_recordings(
#             artist=artist_name, 
#             recording=track_name, 
#             release=album_title, 
#             strict=True
#         )
        
#         # Extract genre tags from the first release
#         tags = []
        
#         for recording in result['recording-list']:
#             # Check all releases for this recording
#             for release in recording.get('release-list', []):
#                 if release['title'] == album_title:
#                     releases.append(release)
                    
#                     # Get detailed release information with tags
#                     try:
#                         # Include tags in the request
#                         release_details = musicbrainzngs.get_release_by_id(
#                             release['id'],
#                             includes=["tags"]  # Request tag information
#                         )
                        
#                         # Extract tags from release details
#                         if 'tag-list' in release_details['release']:
#                             for tag in release_details['release']['tag-list']:
#                                 tags.append({
#                                     'name': tag.get('name', ''),
#                                     'count': tag.get('count', 0)
#                                 })
                        
#                     except Exception as e:
#                         print(f"Error fetching tags for release {release['id']}: {e}")
        
#         # Sort releases by date (oldest first)
#         releases.sort(key=lambda x: parse_release_date(x.get('date', '0000')))
        
#         # Return both releases and tags
#         return releases, tags[:10]  # Return top 10 tags
        
#     except Exception as e:
#         print(f"Error searching MusicBrainz: {e}")
#         return [], []


def get_genre(album_name, artist_name=None, track_name=None):
    """Get genre information from Deezer using album name"""
    
    if not album_name:
        return {"genres": [], "album": "", "artist": "", "track": ""}
    
    try:
        # Search for album by name
        search_query = album_name
        if artist_name:
            search_query = f"{album_name} {artist_name}"
        
        search_query = search_query.replace(" ", "+")
        search_url = f"https://api.deezer.com/search/album/?q={search_query}"
        search_response = urllib.request.urlopen(search_url).read().decode('utf-8')
        search_data = json.loads(search_response)
        
        if not search_data["data"]:
            print(f"No album found for: {album_name}")
            return {"genres": [], "album": "", "artist": "", "track": track_name or ""}
        
        # Get the best match
        album_match = search_data["data"][0]
        album_id = album_match["id"]
        
        # Get album details including genres
        album_url = f"https://api.deezer.com/album/{album_id}"
        album_response = urllib.request.urlopen(album_url).read()
        album_data = json.loads(album_response)
        
        # Extract genres
        genres = []
        if "genres" in album_data and "data" in album_data["genres"]:
            genres = [genre["name"] for genre in album_data["genres"]["data"]]
        
        # Also try to get artist genres as fallback/extra info
        artist_genres = []
        if "artist" in album_data:
            artist_id = album_data["artist"]["id"]
            try:
                artist_url = f"https://api.deezer.com/artist/{artist_id}"
                artist_response = urllib.request.urlopen(artist_url).read()
                artist_data = json.loads(artist_response)
                
                if "genres" in artist_data and "data" in artist_data["genres"]:
                    artist_genres = [genre["name"] for genre in artist_data["genres"]["data"]]
            except Exception as e:
                print(f"Error fetching artist genres: {e}")
        
        # Combine album and artist genres, remove duplicates
        all_genres = list(set(genres + artist_genres))
        
        return {
            "genres": all_genres,
            "album": album_data.get("title", album_name),
            "artist": album_data.get("artist", {}).get("name", artist_name or ""),
            "album_id": album_id,
            "album_genres": genres,
            "artist_genres": artist_genres,
            "track": track_name or ""
        }
        
    except Exception as e:
        print(f"Error fetching genre from Deezer: {e}")
        return {"genres": [], "album": album_name, "artist": artist_name or "", "track": track_name or ""}
    
# genre_info = get_genre("Midnight Marauders")
# print(f"Genres for 'Midnight Marauders': {genre_info['genres']}")

# output = musicbrainz_search("A Tribe Called Quest", "Electric Relaxation", "Midnight Marauders")
# print(output)

# tags = get_tags("A Tribe Called Quest", "Electric Relaxation", "Midnight Marauders")
# print(tags)
def lyrics_genius(artist_name, track_name):
    #--------------------------------MUSICBRAINZ INFO--------------------------------

    from lyricsgenius import Genius

    # artist_name = "Chappell Roan"
    # track_name = "Pink Pony Club"
    # album_title = "The Rise and Fall of a Midwest Princess"



    access_token = os.environ.get("GENIUS_API_KEY")
    print("GENIUS ACCESS",access_token)
    # genius = Genius(os.environ.get("GENIUS_API_KEY"))
    genius = Genius(access_token)
    song = genius.search_song(track_name, artist_name)
    if song is None:
        return "No lyrics found"

    return song.lyrics



def read_csv(filepath):
    
    # print("FILEPATH",filepath)
    # print("0",filepath[0])
    # print(type(filepath))
    df = pd.read_csv(filepath[0], skipinitialspace=True, usecols=['Track Name', 'Artist Name(s)'])
    export = []
    # limit = 0
    for i, j in zip(df['Track Name'], df['Artist Name(s)']):
        # for j in df['Artist Name(s)']:
        # if limit >= 5:
            # break
        # print(j)
        # print(i)
        matches = deezer_search(j, i)
        # print(matches)
        # print("MATCHES 0",matches[0])
        try:
            out = analyze_selected_track(matches[0])
        except:
            print("song not found on deezer")
        else:
            # print("OUT", out)
            estimated_key, tempo = librosa_analysis(out)
            # print(out, "-", estimated_key," and " ,tempo)
            # print(matches[0])
            export.append({"track": i, "artist": j, "key": estimated_key, "tempo": tempo})
            # limit += 1
    return export

# data = read_csv('data.csv')

# df = pd.DataFrame(data)
# df = pd.DataFrame.from_dict(data)
# df = pd.DataFrame.from_records(data)
# df.to_csv("Filename.csv")
