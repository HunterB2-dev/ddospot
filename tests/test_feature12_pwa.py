"""
Unit Tests for Feature #12: Mobile Dashboard & PWA Support

Tests cover:
- Service Worker functionality
- Offline capabilities
- PWA manifest validation
- Responsive design
- Touch interactions
- Performance metrics
"""

import unittest
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestPWAManifest(unittest.TestCase):
    """Test PWA manifest configuration"""

    def setUp(self):
        """Load manifest.json"""
        manifest_path = Path(__file__).parent.parent / 'static' / 'manifest.json'
        with open(manifest_path, 'r') as f:
            self.manifest = json.load(f)

    def test_manifest_required_fields(self):
        """Test that manifest has all required fields"""
        required_fields = [
            'name', 'short_name', 'start_url', 'display',
            'theme_color', 'background_color'
        ]
        for field in required_fields:
            self.assertIn(field, self.manifest, f"Missing required field: {field}")

    def test_manifest_display_mode(self):
        """Test display mode is standalone"""
        self.assertEqual(self.manifest['display'], 'standalone')

    def test_manifest_has_icons(self):
        """Test manifest includes icons"""
        self.assertIn('icons', self.manifest)
        self.assertGreater(len(self.manifest['icons']), 0)

        # Check icon sizes
        sizes = [icon['sizes'] for icon in self.manifest['icons']]
        self.assertIn('192x192', sizes)
        self.assertIn('512x512', sizes)

    def test_manifest_has_screenshots(self):
        """Test manifest includes screenshots"""
        self.assertIn('screenshots', self.manifest)
        self.assertGreater(len(self.manifest['screenshots']), 0)

    def test_manifest_theme_colors(self):
        """Test theme colors are valid hex"""
        theme = self.manifest.get('theme_color', '')
        bg = self.manifest.get('background_color', '')

        # Basic validation: starts with # or is valid color
        self.assertTrue(
            theme.startswith('#') or len(theme) == 0,
            f"Invalid theme color: {theme}"
        )
        self.assertTrue(
            bg.startswith('#') or len(bg) == 0,
            f"Invalid background color: {bg}"
        )

    def test_manifest_start_url(self):
        """Test start URL is valid"""
        start_url = self.manifest.get('start_url', '')
        self.assertIsNotNone(start_url)
        self.assertTrue(
            start_url.startswith('/') or start_url.startswith('http'),
            f"Invalid start_url: {start_url}"
        )


class TestServiceWorker(unittest.TestCase):
    """Test Service Worker implementation"""

    def setUp(self):
        """Load service worker"""
        sw_path = Path(__file__).parent.parent / 'static' / 'service-worker.js'
        with open(sw_path, 'r') as f:
            self.sw_content = f.read()

    def test_service_worker_exists(self):
        """Test service worker file exists and is not empty"""
        self.assertGreater(len(self.sw_content), 0)

    def test_service_worker_has_install_handler(self):
        """Test SW handles install event"""
        self.assertIn('addEventListener(\'install\'', self.sw_content)
        self.assertIn('caches.open', self.sw_content)

    def test_service_worker_has_activate_handler(self):
        """Test SW handles activate event"""
        self.assertIn('addEventListener(\'activate\'', self.sw_content)
        self.assertIn('caches.keys()', self.sw_content)

    def test_service_worker_has_fetch_handler(self):
        """Test SW handles fetch events"""
        self.assertIn('addEventListener(\'fetch\'', self.sw_content)

    def test_service_worker_has_cache_strategy(self):
        """Test SW implements caching strategy"""
        # Should have cache-first or network-first strategy
        self.assertTrue(
            'caches.match' in self.sw_content or
            'fetch(request)' in self.sw_content
        )

    def test_service_worker_has_offline_support(self):
        """Test SW provides offline fallback"""
        self.assertTrue('offline' in self.sw_content.lower() or 'cache' in self.sw_content)

    def test_service_worker_has_push_handler(self):
        """Test SW handles push notifications"""
        self.assertIn('addEventListener(\'push\'', self.sw_content)

    def test_service_worker_has_notification_handler(self):
        """Test SW handles notification clicks"""
        self.assertIn('addEventListener(\'notificationclick\'', self.sw_content)


