import json
import os
import sys

# Ensure backend modules can be imported
sys.path.append(os.getcwd())

try:
    import spacy
except ImportError:
    spacy = None

try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False
    print("Warning: google.generativeai not installed.")

from backend.services.news_gatherer import NewsGatherer
from backend.services.article_scorer import ArticleScorer
from backend.services.opinion_classifier import OpinionClassifier
from backend.services.llm_prompt_builder import LLMPromptBuilder
from backend.services.image_handler import get_article_image

# --- GEMINI CONFIG ---
GEMINI_API_KEYS = [
    "AIzaSyD5XgECWSmiy_cQ_bYilL9FIHDjYagMGHk", 
    "AIzaSyCdz7stqjJCXbfvO9xqJ_BMF-GxWNO7zWk"
]

def generate_summary_with_fallback(prompt):
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

# --- SETUP ---
config_path = os.path.join("backend", "config.json")
gatherer = NewsGatherer(config_path)
scorer = ArticleScorer()
classifier = OpinionClassifier()
builder = LLMPromptBuilder()

topics = [
    {"query": "US attack on Venezuela", "filename": "us-attack-on-venezuela.json"},
    {"query": "Iran Crisis", "filename": "iran-crisis.json"},
    {"query": "Trump nobel prize", "filename": "trump-nobel-prize.json"},
    {"query": "Carney china deal", "filename": "carney-china-deal.json"}
]

cache_dir = os.path.join("frontend", "public", "cache")
os.makedirs(cache_dir, exist_ok=True)

for item in topics:
    topic = item["query"]
    filename = item["filename"]
    print(f"Generating cache for: {topic}")
    
    # 1. Gather
    articles = gatherer.gather_articles(topic)
    
    # 2. Score & Image
    for art in articles:
        art['scores'] = scorer.score_article(art)
        art['image'] = get_article_image(art.get('link', ''), art['source'])
        
    # 3. Classify
    classified = classifier.classify_articles(articles)
    
    # Group
    in_favor = [a for a in classified if a['stance'] == 'IN_FAVOR']
    against = [a for a in classified if a['stance'] == 'AGAINST']
    
    # 4. Prompt & Summary (REAL)
    prompt = builder.build_prompt(topic, in_favor, against)
    print("  ... contacting Gemini ...")
    summary = generate_summary_with_fallback(prompt)
    
    data = {
        "topic": topic,
        "articles": classified,
        "summary": summary,
        "prompt_used": prompt
    }
    
    with open(os.path.join(cache_dir, filename), 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

print("Cache generation complete.")
