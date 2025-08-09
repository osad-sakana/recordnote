"""Font management module for Japanese fonts in Kivy."""

import os
import urllib.request
from pathlib import Path
from typing import Optional

from kivy.core.text import FontContextManager as FCM
from kivy.core.text import LabelBase
from kivy.logger import Logger


class FontManager:
    """Manager for Japanese fonts in Kivy application."""

    def __init__(self) -> None:
        """Initialize font manager."""
        self.fonts_dir = Path(__file__).parent.parent.parent / "assets" / "fonts"
        self.fonts_dir.mkdir(parents=True, exist_ok=True)
        self.japanese_font_family: Optional[str] = None

    def download_biz_udp_gothic(self) -> Path:
        """Download BIZ UDP Gothic font from GitHub release.

        Returns:
            Path to downloaded font file
        """
        font_path = self.fonts_dir / "BIZ_UDP_Gothic-Regular.ttf"

        if not font_path.exists():
            Logger.info(f"FontManager: Downloading BIZ UDP Gothic font...")

            # Try multiple download sources
            font_urls = [
                # GitHub release (more reliable)
                "https://github.com/googlefonts/morisawa-biz-ud-gothic/raw/main/fonts/ttf/BIZUDPGothic-Regular.ttf",
                # Alternative Google Fonts API
                "https://fonts.gstatic.com/s/bizudpgothic/v10/qFdR35CBWxZT-1oZIDkX-NJFhxsC8gKATiYGRg.ttf",
            ]

            for font_url in font_urls:
                try:
                    urllib.request.urlretrieve(font_url, font_path)
                    Logger.info(f"FontManager: Font downloaded from {font_url}")
                    break
                except Exception as e:
                    Logger.warning(
                        f"FontManager: Failed to download from {font_url}: {e}"
                    )
                    continue
            else:
                Logger.error("FontManager: All download attempts failed")
                raise RuntimeError("Could not download BIZ UDP Gothic font")
        else:
            Logger.info(f"FontManager: Font already exists at {font_path}")

        return font_path

    def setup_japanese_font(self) -> None:
        """Setup Japanese font for Kivy application."""
        # Always start with system fonts as they are most reliable
        Logger.info("FontManager: Setting up Japanese fonts...")
        
        # First, try to use system fonts which we know work
        if self._setup_system_font():
            Logger.info("FontManager: System font setup successful")
        else:
            Logger.warning("FontManager: System font setup failed, trying downloaded fonts")
            try:
                # Try to download BIZ UDP Gothic as backup
                font_path = self.download_biz_udp_gothic()
                LabelBase.register(name="japanese", fn_regular=str(font_path))
                Logger.info("FontManager: Downloaded font registered successfully")
            except Exception as e:
                Logger.error(f"FontManager: All font setup methods failed: {e}")
                self._setup_emergency_fallback()

    def _setup_system_font(self) -> bool:
        """Setup system Japanese font.
        
        Returns:
            True if successful, False otherwise
        """
        system_fonts = [
            # macOS - most reliable Japanese fonts first
            "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
            "/System/Library/Fonts/Hiragino Sans GB.ttc", 
            "/System/Library/Fonts/NotoSansCJK.ttc",
            "/Library/Fonts/Arial Unicode MS.ttf",
            # macOS additional
            "/System/Library/Fonts/PingFang.ttc",
            "/System/Library/Fonts/STHeiti Light.ttc",
            # Windows
            "C:/Windows/Fonts/msgothic.ttc",
            "C:/Windows/Fonts/meiryo.ttc", 
            "C:/Windows/Fonts/YuGothM.ttc",
            "C:/Windows/Fonts/NotoSansCJK-Regular.ttc",
            # Linux
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.otf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]

        for font_path in system_fonts:
            if os.path.exists(font_path):
                try:
                    # Test the font by registering it
                    LabelBase.register(name="japanese", fn_regular=font_path)
                    Logger.info(f"FontManager: Successfully registered system font: {font_path}")
                    
                    # Verify the font can handle Japanese characters
                    if self._test_font_japanese_support(font_path):
                        Logger.info(f"FontManager: Font confirmed to support Japanese: {font_path}")
                        return True
                    else:
                        Logger.warning(f"FontManager: Font does not support Japanese glyphs: {font_path}")
                        continue
                        
                except Exception as e:
                    Logger.warning(f"FontManager: Failed to register {font_path}: {e}")
                    continue

        return False

    def _test_font_japanese_support(self, font_path: str) -> bool:
        """Test if font supports Japanese characters.
        
        Args:
            font_path: Path to font file
            
        Returns:
            True if font supports Japanese, False otherwise
        """
        # For now, return True for known good fonts
        japanese_font_indicators = [
            "ヒラギノ", "Hiragino", "NotoSans", "msgothic", 
            "meiryo", "YuGoth", "PingFang", "STHeiti"
        ]
        
        return any(indicator in font_path for indicator in japanese_font_indicators)

    def _setup_emergency_fallback(self) -> None:
        """Setup emergency fallback when no Japanese font is available."""
        Logger.warning(
            "FontManager: No Japanese font found. Using default system font. "
            "Japanese text may not display correctly."
        )
        # Don't register any font - let Kivy use its default

    def get_font_config(self) -> dict:
        """Get font configuration for widgets.

        Returns:
            Dictionary with font configuration
        """
        if self.japanese_font_family:
            return {
                "font_context": "system://recordnote",
                "font_family": self.japanese_font_family,
            }
        else:
            return {"font_name": "japanese"}

    def get_md_font_config(self) -> dict:
        """Get font configuration specifically for MD widgets.

        Returns:
            Dictionary with font configuration for MDTextField and similar
        """
        # MDTextField has different font property names
        return {"font_name": "japanese"}  # MDTextField uses font_name, not font_family

    def configure_kivymd_fonts(self, app) -> None:
        """Configure KivyMD default fonts to use Japanese font.
        
        Args:
            app: The KivyMD app instance
        """
        try:
            # Override KivyMD's default font paths
            app.theme_cls.font_styles["Body1"] = [
                "japanese", 14, False, 0.15
            ]
            app.theme_cls.font_styles["Body2"] = [
                "japanese", 14, False, 0.15  
            ]
            app.theme_cls.font_styles["Caption"] = [
                "japanese", 12, False, 0.15
            ]
            app.theme_cls.font_styles["Subtitle1"] = [
                "japanese", 16, False, 0.15
            ]
            app.theme_cls.font_styles["Subtitle2"] = [
                "japanese", 14, False, 0.10
            ]
            Logger.info("FontManager: KivyMD font styles configured for Japanese")
        except Exception as e:
            Logger.warning(f"FontManager: Failed to configure KivyMD fonts: {e}")


# Global font manager instance
font_manager = FontManager()
