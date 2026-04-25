import sys
import analysis_functions as af
import datetime
import os

from PySide6.QtCore import Qt, QUrl, QTimer
from PySide6.QtGui import QPixmap
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QLineEdit,
    QMainWindow,
    QVBoxLayout,
    QWidget,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QHBoxLayout,
    QGroupBox,
    QDialog,
    QDialogButtonBox,
    QCheckBox,
    QFrame,
    QScrollArea,
    QProgressBar,
    QSizePolicy,
    QTextEdit,
    QFileDialog,
    QStackedWidget
)



# Progress bar for analysis
class AnalysisProgressDialog(QDialog):
    def __init__(self, total_tracks, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Analyzing Tracks")
        # dont prevent interacting with the main window
        self.setModal(False)
        self.setMinimumWidth(500)
        self.setMinimumHeight(350)
        
        # stay on top
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        
        self.total_tracks = total_tracks
        self.completed_tracks = 0
        
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # title
        title_label = QLabel("Analysis Progress")
        title_label.setObjectName("dialogTitle")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #DABFFF;
                padding: 10px;
            }
        """)
        
        # overall progress
        overall_group = QGroupBox("Overall Progress")
        overall_layout = QVBoxLayout(overall_group)
        
        self.overall_progress_bar = QProgressBar()
        self.overall_progress_bar.setRange(0, self.total_tracks)
        self.overall_progress_bar.setValue(0)
        self.overall_progress_bar.setTextVisible(True)
        self.overall_progress_bar.setFormat("%v / %m tracks completed")
        self.overall_progress_bar.setMinimumHeight(30)
        self.overall_progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #967bb6;
                border-radius: 8px;
                text-align: center;
                font-weight: bold;
                font-size: 14px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 6px;
            }
        """)
        
        overall_layout.addWidget(self.overall_progress_bar)
        
        # Current track
        current_group = QGroupBox("Current Track")
        current_layout = QVBoxLayout(current_group)
        
        self.current_track_label = QLabel("Waiting to start...")
        self.current_track_label.setWordWrap(True)
        self.current_track_label.setAlignment(Qt.AlignCenter)
        self.current_track_label.setMinimumHeight(50)
        self.current_track_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #FFFFFF;
                padding: 10px;
                background-color: #2A2A2A;
                border-radius: 6px;
            }
        """)
        
        current_layout.addWidget(self.current_track_label)
        
        # Track progress
        self.track_progress_bar = QProgressBar()
        self.track_progress_bar.setRange(0, 100)
        self.track_progress_bar.setValue(0)
        self.track_progress_bar.setTextVisible(True)
        self.track_progress_bar.setFormat("%p%")
        self.track_progress_bar.setMinimumHeight(25)
        self.track_progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #535353;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #967bb6;
                border-radius: 4px;
            }
        """)
        
        current_layout.addWidget(self.track_progress_bar)
        
        # Status label
        self.status_label = QLabel("Preparing analysis...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #B3B3B3;
                padding: 5px;
            }
        """)
        
        # Completed tracks list
        completed_group = QGroupBox("Completed Tracks")
        completed_layout = QVBoxLayout(completed_group)
        
        self.completed_list = QTextEdit()
        self.completed_list.setReadOnly(True)
        self.completed_list.setMaximumHeight(150)
        self.completed_list.setStyleSheet("""
            QTextEdit {
                background-color: #1E1E1E;
                border: 1px solid #3A3A3A;
                border-radius: 5px;
                padding: 8px;
                color: #4CAF50;
                font-size: 11px;
            }
        """)
        
        completed_layout.addWidget(self.completed_list)

        layout.addWidget(title_label)
        layout.addWidget(overall_group)
        layout.addWidget(current_group)
        layout.addWidget(self.status_label)
        layout.addWidget(completed_group)
        
    # updates progress bar
    def update_progress(self, current_track_info, track_progress, status=""):
        
        self.current_track_label.setText(
            f"Current: {current_track_info.get('track', 'Unknown')} - {current_track_info.get('artist', 'Unknown')}"
            # "Current: "+current_track_info.get('track', 'Unknown') - current_track_info.get('artist', 'Unknown')
        )
        self.track_progress_bar.setValue(track_progress)
        
        if status:
            self.status_label.setText(status)
            
    def track_completed(self, track_info, success=True):
        """Mark a track as completed"""
        self.completed_tracks += 1
        self.overall_progress_bar.setValue(self.completed_tracks)
        
        # Add to completed list
        status_symbol = "✓" if success else "✗"
        
        track_text = f"{status_symbol} {track_info.get('track', 'Unknown')} - {track_info.get('artist', 'Unknown')}"
        
        # Append to completed list
        current_text = self.completed_list.toPlainText()
        if current_text:
            self.completed_list.setPlainText(current_text + "\n" + track_text)
        else:
            self.completed_list.setPlainText(track_text)
            
        # Scroll to bottom
        self.completed_list.verticalScrollBar().setValue(
            self.completed_list.verticalScrollBar().maximum()
        )
        
        # Check if all tracks are completed
        if self.completed_tracks >= self.total_tracks:
            self.analysis_complete()
            
    def analysis_complete(self):
        """Called when all tracks have been analyzed"""
        self.status_label.setText("✓ Analysis complete! ✓")
        self.status_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #4CAF50;
                padding: 5px;
                font-weight: bold;
            }
        """)
        self.current_track_label.setText("All tracks analyzed successfully!")
        



