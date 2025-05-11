import sqlite3
from datetime import datetime, timedelta
import json
import logging
from ai_engine import AIEngine
import pandas as pd

class SmartFollowUpSystem:
    def __init__(self, ai_engine=None, db_path='whatsapp_pro.db'):
        self.db_path = db_path
        self.ai_engine = ai_engine or AIEngine()
        self.logger = logging.getLogger(__name__)
        
        # Initialize database
        self.init_database()
    
    def init_database(self):
        """Initialize follow-up tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS follow_ups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contact TEXT,
                original_message_id INTEGER,
                follow_up_type TEXT,
                follow_up_message TEXT,
                scheduled_time TIMESTAMP,
                executed BOOLEAN,
                response_received BOOLEAN,
                created_at TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS follow_up_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                trigger_condition TEXT,
                follow_up_delay INTEGER,
                message_template TEXT,
                max_attempts INTEGER,
                active BOOLEAN
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_follow_up_rules(self):
        """Create default follow-up rules"""
        default_rules = [
            {
                'name': 'No Response - 24h',
                'trigger_condition': json.dumps({'type': 'no_response', 'hours': 24}),
                'follow_up_delay': 24,
                'message_template': 'Hi {first_name}, just following up on my previous message. Did you have a chance to review it?',
                'max_attempts': 2
            },
            {
                'name': 'Positive Response Follow-up',
                'trigger_condition': json.dumps({'type': 'sentiment', 'value': 'positive'}),
                'follow_up_delay': 48,
                'message_template': 'Hi {first_name}, great to hear from you! Is there anything specific you\'d like to know more about?',
                'max_attempts': 1
            },
            {
                'name': 'Negative Response Recovery',
                'trigger_condition': json.dumps({'type': 'sentiment', 'value': 'negative'}),
                'follow_up_delay': 1,
                'message_template': 'Hi {first_name}, I understand your concern. Let me help resolve this issue. Could you please provide more details?',
                'max_attempts': 1
            },
            {
                'name': 'Partial Response',
                'trigger_condition': json.dumps({'type': 'response_length', 'max_words': 5}),
                'follow_up_delay': 6,
                'message_template': 'Thanks for your response, {first_name}. Could you elaborate a bit more so I can better assist you?',
                'max_attempts': 1
            }
        ]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for rule in default_rules:
            cursor.execute('''
                INSERT OR REPLACE INTO follow_up_rules 
                (name, trigger_condition, follow_up_delay, message_template, max_attempts, active)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                rule['name'],
                rule['trigger_condition'],
                rule['follow_up_delay'],
                rule['message_template'],
                rule['max_attempts'],
                True
            ))
        
        conn.commit()
        conn.close()
    
    def analyze_conversation(self, contact, message_id):
        """Analyze conversation and determine if follow-up is needed"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get conversation history
        cursor.execute('''
            SELECT * FROM messages 
            WHERE contact = ? AND id >= ?
            ORDER BY sent_time
        ''', (contact, message_id))
        
        messages = cursor.fetchall()
        
        # Get active follow-up rules
        cursor.execute('SELECT * FROM follow_up_rules WHERE active = 1')
        rules = cursor.fetchall()
        
        # Analyze against each rule
        for rule in rules:
            rule_data = {
                'id': rule[0],
                'name': rule[1],
                'trigger_condition': json.loads(rule[2]),
                'follow_up_delay': rule[3],
                'message_template': rule[4],
                'max_attempts': rule[5]
            }
            
            if self.check_trigger_condition(messages, rule_data['trigger_condition']):
                self.schedule_follow_up(contact, message_id, rule_data)
        
        conn.close()
    
    def check_trigger_condition(self, messages, condition):
        """Check if a trigger condition is met"""
        condition_type = condition.get('type')
        
        if condition_type == 'no_response':
            hours = condition.get('hours', 24)
            
            # Check if original message has no response within specified hours
            if len(messages) == 1:  # Only original message exists
                sent_time = datetime.fromisoformat(messages[0][4])  # sent_time column
                if datetime.now() - sent_time > timedelta(hours=hours):
                    return True
        
        elif condition_type == 'sentiment':
            expected_sentiment = condition.get('value')
            
            # Check last response sentiment
            for message in reversed(messages):
                if message[8]:  # response column
                    sentiment_score, sentiment_label = self.ai_engine.analyze_sentiment(message[8])
                    if sentiment_label.lower() == expected_sentiment.lower():
                        return True
        
        elif condition_type == 'response_length':
            max_words = condition.get('max_words', 5)
            
            # Check if response is too short
            for message in reversed(messages):
                if message[8]:  # response column
                    word_count = len(message[8].split())
                    if word_count <= max_words:
                        return True
        
        elif condition_type == 'keyword':
            keywords = condition.get('keywords', [])
            
            # Check if response contains specific keywords
            for message in reversed(messages):
                if message[8]:  # response column
                    response_lower = message[8].lower()
                    if any(keyword.lower() in response_lower for keyword in keywords):
                        return True
        
        return False
    
    def schedule_follow_up(self, contact, original_message_id, rule_data):
        """Schedule a follow-up message"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if follow-up already exists
        cursor.execute('''
            SELECT COUNT(*) FROM follow_ups 
            WHERE contact = ? AND original_message_id = ? AND follow_up_type = ?
        ''', (contact, original_message_id, rule_data['name']))
        
        if cursor.fetchone()[0] > 0:
            conn.close()
            return
        
        # Get contact data for personalization
        cursor.execute('SELECT * FROM contacts WHERE phone = ?', (contact,))
        contact_data = cursor.fetchone()
        
        # Personalize message
        message = self.personalize_message(rule_data['message_template'], contact_data)
        
        # Calculate follow-up time
        follow_up_time = datetime.now() + timedelta(hours=rule_data['follow_up_delay'])
        
        # Insert follow-up
        cursor.execute('''
            INSERT INTO follow_ups 
            (contact, original_message_id, follow_up_type, follow_up_message, 
             scheduled_time, executed, response_received, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            contact,
            original_message_id,
            rule_data['name'],
            message,
            follow_up_time,
            False,
            False,
            datetime.now()
        ))
        
        conn.commit()
        conn.close()
        
        self.logger.info(f"Scheduled follow-up for {contact} at {follow_up_time}")
    
    def get_pending_follow_ups(self):
        """Get all pending follow-ups that need to be executed"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM follow_ups 
            WHERE executed = 0 AND scheduled_time <= ?
        ''', (datetime.now(),))
        
        follow_ups = cursor.fetchall()
        conn.close()
        
        return follow_ups
    
    def execute_follow_up(self, follow_up_id):
        """Mark a follow-up as executed"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE follow_ups 
            SET executed = 1 
            WHERE id = ?
        ''', (follow_up_id,))
        
        conn.commit()
        conn.close()
    
    def analyze_follow_up_effectiveness(self):
        """Analyze the effectiveness of follow-up campaigns"""
        conn = sqlite3.connect(self.db_path)
        
        # Get follow-up statistics
        query = '''
            SELECT 
                follow_up_type,
                COUNT(*) as total_follow_ups,
                SUM(CASE WHEN response_received = 1 THEN 1 ELSE 0 END) as responses,
                AVG(CASE WHEN response_received = 1 THEN 1.0 ELSE 0.0 END) as response_rate
            FROM follow_ups
            WHERE executed = 1
            GROUP BY follow_up_type
        '''
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        return df
    
    def get_follow_up_suggestions(self, contact):
        """Get AI-powered follow-up suggestions for a contact"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get contact history
        cursor.execute('''
            SELECT * FROM messages 
            WHERE contact = ? 
            ORDER BY sent_time DESC 
            LIMIT 10
        ''', (contact,))
        
        messages = cursor.fetchall()
        
        # Get contact data
        cursor.execute('SELECT * FROM contacts WHERE phone = ?', (contact,))
        contact_data = cursor.fetchone()
        
        conn.close()
        
        # Analyze conversation pattern
        suggestions = []
        
        if messages:
            # Check last interaction time
            last_message_time = datetime.fromisoformat(messages[0][4])
            days_since = (datetime.now() - last_message_time).days
            
            if days_since > 30:
                suggestions.append({
                    'type': 're-engagement',
                    'message': f"Hi {contact_data[2]}, it's been a while! We have some exciting updates to share...",
                    'priority': 'high'
                })
            elif days_since > 7:
                suggestions.append({
                    'type': 'check-in',
                    'message': f"Hi {contact_data[2]}, just checking in. How's everything going?",
                    'priority': 'medium'
                })
            
            # Check sentiment trend
            sentiments = [msg[9] for msg in messages if msg[9] is not None]
            if sentiments and sum(sentiments) / len(sentiments) < 0:
                suggestions.append({
                    'type': 'satisfaction-check',
                    'message': f"Hi {contact_data[2]}, we want to ensure you're completely satisfied. Is there anything we can improve?",
                    'priority': 'high'
                })
            
            # Check for unanswered questions
            last_sent_message = next((msg for msg in messages if msg[3] == 'sent'), None)
            if last_sent_message and '?' in last_sent_message[2] and not any(msg[8] for msg in messages):
                suggestions.append({
                    'type': 'question-follow-up',
                    'message': f"Hi {contact_data[2]}, I noticed you might not have seen my previous question. When would be a good time to discuss?",
                    'priority': 'high'
                })
        
        return suggestions
    
    def personalize_message(self, template, contact_data):
        """Personalize message template"""
        if not contact_data:
            return template
        
        # Extract contact info
        phone = contact_data[1]
        name = contact_data[2] or 'there'
        first_name = name.split()[0] if name != 'there' else 'there'
        
        # Replace placeholders
        message = template.replace('{name}', name)
        message = message.replace('{first_name}', first_name)
        message = message.replace('{phone}', phone)
        
        # Add dynamic elements based on contact data
        preferences = json.loads(contact_data[6]) if contact_data[6] else {}
        
        if preferences.get('preferred_name'):
            message = message.replace(name, preferences['preferred_name'])
        
        return message
    
    def generate_follow_up_report(self):
        """Generate a comprehensive follow-up report"""
        conn = sqlite3.connect(self.db_path)
        
        # Overall statistics
        overall_stats = pd.read_sql_query('''
            SELECT 
                COUNT(*) as total_follow_ups,
                SUM(CASE WHEN executed = 1 THEN 1 ELSE 0 END) as executed,
                SUM(CASE WHEN response_received = 1 THEN 1 ELSE 0 END) as responses,
                AVG(CASE WHEN response_received = 1 THEN 1.0 ELSE 0.0 END) as response_rate
            FROM follow_ups
        ''', conn)
        
        # Performance by type
        type_performance = pd.read_sql_query('''
            SELECT 
                follow_up_type,
                COUNT(*) as count,
                AVG(CASE WHEN response_received = 1 THEN 1.0 ELSE 0.0 END) as response_rate
            FROM follow_ups
            WHERE executed = 1
            GROUP BY follow_up_type
            ORDER BY response_rate DESC
        ''', conn)
        
        # Best performing templates
        template_performance = pd.read_sql_query('''
            SELECT 
                follow_up_message,
                COUNT(*) as times_used,
                AVG(CASE WHEN response_received = 1 THEN 1.0 ELSE 0.0 END) as response_rate
            FROM follow_ups
            WHERE executed = 1
            GROUP BY follow_up_message
            HAVING COUNT(*) > 5
            ORDER BY response_rate DESC
            LIMIT 10
        ''', conn)
        
        conn.close()
        
        return {
            'overall_stats': overall_stats,
            'type_performance': type_performance,
            'template_performance': template_performance
        }
