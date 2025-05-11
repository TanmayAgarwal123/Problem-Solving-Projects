import sqlite3
import json
from datetime import datetime, timedelta
import os

class Analytics:
    def __init__(self, db_path="file_organizer.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize the analytics database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS organization_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                file_path TEXT,
                file_name TEXT,
                file_size INTEGER,
                original_location TEXT,
                new_location TEXT,
                category TEXT,
                action TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def log_organization(self, file_info, category, action="organized"):
        """Log file organization event"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO organization_log 
            (timestamp, file_path, file_name, file_size, category, action)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now(),
            file_info['path'],
            file_info['name'],
            file_info['size'],
            category,
            action
        ))
        
        conn.commit()
        conn.close()
    
    def get_statistics(self):
        """Get comprehensive statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total files organized
        cursor.execute('SELECT COUNT(*) FROM organization_log')
        total_files = cursor.fetchone()[0]
        
        # Total size
        cursor.execute('SELECT SUM(file_size) FROM organization_log')
        total_size = cursor.fetchone()[0] or 0
        
        # By category
        cursor.execute('''
            SELECT category, COUNT(*), SUM(file_size)
            FROM organization_log
            GROUP BY category
        ''')
        by_category = {}
        for category, count, size in cursor.fetchall():
            by_category[category] = {
                'count': count,
                'size': size or 0
            }
        
        # Timeline (last 30 days)
        cursor.execute('''
            SELECT date(timestamp), COUNT(*)
            FROM organization_log
            WHERE timestamp > datetime('now', '-30 days')
            GROUP BY date(timestamp)
            ORDER BY date(timestamp)
        ''')
        timeline = {}
        for date, count in cursor.fetchall():
            timeline[date] = count
        
        # Last run
        cursor.execute('SELECT MAX(timestamp) FROM organization_log')
        last_run = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_files': total_files,
            'total_size': total_size,
            'by_category': by_category,
            'timeline': timeline,
            'last_run': last_run
        }