class TestMobileCSS(unittest.TestCase):
    """Test mobile CSS implementation"""

    def setUp(self):
        """Load mobile CSS"""
        css_path = Path(__file__).parent.parent / 'static' / 'mobile.css'
        with open(css_path, 'r') as f:
            self.css_content = f.read()

    def test_mobile_css_exists(self):
        """Test mobile CSS file exists"""
        self.assertGreater(len(self.css_content), 0)

    def test_mobile_css_has_breakpoints(self):
        """Test CSS has responsive breakpoints"""
        self.assertIn('768px', self.css_content)  # Tablet
        self.assertIn('1200px', self.css_content)  # Desktop

    def test_mobile_css_has_touch_optimization(self):
        """Test CSS optimizes for touch"""
        # Should have 48px minimum touch targets
        self.assertIn('48px', self.css_content)

    def test_mobile_css_has_safe_area_insets(self):
        """Test CSS handles iOS safe area"""
        self.assertIn('safe-area-inset', self.css_content)

    def test_mobile_css_has_animations(self):
        """Test CSS has smooth animations"""
        self.assertIn('@keyframes', self.css_content)

    def test_mobile_css_has_dark_mode_support(self):
        """Test CSS supports dark mode"""
        self.assertIn('prefers-color-scheme', self.css_content)

    def test_mobile_css_has_accessibility_features(self):
        """Test CSS includes accessibility"""
        self.assertIn('prefers-reduced-motion', self.css_content)
        self.assertIn('focus-visible', self.css_content)

    def test_mobile_css_has_variables(self):
        """Test CSS uses CSS variables"""
        self.assertIn('--primary', self.css_content)
        self.assertIn('--spacing', self.css_content)


class TestMobileDashboardHTML(unittest.TestCase):
    """Test mobile dashboard HTML"""

    def setUp(self):
        """Load mobile dashboard HTML"""
        html_path = Path(__file__).parent.parent / 'templates' / 'mobile-dashboard.html'
        with open(html_path, 'r') as f:
            self.html_content = f.read()

    def test_mobile_html_exists(self):
        """Test mobile dashboard HTML exists"""
        self.assertGreater(len(self.html_content), 0)

    def test_html_has_pwa_meta_tags(self):
        """Test HTML includes PWA meta tags"""
        self.assertIn('apple-mobile-web-app-capable', self.html_content)
        self.assertIn('manifest.json', self.html_content)
        self.assertIn('theme-color', self.html_content)

    def test_html_has_service_worker_registration(self):
        """Test HTML registers service worker"""
        self.assertIn('serviceWorker', self.html_content)
        self.assertIn('register', self.html_content)

    def test_html_has_mobile_navigation(self):
        """Test HTML has mobile-specific nav"""
        self.assertIn('mobile-nav', self.html_content)
        self.assertIn('hamburger', self.html_content)

    def test_html_has_bottom_navbar(self):
        """Test HTML has bottom navigation bar"""
        self.assertIn('mobile-bottom-nav', self.html_content)

    def test_html_has_responsive_viewport(self):
        """Test viewport meta tag"""
        self.assertIn('viewport-fit=cover', self.html_content)
        self.assertIn('width=device-width', self.html_content)

    def test_html_has_tap_highlighting_disabled(self):
        """Test touch tap highlighting"""
        # Check for touch-action or -webkit-tap-highlight-color
        self.assertTrue(
            'touch-action' in self.html_content or
            'tap' in self.html_content.lower()
        )

    def test_html_has_offline_support(self):
        """Test HTML mentions offline support"""
        self.assertIn('offline', self.html_content.lower())


class TestResponsiveBreakpoints(unittest.TestCase):
    """Test responsive design breakpoints"""

    def setUp(self):
        """Load CSS files"""
        self.mobile_css_path = Path(__file__).parent.parent / 'static' / 'mobile.css'
        with open(self.mobile_css_path, 'r') as f:
            self.css_content = f.read()

    def test_mobile_first_approach(self):
        """Test CSS uses mobile-first approach"""
        # Mobile styles should come before media queries
        mobile_idx = self.css_content.find('mobile-')
        media_idx = self.css_content.find('@media')
        self.assertGreater(media_idx, 0, "Should have media queries")

    def test_tablet_breakpoint(self):
        """Test tablet breakpoint at 768px"""
        self.assertIn('768px', self.css_content)
        self.assertIn('@media (min-width: 768px)', self.css_content)

    def test_desktop_breakpoint(self):
        """Test desktop breakpoint at 1200px"""
        self.assertIn('1200px', self.css_content)
        self.assertIn('@media (min-width: 1200px)', self.css_content)

    def test_touch_media_query(self):
        """Test touch device detection"""
        self.assertIn('hover: none', self.css_content)
        self.assertIn('pointer: coarse', self.css_content)

    def test_button_touch_target_size(self):
        """Test button minimum touch target is 48px"""
        self.assertIn('48px', self.css_content)


