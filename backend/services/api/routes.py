"""
api/routes.py

Define Flask endpoints for the Hack-The-Bias demo.
"""
from flask import Blueprint, jsonify, request
import os
import sys

# Ensure backend root is in path to import services if needed, 
# though relative imports from within the package should work if run as module.
# However, for simplicity in this structure:

from services.news_gatherer import NewsGatherer
from services.opinion_classifier import OpinionClassifier
from services.llm_prompt_builder import LLMPromptBuilder
from services.article_scorer import ArticleScorer
from services.image_handler import get_article_image

try:
    import google.generativeai as genai
    HAS_GEMINI = True
    # List of API Keys for redundancy
    GEMINI_API_KEYS = [
        #KEYS HERE
    ]
except ImportError:
    HAS_GEMINI = False

api_bp = Blueprint('api', __name__, url_prefix='/api')

# --- CONFIG LOADING ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, 'config.json')

def generate_summary_with_fallback(prompt):
    """Try generating content with multiple API keys in sequence."""
    if not HAS_GEMINI:
        return "Gemini Library Missing"
        
    errors = []
    for key in GEMINI_API_KEYS:
        try:
            genai.configure(api_key=key)
            model = genai.GenerativeModel('models/gemini-2.5-flash')
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            errors.append(f"Key ...{key[-4:]} failed: {str(e)}")
            continue
            
    return f"All Gemini Keys Failed. Errors: {'; '.join(errors)}"

@api_bp.route('/topics', methods=['GET'])
def get_topics():
    """Return list of demo topics."""
    return jsonify([
        {"id": "venezuela", "name": "Venezuelan Crisis"},
        {"id": "iran", "name": "Iran Crisis"},
        {"id": "farmers", "name": "Indian Farmers Protest 2020"},
        {"id": "truckers", "name": "Canadian Trucker Protest 2022"}
    ])

@api_bp.route('/analyze', methods=['POST'])
def analyze_topic():
    """
    Full pipeline run for a topic.
    Body: { "topic": "Venezuelan Crisis" }
    """
    data = request.json
    topic = data.get('topic', 'Unknown Topic')
    
    # Gather (Mocked via logic in NewsGatherer for demo)
    gatherer = NewsGatherer(CONFIG_PATH)
    articles = gatherer.gather_articles(topic)
    
    scorer = ArticleScorer()
    for art in articles:
        art['scores'] = scorer.score_article(art)
        art['image'] = get_article_image(art.get('link', ''), art['source'])

    # Classify
    classifier = OpinionClassifier()
    classified_articles = classifier.classify_articles(articles)
    
    # Group them
    in_favor = [a for a in classified_articles if a['stance'] == 'IN_FAVOR']
    against = [a for a in classified_articles if a['stance'] == 'AGAINST']
    
    # Build Prompt
    builder = LLMPromptBuilder()
    prompt = builder.build_prompt(topic, in_favor, against)
    
    # Gemini Call with Fallback
    summary = generate_summary_with_fallback(prompt)
            
    import json
    
    response_data = {
        "topic": topic,
        "articles": classified_articles,
        "summary": summary,
        "prompt_used": prompt
    }

    try:
        # Resolve path relative to backend/ (BASE_DIR is backend/)
        # Target: frontend/public/cache
        cache_dir = os.path.abspath(os.path.join(BASE_DIR, '..', 'frontend', 'public', 'cache'))
        os.makedirs(cache_dir, exist_ok=True)
        
        # Sanitize filename
        safe_filename = "".join([c if c.isalnum() else "-" for c in topic.lower()])
        filename = f"{safe_filename}.json"
        
        with open(os.path.join(cache_dir, filename), 'w', encoding='utf-8') as f:
            json.dump(response_data, f, indent=2)
            print(f"Cached result for '{topic}' to {filename}")
            
    except Exception as e:
        print(f"Failed to cache result: {e}")

    return jsonify(response_data)