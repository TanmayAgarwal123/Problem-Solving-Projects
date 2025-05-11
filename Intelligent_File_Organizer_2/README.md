# Intelligent File Organizer 2.0

An AI-powered file organization system that automatically classifies, organizes, and manages your files using machine learning.

## Features

- **AI-Powered Classification**: Uses deep learning to intelligently categorize files based on content
- **Smart Duplicate Detection**: Finds similar files, not just exact matches
- **Automated Scheduling**: Set up automatic organization on daily, weekly, or custom schedules
- **Analytics Dashboard**: Track organization statistics and visualize file distributions
- **Professional GUI**: User-friendly interface with PyQt5
- **File Clustering**: Groups similar files together automatically
- **Content Analysis**: Deep inspection of file contents for better classification

## Tech Stack

- **Backend**: Python 3.8+
- **AI/ML**: TensorFlow, Scikit-learn, OpenCV
- **GUI**: PyQt5
- **Database**: SQLite
- **Task Scheduling**: Windows Task Scheduler integration

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/intelligent-file-organizer.git
cd intelligent-file-organizer
```

2. Create and activate virtual environment:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```
4. Run the application:
```bash
python main.py
```