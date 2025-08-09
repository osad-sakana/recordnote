#!/usr/bin/env python3
"""Font testing utility for debugging Japanese text display issues."""

import os
from kivy.core.text import LabelBase, Label
from kivy.logger import Logger

def test_system_fonts():
    """Test available system fonts for Japanese support."""
    print("Testing system fonts for Japanese support...")
    
    system_fonts = [
        "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc", 
        "/System/Library/Fonts/NotoSansCJK.ttc",
        "/Library/Fonts/Arial Unicode MS.ttf",
        "/System/Library/Fonts/PingFang.ttc",
    ]
    
    test_text = "こんにちは世界"  # "Hello World" in Japanese
    
    for font_path in system_fonts:
        if os.path.exists(font_path):
            try:
                print(f"Testing font: {font_path}")
                LabelBase.register(name="test_font", fn_regular=font_path)
                
                # Create a label to test rendering
                label = Label(text=test_text, font_name="test_font")
                print(f"  ✓ Successfully created label with Japanese text")
                print(f"  Font size: {label.font_size}")
                print(f"  Text: {label.text}")
                
            except Exception as e:
                print(f"  ✗ Failed to use font: {e}")
        else:
            print(f"Font not found: {font_path}")

if __name__ == "__main__":
    from kivy.app import App
    from kivy.uix.label import Label as KivyLabel
    
    class FontTestApp(App):
        def build(self):
            test_system_fonts()
            return KivyLabel(text="Font test completed - check console output")
    
    FontTestApp().run()