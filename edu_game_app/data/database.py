"""
Database operations for the educational app
"""
import sqlite3
from datetime import datetime
from typing import List, Optional
from edu_game_app.data.models import ChildProfile, Passage, Question, QuizAttempt, GameSession


class Database:
    """SQLite database manager"""

    def __init__(self, db_path: str = "edu_app.db"):
        self.db_path = db_path
        self.conn = None
        self.init_database()

    def init_database(self):
        """Initialize database and create tables"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        cursor = self.conn.cursor()

        # Child profile table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS child_profile (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                current_level INTEGER DEFAULT 1,
                total_quizzes INTEGER DEFAULT 0,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Passages table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS passages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                difficulty_level INTEGER DEFAULT 1,
                word_count INTEGER,
                topic TEXT DEFAULT 'general',
                is_seed INTEGER DEFAULT 0
            )
        ''')

        # Migrate existing passages table if is_seed column is missing
        try:
            cursor.execute("ALTER TABLE passages ADD COLUMN is_seed INTEGER DEFAULT 0")
            self.conn.commit()
        except Exception:
            pass  # Column already exists

        # Questions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                passage_id INTEGER NOT NULL,
                question_text TEXT NOT NULL,
                correct_answer TEXT NOT NULL,
                option_a TEXT,
                option_b TEXT,
                option_c TEXT,
                option_d TEXT,
                question_type TEXT DEFAULT 'multiple_choice',
                FOREIGN KEY (passage_id) REFERENCES passages(id)
            )
        ''')

        # Quiz attempts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quiz_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                passage_id INTEGER,
                difficulty_level INTEGER,
                score REAL,
                time_taken INTEGER,
                questions_total INTEGER,
                questions_correct INTEGER,
                FOREIGN KEY (passage_id) REFERENCES passages(id)
            )
        ''')

        # Game sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS game_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                minutes_earned INTEGER DEFAULT 0,
                minutes_used INTEGER DEFAULT 0,
                balance INTEGER DEFAULT 0
            )
        ''')

        self.conn.commit()
        self._seed_offline_passages()

    def get_or_create_profile(self, name: str = "Student") -> ChildProfile:
        """Get existing profile or create new one"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM child_profile LIMIT 1")
        row = cursor.fetchone()

        if row:
            return ChildProfile(
                id=row['id'],
                name=row['name'],
                current_level=row['current_level'],
                total_quizzes=row['total_quizzes'],
                created_date=datetime.fromisoformat(row['created_date'])
            )
        else:
            # Create new profile
            cursor.execute(
                "INSERT INTO child_profile (name, current_level, total_quizzes) VALUES (?, ?, ?)",
                (name, 4, 0)
            )
            self.conn.commit()
            return self.get_or_create_profile(name)

    def update_profile(self, profile: ChildProfile):
        """Update child profile"""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE child_profile
            SET name = ?, current_level = ?, total_quizzes = ?
            WHERE id = ?
        ''', (profile.name, profile.current_level, profile.total_quizzes, profile.id))
        self.conn.commit()

    def save_passage(self, passage: Passage) -> int:
        """Save passage and its questions"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO passages (title, content, difficulty_level, word_count, topic)
            VALUES (?, ?, ?, ?, ?)
        ''', (passage.title, passage.content, passage.difficulty_level,
              passage.word_count, passage.topic))
        passage_id = cursor.lastrowid

        # Save questions
        for question in passage.questions:
            cursor.execute('''
                INSERT INTO questions (passage_id, question_text, correct_answer,
                                     option_a, option_b, option_c, option_d, question_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (passage_id, question.question_text, question.correct_answer,
                  question.option_a, question.option_b, question.option_c,
                  question.option_d, question.question_type))

        self.conn.commit()
        return passage_id

    def get_passage_with_questions(self, passage_id: int) -> Optional[Passage]:
        """Get passage with all its questions"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM passages WHERE id = ?", (passage_id,))
        row = cursor.fetchone()

        if not row:
            return None

        passage = Passage(
            id=row['id'],
            title=row['title'],
            content=row['content'],
            difficulty_level=row['difficulty_level'],
            word_count=row['word_count'],
            topic=row['topic']
        )

        # Get questions
        cursor.execute("SELECT * FROM questions WHERE passage_id = ?", (passage_id,))
        questions = []
        for q_row in cursor.fetchall():
            questions.append(Question(
                id=q_row['id'],
                passage_id=q_row['passage_id'],
                question_text=q_row['question_text'],
                correct_answer=q_row['correct_answer'],
                option_a=q_row['option_a'],
                option_b=q_row['option_b'],
                option_c=q_row['option_c'],
                option_d=q_row['option_d'],
                question_type=q_row['question_type']
            ))
        passage.questions = questions

        return passage

    def save_quiz_attempt(self, attempt: QuizAttempt) -> int:
        """Save quiz attempt"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO quiz_attempts
            (passage_id, difficulty_level, score, time_taken, questions_total, questions_correct)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (attempt.passage_id, attempt.difficulty_level, attempt.score,
              attempt.time_taken, attempt.questions_total, attempt.questions_correct))
        self.conn.commit()
        return cursor.lastrowid

    def get_recent_attempts(self, limit: int = 10) -> List[QuizAttempt]:
        """Get recent quiz attempts"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM quiz_attempts
            ORDER BY date DESC
            LIMIT ?
        ''', (limit,))

        attempts = []
        for row in cursor.fetchall():
            attempts.append(QuizAttempt(
                id=row['id'],
                date=datetime.fromisoformat(row['date']),
                passage_id=row['passage_id'],
                difficulty_level=row['difficulty_level'],
                score=row['score'],
                time_taken=row['time_taken'],
                questions_total=row['questions_total'],
                questions_correct=row['questions_correct']
            ))
        return attempts

    def get_game_time_balance(self) -> int:
        """Get current game time balance in minutes"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT SUM(balance) as total FROM game_sessions")
        row = cursor.fetchone()
        return row['total'] if row['total'] else 0

    def add_game_time(self, minutes: int):
        """Add earned game time"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO game_sessions (minutes_earned, minutes_used, balance)
            VALUES (?, 0, ?)
        ''', (minutes, minutes))
        self.conn.commit()

    def use_game_time(self, minutes: int):
        """Deduct used game time"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO game_sessions (minutes_earned, minutes_used, balance)
            VALUES (0, ?, ?)
        ''', (minutes, -minutes))
        self.conn.commit()

    def reset_game_time_balance(self):
        """Reset game time balance to 0 (called on every app startup)"""
        current = self.get_game_time_balance()
        if current > 0:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO game_sessions (minutes_earned, minutes_used, balance)
                VALUES (0, ?, ?)
            ''', (current, -current))
            self.conn.commit()

    def get_random_passage_by_level(self, level: int) -> Optional['Passage']:
        """Return a random seeded passage at the given difficulty level."""
        import random
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT id FROM passages WHERE difficulty_level = ? AND is_seed = 1",
            (level,)
        )
        rows = cursor.fetchall()
        if not rows:
            # Fall back to any level if nothing at the requested level
            cursor.execute("SELECT id FROM passages WHERE is_seed = 1")
            rows = cursor.fetchall()
        if not rows:
            return None
        chosen_id = random.choice(rows)['id']
        return self.get_passage_with_questions(chosen_id)

    def _seed_offline_passages(self):
        """Insert built-in offline passages if they haven't been seeded yet."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) as n FROM passages WHERE is_seed = 1")
        total_seeded = cursor.fetchone()['n']
        cursor.execute("SELECT COUNT(*) as n FROM passages WHERE is_seed = 1 AND difficulty_level = 4")
        level4_seeded = cursor.fetchone()['n']

        seed_all = total_seeded == 0
        seed_level4 = level4_seeded == 0

        if not seed_all and not seed_level4:
            return  # Already fully seeded

        # Format: (title, level, topic, content, [(question, correct_letter, [optA, optB, optC, optD]), ...])
        passages = [
            # ── LEVEL 1 ──────────────────────────────────────────────────
            (
                "My Cat Lily", 1, "animals",
                "I have a cat. Her name is Lily. Lily is small and white. "
                "She has big blue eyes. Lily likes to sleep on my bed. "
                "She purrs when I pet her. I love Lily. She is a good cat.",
                [
                    ("What is the cat's name?", "A", ["Lily", "Max", "Bella", "Coco"]),
                    ("What color is Lily?", "B", ["black", "white", "orange", "grey"]),
                    ("What does Lily like to do?", "C", ["swim", "run", "sleep", "jump"]),
                    ("Where does Lily sleep?", "D", ["on the floor", "in a box", "outside", "on the bed"]),
                    ("What does Lily do when petted?", "B", ["meows", "purrs", "runs", "bites"]),
                ]
            ),
            (
                "The Red Ball", 1, "toys",
                "Tom has a red ball. He plays with it every day. Tom kicks the ball high. "
                "The ball goes up and up. It lands in the garden. Tom runs to get it. "
                "He laughs and kicks it again. The red ball is his favorite toy.",
                [
                    ("What color is Tom's ball?", "A", ["red", "blue", "green", "yellow"]),
                    ("Where does the ball land?", "C", ["on the roof", "in a tree", "in the garden", "in the road"]),
                    ("What does Tom do every day?", "D", ["reads", "sleeps", "cooks", "plays with the ball"]),
                    ("How does Tom feel?", "C", ["sad", "angry", "happy", "tired"]),
                    ("What is Tom's favorite toy?", "D", ["a car", "a kite", "a drum", "the red ball"]),
                ]
            ),
            (
                "My Family", 1, "family",
                "I have a big family. I have a mum, a dad, and a baby sister. "
                "My dad is tall. My mum has long hair. My sister is very small. "
                "We eat dinner together every night. I love my family.",
                [
                    ("How many people are in the family?", "C", ["two", "three", "four", "five"]),
                    ("Who has long hair?", "C", ["dad", "sister", "mum", "grandma"]),
                    ("What does the family do every night?", "C", ["watch TV", "sing songs", "eat dinner", "go for a walk"]),
                    ("What does the narrator love?", "B", ["school", "family", "food", "toys"]),
                    ("What is the dad like?", "C", ["short", "funny", "tall", "loud"]),
                ]
            ),
            (
                "Breakfast Time", 1, "food",
                "I wake up in the morning. I go to the kitchen. "
                "Mum makes porridge for me. I put honey on top. "
                "It is sweet and warm. I drink a glass of milk. "
                "Then I brush my teeth. I am ready for school.",
                [
                    ("What does Mum make?", "D", ["toast", "eggs", "pancakes", "porridge"]),
                    ("What does the child put on top?", "B", ["sugar", "honey", "jam", "butter"]),
                    ("What does the child drink?", "C", ["juice", "tea", "milk", "water"]),
                    ("What does the child do after eating?", "D", ["plays", "reads", "sleeps", "brushes teeth"]),
                    ("Where does the child go after breakfast?", "C", ["park", "shop", "school", "garden"]),
                ]
            ),
            (
                "The Garden", 1, "nature",
                "We have a garden at home. There are red and yellow flowers. "
                "A big tree grows in the corner. Birds sit on the tree and sing. "
                "I like to water the flowers. The garden smells nice. It is my favorite place.",
                [
                    ("What colors are the flowers?", "B", ["blue and white", "red and yellow", "pink and purple", "orange and green"]),
                    ("What grows in the corner?", "C", ["a bush", "a swing", "a big tree", "a pond"]),
                    ("What do the birds do?", "D", ["eat", "sleep", "fly away", "sit and sing"]),
                    ("What does the child like to do?", "B", ["climb the tree", "water the flowers", "catch birds", "plant seeds"]),
                    ("How does the garden smell?", "D", ["bad", "like rain", "like food", "nice"]),
                ]
            ),
            (
                "At School", 1, "school",
                "I go to school every day. My teacher is kind. "
                "We read books and write letters. I have five friends in my class. "
                "We play together at break time. My favorite subject is art. "
                "I like to draw and paint.",
                [
                    ("What is the teacher like?", "C", ["strict", "funny", "kind", "loud"]),
                    ("What do students do in class?", "B", ["sing and dance", "read and write", "cook and eat", "run and jump"]),
                    ("How many friends does the narrator have?", "C", ["three", "four", "five", "six"]),
                    ("When do they play together?", "B", ["after school", "at break time", "in the morning", "before class"]),
                    ("What is the narrator's favorite subject?", "D", ["math", "science", "reading", "art"]),
                ]
            ),
            (
                "My New Shoes", 1, "daily life",
                "I got new shoes today. They are blue with white stripes. "
                "They are soft and light. I put them on and ran outside. "
                "I ran so fast! My dog chased me around the yard. "
                "I felt very happy in my new shoes.",
                [
                    ("What color are the new shoes?", "B", ["red and black", "blue and white", "green and yellow", "pink and purple"]),
                    ("How do the shoes feel?", "C", ["heavy and hard", "tight and old", "soft and light", "big and wide"]),
                    ("What did the narrator do after putting on the shoes?", "D", ["danced", "jumped", "slept", "ran outside"]),
                    ("Who chased the narrator?", "C", ["a cat", "a bird", "a dog", "a friend"]),
                    ("How did the narrator feel?", "D", ["tired", "sad", "scared", "very happy"]),
                ]
            ),
            # ── LEVEL 2 ──────────────────────────────────────────────────
            (
                "The Lost Kite", 2, "outdoor",
                "On a windy day, Sam flew his kite in the park. The kite was bright orange "
                "with a long tail. A strong gust of wind pulled the string from Sam's hand. "
                "The kite flew up into the big oak tree. Sam was sad. His dad lifted him up "
                "and they got the kite down together. Sam smiled again.",
                [
                    ("What color was the kite?", "C", ["yellow", "blue", "orange", "red"]),
                    ("Where did Sam fly his kite?", "D", ["at home", "at school", "on the beach", "in the park"]),
                    ("Why did the kite get stuck?", "B", ["it was too heavy", "a strong wind pulled the string", "Sam let go on purpose", "the string broke"]),
                    ("Where did the kite get stuck?", "C", ["on a roof", "in a lake", "in an oak tree", "on a fence"]),
                    ("How did Sam get the kite back?", "D", ["he climbed up alone", "his mum threw a rope", "it fell down by itself", "his dad lifted him up"]),
                ]
            ),
            (
                "Making a Cake", 2, "food",
                "Anna and her mum decided to make a birthday cake. They mixed flour, eggs, "
                "butter, and sugar in a big bowl. Anna stirred the batter until it was smooth. "
                "Mum poured it into a tin and put it in the oven. The kitchen smelled wonderful. "
                "When the cake cooled, they covered it with pink icing. Dad said it was the best cake ever.",
                [
                    ("What kind of cake were they making?", "B", ["chocolate", "birthday", "fruit", "cheese"]),
                    ("What did Anna do with the batter?", "C", ["tasted it", "poured it", "stirred it", "baked it"]),
                    ("Where did Mum put the cake tin?", "C", ["in the fridge", "on the shelf", "in the oven", "on the table"]),
                    ("What color was the icing?", "D", ["white", "yellow", "blue", "pink"]),
                    ("What did Dad say?", "B", ["it needs more sugar", "it was the best cake ever", "it was too small", "he didn't like it"]),
                ]
            ),
            (
                "The Swimming Pool", 2, "sports",
                "Mia visited the swimming pool with her class. She wore her red swimsuit and "
                "yellow goggles. At first, Mia was nervous because the water looked deep. "
                "Her teacher showed her how to kick her legs and move her arms. After a few tries, "
                "Mia swam across the pool! She felt so proud. Now she wants to swim every week.",
                [
                    ("What did Mia wear on her eyes?", "C", ["sunglasses", "a hat", "yellow goggles", "a mask"]),
                    ("How did Mia feel at first?", "B", ["excited", "nervous", "bored", "angry"]),
                    ("Who helped Mia learn to swim?", "D", ["her mum", "a lifeguard", "her friend", "her teacher"]),
                    ("What did Mia do after a few tries?", "C", ["got out of the pool", "cried", "swam across the pool", "jumped in the deep end"]),
                    ("How did Mia feel after swimming?", "C", ["tired", "sad", "proud", "scared"]),
                ]
            ),
            (
                "A Trip to the Zoo", 2, "animals",
                "Jake went to the zoo with his family. He saw lions, elephants, and colourful parrots. "
                "The elephants were Jake's favourite. One elephant sprayed water from its trunk and made "
                "everyone laugh. Jake ate an ice cream while watching the penguins waddle about. "
                "At the end of the day, Jake said the zoo was the best place in the world.",
                [
                    ("Who did Jake go to the zoo with?", "C", ["his class", "his friends", "his family", "his teacher"]),
                    ("Which animals were Jake's favourite?", "D", ["lions", "parrots", "penguins", "elephants"]),
                    ("What did the elephant spray?", "C", ["sand", "food", "water", "mud"]),
                    ("What did Jake eat at the zoo?", "D", ["a hot dog", "popcorn", "a sandwich", "ice cream"]),
                    ("What did Jake say about the zoo?", "C", ["it was boring", "it was scary", "it was the best place in the world", "he didn't want to go back"]),
                ]
            ),
            (
                "My New Bike", 2, "outdoor",
                "On his birthday, Ben received a shiny red bike. It had a silver bell and a "
                "water bottle holder. Ben put on his helmet and knee pads, then rode up and down "
                "the street. At first he wobbled, but he kept trying. By afternoon, he could ride "
                "in a straight line without stopping. His grandpa cheered and clapped for him.",
                [
                    ("What did Ben get for his birthday?", "B", ["a scooter", "a red bike", "a skateboard", "roller skates"]),
                    ("What did Ben wear to stay safe?", "C", ["goggles and gloves", "a coat and boots", "a helmet and knee pads", "a hat and scarf"]),
                    ("What happened when Ben first tried to ride?", "D", ["he fell off", "he rode perfectly", "he stopped", "he wobbled"]),
                    ("What could Ben do by the afternoon?", "C", ["do tricks", "ride very fast", "ride in a straight line", "ride with no hands"]),
                    ("Who cheered for Ben?", "D", ["his mum", "his friend", "his teacher", "his grandpa"]),
                ]
            ),
            (
                "The Little Frog", 2, "animals",
                "Near the pond, a little green frog sat on a lily pad. It watched a dragonfly zoom past. "
                "With one big leap, the frog jumped into the cool water. It swam to the muddy bank and "
                "climbed out again. A duck waddled over to look, but the frog hopped away quickly "
                "into the tall grass and hid.",
                [
                    ("Where was the frog sitting?", "C", ["on a rock", "on a log", "on a lily pad", "on the bank"]),
                    ("What flew past the frog?", "D", ["a butterfly", "a bee", "a bird", "a dragonfly"]),
                    ("Where did the frog jump?", "C", ["into the grass", "onto a rock", "into the cool water", "onto the duck"]),
                    ("What came to look at the frog?", "B", ["a cat", "a duck", "a dog", "a rabbit"]),
                    ("Where did the frog hide?", "D", ["under water", "in a tree", "in the mud", "in the tall grass"]),
                ]
            ),
            (
                "The Helpful Robot", 2, "science",
                "Tim built a small robot in his garage. The robot had two round eyes and a square body "
                "painted blue. Tim taught it to pick up toys and put them in a box. When Mum saw the "
                "tidy room, she was amazed. She asked Tim if the robot could wash the dishes too. "
                "Tim laughed and said he would need to add more buttons.",
                [
                    ("Where did Tim build the robot?", "C", ["at school", "in his bedroom", "in the garage", "in the kitchen"]),
                    ("What colour was the robot painted?", "D", ["red", "green", "yellow", "blue"]),
                    ("What did the robot do with the toys?", "C", ["broke them", "hid them", "put them in a box", "sorted them by colour"]),
                    ("Who was amazed?", "B", ["Dad", "Mum", "Tim", "a friend"]),
                    ("What did Mum ask the robot to do?", "C", ["cook dinner", "sweep the floor", "wash the dishes", "water the plants"]),
                ]
            ),
            # ── LEVEL 3 ──────────────────────────────────────────────────
            (
                "The Brave Little Turtle", 3, "animals",
                "Deep in the forest, a small turtle named Pip lived beside a clear stream. "
                "Unlike other turtles, Pip was afraid of the water. Every morning, the other turtles "
                "dove in and swam happily, but Pip stayed on the bank. One hot summer day, a bird "
                "dropped a shiny pebble into the stream. Pip wanted that pebble so much that he took "
                "a deep breath, closed his eyes, and stepped in. The cool water felt wonderful! "
                "From that day on, Pip was the first turtle into the stream every morning.",
                [
                    ("Where did Pip live?", "C", ["in a lake", "in the sea", "beside a stream", "in a pond"]),
                    ("What was Pip afraid of?", "D", ["birds", "other turtles", "the forest", "the water"]),
                    ("What did the bird drop into the stream?", "B", ["a leaf", "a shiny pebble", "a fish", "a twig"]),
                    ("How did the cool water feel to Pip?", "C", ["cold and scary", "too deep", "wonderful", "like ice"]),
                    ("What happened after Pip's first swim?", "C", ["he told all his friends", "he was still scared", "he became the first in the stream each morning", "he swam to another forest"]),
                ]
            ),
            (
                "The Night Sky", 3, "science",
                "On a clear evening, Rosa and her grandfather climbed the hill behind their house. "
                "Grandfather pointed out the North Star, which sailors used to find their way across "
                "the ocean. Then he showed Rosa the Milky Way — a faint band of millions of stars "
                "stretching across the sky. Rosa counted as many stars as she could before losing track. "
                "She asked if anyone lived on those distant stars. Grandfather smiled and said that was "
                "a question scientists were still trying to answer.",
                [
                    ("Where did Rosa and her grandfather go?", "C", ["to the beach", "to an observatory", "to the hill behind their house", "to a park"]),
                    ("What did sailors use the North Star for?", "D", ["to tell the time", "to predict rain", "to count stars", "to find their way across the ocean"]),
                    ("What is the Milky Way described as?", "C", ["a single bright star", "the moon's path", "a faint band of millions of stars", "a cluster of five stars"]),
                    ("What did Rosa ask her grandfather?", "B", ["how far away the moon was", "if anyone lived on distant stars", "when the stars would fall", "how to find the North Star"]),
                    ("What was grandfather's answer about life on other stars?", "D", ["yes, definitely", "no, never", "only robots live there", "scientists were still trying to find out"]),
                ]
            ),
            (
                "How Butterflies Grow", 3, "nature",
                "A butterfly begins its life as a tiny egg laid on a leaf. When the egg hatches, "
                "a small caterpillar crawls out and begins to eat leaves. The caterpillar grows bigger "
                "every day. When it is ready, it wraps itself in a silky shell called a chrysalis. "
                "Inside the chrysalis, something amazing happens — the caterpillar slowly changes its "
                "entire body. After a few weeks, the shell splits open and a beautiful butterfly "
                "stretches its new wings and flies away.",
                [
                    ("What does a butterfly start as?", "C", ["a caterpillar", "a chrysalis", "a tiny egg", "a cocoon"]),
                    ("What does the caterpillar do when it first hatches?", "D", ["flies away", "spins a web", "digs a hole", "begins to eat leaves"]),
                    ("What is the silky shell called?", "B", ["a cocoon", "a chrysalis", "an egg case", "a pod"]),
                    ("What happens inside the chrysalis?", "C", ["the caterpillar sleeps", "it lays eggs", "the body slowly changes", "it grows more legs"]),
                    ("What does the butterfly do when it comes out?", "D", ["eats a leaf", "lays eggs", "makes a chrysalis", "stretches its wings and flies away"]),
                ]
            ),
            (
                "The Old Library", 3, "school",
                "At the end of Oak Street stood an old library with a green door and tall windows. "
                "Inside, the shelves reached up to the ceiling, packed with thousands of books. "
                "The librarian, Mrs. Lee, knew where every single book was kept. When new student "
                "Cleo visited for the first time, she felt lost among the towering shelves. "
                "Mrs. Lee gave her a map of the library and suggested three books about faraway lands. "
                "Cleo borrowed all three and came back the very next day.",
                [
                    ("What colour was the library door?", "D", ["blue", "red", "brown", "green"]),
                    ("What did Mrs. Lee know?", "B", ["how to fix computers", "where every book was", "every student's name", "how to bake"]),
                    ("How did Cleo feel when she first arrived?", "C", ["excited and happy", "angry", "lost", "bored"]),
                    ("What did Mrs. Lee give Cleo?", "C", ["a library card", "a book to read", "a map of the library", "a list of rules"]),
                    ("What did Cleo do with the three books?", "D", ["put them back", "read one and returned two", "lost them", "borrowed all three and came back next day"]),
                ]
            ),
            (
                "A Visit to Grandma's Farm", 3, "family",
                "Every summer, Maya visited her grandma's farm in the countryside. The farm had "
                "a red barn, a vegetable patch, and a small pond where ducks swam. Maya's favourite "
                "job was collecting the warm eggs from the henhouse each morning. Grandma taught her "
                "how to plant carrot seeds in neat rows. They watered them together and watched tiny "
                "green shoots appear after a few days. Maya took a photo of the carrots to show "
                "her class back in the city.",
                [
                    ("What colour was the barn?", "C", ["white", "brown", "red", "yellow"]),
                    ("What was Maya's favourite job on the farm?", "D", ["feeding the ducks", "watering the garden", "milking the cows", "collecting eggs"]),
                    ("What did Grandma teach Maya to plant?", "C", ["tomatoes", "sunflowers", "carrot seeds", "beans"]),
                    ("What appeared after a few days?", "B", ["flowers", "tiny green shoots", "vegetables", "fruit"]),
                    ("What did Maya take back to show her class?", "C", ["a carrot", "an egg", "a photo of the carrots", "a flower"]),
                ]
            ),
            (
                "The Snowman", 3, "seasons",
                "After the heaviest snowfall in years, siblings Leo and Freya rushed outside to build "
                "a snowman. They rolled three large snowballs and stacked them on top of each other. "
                "They gave him a carrot nose, coal eyes, and an old striped scarf. Dad brought out "
                "his favourite hat and placed it on the snowman's head. That evening, the temperature "
                "rose and the snowman began to melt. Leo felt sad, but Freya reminded him that they "
                "could build an even bigger one next time it snowed.",
                [
                    ("What had just happened before they went outside?", "B", ["a storm", "the heaviest snowfall in years", "a frost", "heavy rain"]),
                    ("How many snowballs did they roll?", "D", ["two", "four", "five", "three"]),
                    ("What did they use for the snowman's nose?", "D", ["a stone", "a button", "a stick", "a carrot"]),
                    ("What happened that evening?", "C", ["it snowed more", "they took a photo", "the snowman began to melt", "the hat blew off"]),
                    ("What did Freya tell Leo?", "B", ["to stop being sad", "they could build a bigger one next time", "they should go inside", "snowmen always melt"]),
                ]
            ),
            # ── LEVEL 4 (Primary 6 / PSLE Singapore) ─────────────────────
            (
                "The Kampong Spirit", 4, "heritage",
                "Before Singapore became a modern city, many people lived in kampongs — villages of wooden "
                "houses surrounded by fruit trees and open land. Life in the kampong was simple but filled "
                "with warmth. Neighbours shared food, helped one another repair their homes, and celebrated "
                "festivals together. Children played barefoot in the dirt, chased chickens, and climbed "
                "rambutan trees after school. "
                "Today, almost no kampongs remain in Singapore. The government built Housing Development "
                "Board flats to provide every family with a clean, safe, and comfortable home. Thousands "
                "of families moved from kampongs into these high-rise apartments during the 1960s and 1970s. "
                "However, the 'kampong spirit' — the feeling of care and togetherness — did not disappear. "
                "Community centres were set up in every neighbourhood so that residents could gather, learn "
                "new skills, and celebrate national events. Block parties, where neighbours share food at "
                "long tables in the void deck, keep that old spirit alive in a modern setting. "
                "Historians believe that remembering the kampong way of life helps Singaporeans stay "
                "connected to their roots. Although the physical kampongs are gone, the values they "
                "represented — kindness, sharing, and looking out for one another — remain an important "
                "part of Singapore's national identity.",
                [
                    ("What is a kampong?", "A",
                     ["a village of wooden houses surrounded by fruit trees and open land",
                      "a type of HDB flat built in the 1960s", "a community centre for residents", "a modern shopping district"]),
                    ("What does 'kampong spirit' mean in this passage?", "B",
                     ["the physical buildings and land of a kampong",
                      "the feeling of care and togetherness among neighbours",
                      "the outdoor games children played", "the festivals celebrated in the village"]),
                    ("Why did families move from kampongs to HDB flats?", "C",
                     ["kampong life was too dangerous", "the government forced all residents to leave",
                      "to have clean, safe, and comfortable homes", "HDB flats were located near better schools"]),
                    ("What keeps the kampong spirit alive in modern Singapore?", "D",
                     ["rebuilding old kampong structures", "planting fruit trees around HDB blocks",
                      "returning to traditional festivals only", "community centres and void-deck block parties"]),
                    ("What is the main message of the passage?", "C",
                     ["Singapore should rebuild its kampongs", "HDB flats are superior to kampong houses",
                      "the values of the kampong live on in modern Singapore", "technology has replaced traditional communities"]),
                ]
            ),
            (
                "Solar Energy in Singapore", 4, "science",
                "Singapore is a small country with limited land and no natural resources such as coal or oil. "
                "To meet its growing energy needs, Singapore has been investing heavily in solar power. Solar "
                "panels, which convert sunlight into electricity, are now found on the rooftops of schools, "
                "community centres, and Housing Development Board flats across the island. "
                "One major challenge is Singapore's tropical weather. Although the country receives plentiful "
                "sunlight throughout the year, frequent clouds and heavy rain can reduce the amount of "
                "electricity that solar panels produce. Engineers are working on ways to store the energy "
                "collected on sunny days so that it can be used when the sky is overcast. "
                "Singapore has also placed thousands of floating solar panels on reservoirs such as Tengeh "
                "Reservoir in Tuas. This floating solar farm is one of the largest in the world and produces "
                "enough electricity to power the waterworks that clean and supply water to the entire island. "
                "The government aims to have solar panels on most of Singapore's suitable rooftops by 2030. "
                "This shift towards clean energy helps reduce carbon emissions, which contribute to climate "
                "change. By harnessing the power of the sun, Singapore is working towards a greener and "
                "more sustainable future for all its residents.",
                [
                    ("Why does Singapore invest in solar energy?", "A",
                     ["it has limited land and no natural resources like coal or oil",
                      "solar panels are inexpensive to install", "Singapore has very few buildings",
                      "other energy sources have been banned"]),
                    ("What challenge does Singapore's tropical weather create for solar energy?", "B",
                     ["the sun shines too brightly and damages the panels",
                      "frequent clouds and heavy rain can reduce electricity production",
                      "the heat melts the solar panel components", "strong winds blow the panels off rooftops"]),
                    ("What does the word 'overcast' mean in the passage?", "C",
                     ["extremely sunny and bright", "stormy with heavy rain",
                      "covered with clouds", "very hot and humid"]),
                    ("What is significant about Tengeh Reservoir?", "D",
                     ["it is the largest reservoir in Asia", "it supplies water to Malaysia",
                      "it generates power from wind turbines",
                      "it hosts one of the largest floating solar farms in the world"]),
                    ("How does increasing solar energy use benefit Singapore?", "C",
                     ["it creates more jobs than any other industry", "it removes the need to import water",
                      "it reduces carbon emissions and supports a greener future",
                      "it powers all vehicles on the island"]),
                ]
            ),
            (
                "Ling's Big Decision", 4, "values",
                "Ling had been saving her pocket money for three months. She had exactly ninety dollars — "
                "just enough to buy the pair of limited-edition sneakers she had been dreaming about. On "
                "the day she planned to visit the mall, she noticed a poster at school asking for donations "
                "to help families affected by a recent flood in Malaysia. "
                "The poster showed photographs of children her age standing in flooded homes, their "
                "belongings ruined by muddy water. Ling felt a tug in her heart. She thought about how "
                "she already had three pairs of perfectly good shoes at home, while some of these children "
                "might not even have one. "
                "That evening, Ling spoke to her father about what she had seen. He listened carefully "
                "without telling her what to do. 'It's your money, Ling,' he said. 'Whatever you decide, "
                "make sure you can live with it.' "
                "The next morning, Ling placed an envelope with fifty dollars into the donation box. She "
                "kept forty dollars to continue saving for the sneakers. It would take longer now, but she "
                "felt lighter somehow — as though she had set down a heavy bag she hadn't known she was "
                "carrying. Her teacher, who had seen Ling drop the envelope in, simply smiled and said "
                "nothing. Some decisions, Ling realised, didn't need applause to feel right.",
                [
                    ("What had Ling been saving money for?", "A",
                     ["to buy limited-edition sneakers", "to go on a holiday",
                      "to donate to a charity", "to buy a birthday gift for a friend"]),
                    ("What caused Ling to reconsider spending all her money?", "C",
                     ["her father told her not to buy the sneakers", "the sneakers were sold out at the mall",
                      "she saw a poster about families affected by a flood",
                      "her teacher asked the class to donate"]),
                    ("What does Ling's father's response suggest about him?", "D",
                     ["he was disappointed that Ling wanted expensive sneakers",
                      "he wanted Ling to donate all of her money",
                      "he believed children should not make financial decisions",
                      "he respected Ling's ability to make her own choices"]),
                    ("What does 'felt lighter somehow' suggest about Ling after donating?", "B",
                     ["she had become physically lighter from walking to school",
                      "she felt relieved and at peace after making a generous decision",
                      "she was glad to have less money to keep track of",
                      "she felt tired and wanted to go home and rest"]),
                    ("What is the main message of this story?", "C",
                     ["people should never spend money on luxury items",
                      "saving money is more important than spending it",
                      "true satisfaction often comes from thinking of others",
                      "parents should always decide how children spend their money"]),
                ]
            ),
            (
                "The Deep-Sea Discovery", 4, "science",
                "More than eighty percent of the world's oceans remain unexplored. Scientists aboard the "
                "research vessel Horizon were therefore not surprised to encounter something unusual during "
                "their latest dive near the Mariana Trench — the deepest point on Earth, stretching nearly "
                "eleven kilometres below the surface. "
                "Using a remote-controlled submersible, the team captured footage of a creature they had "
                "never seen before. It was pale, almost transparent, with long ribbon-like fins that "
                "rippled gracefully in the total darkness. The creature appeared to produce its own soft "
                "blue light through a process called bioluminescence — the same natural ability seen in "
                "fireflies and certain deep-sea jellyfish. "
                "Dr Amara, the team's marine biologist, was cautious despite her excitement. 'We cannot "
                "say with certainty what species this is,' she told reporters. 'Deep-sea creatures are so "
                "rarely observed that our knowledge of them remains very limited. This discovery reminds "
                "us how much there is still to learn.' "
                "The footage was shared with universities and research institutes around the world. "
                "Scientists noticed that the creature's light patterns changed when a second, smaller "
                "creature swam nearby, suggesting that bioluminescence might serve as a means of "
                "communication. This discovery has renewed calls for greater funding and protection of "
                "deep-sea habitats, which are increasingly threatened by pollution and mining operations.",
                [
                    ("What percentage of the world's oceans remain unexplored?", "A",
                     ["more than eighty percent", "about fifty percent",
                      "less than twenty percent", "exactly sixty percent"]),
                    ("What is bioluminescence?", "C",
                     ["a method of swimming in complete darkness",
                      "a type of deep-sea pollution caused by chemicals",
                      "the natural ability of a living thing to produce its own light",
                      "a scientific tool used to film underwater creatures"]),
                    ("Why was Dr Amara cautious about the discovery?", "D",
                     ["she believed the creature was dangerous to approach",
                      "the video footage was too blurry to study",
                      "she was not convinced the creature was real",
                      "deep-sea creatures are rarely observed and difficult to identify with certainty"]),
                    ("What did scientists conclude from the creature's changing light patterns?", "B",
                     ["the creature was frightened by the submersible's lights",
                      "bioluminescence may be used as a form of communication",
                      "the creature was trying to hide from the camera",
                      "the light patterns matched those of known deep-sea jellyfish"]),
                    ("What does the word 'transparent' mean in the passage?", "D",
                     ["extremely large and powerful in the deep sea",
                      "colourful and easy to spot in darkness",
                      "capable of surviving in extremely cold water",
                      "see-through or nearly clear"]),
                ]
            ),
            (
                "Singapore's Water Story", 4, "environment",
                "Water is one of Singapore's most precious resources. As a small island nation with no "
                "natural lakes or rivers large enough to store significant amounts of water, Singapore "
                "has had to be creative and disciplined in managing its water supply. "
                "Singapore uses four main sources of water, known as the 'Four National Taps'. The first "
                "is rainwater collected and stored in reservoirs. The second is water imported from the "
                "Johor River in Malaysia under long-term agreements. The third is NEWater — highly "
                "purified recycled water treated until it is cleaner than most drinking water in the "
                "world. The fourth is desalinated water, which is seawater with the salt removed. "
                "NEWater was once considered an unusual idea, but today it supplies about forty percent "
                "of Singapore's water needs. The technology uses micro-filtration, reverse osmosis, and "
                "ultraviolet disinfection to remove all impurities. "
                "Singapore's national water agency runs regular campaigns encouraging residents to use "
                "water wisely. Schools teach water conservation from an early age, and water-efficient "
                "fittings are required in all new buildings. Because Singapore knows from experience "
                "what it means to face water shortages, it treats every drop as valuable. This careful, "
                "forward-thinking approach to water management is now studied and admired by countries "
                "around the world.",
                [
                    ("Why does Singapore face challenges in managing its water supply?", "C",
                     ["it has too many rivers to manage efficiently",
                      "its population is too small to build large dams",
                      "it is a small island with no large lakes or rivers",
                      "heavy rain causes constant flooding in its reservoirs"]),
                    ("What are the 'Four National Taps'?", "B",
                     ["four rivers that supply Singapore with water",
                      "four methods Singapore uses to collect and produce water",
                      "four companies that manage Singapore's water supply",
                      "four dams built along Singapore's coastline"]),
                    ("What does the word 'desalinated' mean in the passage?", "D",
                     ["recycled and purified through filtration", "collected from rainfall and stored",
                      "tested for safety before drinking", "having had the salt removed"]),
                    ("What does Singapore's development of NEWater show about the country?", "C",
                     ["Singapore relies on Malaysia for the majority of its water",
                      "Singapore prefers importing water over producing its own",
                      "Singapore is willing to use creative solutions to overcome challenges",
                      "Singapore's water technology was entirely borrowed from other countries"]),
                    ("Why is Singapore's water management admired worldwide?", "D",
                     ["it is the cheapest water system in Asia",
                      "it relies on a single source to supply all its water",
                      "it was designed entirely by international experts",
                      "it is a forward-thinking solution to the challenge of scarce water resources"]),
                ]
            ),
            (
                "The Rainforest at Night", 4, "nature",
                "As the sun dips below the horizon in the tropical rainforest, a different world stirs "
                "to life. Animals that remain hidden during the heat of the day emerge cautiously in the "
                "cooler darkness. This pattern of being active at night, known as nocturnal behaviour, "
                "helps many species avoid the intense daytime heat and predators that hunt by sight. "
                "Owls launch silently from their perches, using exceptional hearing to locate prey "
                "beneath layers of fallen leaves. Tree frogs cling to damp bark and fill the night air "
                "with calls that scientists use to measure the health of a forest ecosystem. Slow lorises "
                "— small primates with enormous round eyes — move carefully through the canopy, their "
                "eyes absorbing every trace of moonlight. "
                "Perhaps the most dramatic nighttime display belongs to fireflies. In parts of Southeast "
                "Asia, thousands of fireflies gather in the same trees and flash their lights in perfect "
                "synchrony. Scientists believe this coordinated display may help them attract mates "
                "across long distances in the dense forest. "
                "Rainforests cover only about six percent of the Earth's land surface yet are home to "
                "more than half of the world's plant and animal species. Protecting these habitats — "
                "including their nocturnal ecosystems — is essential for maintaining the rich "
                "biodiversity that our planet depends on.",
                [
                    ("Why do some animals prefer to be active at night?", "C",
                     ["there is more food available after dark",
                      "they are frightened of humans during the day",
                      "to avoid intense heat and predators that hunt by sight",
                      "nocturnal animals are physically unable to see in daylight"]),
                    ("How do owls locate their prey in total darkness?", "D",
                     ["by using a keen sense of smell", "by following the movements of other animals",
                      "by seeing clearly in complete darkness", "by using their exceptional hearing"]),
                    ("What do scientists learn from studying tree frog calls?", "C",
                     ["the average temperature of the rainforest at night",
                      "how far away other nocturnal animals are",
                      "the health of a forest ecosystem",
                      "which trees frogs prefer to climb and rest on"]),
                    ("What does the word 'synchrony' mean in the passage?", "C",
                     ["randomly and without any pattern", "in a slow and gradual manner",
                      "at the same time in a perfectly coordinated way",
                      "in reaction to a sudden threat or danger"]),
                    ("Why is protecting rainforests described as 'essential'?", "D",
                     ["they produce most of the world's fresh drinking water",
                      "they cover more than half of the Earth's land surface",
                      "they are the natural habitat of the world's largest animals",
                      "they are home to more than half of all plant and animal species on Earth"]),
                ]
            ),
        ]

        for title, level, topic, content, questions in passages:
            if not seed_all and level != 4:
                continue  # Only insert level-4 passages when upgrading an existing database
            cursor.execute(
                "INSERT INTO passages (title, content, difficulty_level, word_count, topic, is_seed) VALUES (?, ?, ?, ?, ?, 1)",
                (title, content, level, len(content.split()), topic)
            )
            passage_id = cursor.lastrowid
            for q_text, correct, options in questions:
                cursor.execute(
                    "INSERT INTO questions (passage_id, question_text, correct_answer, option_a, option_b, option_c, option_d) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (passage_id, q_text, correct, options[0], options[1], options[2], options[3])
                )
        self.conn.commit()

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
