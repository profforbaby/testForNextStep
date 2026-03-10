"""
AI-powered content generator for reading passages and questions
Uses Anthropic Claude API to generate age-appropriate content
"""
import json
import os
from typing import List, Optional
from anthropic import Anthropic
from edu_game_app.data.models import Passage, Question


class ContentGenerator:
    """Generate reading passages and questions using AI"""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize with Anthropic API key"""
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("Anthropic API key is required. Set ANTHROPIC_API_KEY environment variable.")
        self.client = Anthropic(api_key=self.api_key)

    def generate_passage(self, difficulty_level: int = 1, topic: str = "random") -> Passage:
        """
        Generate a reading passage suitable for Primary 1 students

        Args:
            difficulty_level: 1 (easy), 2 (medium), 3 (challenging)
            topic: Subject matter (animals, family, school, nature, toys, food, etc.)

        Returns:
            Passage object with content and questions
        """
        # Define word count ranges by difficulty
        word_ranges = {
            1: (30, 50),
            2: (50, 80),
            3: (80, 100)
        }

        word_min, word_max = word_ranges.get(difficulty_level, (30, 50))

        prompt = self._create_passage_prompt(difficulty_level, topic, word_min, word_max)
        response = self.client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2000,
            temperature=0.7,
            system="You are an expert elementary school teacher creating reading materials for 6-7 year old children (Primary 1/Grade 1). Always respond with valid JSON only.",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        # Parse response - strip markdown code fences if present
        response_text = response.content[0].text.strip()
        if response_text.startswith("```"):
            lines = response_text.split('\n')
            response_text = '\n'.join(lines[1:-1]).strip()
        content = json.loads(response_text)

        # Create Passage object
        passage = Passage(
            title=content['title'],
            content=content['passage'],
            difficulty_level=difficulty_level,
            topic=topic if topic != "random" else content.get('topic', 'general'),
            questions=[]
        )

        # Create Question objects
        for q_data in content['questions']:
            question = Question(
                question_text=q_data['question'],
                correct_answer=q_data['correct_answer'],
                option_a=q_data['options'][0],
                option_b=q_data['options'][1],
                option_c=q_data['options'][2],
                option_d=q_data['options'][3],
                question_type="multiple_choice"
            )
            passage.questions.append(question)

        return passage

    def _create_passage_prompt(self, level: int, topic: str, word_min: int, word_max: int) -> str:
        """Create detailed prompt for passage generation"""

        difficulty_descriptions = {
            1: "very simple sentences, basic sight words (the, and, is, can, I, see), present tense only",
            2: "simple compound sentences, common vocabulary, mix of present and past tense",
            3: "some descriptive language, a few challenging words with context clues, varied sentence structures"
        }

        topic_instruction = f"about {topic}" if topic != "random" else "on any child-friendly topic (animals, family, daily activities, nature, toys, food, friends, or school)"

        prompt = f"""Generate a reading passage for a 6-7 year old child (Primary 1/Grade 1 level).

Requirements:
- Length: {word_min}-{word_max} words
- Difficulty: Level {level} - {difficulty_descriptions[level]}
- Topic: {topic_instruction}
- Must be engaging and appropriate for young children
- Include a clear beginning, middle, and end
- Use simple, concrete concepts

Also create 5 multiple choice questions based on the passage:
- Questions should test comprehension (main idea, details, sequence, simple inference)
- Each question should have 4 answer options (A, B, C, D)
- Only ONE correct answer per question
- Wrong answers should be plausible but clearly incorrect
- Questions should be answerable from the passage

Return response in this exact JSON format:
{{
    "title": "Engaging title for the passage",
    "topic": "the main topic category",
    "passage": "The complete reading passage text...",
    "questions": [
        {{
            "question": "Question text?",
            "correct_answer": "A",
            "options": ["correct answer text", "wrong answer 1", "wrong answer 2", "wrong answer 3"]
        }}
    ]
}}

