"""
Remove all Unicode characters from test files to fix Windows encoding issues
"""

import os
import re

def clean_unicode(text):
    """Remove all Unicode characters and replace with ASCII equivalents"""
    # Replace common Unicode characters
    replacements = {
        '✅': '[OK]',
        '❌': '[FAIL]',
        '🎉': '[DONE]',
        '🧪': '[TEST]',
        '🤖': '[AI]',
        '🔧': '[TOOL]',
        '📋': '[LIST]',
        '🔹': '[ITEM]',
        '1️⃣': '1.',
        '2️⃣': '2.',
        '3️⃣': '3.',
        '4️⃣': '4.',
        '5️⃣': '5.',
        '6️⃣': '6.',
        '7️⃣': '7.',
        '🚀': '[START]',
        '🎯': '[TARGET]',
        '📥': '[INPUT]',
        '📤': '[OUTPUT]',
        '⚙️': '[PARAM]',
        '🔍': '[SEARCH]',
        '💡': '[TIP]',
        '🔗': '[LINK]',
        '📊': '[DATA]',
        '🎨': '[DESIGN]',
        '🛠️': '[TOOL]',
        '📁': '[FOLDER]',
        '🆕': '[NEW]',
        '🔧': '[FIX]',
        '📝': '[NOTE]',
        '🎪': '[CIRCUS]',
        '🎭': '[MASK]',
        '🎨': '[ART]',
        '🎵': '[MUSIC]',
        '🎬': '[MOVIE]',
        '🎮': '[GAME]',
        '🎯': '[TARGET]',
        '🎲': '[DICE]',
        '🎳': '[BOWLING]',
        '🎸': '[GUITAR]',
        '🎺': '[TRUMPET]',
        '🎻': '[VIOLIN]',
        '🎼': '[SCORE]',
        '🎽': '[RUNNING]',
        '🎾': '[TENNIS]',
        '🎿': '[SKIING]',
        '🏀': '[BASKETBALL]',
        '🏁': '[FINISH]',
        '🏂': '[SNOWBOARD]',
        '🏃': '[RUNNING]',
        '🏄': '[SURFING]',
        '🏅': '[MEDAL]',
        '🏆': '[TROPHY]',
        '🏇': '[HORSE]',
        '🏈': '[FOOTBALL]',
        '🏉': '[RUGBY]',
        '🏊': '[SWIMMING]',
        '🏋': '[WEIGHTLIFTING]',
        '🏌': '[GOLF]',
        '🏍': '[MOTORCYCLE]',
        '🏎': '[RACING]',
        '🏏': '[CRICKET]',
        '🏐': '[VOLLEYBALL]',
        '🏑': '[HOCKEY]',
        '🏒': '[HOCKEY]',
        '🏓': '[PINGPONG]',
        '🏔': '[MOUNTAIN]',
        '🏕': '[CAMPING]',
        '🏖': '[BEACH]',
        '🏗': '[CONSTRUCTION]',
        '🏘': '[HOUSES]',
        '🏙': '[CITY]',
        '🏚': '[HOUSE]',
        '🏛': '[BUILDING]',
        '🏜': '[DESERT]',
        '🏝': '[ISLAND]',
        '🏞': '[PARK]',
        '🏟': '[STADIUM]',
        '🏠': '[HOUSE]',
        '🏡': '[HOUSE]',
        '🏢': '[OFFICE]',
        '🏣': '[POST]',
        '🏤': '[EURO]',
        '🏥': '[HOSPITAL]',
        '🏦': '[BANK]',
        '🏧': '[ATM]',
        '🏨': '[HOTEL]',
        '🏩': '[LOVE]',
        '🏪': '[STORE]',
        '🏫': '[SCHOOL]',
        '🏬': '[DEPARTMENT]',
        '🏭': '[FACTORY]',
        '🏮': '[LANTERN]',
        '🏯': '[CASTLE]',
        '🏰': '[CASTLE]',
        '🏱': '[FLAG]',
        '🏲': '[FLAG]',
        '🏳': '[FLAG]',
        '🏴': '[FLAG]',
        '🏵': '[ROSETTE]',
        '🏶': '[LABEL]',
        '🏷': '[LABEL]',
        '🏸': '[BADMINTON]',
        '🏹': '[BOW]',
        '🏺': '[POT]',
        '🏻': '',  # Skin tone modifiers
        '🏼': '',
        '🏽': '',
        '🏾': '',
        '🏿': '',
    }
    
    # Apply replacements
    for unicode_char, ascii_replacement in replacements.items():
        text = text.replace(unicode_char, ascii_replacement)
    
    # Remove any remaining Unicode characters
    text = re.sub(r'[^\x00-\x7F]+', '', text)
    
    return text

def clean_file(file_path):
    """Clean a single file"""
    print(f"Cleaning {file_path}...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    cleaned_content = clean_unicode(content)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(cleaned_content)
    
    print(f"✅ Cleaned {file_path}")

def main():
    """Clean all test files"""
    tests_dir = os.path.join(os.path.dirname(__file__), 'tests')
    
    test_files = [
        'test_node_registry.py',
        'test_language_model_tool.py',
        'test_language_model_node.py',
        'test_all_refactored_nodes.py'
    ]
    
    for test_file in test_files:
        file_path = os.path.join(tests_dir, test_file)
        if os.path.exists(file_path):
            clean_file(file_path)
        else:
            print(f"❌ File not found: {file_path}")
    
    print("\n🎉 All test files cleaned!")

if __name__ == "__main__":
    main()
