from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import logging
import json
from datetime import datetime, timezone
import sqlite3
import os

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Simple sentiment analyzer using TextBlob
try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False
    logger.warning("TextBlob not available, using simple fallback")

class SimpleSentimentAnalyzer:
    def predict_sentiment(self, text):
        if TEXTBLOB_AVAILABLE:
            try:
                blob = TextBlob(text)
                polarity = blob.sentiment.polarity

                if polarity > 0.1:
                    sentiment = 'positive'
                elif polarity < -0.1:
                    sentiment = 'negative'
                else:
                    sentiment = 'neutral'

                return {
                    'sentiment': sentiment,
                    'confidence': abs(polarity),
                    'model_type': 'textblob'
                }
            except Exception as e:
                logger.error(f"TextBlob error: {e}")

        # Fallback: simple keyword-based analysis
        text_lower = text.lower()
        positive_words = ['good', 'great', 'excellent', 'amazing', 'love', 'perfect', 'awesome', 'fantastic', 'wonderful', 'outstanding', 'superb', 'brilliant']
        negative_words = ['bad', 'terrible', 'awful', 'hate', 'poor', 'worst', 'horrible', 'disappointing', 'pathetic', 'useless', 'garbage', 'disgusting']

        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)

        if positive_count > negative_count:
            sentiment = 'positive'
            confidence = min(positive_count * 0.3, 1.0)
        elif negative_count > positive_count:
            sentiment = 'negative'
            confidence = min(negative_count * 0.3, 1.0)
        else:
            sentiment = 'neutral'
            confidence = 0.1

        return {
            'sentiment': sentiment,
            'confidence': confidence,
            'model_type': 'keyword_fallback'
        }

# Simple database manager
class SimpleDatabase:
    def __init__(self):
        self.db_path = 'predictions.db'
        self.create_tables()

    def create_tables(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS predictions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        input_text TEXT NOT NULL,
                        sentiment_label TEXT NOT NULL,
                        sentiment_confidence REAL,
                        topics TEXT,
                        metadata TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                conn.commit()
                logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Database error: {e}")

    def store_prediction(self, input_text, sentiment_label, sentiment_confidence, topics=None, metadata=None):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                topics_json = json.dumps(topics) if topics else None
                metadata_json = json.dumps(metadata) if metadata else None

                cursor.execute('''
                    INSERT INTO predictions 
                    (input_text, sentiment_label, sentiment_confidence, topics, metadata)
                    VALUES (?, ?, ?, ?, ?)
                ''', (input_text, sentiment_label, sentiment_confidence, topics_json, metadata_json))

                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Database storage error: {e}")
            return None

    def get_statistics(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute('SELECT COUNT(*) FROM predictions')
                total_predictions = cursor.fetchone()[0]

                cursor.execute('''
                    SELECT sentiment_label, COUNT(*) 
                    FROM predictions 
                    GROUP BY sentiment_label
                ''')
                sentiment_dist = dict(cursor.fetchall())

                cursor.execute('SELECT AVG(sentiment_confidence) FROM predictions')
                avg_confidence = cursor.fetchone()[0] or 0.0

                return {
                    'total_predictions': total_predictions,
                    'sentiment_distribution': sentiment_dist,
                    'average_confidence': round(avg_confidence, 4)
                }
        except Exception as e:
            logger.error(f"Statistics error: {e}")
            return {}

# Initialize components
sentiment_analyzer = SimpleSentimentAnalyzer()
db_manager = SimpleDatabase()

# Web Interface Routes
@app.route('/')
def index():
    """Serve the main web interface"""
    return render_template('index.html')

@app.route('/api')
def api_info():
    """API information endpoint"""
    return jsonify({
        'message': 'AI-Powered Customer Feedback Analyzer API',
        'version': '1.0.0',
        'status': 'running',
        'web_interface': '/',
        'endpoints': {
            'analyze': '/analyze - POST - Analyze customer feedback',
            'health': '/health - GET - Health check',
            'stats': '/stats - GET - Get statistics',
            'batch_analyze': '/batch_analyze - POST - Analyze multiple texts'
        }
    })

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'models': {
            'sentiment_analyzer': True,
            'database': True,
            'textblob_available': TEXTBLOB_AVAILABLE
        },
        'web_interface': 'available'
    })