# popup window confirming if the user would like to analyze/download the selected track
class ConfirmationDialog(QDialog):
    def __init__(self, track_info, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Confirm Download")
        self.setModal(True)

        print(track_info)
        
        layout = QVBoxLayout()
        
        self.label = QLabel("Would you like to analyze:\n")
        self.label_artist = QLabel("Artist: "+track_info['artist'])
        self.label_track = QLabel("Track: "+track_info['track'])
        self.label_album = QLabel("Album: "+track_info['album'])
        self.label_notice = QLabel("Please be aware that a 30 second preview of the song will be downloaded in wav format. This is necessary to perform acoustic analysis")

        self.label_notice.setStyleSheet("font-size: 10px")
        
        self.label.setWordWrap(True)
        layout.addWidget(self.label)
        layout.addWidget(self.label_track)
        layout.addWidget(self.label_artist)
        layout.addWidget(self.label_album)
        
        # yes/no buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Yes | QDialogButtonBox.No
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        layout.addWidget(self.label_notice)
        
        self.setLayout(layout)
        self.resize(400, 250)


class AnalysisView(QWidget):
    """Widget to display analysis results for a single track"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.track_info = None
        self.track_name = None
        self.player = None
        self.audio = None
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(self.update_progress)
        
        self.setup_ui()
        
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # CENTER PANEL - Analysis Data
        center_panel = QWidget()
        center_layout = QVBoxLayout(center_panel)
        center_layout.setSpacing(10)
        center_layout.setContentsMargins(5, 5, 5, 5)
        
        # Top row with tempo, key, genre
        stats_row = QHBoxLayout()
        stats_row.setSpacing(15)

        # Tempo box
        self.tempo_group = QGroupBox("Tempo")
        tempo_layout = QVBoxLayout(self.tempo_group)
        self.tempo_value_label = QLabel("--")
        self.tempo_value_label.setObjectName("statValue")
        self.tempo_value_label.setAlignment(Qt.AlignCenter)
        tempo_layout.addWidget(self.tempo_value_label)
        tempo_layout.setAlignment(Qt.AlignCenter)

        # Key box
        self.key_group = QGroupBox("Estimated Key")
        key_layout = QVBoxLayout(self.key_group)
        self.key_value_label = QLabel("--")
        self.key_value_label.setObjectName("statValue")
        self.key_value_label.setAlignment(Qt.AlignCenter)
        key_layout.addWidget(self.key_value_label)
        key_layout.setAlignment(Qt.AlignCenter)

        # Genre box
        self.genre_group = QGroupBox("Genre")
        genre_layout = QVBoxLayout(self.genre_group)
        self.genre_value_label = QLabel("--")
        self.genre_value_label.setObjectName("statValue")
        self.genre_value_label.setWordWrap(True)
        self.genre_value_label.setAlignment(Qt.AlignCenter)
        self.genre_value_label.setMinimumHeight(40)
        genre_layout.addWidget(self.genre_value_label)
        genre_layout.setAlignment(Qt.AlignCenter)

        stats_row.addWidget(self.tempo_group)
        stats_row.addWidget(self.key_group)
        stats_row.addWidget(self.genre_group)

        center_layout.addLayout(stats_row)

        # Visualization row
        viz_row = QHBoxLayout()
        viz_row.setSpacing(10)
        
        # Analysis Visualization Area
        librosa_viz_group = QGroupBox("Audio Analysis Visualizations")
        librosa_group_layout = QVBoxLayout(librosa_viz_group)
        
        self.librosa_viz_scroll = QScrollArea()
        self.librosa_viz_scroll.setWidgetResizable(True)
        self.librosa_viz_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.librosa_viz_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.librosa_viz_scroll.setMinimumHeight(300)

        viz_container = QWidget()
        self.librosa_viz_layout = QVBoxLayout(viz_container)
        self.librosa_viz_layout.setSpacing(10)
        self.librosa_viz_layout.setContentsMargins(5, 5, 5, 5)

        self.librosa_viz_scroll.setWidget(viz_container)
        librosa_group_layout.addWidget(self.librosa_viz_scroll)
        viz_row.addWidget(librosa_viz_group, 3)

        # Audio Features and Lyrics
        info_container = QWidget()
        info_container_layout = QVBoxLayout(info_container)
        info_container_layout.setSpacing(10)
        
        # Audio Features Group - styled like "Currently Selected"
        audio_features_group = QGroupBox("Audio Features")
        audio_features_layout = QVBoxLayout(audio_features_group)
        audio_features_layout.setSpacing(8)
        
        # Create labels with proper styling
        self.energy_label = QLabel("Energy: --")
        self.energy_label.setObjectName("detailLabel")
        self.energy_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        self.valence_label = QLabel("Valence: --")
        self.valence_label.setObjectName("detailLabel")
        self.valence_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        self.loudness_label = QLabel("Loudness: --")
        self.loudness_label.setObjectName("detailLabel")
        self.loudness_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        self.loudness_norm_label = QLabel("Loudness Normalized: --")
        self.loudness_norm_label.setObjectName("detailLabel")
        self.loudness_norm_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        self.duration_label = QLabel("Duration: --")
        self.duration_label.setObjectName("detailLabel")
        self.duration_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.danceability_label = QLabel("Danceability: --")
        self.danceability_label.setObjectName("detailLabel")
        self.danceability_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    
        # Add labels to layout
        audio_features_layout.addWidget(self.energy_label)
        audio_features_layout.addWidget(self.valence_label)
        audio_features_layout.addWidget(self.danceability_label)
        audio_features_layout.addWidget(self.loudness_label)
        audio_features_layout.addWidget(self.loudness_norm_label)
        audio_features_layout.addWidget(self.duration_label)
        audio_features_layout.addStretch()

        # Lyrics Group
        lyrics_group = QGroupBox("Lyrics")
        lyrics_layout = QVBoxLayout(lyrics_group)
        
        self.lyrics_text = QTextEdit()
        self.lyrics_text.setReadOnly(True)
        self.lyrics_text.setPlainText("Select a track from Saved Analyses to view results")
        self.lyrics_text.setMaximumHeight(200)
        
        lyrics_layout.addWidget(self.lyrics_text)
        
        info_container_layout.addWidget(audio_features_group)
        info_container_layout.addWidget(lyrics_group)
        viz_row.addWidget(info_container, 2)

        center_layout.addLayout(viz_row)
        center_layout.setStretch(0, 1)
        center_layout.setStretch(1, 4)
        
        main_layout.addWidget(center_panel)

    def set_track(self, track_info, track_name):
        """Set the track to display and update the analysis"""
        self.track_info = track_info
        self.track_name = track_name
        self.update_analysis_display()

    def update_analysis_display(self):
        """Update all analysis displays with results"""
        if not self.track_info or not self.track_name:
            return
        
        # LIBROSA analysis
        key, tempo = af.librosa_analysis(self.track_name)
        af.librosa_graphs(self.track_name)
        tempo_value = round(tempo[0]) if tempo else 0
        
        self.tempo_value_label.setText(str(tempo_value) + " BPM")
        self.key_value_label.setText(str(key) if key else "--")
        
        # Clear existing visualizations
        self.clear_main_viz_layout()
        
        # Create scroll area for graphs
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setMinimumHeight(300)
        
        graphs_container = QWidget()
        graphs_container_layout = QVBoxLayout(graphs_container)
        graphs_container_layout.setSpacing(15)
        graphs_container_layout.setContentsMargins(10, 10, 10, 10)
        
        # Graph files to display
        graph_files = [
            ("figs/chromagram.png", "Chromagram"),
            ("figs/spectrograms.png", "Spectrogram"),
            ("figs/amp_over_time.png", "Amplitude Over Time")
        ]
        
        for graph_file, title in graph_files:
            graph_card = QFrame()
            graph_card.setObjectName("graphCard")
            graph_card.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
            graph_card.setLineWidth(1)
            
            card_layout = QVBoxLayout(graph_card)
            card_layout.setSpacing(8)
            card_layout.setContentsMargins(10, 10, 10, 10)
            
            title_label = QLabel(title)
            title_label.setObjectName("graphTitle")
            title_label.setAlignment(Qt.AlignCenter)
            title_label.setStyleSheet("""
                QLabel {
                    font-weight: bold;
                    font-size: 14px;
                    color: #967bb6;
                    padding: 5px;
                }
            """)
            
            image_container = QFrame()
            image_container.setObjectName("imageContainer")
            image_container.setFrameStyle(QFrame.Panel | QFrame.Sunken)
            image_container.setLineWidth(2)
            image_container.setStyleSheet("""
                QFrame#imageContainer {
                    background-color: white;
                    border: 1px solid #967bb6;
                    border-radius: 6px;
                    padding: 5px;
                }
            """)
            
            image_layout = QVBoxLayout(image_container)
            image_layout.setContentsMargins(5, 5, 5, 5)
            
            image_label = QLabel()
            image_label.setAlignment(Qt.AlignCenter)
            image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            image_label.setMinimumHeight(200)
            image_label.setMaximumHeight(300)
            
            if os.path.exists(graph_file):
                pixmap = QPixmap(graph_file)
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(600, 250, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    image_label.setPixmap(scaled_pixmap)
            
            image_layout.addWidget(image_label)
            card_layout.addWidget(title_label)
            card_layout.addWidget(image_container)
            graphs_container_layout.addWidget(graph_card)
        
        graphs_container_layout.addStretch()
        scroll_area.setWidget(graphs_container)
        self.librosa_viz_layout.addWidget(scroll_area)
        
        # Get lyrics
        lyrics = af.lyrics_genius(self.track_info.get('artist', ''), self.track_info.get('track', ''))
        self.lyrics_text.setPlainText(lyrics)
        
        # Get audio features
        # Get audio features
        try:
            energy = af.get_energy(self.track_name)
            valence = af.get_valence(self.track_name)
            loudness, loudness_norm = af.get_loudness(self.track_name)
            danceability = af.get_danceability(self.track_name)
            
            # Get duration from track_info
            track_duration_seconds = int(self.track_info.get('duration', 0))
            track_duration = str(datetime.timedelta(seconds=track_duration_seconds))

            # Update labels with formatted values
            self.energy_label.setText(f"Energy: {energy}")
            self.valence_label.setText(f"Valence: {valence}")
            self.danceability_label.setText(f"Danceability: {danceability}")
            self.loudness_label.setText(f"Loudness: {loudness:.1f} dB")
            self.loudness_norm_label.setText(f"Loudness Normalized -14 dB LUFS: {loudness_norm:.1f} dB")
            self.duration_label.setText(f"Duration: {track_duration}")
            
            
            # Get genre
            genre_data = af.get_genre(
                album_name=self.track_info.get('album', ''),
                artist_name=self.track_info.get('artist', ''),
                track_name=self.track_info.get('track', '')
            )
            
            if genre_data and genre_data.get("genres"):
                genres = genre_data["genres"]
                genres_text = ", ".join(genres)
                self.genre_value_label.setText(genres_text)
            else:
                self.genre_value_label.setText("No genres found")
                
        except Exception as e:
            print(f"Error fetching audio features: {e}")
            import traceback
            traceback.print_exc()
            self.energy_label.setText("Energy: Error")
            self.valence_label.setText("Valence: Error")
            self.loudness_label.setText("Loudness: Error")
            self.loudness_norm_label.setText("Loudness Normalized: Error")
            self.duration_label.setText("Duration: Error")
            self.danceability_label.setText("Danceability: Error")
        
        # Setup media player
        self.setup_media_player()

    def clear_main_viz_layout(self):
        while self.librosa_viz_layout.count():
            item = self.librosa_viz_layout.takeAt(0)
            if item.widget():
                widget = item.widget()
                widget.setParent(None)
                widget.deleteLater()

    # Media player methods
    def setup_media_player(self):
        audio_url = f"audio_files/{self.track_name}.wav"
        
        if self.player:
            self.player.stop()
            self.player.deleteLater()
            self.player = None
        
        self.player = QMediaPlayer()
        self.audio = QAudioOutput()
        self.player.setAudioOutput(self.audio)
        
        self.player.mediaStatusChanged.connect(self.on_media_status_changed)
        self.player.durationChanged.connect(self.on_duration_changed)
        self.player.positionChanged.connect(self.on_position_changed)
        self.player.playbackStateChanged.connect(self.on_playback_state_changed)
        
        self.player.setSource(QUrl.fromLocalFile(audio_url))

    def toggle_playback(self):
        if not self.player:
            return
            
        if self.player.playbackState() == QMediaPlayer.PlayingState:
            self.player.pause()
            self.progress_timer.stop()
        else:
            self.player.play()
            self.progress_timer.start(100)

    def seek_position(self, position):
        if self.player and self.player.duration() > 0:
            seek_pos = (position / 100) * self.player.duration()
            self.player.setPosition(int(seek_pos))

    def update_progress(self):
        if self.player and self.player.duration() > 0:
            position = self.player.position()
            duration = self.player.duration()
            if duration > 0:
                progress = (position / duration) * 100

    def on_duration_changed(self, duration):
        pass

    def on_position_changed(self, position):
        pass

    def on_playback_state_changed(self, state):
        pass

    def on_media_status_changed(self, status):
        if status == QMediaPlayer.EndOfMedia:
            self.progress_timer.stop()

    def get_analysis_data(self):
        """Return the analysis data for export"""
        if not self.track_info:
            return {}
        
        # Extract values from labels, handling potential errors
        try:
            key = self.key_value_label.text() if self.key_value_label.text() != "--" else "Unknown"
            tempo = self.tempo_value_label.text().replace(' BPM', '') if self.tempo_value_label.text() != "--" else "Unknown"
            genre = self.genre_value_label.text() if self.genre_value_label.text() != "--" else "Unknown"
            energy = self.energy_label.text().replace('Energy: ', '') if 'Energy: --' not in self.energy_label.text() else "Unknown"
            valence = self.valence_label.text().replace('Valence: ', '') if 'Valence: --' not in self.valence_label.text() else "Unknown"
            loudness = self.loudness_label.text().replace('Loudness: ', '').replace(' dB', '') if 'Loudness: --' not in self.loudness_label.text() else "Unknown"
            loudness_norm = self.loudness_norm_label.text().replace('Loudness Normalized -14 dB LUFS: ', '').replace(' dB', '') if 'Loudness Normalized' in self.loudness_norm_label.text() and '--' not in self.loudness_norm_label.text() else "Unknown"
            
            return {
                'key': key,
                'tempo': tempo,
                'genre': genre,
                'energy': energy,
                'valence': valence,
                'loudness': loudness,
                'loudness_norm': loudness_norm
            }
        except Exception as e:
            print(f"Error getting analysis data: {e}")
            return {
                'key': 'Error',
                'tempo': 'Error',
                'genre': 'Error',
                'energy': 'Error',
                'valence': 'Error',
                'loudness': 'Error',
                'loudness_norm': 'Error'
            }


class QueueTrackWidget(QWidget):
    """Widget representing a track in the queue with a checkbox"""
    def __init__(self, track_info, parent=None):
        super().__init__(parent)
        self.track_info = track_info
        self.setMinimumHeight(35)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 3, 5, 3)
        layout.setSpacing(8)
        
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(True)
        
        track_text = f"{self.track_info.get('track', 'Unknown')} - {self.track_info.get('artist', 'Unknown')}"
        self.label = QLabel(track_text)
        self.label.setWordWrap(True)
        self.label.setMinimumHeight(25)
        
        layout.addWidget(self.checkbox)
        layout.addWidget(self.label)
        layout.addStretch()
        
    def is_checked(self):
        return self.checkbox.isChecked()
    
    def set_checked(self, checked):
        self.checkbox.setChecked(checked)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Armonía - Music Information Retrieval Dashboard")
        self.setMinimumSize(1200, 900)

        self.artist_name = ""
        self.track_name = ""
        self.selected_track = {}
        self.player = None
        self.audio = None
        self.analysis_queue = []
        self.queue_widgets = []
        self.progress_dialog = None  # Keep reference to progress dialog
        
        # Cache for analysis views
        self.analysis_views = {}  # key: track_name, value: AnalysisView
        self.current_track_name = None
        self.saved_analyses_data = [] 
        
        # self.progress_timer = QTimer()
        # self.progress_timer.timeout.connect(self.update_progress)

        # Central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # LEFT PANEL - Search and Queue
        left_panel = QWidget()
        left_panel.setObjectName("leftPanel")
        left_panel.setMaximumWidth(350)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(3)

      
        
        # Search
        search_group = QGroupBox("Track Search")
        search_layout = QVBoxLayout(search_group)
        search_layout.setSpacing(5)
        
        self.a_label = QLabel("Artist Name")
        self.t_label = QLabel("Track Name")
        self.a_input = QLineEdit()
        self.t_input = QLineEdit()
        self.covers_check = QCheckBox("Include Covers")
        
        search_layout.addWidget(self.a_label)
        search_layout.addWidget(self.a_input)
        search_layout.addWidget(self.t_label)
        search_layout.addWidget(self.t_input)
        search_layout.addWidget(self.covers_check)
        
        self.search_button = QPushButton("Search For Track")
        self.search_button.clicked.connect(self.search_song)
        self.search_button.setMinimumHeight(40)
        
        search_layout.addWidget(self.search_button)
        
        # Search Results
        results_group = QGroupBox("Search Results")
        results_layout = QVBoxLayout(results_group)
        self.result_list = QListWidget()
        self.result_list.itemClicked.connect(self.on_track_selected)
        self.search_results_full = []
        results_layout.addWidget(self.result_list)
        
        # Add to Queue button
        self.add_to_queue_button = QPushButton("Add Selected to Queue")
        self.add_to_queue_button.clicked.connect(self.add_to_queue)
        self.add_to_queue_button.setEnabled(False)
        self.add_to_queue_button.setMinimumHeight(30)
        
        left_layout.addWidget(search_group)
        left_layout.addWidget(results_group)
        left_layout.addWidget(self.add_to_queue_button)

        # Queue Section
        queue_group = QGroupBox("Analysis Queue")
        queue_main_layout = QVBoxLayout(queue_group)

        # Queue controls (Select All and Remove Selected buttons)
        queue_controls = QHBoxLayout()
        self.select_all_button = QPushButton("Select All")
        self.select_all_button.clicked.connect(self.toggle_select_all_queue)
        self.remove_selected_button = QPushButton("Remove Selected")
        self.remove_selected_button.clicked.connect(self.remove_selected_from_queue)

        queue_controls.addWidget(self.select_all_button)
        queue_controls.addWidget(self.remove_selected_button)

        # Queue scroll area (contains the list of tracks)
        self.queue_scroll = QScrollArea()
        self.queue_scroll.setWidgetResizable(True)
        self.queue_scroll.setMinimumHeight(150)
        self.queue_scroll.setMaximumHeight(300)  # Set a maximum height
        self.queue_scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  # Fixed vertical policy

        self.queue_container = QWidget()
        self.queue_layout = QVBoxLayout(self.queue_container)
        self.queue_layout.setSpacing(2)
        self.queue_layout.setContentsMargins(5, 5, 5, 5)
        # Remove the stretch at the end
        # self.queue_layout.addStretch()  # REMOVE THIS LINE

        self.queue_scroll.setWidget(self.queue_container)

        # Analyze Selected button (now outside the scroll area)
        self.analyze_selected_button = QPushButton("Analyze Selected Tracks")
        self.analyze_selected_button.clicked.connect(self.analyze_selected_tracks)
        self.analyze_selected_button.setEnabled(False)
        self.analyze_selected_button.setMinimumHeight(40)
        self.analyze_selected_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
            }
            QPushButton:disabled {
                background-color: #535353;
                color: #808080;
            }
        """)

        # Add all widgets to the queue_main_layout
        queue_main_layout.addLayout(queue_controls)
        queue_main_layout.addWidget(self.queue_scroll)
        
        # queue_main_layout.addWidget(self.analyze_selected_button)
        

        left_layout.addWidget(queue_group)
        left_layout.addWidget(self.analyze_selected_button)
        left_layout.addStretch()

        # CENTER PANEL - Stacked Widget for Multiple Analysis Views
        center_panel = QWidget()
        center_layout = QVBoxLayout(center_panel)
        center_layout.setSpacing(0)
        center_layout.setContentsMargins(0, 0, 0, 0)
        
        # Stacked widget to hold multiple analysis views
        self.stacked_widget = QStackedWidget()
        center_layout.addWidget(self.stacked_widget)
        
        # Add a placeholder widget for when no analysis is selected
        self.placeholder_widget = QWidget()
        placeholder_layout = QVBoxLayout(self.placeholder_widget)
        placeholder_label = QLabel("Select a track from Saved Analyses to view results")
        placeholder_label.setAlignment(Qt.AlignCenter)
        placeholder_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                color: #B3B3B3;
                padding: 50px;
            }
        """)
        placeholder_layout.addWidget(placeholder_label)
        self.stacked_widget.addWidget(self.placeholder_widget)

        # RIGHT PANEL - Info and Media Player
        right_panel = QWidget()
        right_panel.setObjectName("rightPanel")
        right_panel.setMaximumWidth(300)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(15)



          # Import CSV
        # Import CSV
        self.import_button = QPushButton("Analyze Tracks From CSV File")
        self.import_button.clicked.connect(self.import_csv)

        # Export CSV button
        self.export_button = QPushButton("Export Saved Analyses to CSV")
        self.export_button.clicked.connect(self.export_to_csv)
        self.export_button.setEnabled(False)  # Initially disabled until there are saved analyses
        self.export_button.setMinimumHeight(35)
        self.export_button.setStyleSheet("""
            QPushButton {
                background-color: #5a4a6e;
                color: white;
                font-weight: bold;
            }
            QPushButton:disabled {
                background-color: #535353;
                color: #808080;
            }
        """)

 
        
        # Track Details
        info_group = QGroupBox("Currently Selected")
        info_layout = QVBoxLayout(info_group)
        
        self.detail_artist = QLabel("Artist: --")
        self.detail_track = QLabel("Track: --")
        self.detail_album = QLabel("Album: --")
        self.detail_year = QLabel("Year: --")
        
        info_layout.addWidget(self.detail_track)
        info_layout.addWidget(self.detail_artist)
        info_layout.addWidget(self.detail_album)
        info_layout.addWidget(self.detail_year)
        
        info_layout.addStretch()
        
        # Media Player
        media_group = QGroupBox("Audio Preview")
        media_layout = QVBoxLayout(media_group)

        self.track_info_label = QLabel("No track loaded")
        self.track_info_label.setAlignment(Qt.AlignCenter)
        self.track_info_label.setWordWrap(True)
        self.track_info_label.setObjectName("trackInfo")
        self.track_info_label.setMinimumHeight(60)






        control_layout = QHBoxLayout()
        self.play_button = QPushButton("▶")
        self.play_button.setObjectName("play_button")
        self.play_button.clicked.connect(self.toggle_playback)
        self.play_button.setFixedSize(40, 40)
        self.play_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.play_button.setEnabled(False)

        control_layout.addStretch()
        control_layout.addWidget(self.play_button)
        control_layout.addStretch()

        media_layout.addWidget(self.track_info_label)
        media_layout.addLayout(control_layout)
        media_layout.addStretch()

        # Saved Analyses (Previous Analyses)
        saved_a_group = QGroupBox("Saved Analyses")
        saved_a_layout = QVBoxLayout(saved_a_group)
        
        self.saved_a_list = QListWidget()
        self.saved_a_list.itemClicked.connect(self.load_previous_analysis)
        saved_a_layout.addWidget(self.saved_a_list)
        
        right_layout.addWidget(info_group)
        right_layout.addWidget(media_group)
        right_layout.addWidget(saved_a_group)
        right_layout.addWidget(self.import_button)
        right_layout.addWidget(self.export_button)
        right_layout.addStretch()
        
        # Add panels to main layout
        main_layout.addWidget(left_panel)
        main_layout.addWidget(center_panel)
        main_layout.addWidget(right_panel)
        
        main_layout.setStretchFactor(left_panel, 1)
        main_layout.setStretchFactor(center_panel, 3)
        main_layout.setStretchFactor(right_panel, 1)

    def toggle_select_all_queue(self):
        """Toggle between selecting all and deselecting all tracks in the queue"""
        if not self.queue_widgets:
            return
        
        # all_selected = 
        
        if all(widget.is_checked() for widget in self.queue_widgets):
            for widget in self.queue_widgets:
                widget.set_checked(False)
            self.select_all_button.setText("Select All")
        else:
            for widget in self.queue_widgets:
                widget.set_checked(True)
            self.select_all_button.setText("Deselect All")
        
        self.update_analyze_button_state()

    def update_select_all_button_state(self):
        """Update the Select All button text based on current selection state"""
        if not self.queue_widgets:
            self.select_all_button.setText("Select All")
            return
        
        
        if all(widget.is_checked() for widget in self.queue_widgets):
            self.select_all_button.setText("Deselect All")
        else:
            self.select_all_button.setText("Select All")

    def on_queue_checkbox_changed(self):
        """Handle checkbox state changes"""
        self.update_analyze_button_state()
        self.update_select_all_button_state()

    def show_progress_dialog(self):
        """Show the progress dialog if it exists"""
        if self.progress_dialog:
            self.progress_dialog.show()
            self.progress_dialog.raise_()
            self.progress_dialog.activateWindow()

    def analyze_selected_tracks(self):
        """Analyze all checked tracks in the queue"""
        tracks_to_analyze = []
        
        for i, widget in enumerate(self.queue_widgets):
            if widget.is_checked():
                tracks_to_analyze.append(self.analysis_queue[i])
        
        if not tracks_to_analyze:
            return
        
        # Create and show progress dialog
        self.progress_dialog = AnalysisProgressDialog(len(tracks_to_analyze), self)
        self.progress_dialog.show()
        QApplication.processEvents()
        
        self.analyze_selected_button.setEnabled(False)
        self.analyze_selected_button.setText("Analyzing...")
        QApplication.processEvents()
        
        # Analyze each track
        for i, track_info in enumerate(tracks_to_analyze):
            # Update progress dialog for current track
            if self.progress_dialog:
                self.progress_dialog.update_progress(track_info, 0, f"Starting analysis ({i+1}/{len(tracks_to_analyze)})")
                QApplication.processEvents()
            
            # Analyze the track
            success = self.analyze_single_track_with_progress(track_info)
            
            # Mark track as completed
            if self.progress_dialog:
                self.progress_dialog.track_completed(track_info, success)
                QApplication.processEvents()
        
        self.analyze_selected_button.setText("Analyze Selected Tracks")
        self.analyze_selected_button.setEnabled(True)
        print("REMOVE SELECTED")
        self.remove_selected_from_queue()

    def analyze_single_track_with_progress(self, track_info):
        """Analyze a single track with progress updates"""
        QApplication.processEvents()
        
        try:
            # Update progress - downloading
            if self.progress_dialog:
                self.progress_dialog.update_progress(track_info, 10, "Downloading preview...")
                QApplication.processEvents()
            
            track_name = af.analyze_selected_track(track_info)
            
            if not track_name:
                if self.progress_dialog:
                    self.progress_dialog.update_progress(track_info, 0, "Download failed!")
                return False
            
            # Update progress - analyzing
            if self.progress_dialog:
                self.progress_dialog.update_progress(track_info, 40, "Performing audio analysis...")
                QApplication.processEvents()
            
            # Create and cache the analysis view
            analysis_view = AnalysisView()
            
            # Update progress - generating visualizations
            if self.progress_dialog:
                self.progress_dialog.update_progress(track_info, 60, "Generating visualizations...")
                QApplication.processEvents()
            
            # Set the track and generate analysis (this takes time but only once)
            analysis_view.set_track(track_info, track_name)
            
            # Get analysis data for export
            analysis_data = analysis_view.get_analysis_data()
            
            # Cache the view
            self.analysis_views[track_name] = analysis_view
            self.stacked_widget.addWidget(analysis_view)
            
            # Update progress - fetching metadata
            if self.progress_dialog:
                self.progress_dialog.update_progress(track_info, 80, "Fetching metadata...")
                QApplication.processEvents()
            
            # Add to history with analysis data
            self.add_to_history(track_info, track_name, analysis_data)
            
            # If this is the first analysis, display it
            if len(self.analysis_views) == 1:
                self.stacked_widget.setCurrentWidget(analysis_view)
                self.current_track_name = track_name
                self.update_track_info_display(track_info)
                self.play_button.setEnabled(True)
            
            # Update progress - complete
            if self.progress_dialog:
                self.progress_dialog.update_progress(track_info, 100, "Analysis complete!")
            
            return True
            
        except Exception as e:
            print(f"Error: {e}")
            if self.progress_dialog:
                self.progress_dialog.update_progress(track_info, 0, f"Error: {str(e)[:50]}")
            return False

    def add_to_history(self, track_info, track_name, analysis_data=None):
        """Add analysis to history list"""
        item_text = f"{track_info.get('track', 'Unknown')} - {track_info.get('artist', 'Unknown')}"
        item = QListWidgetItem(item_text)
        item.setData(Qt.UserRole, {'track_info': track_info, 'track_name': track_name})
        self.saved_a_list.insertItem(0, item)
        
        # Store analysis data for export
        if analysis_data:
            self.saved_analyses_data.append({
                'track_info': track_info,
                'analysis_data': analysis_data
            })
        
        # Enable export button if there's data
        if self.saved_analyses_data:
            self.export_button.setEnabled(True)
        
        # Limit history to 20 items
        while self.saved_a_list.count() > 20:
            # Remove the oldest item
            oldest_item = self.saved_a_list.takeItem(self.saved_a_list.count() - 1)
            if oldest_item:
                data = oldest_item.data(Qt.UserRole)
                if data:
                    old_track_name = data['track_name']
                    # Remove from cache if it exists and isn't currently displayed
                    if old_track_name in self.analysis_views and old_track_name != self.current_track_name:
                        view = self.analysis_views[old_track_name]
                        self.stacked_widget.removeWidget(view)
                        view.deleteLater()
                        del self.analysis_views[old_track_name]
            
            # Also remove oldest from saved_analyses_data
            if len(self.saved_analyses_data) > 20:
                self.saved_analyses_data.pop(0)
        # END OF METHOD - NO RETURN STATEMENT

   
        
      

    def load_previous_analysis(self, item):
        """Load a previous analysis from history - instant switch!"""
        data = item.data(Qt.UserRole)
        if data:
            track_info = data['track_info']
            track_name = data['track_name']
            # pause the playback when changing to a different song
            current_view = self.get_current_analysis_view()
            if current_view and hasattr(current_view, 'player') and current_view.player:
                if current_view.player.playbackState() == QMediaPlayer.PlayingState:
                    current_view.player.pause()
                    # Update play button state
                    self.play_button.setText("▶")
            
            # Check if we have this analysis cached
            if track_name in self.analysis_views:
                # Just switch to the cached view - instant!
                self.stacked_widget.setCurrentWidget(self.analysis_views[track_name])
                self.current_track_name = track_name
                
                self.update_track_info_display(track_info)
                self.play_button.setEnabled(True)
            else:
                # This shouldn't happen, but just in case
                print(f"Warning: Analysis for {track_name} not found in cache")

    def get_current_analysis_view(self):
        """Get the currently displayed analysis view"""
        if self.current_track_name and self.current_track_name in self.analysis_views:
            return self.analysis_views[self.current_track_name]
        return None

    def search_song(self):
        self.artist_name = self.a_input.text()
        self.track_name = self.t_input.text()

        if not self.artist_name or not self.track_name:
            return
        
        self.search_button.setText("Searching...")
        self.search_button.setEnabled(False)
        QApplication.processEvents()
        
        try:
            self.search_results_full = af.deezer_search(self.artist_name, self.track_name) 
            self.display_results(self.search_results_full)
        except Exception as e:
            print(f"Search error: {str(e)}")
        finally:
            self.search_button.setText("Search For Track")
            self.search_button.setEnabled(True)

    def display_results(self, results):
        self.result_list.clear()

        if self.covers_check.isChecked():
            for i, track in enumerate(results):
                item_text = f"{track['track']} - {track['artist']}"
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, i)
                self.result_list.addItem(item)
        else:
            i = 0
            track = results[0]
            item_text = f"{track['track']} - {track['artist']}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, i)
            self.result_list.addItem(item)

    def on_track_selected(self, item):
        index = item.data(Qt.UserRole)
        self.selected_track = self.search_results_full[index]

        self.detail_track.setText("Track: " + self.selected_track.get('track', '--'))
        self.detail_artist.setText("Artist: " + self.selected_track.get('artist', '--'))
        self.detail_album.setText("Album: " + self.selected_track.get('album', '--'))
        

        self.detail_year.setText("Release Date: " + str(self.selected_track.get('release_date', '--')))
        
        self.add_to_queue_button.setEnabled(True)

    def add_to_queue(self):
        """Add selected track to the analysis queue"""
        if not self.selected_track:
            return
        
        # Check if track is already in queue
        for track in self.analysis_queue:
            if (track.get('track') == self.selected_track.get('track') and 
                track.get('artist') == self.selected_track.get('artist')):
                return
        
        self.analysis_queue.append(self.selected_track.copy())
        
        # Add widget to queue display
        queue_widget = QueueTrackWidget(self.selected_track)
        self.queue_layout.insertWidget(self.queue_layout.count() - 1, queue_widget)
        self.queue_widgets.append(queue_widget)
        
        self.update_analyze_button_state()
        self.update_select_all_button_state()
        
        queue_widget.checkbox.stateChanged.connect(self.on_queue_checkbox_changed)

    def remove_selected_from_queue(self):
        """Remove checked tracks from the queue"""
        widgets_to_remove = []
        tracks_to_remove = []
        
        for i, widget in enumerate(self.queue_widgets):
            if widget.is_checked():
                widgets_to_remove.append(widget)
                tracks_to_remove.append(self.analysis_queue[i])
        
        for widget in widgets_to_remove:
            self.queue_layout.removeWidget(widget)
            widget.deleteLater()
            self.queue_widgets.remove(widget)
        
        for track in tracks_to_remove:
            self.analysis_queue.remove(track)
        
        self.update_analyze_button_state()
        self.update_select_all_button_state()

    def update_analyze_button_state(self):
        """Enable/disable analyze button based on checked items"""
        has_checked = any(widget.is_checked() for widget in self.queue_widgets)
        self.analyze_selected_button.setEnabled(has_checked)

    def export_to_csv(self):
        """Export saved analyses to CSV file"""
        if not self.saved_analyses_data:
            return
        
        # Open file dialog to choose save location
        dialog = QFileDialog(self)
        filepath, _ = QFileDialog.getSaveFileName(
            self, 
            "Save CSV File", 
            "saved_analyses.csv", 
            "CSV Files (*.csv)"
        )
        
        if filepath:
            try:
                # Call the export function from search module
                filename = af.export_saved_analyses_to_csv(self.saved_analyses_data, filepath)
                
                # Show success message (optional)
                msg = QDialog(self)
                msg.setWindowTitle("Export Successful")
                msg.setMinimumWidth(300)
                layout = QVBoxLayout(msg)
                label = QLabel(f"Successfully exported {len(self.saved_analyses_data)} tracks to:\n{filename}")
                label.setWordWrap(True)
                label.setAlignment(Qt.AlignCenter)
                layout.addWidget(label)
                ok_button = QPushButton("OK")
                ok_button.clicked.connect(msg.accept)
                layout.addWidget(ok_button)
                msg.exec()
                
            except Exception as e:
                # Show error message
                msg = QDialog(self)
                msg.setWindowTitle("Export Failed")
                msg.setMinimumWidth(300)
                layout = QVBoxLayout(msg)
                label = QLabel(f"Failed to export data:\n{str(e)}")
                label.setWordWrap(True)
                label.setAlignment(Qt.AlignCenter)
                layout.addWidget(label)
                ok_button = QPushButton("OK")
                ok_button.clicked.connect(msg.accept)
                layout.addWidget(ok_button)
                msg.exec()
                
    def import_csv(self):
        dialog = QFileDialog(self)
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Select CSV File", "", "CSV Files (*.csv)"
        )
        
        if filepath:
            import time
            start_time = time.time()
            
            data = af.read_csv(filepath)
            
            # Add all tracks to queue
            for track in data:
                self.analysis_queue.append(track)
                
                queue_widget = QueueTrackWidget(track)
                self.queue_layout.insertWidget(self.queue_layout.count() - 1, queue_widget)
                self.queue_widgets.append(queue_widget)
                queue_widget.checkbox.stateChanged.connect(self.on_queue_checkbox_changed)
            
            self.update_analyze_button_state()
            self.update_select_all_button_state()
            
            print("--- %s seconds ---" % (time.time() - start_time))

    def update_track_info_display(self, track_info):
        """Update the track info display in the right panel"""
        # Update media player label
        self.track_info_label.setText(f"{track_info.get('track', 'Unknown')}\n{track_info.get('artist', 'Unknown')}")
        
        # Update Currently Selected box
        self.detail_track.setText("Track: " + track_info.get('track', '--'))
        self.detail_artist.setText("Artist: " + track_info.get('artist', '--'))
        self.detail_album.setText("Album: " + track_info.get('album', '--'))
        
        # Format release date if it exists
        release_date = track_info.get('release_date', '--')
        if release_date and release_date != '--':
            self.detail_year.setText("Release Date: " + str(release_date))
        else:
            self.detail_year.setText("Release Date: --")

    # Media player methods
    def toggle_playback(self):
        current_view = self.get_current_analysis_view()
        if current_view and hasattr(current_view, 'toggle_playback'):
            current_view.toggle_playback()
            self.update_play_button_state()

    # def seek_position(self, position):
    #     current_view = self.get_current_analysis_view()
    #     if current_view and hasattr(current_view, 'seek_position'):
    #         current_view.seek_position(position)

    def update_progress(self):
        current_view = self.get_current_analysis_view()
        if current_view and hasattr(current_view, 'update_progress'):
            current_view.update_progress()

    def update_play_button_state(self):
        current_view = self.get_current_analysis_view()
        if current_view and hasattr(current_view, 'player'):
            if current_view.player and current_view.player.playbackState() == QMediaPlayer.PlayingState:
                self.play_button.setText("⏸")
            else:
                self.play_button.setText("▶")

    def on_media_status_changed(self, status):
        if status == QMediaPlayer.EndOfMedia:
            self.play_button.setText("▶")


app = QApplication(sys.argv)
window = MainWindow()

# Load and apply stylesheet
try:
    with open("style.qss", "r") as f:
        STYLE_QSS = f.read()
    window.setStyleSheet(STYLE_QSS)
except FileNotFoundError:
    print("style.qss not found, using default styling")

window.showMaximized()
app.exec()