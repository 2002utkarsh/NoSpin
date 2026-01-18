"""
llm_prompt_builder.py

This module contains the LLMPromptBuilder class, responsible for constructing
a strict, well-structured prompt for an LLM to generate neutral editorial summaries.

The builder adheres to specific constraints:
- Neutral tone
- No academic or moralizing language
- Structured output (Common Ground, Perspectives, Emphasis)
"""

from typing import List, Dict, Any

class LLMPromptBuilder:
    """
    Constructs an editorial summary prompt for an LLM.
    """

    def build_prompt(self, topic: str, in_favor_articles: List[Dict[str, Any]], against_articles: List[Dict[str, Any]]) -> str:
        """
        Build the full prompt string.

        Args:
            topic (str): The subject of the news stories.
            in_favor_articles (List[Dict]): Articles with IN_FAVOR stance.
            against_articles (List[Dict]): Articles with AGAINST stance.

        Returns:
            str: The constructed prompt.
        """
        
        # 1. System/Role Definition
        system_instructions = self._get_system_instructions()

        # 2. Input Data Formatting
        input_section = self._format_input_data(topic, in_favor_articles, against_articles)

        # 3. Output Requirements
        output_format = self._get_output_format_instructions()

        # Combine all parts
        full_prompt = (
            f"{system_instructions}\n\n"
            f"{input_section}\n\n"
            f"{output_format}"
        )

        return full_prompt

    def _get_system_instructions(self) -> str:
        """
        Define the role and tone constraints.
        """
        return (
            "ROLE: You are a senior newspaper editor. Your task is to synthesize multiple narratives "
            "into a single, high-quality, neutral editorial summary.\n\n"
            "TONE GUIDELINES:\n"
            "- Neutral, precise, and calm.\n"
            "- Editorial style, not academic. Avoid jargon.\n"
            "- No moralizing language (e.g., avoid 'unfortunately', 'rightly').\n"
            "- Do NOT strictly declare one side correct.\n"
            "- Do NOT mention 'bias', 'sentiment', or 'AI'.\n"
            "- Use 'The pro-[topic] narrative emphasizes...' or 'Critics argue...' rather than 'User 1 said...'."
        )

    def _format_input_data(self, topic: str, in_favor: List[Dict], against: List[Dict]) -> str:
        """
        Format the articles into a clear input block.
        """
        section = f"TOPIC: {topic}\n\nINPUT DATA:\n"

        section += "--- GROUP A: ARTICLES IN FAVOR (SUPPORTING) ---\n"
        if not in_favor:
            section += "(No articles in this group)\n"
        else:
            for i, art in enumerate(in_favor, 1):
                # Extract source and points. Fallback to title if points missing.
                source = art.get('source', 'Unknown Source')
                bucket = art.get('political_bucket', 'Unknown')
                points = art.get('key_points', art.get('title', ''))
                section += f"{i}. [{source} | {bucket}] Summary: {points}\n"

        section += "\n--- GROUP B: ARTICLES AGAINST (OPPOSING) ---\n"
        if not against:
            section += "(No articles in this group)\n"
        else:
            for i, art in enumerate(against, 1):
                source = art.get('source', 'Unknown Source')
                bucket = art.get('political_bucket', 'Unknown')
                points = art.get('key_points', art.get('title', ''))
                section += f"{i}. [{source} | {bucket}] Summary: {points}\n"
        
        return section

    def _get_output_format_instructions(self) -> str:
        """
        Define the strictly required output sections.
        """
        return (
            "OUTPUT INSTRUCTIONS:\n"
            "Produce a written summary with the following FOUR clearly labeled sections. "
            "IMPORTANT: Do NOT use any markdown formatting (like *, #, **). Output strictly plain text. "
            "Do NOT make titles bold. Do NOT use bullet points unless creating a list.\n\n"
            "1. COMMON GROUND\n"
            "   - Identify facts or points agreed upon by both groups.\n"
            "   - If no obvious agreement, note the shared subject matter factually.\n\n"
            "2. THE CASE IN FAVOR\n"
            "   - Summarize the arguments and focus of the IN FAVOR group.\n"
            "   - Attribute these views generally to proponents.\n\n"
            "3. THE CASE AGAINST\n"
            "   - Summarize the arguments and focus of the AGAINST group.\n"
            "   - Attribute these views generally to critics or opponents.\n\n"
            "4. OBSERVATIONS ON EMPHASIS\n"
            "   - Briefly note what each side specifically highlights or omits.\n"
            "   - Example: 'Supporters focus on economic growth, while opponents focus on environmental risk.'\n"
            "   - Keep this descriptive."
        )
