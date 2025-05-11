import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from textblob import TextBlob
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import re
from datetime import datetime, timedelta
import json
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch

# Download required NLTK data
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
except:
    pass

class AIEngine:
    def __init__(self):
        self.sentiment_analyzer = None
        self.response_generator = None
        self.contact_analyzer = None
        self.message_optimizer = None
        
        # Initialize models
        self.initialize_models()
    
    def initialize_models(self):
        """Initialize AI/ML models"""
        try:
            # Sentiment analysis model
            self.sentiment_analyzer = pipeline(
                "sentiment-analysis",
                model="distilbert-base-uncased-finetuned-sst-2-english"
            )
            
            # Response generation model (for demo purposes)
            # In production, you'd use a more sophisticated model
            self.response_templates = {
                'positive': [
                    "Thank you for your positive feedback! We're glad you're happy with our service.",
                    "We appreciate your kind words! Is there anything else we can help you with?",
                    "That's wonderful to hear! We're always here to assist you."
                ],
                'neutral': [
                    "Thank you for your message. How can we assist you today?",
                    "We've received your message. Is there something specific you need help with?",
                    "Thanks for reaching out. We're here to help!"
                ],
                'negative': [
                    "We apologize for any inconvenience. Let us help resolve this issue.",
                    "We're sorry to hear about your experience. Can you provide more details?",
                    "We understand your concern and want to make things right."
                ]
            }
        except Exception as e:
            print(f"Error initializing models: {e}")
    
    def analyze_sentiment(self, text):
        """Analyze sentiment of text"""
        try:
            if self.sentiment_analyzer:
                result = self.sentiment_analyzer(text)[0]
                score = result['score'] if result['label'] == 'POSITIVE' else -result['score']
                return score, result['label']
            else:
                # Fallback to TextBlob
                blob = TextBlob(text)
                polarity = blob.sentiment.polarity
                label = 'POSITIVE' if polarity > 0.1 else 'NEGATIVE' if polarity < -0.1 else 'NEUTRAL'
                return polarity, label
        except Exception as e:
            print(f"Error in sentiment analysis: {e}")
            return 0.0, 'NEUTRAL'
    
    def personalize_message(self, template, contact_data):
        """Personalize message using contact data"""
        try:
            # Extract contact information
            name = contact_data.get('name', 'there')
            last_interaction = contact_data.get('last_interaction')
            preferences = contact_data.get('preferences', {})
            
            # Personalize message
            message = template.replace('{name}', name)
            
            # Add contextual personalization
            if last_interaction:
                days_since = (datetime.now() - last_interaction).days
                if days_since > 30:
                    message += f" It's been a while since we last connected!"
            
            # Add preference-based content
            if preferences:
                if preferences.get('preferred_time'):
                    message += f" (Best time to reach you: {preferences['preferred_time']})"
            
            return message
        except Exception as e:
            print(f"Error personalizing message: {e}")
            return template
    
    def optimize_send_time(self, contact_history):
        """Optimize message send time based on contact history"""
        try:
            if not contact_history:
                # Default to business hours
                return datetime.now().replace(hour=10, minute=0, second=0)
            
            # Analyze response patterns
            response_times = []
            for interaction in contact_history:
                if interaction.get('response_time'):
                    response_times.append(interaction['response_time'].hour)
            
            if response_times:
                # Find the most common response hour
                optimal_hour = max(set(response_times), key=response_times.count)
                return datetime.now().replace(hour=optimal_hour, minute=0, second=0)
            
            return datetime.now()
        except Exception as e:
            print(f"Error optimizing send time: {e}")
            return datetime.now()
    
    def cluster_contacts(self, contacts_df):
        """Cluster contacts based on behavior patterns"""
        try:
            # Features for clustering
            features = ['interaction_count', 'sentiment_score', 'response_rate']
            
            # Prepare data
            X = contacts_df[features].fillna(0)
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # Perform clustering
            kmeans = KMeans(n_clusters=3, random_state=42)
            contacts_df['cluster'] = kmeans.fit_predict(X_scaled)
            
            # Assign cluster labels
            cluster_labels = {
                0: 'High Engagement',
                1: 'Medium Engagement',
                2: 'Low Engagement'
            }
            
            contacts_df['engagement_level'] = contacts_df['cluster'].map(cluster_labels)
            
            return contacts_df
        except Exception as e:
            print(f"Error clustering contacts: {e}")
            return contacts_df
    
    def generate_response_suggestion(self, customer_message):
        """Generate AI response suggestion based on customer message"""
        try:
            # Analyze sentiment
            sentiment, label = self.analyze_sentiment(customer_message)
            
            # Select appropriate template
            templates = self.response_templates.get(label.lower(), self.response_templates['neutral'])
            
            # Choose a random template
            import random
            suggestion = random.choice(templates)
            
            # Add specific context if needed
            if "price" in customer_message.lower() or "cost" in customer_message.lower():
                suggestion += " I'd be happy to discuss our pricing options with you."
            elif "problem" in customer_message.lower() or "issue" in customer_message.lower():
                suggestion += " Let me help you resolve this as quickly as possible."
            elif "thank" in customer_message.lower():
                suggestion = "You're very welcome! Is there anything else I can help you with?"
            
            return suggestion
        except Exception as e:
            print(f"Error generating response suggestion: {e}")
            return "Thank you for your message. How can I assist you?"
    
    def predict_churn_risk(self, contact_data):
        """Predict customer churn risk using ML"""
        try:
            # Features that indicate churn risk
            days_since_interaction = (datetime.now() - contact_data.get('last_interaction', datetime.now())).days
            interaction_count = contact_data.get('interaction_count', 0)
            sentiment_score = contact_data.get('sentiment_score', 0)
            response_rate = contact_data.get('response_rate', 0)
            
            # Simple churn risk calculation (in production, use a trained ML model)
            risk_score = 0
            
            if days_since_interaction > 60:
                risk_score += 0.4
            elif days_since_interaction > 30:
                risk_score += 0.2
            
            if interaction_count < 5:
                risk_score += 0.2
            
            if sentiment_score < -0.5:
                risk_score += 0.3
            
            if response_rate < 0.3:
                risk_score += 0.1
            
            return min(risk_score, 1.0)
        except Exception as e:
            print(f"Error predicting churn risk: {e}")
            return 0.5
    
    def extract_keywords(self, text):
        """Extract keywords from text for better targeting"""
        try:
            # Remove stopwords
            stop_words = set(stopwords.words('english'))
            tokens = word_tokenize(text.lower())
            keywords = [word for word in tokens if word.isalnum() and word not in stop_words]
            
            # Use TF-IDF to find important terms
            if len(keywords) > 3:
                vectorizer = TfidfVectorizer(max_features=5)
                tfidf_matrix = vectorizer.fit_transform([' '.join(keywords)])
                feature_names = vectorizer.get_feature_names_out()
                return list(feature_names)
            
            return keywords[:5]
        except Exception as e:
            print(f"Error extracting keywords: {e}")
            return []
    
    def recommend_message_improvements(self, message):
        """Provide AI recommendations to improve message effectiveness"""
        recommendations = []
        
        try:
            # Check message length
            if len(message) > 500:
                recommendations.append("Consider making the message shorter for better engagement")
            elif len(message) < 50:
                recommendations.append("Consider adding more details to make the message more informative")
            
            # Check for personalization
            if "{name}" not in message and not re.search(r'\b(you|your)\b', message, re.I):
                recommendations.append("Add personalization by using the recipient's name or 'you/your'")
            
            # Check for call-to-action
            cta_keywords = ['click', 'visit', 'call', 'reply', 'contact', 'buy', 'order', 'subscribe']
            if not any(keyword in message.lower() for keyword in cta_keywords):
                recommendations.append("Add a clear call-to-action to improve response rates")
            
            # Check sentiment
            sentiment, label = self.analyze_sentiment(message)
            if label == 'NEGATIVE':
                recommendations.append("The message tone seems negative. Consider making it more positive")
            
            # Check for urgency (if promotional)
            if 'offer' in message.lower() or 'discount' in message.lower():
                urgency_words = ['limited', 'today', 'now', 'hurry', 'last chance', 'expires']
                if not any(word in message.lower() for word in urgency_words):
                    recommendations.append("Add urgency to promotional messages (e.g., 'limited time offer')")
            
            return recommendations
        except Exception as e:
            print(f"Error generating recommendations: {e}")
            return ["Error analyzing message"]
    
    def calculate_engagement_score(self, contact_data, message_history):
        """Calculate engagement score for a contact"""
        try:
            # Base score from interaction metrics
            interaction_count = contact_data.get('interaction_count', 0)
            response_rate = contact_data.get('response_rate', 0)
            avg_sentiment = contact_data.get('sentiment_score', 0)
            
            # Calculate base score
            base_score = (
                (min(interaction_count, 20) / 20) * 0.3 +  # Interaction frequency
                response_rate * 0.4 +                       # Response rate
                (avg_sentiment + 1) / 2 * 0.3              # Sentiment (normalized to 0-1)
            )
            
            # Recency factor
            last_interaction = contact_data.get('last_interaction')
            if last_interaction:
                days_since = (datetime.now() - last_interaction).days
                recency_factor = max(0, 1 - (days_since / 90))  # Decay over 90 days
                base_score *= (0.7 + 0.3 * recency_factor)
            
            return round(base_score * 100, 2)
        except Exception as e:
            print(f"Error calculating engagement score: {e}")
            return 50.0
    
    def generate_campaign_insights(self, campaign_data):
        """Generate AI insights from campaign data"""
        insights = []
        
        try:
            # Analyze overall performance
            total_sent = len(campaign_data)
            delivered = sum(1 for msg in campaign_data if msg.get('delivered'))
            read = sum(1 for msg in campaign_data if msg.get('read_receipt'))
            responses = sum(1 for msg in campaign_data if msg.get('response'))
            
            delivery_rate = delivered / total_sent if total_sent > 0 else 0
            read_rate = read / delivered if delivered > 0 else 0
            response_rate = responses / delivered if delivered > 0 else 0
            
            # Performance insights
            if delivery_rate < 0.9:
                insights.append(f"Low delivery rate ({delivery_rate:.1%}). Check contact list quality.")
            
            if read_rate > 0.7:
                insights.append(f"Excellent read rate ({read_rate:.1%})! Your timing and subject lines are effective.")
            elif read_rate < 0.3:
                insights.append(f"Low read rate ({read_rate:.1%}). Consider improving message previews or send timing.")
            
            if response_rate > 0.1:
                insights.append(f"Great response rate ({response_rate:.1%})! Your messages are engaging.")
            elif response_rate < 0.05:
                insights.append(f"Low response rate ({response_rate:.1%}). Add stronger calls-to-action.")
            
            # Sentiment analysis
            sentiments = [msg.get('sentiment', 0) for msg in campaign_data if msg.get('sentiment') is not None]
            if sentiments:
                avg_sentiment = sum(sentiments) / len(sentiments)
                if avg_sentiment > 0.2:
                    insights.append(f"Positive sentiment score ({avg_sentiment:.2f}). Recipients appreciate your messages.")
                elif avg_sentiment < -0.2:
                    insights.append(f"Negative sentiment score ({avg_sentiment:.2f}). Review message content and tone.")
            
            # Time analysis
            send_times = [msg.get('sent_time') for msg in campaign_data if msg.get('sent_time')]
            if send_times:
                # Find best performing hours
                hour_performance = {}
                for msg in campaign_data:
                    if msg.get('sent_time') and msg.get('read_receipt'):
                        hour = msg['sent_time'].hour
                        hour_performance[hour] = hour_performance.get(hour, 0) + 1
                
                if hour_performance:
                    best_hour = max(hour_performance.items(), key=lambda x: x[1])[0]
                    insights.append(f"Best engagement at {best_hour}:00. Schedule future messages around this time.")
            
            return insights
        except Exception as e:
            print(f"Error generating insights: {e}")
            return ["Unable to generate insights due to an error"]
