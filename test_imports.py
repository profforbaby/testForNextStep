"""
Test script to verify all imports work correctly
"""
print("Testing imports...")

try:
    print("1. Testing data models...")
    from edu_game_app.data.models import ChildProfile, Passage, Question
    print("   [OK] Data models OK")

    print("2. Testing database...")
    from edu_game_app.data import Database
    print("   [OK] Database OK")

    print("3. Testing core modules...")
    from edu_game_app.core import QuizEngine, DifficultyManager
    print("   [OK] Core modules OK")

    print("4. Testing GUI modules...")
    from edu_game_app.gui import MainWindow
    print("   [OK] GUI modules OK")

    print("\n[SUCCESS] All imports successful!")
    print("\nYou can now run the app with:")
    print("  python run_edu_app.py")
    print("  OR")
    print("  python edu_game_app/app.py")

except ImportError as e:
    print(f"\n[ERROR] Import error: {e}")
    print("\nMake sure you've installed dependencies:")
    print("  pip install -r edu_game_app/requirements.txt")
