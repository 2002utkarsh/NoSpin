# NoSpin: Narrative Comparison System

NoSpin is an AI-powered news analysis engine designed to deconstruct media bias. By analyzing how major events are covered across diverse news outlets, NoSpin allows users to look past polarized headlines to find objective "Common Ground."

The goal of this project is not persuasion. The goal is comparative understanding. The system does not rank truth; it exposes framing.

## Key Features

**Real-time Aggregation:** Pulls articles from 25+ major news sources using RSS feeds for any searched topic (e.g., "Iran Crisis" or "Farmers Protest").

**Automated Classification:** Sorts outlets into Left-leaning, Right-leaning, and Center affiliations to provide a balanced perspective.

**The Biasness Scale:** Assigns each article a transparent score from 1 to 10 based on sentiment density and linguistic markers.

**Narrative Synthesis:** Generates a comprehensive summary highlighting shared facts, points of disagreement, and differences in emphasis between sources.

## The Engineering Challenge: Mitigating LLM Bias

One of the primary challenges was ensuring the system remained objective. Because Large Language Models can carry their own inherent biases, we moved beyond basic API calls to develop a more rigorous pipeline:

**Research-Driven Design:** We reviewed over 15 research articles on political framing and NLP to identify reliable metrics for "spin" and tone.

**Weighted Scoring System:** We implemented a weighted approach to bias mitigation. By distributing weightage across multiple analytical passes and using structured system prompts, we neutralized the model's tendency to take a moral stance.

**The Senior Editor Prompt:** We engineered a robust system prompt for the LLM, instructing it to act as a neutral "Senior Newspaper Editor" with strict constraints on output schema and tone.

## Tech Stack

### Frontend
- React + Vite: For a fast, responsive user interface.
- Tailwind CSS: For streamlined styling and layout.

### Backend
- Python / Flask: Core logic and API development.
- Netlify Functions (Serverless): Deployed using a custom WSGI adapter to run Flask in a stateless, serverless environment.

### AI & NLP
- LLM (System Prompt Engineering): Used for narrative synthesis and structured context analysis.
- VADER (Valence Aware Dictionary and sEntiment Reasoner): For initial sentiment scoring and article classification.

## Installation and Setup

### Prerequisites
- Node.js (v18+)
- Python 3.9+
- API Key for the LLM provider

### Backend Setup
1. Navigate to the /backend directory.
2. Install dependencies: `pip install -r requirements.txt`.
3. Create a .env file and add your API_KEY.
4. Run the server: `python app.py`.

### Frontend Setup
1. Navigate to the /frontend directory.
2. Install dependencies: `npm install`.
3. Start the development server: `npm run dev`.

## The Team

This project was built over a single weekend for the Hack-The-Bias hackathon by:

- Utkarsh Gupta
- Gurnoor Singh