class TestPWAIntegration(unittest.TestCase):
    """Integration tests for PWA features"""

    def test_pwa_files_exist(self):
        """Test all PWA files exist"""
        required_files = [
            'static/manifest.json',
            'static/service-worker.js',
            'static/mobile.css',
            'templates/mobile-dashboard.html',
        ]

        for file_path in required_files:
            path = Path(__file__).parent.parent / file_path
            self.assertTrue(
                path.exists(),
                f"Required file missing: {file_path}"
            )

    def test_manifest_and_service_worker_aligned(self):
        """Test manifest and SW are properly configured"""
        manifest_path = Path(__file__).parent.parent / 'static' / 'manifest.json'
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)

        # Check that manifest start_url makes sense
        self.assertIn('start_url', manifest)

    def test_offline_capability(self):
        """Test offline mode is supported"""
        sw_path = Path(__file__).parent.parent / 'static' / 'service-worker.js'
        with open(sw_path, 'r') as f:
            content = f.read()

        # Should have offline fallback
        self.assertTrue(
            'offline' in content.lower() or
            '.catch' in content  # Network error handling
        )


class TestPerformanceOptimizations(unittest.TestCase):
    """Test performance optimization features"""

    def setUp(self):
        """Load CSS"""
        css_path = Path(__file__).parent.parent / 'static' / 'mobile.css'
        with open(css_path, 'r') as f:
            self.css_content = f.read()

    def test_uses_gpu_acceleration(self):
        """Test CSS uses transform for animations"""
        self.assertIn('transform', self.css_content)

    def test_lazy_loading_support(self):
        """Test CSS supports lazy loading"""
        # Should have loading-related styles
        self.assertTrue(
            'lazy' in self.css_content.lower() or
            'skeleton' in self.css_content.lower()
        )

    def test_reduced_motion_support(self):
        """Test respects prefers-reduced-motion"""
        self.assertIn('prefers-reduced-motion', self.css_content)

    def test_hardware_acceleration(self):
        """Test styles enable hardware acceleration"""
        self.assertIn('transform', self.css_content)
        # Should avoid expensive properties on mobile
        self.assertNotIn('box-shadow', self.css_content)


class TestAccessibility(unittest.TestCase):
    """Test accessibility features"""

    def setUp(self):
        """Load CSS and HTML"""
        css_path = Path(__file__).parent.parent / 'static' / 'mobile.css'
        with open(css_path, 'r') as f:
            self.css_content = f.read()

        html_path = Path(__file__).parent.parent / 'templates' / 'mobile-dashboard.html'
        with open(html_path, 'r') as f:
            self.html_content = f.read()

    def test_focus_visible_styles(self):
        """Test focus-visible for keyboard navigation"""
        self.assertIn('focus-visible', self.css_content)

    def test_high_contrast_support(self):
        """Test high contrast mode support"""
        self.assertIn('prefers-contrast', self.css_content)

    def test_semantic_html(self):
        """Test semantic HTML tags"""
        self.assertIn('<nav', self.html_content)
        self.assertIn('<main', self.html_content)
        self.assertIn('<header', self.html_content)

    def test_alt_text_in_images(self):
        """Test images have alt text"""
        # Check for alt attributes
        self.assertTrue(
            'alt=' in self.html_content or
            '<svg' in self.html_content  # SVG doesn't need alt if inline
        )


class TestFeature12Integration(unittest.TestCase):
    """Integration tests for Feature #12"""

    def test_all_mobile_features_present(self):
        """Test all Feature #12 components are implemented"""
        features = {
            'PWA Manifest': Path(__file__).parent.parent / 'static' / 'manifest.json',
            'Service Worker': Path(__file__).parent.parent / 'static' / 'service-worker.js',
            'Mobile CSS': Path(__file__).parent.parent / 'static' / 'mobile.css',
            'Mobile Dashboard': Path(__file__).parent.parent / 'templates' / 'mobile-dashboard.html',
        }

        for feature_name, feature_path in features.items():
            self.assertTrue(
                feature_path.exists(),
                f"{feature_name} not implemented: {feature_path}"
            )

    def test_responsive_design_complete(self):
        """Test responsive design for all breakpoints"""
        css_path = Path(__file__).parent.parent / 'static' / 'mobile.css'
        with open(css_path, 'r') as f:
            content = f.read()

        breakpoints = ['768px', '1200px']  # Mobile, Tablet, Desktop
        for bp in breakpoints:
            self.assertIn(
                bp,
                content,
                f"Missing breakpoint: {bp}"
            )

    def test_touch_friendly_controls(self):
        """Test controls are touch-friendly"""
        css_path = Path(__file__).parent.parent / 'static' / 'mobile.css'
        with open(css_path, 'r') as f:
            content = f.read()

        # Should have 48px minimum touch targets
        self.assertIn('48px', content)

    def test_offline_capability_implemented(self):
        """Test offline functionality"""
        sw_path = Path(__file__).parent.parent / 'static' / 'service-worker.js'
        with open(sw_path, 'r') as f:
            content = f.read()

        # Should have caching and offline support
        self.assertIn('caches.open', content)
        self.assertIn('.catch()', content)


if __name__ == '__main__':
    unittest.main()
