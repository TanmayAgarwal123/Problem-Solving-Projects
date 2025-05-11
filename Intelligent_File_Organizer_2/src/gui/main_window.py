import sys
import os
import json
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QPushButton, QFileDialog, QTextEdit,
                           QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
                           QMessageBox, QLabel, QComboBox, QTimeEdit, QSpinBox,
                           QCheckBox, QGroupBox, QRadioButton, QButtonGroup)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QTime
from PyQt5.QtGui import QIcon, QPixmap
import pyqtgraph as pg
from datetime import datetime

from ..core.organizer import SmartOrganizer
from ..core.scheduler import ScheduleManager
from ..utils.analytics import Analytics

class OrganizeThread(QThread):
    update_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(dict)
    
    def __init__(self, source_folder, destination_folder=None, organization_mode="type",
                 preserve_structure=True, include_subfolders=False):
        super().__init__()
        self.source_folder = source_folder
        self.destination_folder = destination_folder
        self.organization_mode = organization_mode
        self.preserve_structure = preserve_structure
        self.include_subfolders = include_subfolders
    
    def run(self):
        try:
            organizer = SmartOrganizer()
            self.update_signal.emit(f"Starting organization by {self.organization_mode}...")
            stats = organizer.organize_folder(
                self.source_folder, 
                self.destination_folder,
                organization_mode=self.organization_mode,
                preserve_structure=self.preserve_structure,
                include_subfolders=self.include_subfolders
            )
            self.finished_signal.emit(stats)
        except Exception as e:
            self.update_signal.emit(f"Error: {str(e)}")
            self.finished_signal.emit({"error": str(e)})

class FileOrganizerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.scheduler = ScheduleManager()
        self.analytics = Analytics()
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Intelligent File Organizer 2.0")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.create_organize_tab()
        self.create_schedule_tab()
        self.create_analytics_tab()
        self.create_settings_tab()
        
        # Set style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QTabWidget::pane {
                border: 1px solid #cccccc;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #e0e0e0;
                padding: 10px 20px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid #0084ff;
            }
            QPushButton {
                background-color: #0084ff;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0066cc;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
    def create_organize_tab(self):
        organize_widget = QWidget()
        layout = QVBoxLayout(organize_widget)
        
        # Folder selection
        folder_group = QGroupBox("Folder Selection")
        folder_layout = QVBoxLayout()

        warning_label = QLabel("⚠️ Always test on a small folder first and ensure backups exist!")
        warning_label.setStyleSheet("color: red; font-weight: bold; padding: 10px;")
        layout.addWidget(warning_label)
        
        # Source folder
        source_layout = QHBoxLayout()
        self.source_label = QLabel("Source Folder: Not selected")
        self.source_btn = QPushButton("Select Source")
        self.source_btn.clicked.connect(self.select_source_folder)
        source_layout.addWidget(self.source_label)
        source_layout.addWidget(self.source_btn)
        source_layout.addStretch()
        folder_layout.addLayout(source_layout)
        
        # Destination folder
        dest_layout = QHBoxLayout()
        self.dest_label = QLabel("Destination: Same as source")
        self.dest_btn = QPushButton("Select Destination")
        self.dest_btn.clicked.connect(self.select_destination_folder)
        dest_layout.addWidget(self.dest_label)
        dest_layout.addWidget(self.dest_btn)
        dest_layout.addStretch()
        folder_layout.addLayout(dest_layout)
        
        folder_group.setLayout(folder_layout)
        layout.addWidget(folder_group)
        
        # Organization Method
        method_group = QGroupBox("Organization Method")
        method_layout = QVBoxLayout()
        
        self.method_group = QButtonGroup()
        
        type_radio = QRadioButton("Organize by File Type")
        type_radio.setChecked(True)
        self.method_group.addButton(type_radio, 0)
        method_layout.addWidget(type_radio)
        
        date_radio = QRadioButton("Organize by Date (Year/Month)")
        self.method_group.addButton(date_radio, 1)
        method_layout.addWidget(date_radio)
        
        size_radio = QRadioButton("Organize by Size")
        self.method_group.addButton(size_radio, 2)
        method_layout.addWidget(size_radio)
        
        ai_radio = QRadioButton("AI-Powered Organization (Advanced)")
        self.method_group.addButton(ai_radio, 3)
        method_layout.addWidget(ai_radio)
        
        method_group.setLayout(method_layout)
        layout.addWidget(method_group)
        
        # Options
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout()
        
        self.preserve_structure = QCheckBox("Preserve existing folder structure (Recommended)")
        self.preserve_structure.setChecked(True)
        self.preserve_structure.setToolTip("Keep files in existing subfolders unchanged")
        options_layout.addWidget(self.preserve_structure)
        
        self.include_subfolders = QCheckBox("Include files from subfolders")
        self.include_subfolders.setChecked(False)  # Default to False for safety
        self.include_subfolders.setToolTip("Process files in subdirectories (only works if not preserving structure)")
        options_layout.addWidget(self.include_subfolders)
        
        # Connect to disable include_subfolders when preserve_structure is checked
        self.preserve_structure.stateChanged.connect(self.on_preserve_structure_changed)
        
        self.handle_duplicates = QCheckBox("Remove exact duplicates")
        self.handle_duplicates.setChecked(True)
        options_layout.addWidget(self.handle_duplicates)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        # Organize button
        self.organize_btn = QPushButton("Organize Files")
        self.organize_btn.clicked.connect(self.organize_files)
        self.organize_btn.setEnabled(False)
        layout.addWidget(self.organize_btn)
        
        # Progress display
        self.progress_text = QTextEdit()
        self.progress_text.setReadOnly(True)
        layout.addWidget(self.progress_text)
        
        self.tab_widget.addTab(organize_widget, "Organize")
    
    def on_preserve_structure_changed(self, state):
        """Disable include_subfolders when preserve_structure is checked"""
        if state == Qt.Checked:
            self.include_subfolders.setChecked(False)
            self.include_subfolders.setEnabled(False)
        else:
            self.include_subfolders.setEnabled(True)
        
    def create_schedule_tab(self):
        schedule_widget = QWidget()
        layout = QVBoxLayout(schedule_widget)
        
        # Add schedule form
        form_layout = QHBoxLayout()
        
        self.schedule_folder = QLabel("No folder selected")
        self.schedule_folder_btn = QPushButton("Select Folder")
        self.schedule_folder_btn.clicked.connect(self.select_schedule_folder)
        
        self.schedule_type = QComboBox()
        self.schedule_type.addItems(["Daily", "Weekly", "Hourly", "Every X Minutes"])
        self.schedule_type.currentTextChanged.connect(self.on_schedule_type_changed)
        
        self.schedule_time = QTimeEdit()
        self.schedule_time.setTime(QTime(9, 0))
        
        self.schedule_day = QComboBox()
        self.schedule_day.addItems(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
        self.schedule_day.hide()
        
        self.schedule_minutes = QSpinBox()
        self.schedule_minutes.setRange(5, 1440)
        self.schedule_minutes.setValue(60)
        self.schedule_minutes.setSuffix(" minutes")
        self.schedule_minutes.hide()
        
        form_layout.addWidget(self.schedule_folder)
        form_layout.addWidget(self.schedule_folder_btn)
        form_layout.addWidget(self.schedule_type)
        form_layout.addWidget(self.schedule_time)
        form_layout.addWidget(self.schedule_day)
        form_layout.addWidget(self.schedule_minutes)
        
        self.add_schedule_btn = QPushButton("Add Schedule")
        self.add_schedule_btn.clicked.connect(self.add_schedule)
        form_layout.addWidget(self.add_schedule_btn)
        
        layout.addLayout(form_layout)
        
        # Schedule list
        self.schedule_table = QTableWidget()
        self.schedule_table.setColumnCount(6)
        self.schedule_table.setHorizontalHeaderLabels(["ID", "Folder", "Type", "Time", "Last Run", "Actions"])
        self.schedule_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.schedule_table)
        
        # Load existing schedules
        self.refresh_schedule_list()
        
        self.tab_widget.addTab(schedule_widget, "Schedule")
        
    def create_analytics_tab(self):
        analytics_widget = QWidget()
        layout = QVBoxLayout(analytics_widget)
        
        # Summary statistics
        stats_layout = QHBoxLayout()
        
        self.total_files_label = QLabel("Total Files Organized: 0")
        self.total_size_label = QLabel("Total Size: 0 MB")
        self.last_run_label = QLabel("Last Run: Never")
        
        stats_layout.addWidget(self.total_files_label)
        stats_layout.addWidget(self.total_size_label)
        stats_layout.addWidget(self.last_run_label)
        stats_layout.addStretch()
        
        layout.addLayout(stats_layout)
        
        # Charts
        charts_layout = QHBoxLayout()
        
        # File type distribution chart
        self.type_chart = pg.PlotWidget(title="File Type Distribution")
        self.type_chart.setBackground('w')
        charts_layout.addWidget(self.type_chart)
        
        # Organization timeline chart
        self.timeline_chart = pg.PlotWidget(title="Organization Timeline")
        self.timeline_chart.setBackground('w')
        self.timeline_chart.setLabel('left', 'Files')
        self.timeline_chart.setLabel('bottom', 'Date')
        charts_layout.addWidget(self.timeline_chart)
        
        layout.addLayout(charts_layout)
        
        # Detailed statistics table
        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(4)
        self.stats_table.setHorizontalHeaderLabels(["Category", "File Count", "Total Size", "Percentage"])
        self.stats_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.stats_table)
        
        # Refresh button
        refresh_btn = QPushButton("Refresh Analytics")
        refresh_btn.clicked.connect(self.refresh_analytics)
        layout.addWidget(refresh_btn)
        
        self.tab_widget.addTab(analytics_widget, "Analytics")
        
    def create_settings_tab(self):
        settings_widget = QWidget()
        layout = QVBoxLayout(settings_widget)
        
        # File Type Mappings
        mapping_group = QGroupBox("File Type Mappings")
        mapping_layout = QVBoxLayout()
        
        self.mapping_table = QTableWidget()
        self.mapping_table.setColumnCount(2)
        self.mapping_table.setHorizontalHeaderLabels(["Category", "Extensions"])
        self.mapping_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # Load default mappings
        self.load_file_mappings()
        
        mapping_layout.addWidget(self.mapping_table)
        
        # Add/Remove mapping buttons
        mapping_btn_layout = QHBoxLayout()
        add_mapping_btn = QPushButton("Add Category")
        add_mapping_btn.clicked.connect(self.add_mapping_row)
        remove_mapping_btn = QPushButton("Remove Selected")
        remove_mapping_btn.clicked.connect(self.remove_mapping_row)
        mapping_btn_layout.addWidget(add_mapping_btn)
        mapping_btn_layout.addWidget(remove_mapping_btn)
        mapping_btn_layout.addStretch()
        mapping_layout.addLayout(mapping_btn_layout)
        
        mapping_group.setLayout(mapping_layout)
        layout.addWidget(mapping_group)
        
        # Advanced Settings
        advanced_group = QGroupBox("Advanced Settings")
        advanced_layout = QVBoxLayout()
        
        self.enable_ai_features = QCheckBox("Enable AI features (requires more resources)")
        advanced_layout.addWidget(self.enable_ai_features)
        
        self.enable_clustering = QCheckBox("Enable file clustering")
        advanced_layout.addWidget(self.enable_clustering)
        
        similarity_layout = QHBoxLayout()
        similarity_layout.addWidget(QLabel("Duplicate similarity threshold:"))
        self.similarity_threshold = QSpinBox()
        self.similarity_threshold.setRange(0, 100)
        self.similarity_threshold.setValue(85)
        self.similarity_threshold.setSuffix("%")
        similarity_layout.addWidget(self.similarity_threshold)
        similarity_layout.addStretch()
        advanced_layout.addLayout(similarity_layout)
        
        advanced_group.setLayout(advanced_layout)
        layout.addWidget(advanced_group)
        
        # Save button
        save_btn = QPushButton("Save Settings")
        save_btn.clicked.connect(self.save_settings)
        layout.addWidget(save_btn)
        
        layout.addStretch()
        
        self.tab_widget.addTab(settings_widget, "Settings")
        
    def select_source_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Source Folder")
        if folder:
            self.source_label.setText(f"Source Folder: {folder}")
            self.source_folder = folder
            self.organize_btn.setEnabled(True)
            
    def select_destination_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Destination Folder")
        if folder:
            self.dest_label.setText(f"Destination: {folder}")
            self.destination_folder = folder
        else:
            self.dest_label.setText("Destination: Same as source")
            self.destination_folder = None
            
    def organize_files(self):
        if not hasattr(self, 'source_folder'):
            return
            
        self.organize_btn.setEnabled(False)
        self.progress_text.clear()
        
        # Get selected organization method
        method_id = self.method_group.checkedId()
        organization_modes = ["type", "date", "size", "ai"]
        organization_mode = organization_modes[method_id]
        
        # Get options
        preserve_structure = self.preserve_structure.isChecked()
        include_subfolders = self.include_subfolders.isChecked()
        
        # Start organization in a separate thread
        self.organize_thread = OrganizeThread(
            self.source_folder,
            getattr(self, 'destination_folder', None),
            organization_mode,
            preserve_structure,
            include_subfolders
        )
        self.organize_thread.update_signal.connect(self.update_progress)
        self.organize_thread.finished_signal.connect(self.organization_finished)
        self.organize_thread.start()
        
    def update_progress(self, message):
        self.progress_text.append(f"{datetime.now().strftime('%H:%M:%S')}: {message}")
        
    def organization_finished(self, stats):
        self.organize_btn.setEnabled(True)
        if "error" in stats:
            QMessageBox.critical(self, "Error", f"Organization failed: {stats['error']}")
        else:
            QMessageBox.information(self, "Success", 
                f"Organization complete!\n"
                f"Files moved: {stats.get('moved', 0)}\n"
                f"Files preserved: {stats.get('preserved', 0)}\n"
                f"Duplicates found: {stats.get('duplicates', 0)}\n"
                f"Errors: {stats.get('errors', 0)}")
        self.refresh_analytics()
        
    def select_schedule_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder to Schedule")
        if folder:
            self.schedule_folder.setText(folder)
            self.scheduled_folder = folder
            
    def on_schedule_type_changed(self, text):
        self.schedule_time.setVisible(text in ["Daily", "Weekly"])
        self.schedule_day.setVisible(text == "Weekly")
        self.schedule_minutes.setVisible(text == "Every X Minutes")
        
    def add_schedule(self):
        if not hasattr(self, 'scheduled_folder'):
            QMessageBox.warning(self, "Warning", "Please select a folder first")
            return
            
        schedule_type = self.schedule_type.currentText().lower()
        
        # Prepare time value based on schedule type
        if schedule_type == "daily":
            time_value = self.schedule_time.time().toString("HH:mm")
        elif schedule_type == "weekly":
            day = self.schedule_day.currentText()
            time = self.schedule_time.time().toString("HH:mm")
            time_value = f"{day} {time}"
        elif schedule_type == "every x minutes":
            time_value = str(self.schedule_minutes.value())
            schedule_type = "minutes"
        else:
            time_value = None
            
        # Generate job ID
        job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Add schedule
        self.scheduler.add_schedule(job_id, self.scheduled_folder, schedule_type, time_value)
        
        QMessageBox.information(self, "Success", f"Schedule added successfully! Job ID: {job_id}")
        self.refresh_schedule_list()
        
    def refresh_schedule_list(self):
        schedules = self.scheduler.list_schedules()
        self.schedule_table.setRowCount(len(schedules))
        
        for i, schedule in enumerate(schedules):
            self.schedule_table.setItem(i, 0, QTableWidgetItem(schedule['id']))
            self.schedule_table.setItem(i, 1, QTableWidgetItem(schedule['folder']))
            self.schedule_table.setItem(i, 2, QTableWidgetItem(schedule['schedule_type']))
            self.schedule_table.setItem(i, 3, QTableWidgetItem(str(schedule.get('time_value', ''))))
            self.schedule_table.setItem(i, 4, QTableWidgetItem(schedule.get('last_run', 'Never')))
            
            # Add remove button
            remove_btn = QPushButton("Remove")
            remove_btn.clicked.connect(lambda checked, job_id=schedule['id']: self.remove_schedule(job_id))
            self.schedule_table.setCellWidget(i, 5, remove_btn)
            
    def remove_schedule(self, job_id):
        reply = QMessageBox.question(self, "Confirm", f"Remove schedule {job_id}?", 
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            if self.scheduler.remove_schedule(job_id):
                QMessageBox.information(self, "Success", "Schedule removed successfully!")
                self.refresh_schedule_list()
            else:
                QMessageBox.warning(self, "Error", "Failed to remove schedule")
                
    def refresh_analytics(self):
        try:
            stats = self.analytics.get_statistics()
            
            # Update summary labels
            self.total_files_label.setText(f"Total Files Organized: {stats['total_files']}")
            self.total_size_label.setText(f"Total Size: {stats['total_size'] / (1024*1024):.2f} MB")
            self.last_run_label.setText(f"Last Run: {stats.get('last_run', 'Never')}")
            
            # Update type distribution chart
            self.type_chart.clear()
            categories = list(stats['by_category'].keys())
            values = [stats['by_category'][cat]['count'] for cat in categories]
            
            if categories and values:
                bar_graph = pg.BarGraphItem(x=range(len(categories)), height=values, width=0.6)
                self.type_chart.addItem(bar_graph)
                self.type_chart.getAxis('bottom').setTicks([[(i, cat) for i, cat in enumerate(categories)]])
            
            # Update timeline chart
            self.timeline_chart.clear()
            timeline_data = stats.get('timeline', {})
            if timeline_data:
                dates = list(timeline_data.keys())
                counts = list(timeline_data.values())
                self.timeline_chart.plot(range(len(dates)), counts, pen='b', symbol='o')
                self.timeline_chart.getAxis('bottom').setTicks([[(i, date) for i, date in enumerate(dates)]])
            
            # Update statistics table
            self.stats_table.setRowCount(len(stats['by_category']))
            total_size = stats['total_size'] if stats['total_size'] > 0 else 1
            
            for i, (category, data) in enumerate(stats['by_category'].items()):
                self.stats_table.setItem(i, 0, QTableWidgetItem(category))
                self.stats_table.setItem(i, 1, QTableWidgetItem(str(data['count'])))
                self.stats_table.setItem(i, 2, QTableWidgetItem(f"{data['size'] / (1024*1024):.2f} MB"))
                percentage = (data['size'] / total_size) * 100
                self.stats_table.setItem(i, 3, QTableWidgetItem(f"{percentage:.1f}%"))
                
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load analytics: {str(e)}")
            
    def load_file_mappings(self):
        mappings = {
            "documents": ".pdf, .docx, .doc, .txt, .odt, .rtf",
            "images": ".jpg, .jpeg, .png, .gif, .bmp, .svg",
            "videos": ".mp4, .avi, .mkv, .mov, .wmv",
            "audio": ".mp3, .wav, .flac, .aac, .ogg",
            "archives": ".zip, .rar, .7z, .tar, .gz",
            "code": ".py, .js, .html, .css, .cpp, .java",
            "spreadsheets": ".xlsx, .xls, .csv, .ods",
            "presentations": ".pptx, .ppt, .odp"
        }
        
        self.mapping_table.setRowCount(len(mappings))
        for i, (category, extensions) in enumerate(mappings.items()):
            self.mapping_table.setItem(i, 0, QTableWidgetItem(category))
            self.mapping_table.setItem(i, 1, QTableWidgetItem(extensions))
    
    def add_mapping_row(self):
        row_count = self.mapping_table.rowCount()
        self.mapping_table.insertRow(row_count)
        self.mapping_table.setItem(row_count, 0, QTableWidgetItem("new_category"))
        self.mapping_table.setItem(row_count, 1, QTableWidgetItem(".ext"))
    
    def remove_mapping_row(self):
        current_row = self.mapping_table.currentRow()
        if current_row >= 0:
            self.mapping_table.removeRow(current_row)
            
    def save_settings(self):
        try:
            # Collect mappings from table
            mappings = {}
            for row in range(self.mapping_table.rowCount()):
                category = self.mapping_table.item(row, 0).text()
                extensions = self.mapping_table.item(row, 1).text()
                extensions_list = [ext.strip() for ext in extensions.split(',')]
                mappings[category] = extensions_list
            
            # Create config
            config = {
                "folders": mappings,
                "rules": {
                    "use_ai_classification": self.enable_ai_features.isChecked(),
                    "cluster_similar_files": self.enable_clustering.isChecked(),
                    "min_duplicate_similarity": self.similarity_threshold.value() / 100.0,
                    "preserve_folder_structure": True,
                    "organization_mode": "type"
                }
            }
            
            # Save to file
            with open("config.json", "w") as f:
                json.dump(config, f, indent=2)
            
            QMessageBox.information(self, "Success", "Settings saved successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings: {str(e)}")
        
    def closeEvent(self, event):
        self.scheduler.stop()
        event.accept()