IMPORTANT:
- The correct_answer must be "A", "B", "C", or "D"
- The options array should have the correct answer at the position matching correct_answer (A=0, B=1, C=2, D=3)
- Make sure the passage is exactly {word_min}-{word_max} words
"""
        return prompt

    def _get_fallback_passage(self, level: int) -> Passage:
        """Return a pre-made passage if API fails"""
        fallback_passages = {
            1: {
                "title": "My Dog Max",
                "content": "I have a dog. His name is Max. Max is big and brown. He likes to play. Max runs and jumps. He wags his tail. I love Max. Max is my best friend.",
                "questions": [
                    ("What is the dog's name?", "A", ["Max", "Sam", "Rex", "Buddy"]),
                    ("What color is Max?", "B", ["black", "brown", "white", "yellow"]),
                    ("What does Max like to do?", "C", ["sleep", "eat", "play", "swim"]),
                    ("How does Max feel?", "D", ["sad", "angry", "tired", "happy"]),
                    ("Who loves Max?", "A", ["I do", "Mom", "Teacher", "Friend"])
                ]
            },
            2: {
                "title": "A Day at the Park",
                "content": "Tom and his sister Lily went to the park. They played on the swings and ran on the grass. Lily found a butterfly and tried to catch it. The butterfly flew away. They ate sandwiches under a big tree. It was a happy day.",
                "questions": [
                    ("Who went to the park?", "A", ["Tom and Lily", "Tom and Max", "Lily and Mom", "Tom and Dad"]),
                    ("What did Lily find?", "B", ["a flower", "a butterfly", "a bird", "a leaf"]),
                    ("What did they eat?", "C", ["cake", "apples", "sandwiches", "biscuits"]),
                    ("Where did they eat?", "D", ["on the swings", "on the grass", "near the pond", "under a big tree"]),
                    ("How was the day?", "A", ["happy", "rainy", "boring", "scary"])
                ]
            },
            3: {
                "title": "The Little Seed",
                "content": "A tiny seed fell into the soft brown soil. Every day, the rain gave it water and the sun gave it warmth. Slowly, a small green shoot pushed through the ground. The shoot grew taller and taller. One bright morning, a beautiful yellow flower opened its petals. A bee flew over to collect sweet nectar. The seed had become a flower at last.",
                "questions": [
                    ("Where did the seed fall?", "A", ["into soft brown soil", "into a river", "onto a rock", "into a pot"]),
                    ("What two things helped the seed grow?", "B", ["wind and snow", "rain and sun", "soil and wind", "clouds and rain"]),
                    ("What colour was the flower?", "C", ["red", "blue", "yellow", "pink"]),
                    ("What did the bee collect?", "D", ["water", "soil", "pollen", "nectar"]),
                    ("What is the main idea of the story?", "A", ["A seed grows into a flower", "A bee visits a garden", "Rain helps animals", "A child plants a tree"])
                ]
            }
        }

        data = fallback_passages.get(level, fallback_passages[1])
        passage = Passage(
            title=data['title'],
            content=data['content'],
            difficulty_level=level,
            topic="animals"
        )

        for q_text, correct, options in data['questions']:
            passage.questions.append(Question(
                question_text=q_text,
                correct_answer=correct,
                option_a=options[0],
                option_b=options[1],
                option_c=options[2],
                option_d=options[3]
            ))

        return passage

    def generate_custom_passage(self, custom_prompt: str) -> Passage:
        """Generate passage from custom parent-provided prompt"""
        prompt = f"""Based on this request: "{custom_prompt}"

Create a reading passage suitable for a 6-7 year old child (Primary 1 level).
Keep it 30-80 words, use simple language, and make it engaging.

Also create 5 multiple choice questions to test comprehension.

Return in this JSON format:
{{
    "title": "passage title",
    "topic": "topic category",
    "passage": "passage text",
    "questions": [
        {{
            "question": "question text",
            "correct_answer": "A",
            "options": ["option a", "option b", "option c", "option d"]
        }}
    ]
}}
"""

        response = self.client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2000,
            temperature=0.7,
            system="You are an expert elementary school teacher. Always respond with valid JSON only.",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        response_text = response.content[0].text.strip()
        if response_text.startswith("```"):
            lines = response_text.split('\n')
            response_text = '\n'.join(lines[1:-1]).strip()
        content = json.loads(response_text)

        passage = Passage(
            title=content['title'],
            content=content['passage'],
            difficulty_level=2,
            topic=content.get('topic', 'custom'),
            questions=[]
        )

        for q_data in content['questions']:
            question = Question(
                question_text=q_data['question'],
                correct_answer=q_data['correct_answer'],
                option_a=q_data['options'][0],
                option_b=q_data['options'][1],
                option_c=q_data['options'][2],
                option_d=q_data['options'][3]
            )
            passage.questions.append(question)

        return passage
