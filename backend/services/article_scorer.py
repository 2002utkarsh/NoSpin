try:
    import spacy
except ImportError:
    spacy = None

ABSOLUTIST_WORDS = {
    "always", "never", "undeniably", "indisputable", "worst", "best", 
    "disastrous", "perfect", "everyone", "nobody", "must", "impossible"
}

IMPERATIVE_TRIGGERS = {
    "demand", "join", "stop", "sign", "donate", "refuse", "stand", "fight", "wake"
}

class ArticleScorer:
    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("Downloading language model en_core_web_sm...")
            from spacy.cli import download
            download("en_core_web_sm")
            self.nlp = spacy.load("en_core_web_sm")
        except Exception as e:
            print(f"Warning: Spacy load failed ({e}). Scoring will be mocked.")
            self.nlp = None

    # --- HELPER: SCALING ---
    def _normalize(self, value, max_val, weight):
        """Clamps score and applies weight."""
        normalized = min(value / max_val, 1.0)
        return round(normalized * weight, 1)

    def metric_subjectivity(self, doc, weight=30):
        counts = doc.count_by(spacy.attrs.POS)
        # spaCy POS constants: ADJ=84, ADV=86, NOUN=92, VERB=100
        # Fallback if constants differ in version, but usually stable
        adj = counts.get(84, 0) + counts.get(86, 0)
        fact = counts.get(92, 0) + counts.get(100, 0)
        
        if fact == 0: return 0
        ratio = (adj / fact)
        return self._normalize(ratio, 0.25, weight)

    def metric_attribution_balance(self, doc, weight=30):
        speaking_verbs = ["said", "claimed", "stated", "argued", "told"]
        sources = set()
        
        for sent in doc.sents:
            for token in sent:
                if token.lemma_ in speaking_verbs:
                    for child in token.children:
                        if child.dep_ == "nsubj" and child.ent_type_ in ["PERSON", "ORG"]:
                            sources.add(child.text)
                            
        unique_sources = len(sources)
        if unique_sources == 0: score = 1.0 # High bias penalty
        elif unique_sources == 1: score = 0.8
        elif unique_sources == 2: score = 0.4
        else: score = 0.0
        
        return round(score * weight, 1)

    def metric_absolutism(self, doc, weight=20):
        count = 0
        for token in doc:
            if token.lower_ in ABSOLUTIST_WORDS:
                count += 1
        return self._normalize(count, 5, weight)

    def metric_call_to_action(self, doc, weight=20):
        cta_count = 0
        for sent in doc.sents:
            root = sent.root
            if (root.pos_ == "VERB" and root.tag_ == "VB") or (root.lemma_ in IMPERATIVE_TRIGGERS):
                cta_count += 1
        return self._normalize(cta_count, 2, weight)

    def analyze_article(self, text):
        if not self.nlp:
            return {"bias_score_1_to_10": 5.0, "details": "Mocked (Spacy Missing)"}

        # Truncate text to avoid massive processing time for huge articles
        doc = self.nlp(text[:5000])
        
        b1 = self.metric_subjectivity(doc)
        b2 = self.metric_attribution_balance(doc)
        b3 = self.metric_absolutism(doc)
        b4 = self.metric_call_to_action(doc)
        total_bias = b1 + b2 + b3 + b4
        
        # Scale to 1-10
        score = round(total_bias / 10.0, 1)
        # Ensure it's at least 1.0
        score = max(1.0, min(10.0, score))
        
        return {
            "bias_score_1_to_10": score,
            "details": {
                "subjectivity": b1, 
                "attribution": b2, 
                "absolutism": b3, 
                "cta": b4
            }
        }
    
    # Alias for compatibility if routes calling this
    def score_article(self, article_dict):
        # Combine title and content
        text = f"{article_dict.get('title', '')} . {article_dict.get('content', '')}"
        result = self.analyze_article(text)
        # Return simpler dict or just the score depending on needs.
        # But routes.py expects art['scores'] to be whatever this returns.
        # Let's return the full result object.
        return result