@app.route('/analyze', methods=['POST'])
def analyze_feedback():
    """Analyze single customer feedback"""
    try:
        data = request.get_json()

        if not data or 'text' not in data:
            return jsonify({'error': 'Missing text field in request'}), 400

        text = data['text']

        if not text or not isinstance(text, str) or len(text.strip()) == 0:
            return jsonify({'error': 'Invalid text input'}), 400

        # Analyze sentiment
        sentiment_result = sentiment_analyzer.predict_sentiment(text)

        # Prepare response
        analysis_result = {
            'text': text,
            'sentiment': {
                'label': sentiment_result['sentiment'],
                'confidence': sentiment_result.get('confidence', 0.0),
                'model_type': sentiment_result.get('model_type', 'unknown')
            },
            'topics': [],
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'analysis_id': None
        }

        # Store in database
        try:
            analysis_id = db_manager.store_prediction(
                input_text=text,
                sentiment_label=sentiment_result['sentiment'],
                sentiment_confidence=sentiment_result.get('confidence', 0.0),
                topics=None,
                metadata=data.get('metadata', {})
            )
            analysis_result['analysis_id'] = analysis_id
        except Exception as e:
            logger.error(f"Database storage failed: {e}")

        return jsonify(analysis_result)

    except Exception as e:
        logger.error(f"Analysis error: {e}")
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500

@app.route('/batch_analyze', methods=['POST'])
def batch_analyze():
    """Analyze multiple customer feedbacks"""
    try:
        data = request.get_json()

        if not data or 'texts' not in data:
            return jsonify({'error': 'Missing texts field in request'}), 400

        texts = data['texts']

        if not isinstance(texts, list) or len(texts) == 0:
            return jsonify({'error': 'texts must be a non-empty list'}), 400

        if len(texts) > 100:
            return jsonify({'error': 'Batch size too large (max 100)'}), 400

        results = []

        for i, text in enumerate(texts):
            try:
                if not text or not isinstance(text, str):
                    continue

                sentiment_result = sentiment_analyzer.predict_sentiment(text)

                result = {
                    'index': i,
                    'text': text,
                    'sentiment': {
                        'label': sentiment_result['sentiment'],
                        'confidence': sentiment_result.get('confidence', 0.0)
                    },
                    'topics': []
                }

                results.append(result)

                # Store in database
                db_manager.store_prediction(
                    input_text=text,
                    sentiment_label=sentiment_result['sentiment'],
                    sentiment_confidence=sentiment_result.get('confidence', 0.0)
                )

            except Exception as e:
                logger.error(f"Error processing item {i}: {e}")
                results.append({
                    'index': i,
                    'text': text,
                    'error': str(e)
                })

        return jsonify({
            'results': results,
            'processed_count': len(results),
            'timestamp': datetime.now(timezone.utc).isoformat()
        })

    except Exception as e:
        logger.error(f"Batch analysis error: {e}")
        return jsonify({'error': f'Batch analysis failed: {str(e)}'}), 500

@app.route('/stats')
def get_statistics():
    """Get analysis statistics"""
    try:
        stats = db_manager.get_statistics()
        return jsonify({
            'database_stats': stats,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        return jsonify({'error': f'Failed to get statistics: {str(e)}'}), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({'error': 'Method not allowed'}), 405

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    logger.info("🤖 Starting AI Customer Feedback Analyzer")
    logger.info("🌐 Web Interface: http://localhost:5000")
    logger.info("📡 API Endpoints: http://localhost:5000/api")
    logger.info("🏥 Health Check: http://localhost:5000/health")
    app.run(host='0.0.0.0', port=5000, debug=True)