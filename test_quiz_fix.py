"""
Test script to verify the quiz answer selection bug is fixed
"""
print("Testing Quiz Answer Storage...")
print("=" * 50)

from edu_game_app.data.models import Passage, Question
from edu_game_app.core import QuizEngine

# Create a simple test passage
passage = Passage(
    id=1,
    title="Test Passage",
    content="This is a test passage.",
    difficulty_level=1,
    topic="test"
)

# Add test questions
for i in range(5):
    question = Question(
        id=i+1,
        passage_id=1,
        question_text=f"Question {i+1}?",
        correct_answer="A",
        option_a="Correct Answer",
        option_b="Wrong Answer 1",
        option_c="Wrong Answer 2",
        option_d="Wrong Answer 3"
    )
    passage.questions.append(question)

# Test the quiz engine
quiz_engine = QuizEngine()
session = quiz_engine.start_quiz(passage)

print("\n1. Testing answer storage...")
print("-" * 50)

# Answer all questions
for i in range(5):
    session.current_question_index = i
    session.answer_question("A")  # Answer with A
    print(f"Question {i+1}: Answered 'A' - Stored: {session.get_answer(i)}")

# Check if all answers were stored
print("\n2. Checking if answers are saved...")
print("-" * 50)
all_saved = True
for i in range(5):
    answer = session.get_answer(i)
    if answer:
        print(f"✓ Question {i+1}: Answer '{answer}' saved correctly")
    else:
        print(f"✗ Question {i+1}: NO ANSWER SAVED (BUG!)")
        all_saved = False

# Test completion check
print("\n3. Testing quiz completion...")
print("-" * 50)
is_complete = session.is_complete()
answered, total = session.get_progress()
print(f"Answered: {answered}/{total}")
print(f"Is Complete: {is_complete}")

# Test scoring
print("\n4. Testing score calculation...")
print("-" * 50)
score, correct, total = session.calculate_score()
print(f"Score: {score * 100:.0f}%")
print(f"Correct: {correct}/{total}")

# Final result
print("\n" + "=" * 50)
if all_saved and is_complete and score == 1.0:
    print("✓✓✓ ALL TESTS PASSED! Quiz is working correctly!")
else:
    print("✗✗✗ SOME TESTS FAILED - There may still be issues")

print("\nNow test in the actual app:")
print("1. Run: python run_edu_app.py")
print("2. Start a reading passage")
print("3. Take the quiz")
print("4. Select answers for all questions")
print("5. Submit - you should see your correct score!")
