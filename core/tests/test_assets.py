from pathlib import Path

from django.conf import settings

from .base import BaseCase


class CompiledStyles(BaseCase):
    def test_no_template_loads_the_tailwind_cdn(self):
        offenders = [
            str(p) for p in Path(settings.BASE_DIR, "templates").rglob("*.html")
            if "cdn.tailwindcss.com" in p.read_text()
        ]
        self.assertEqual(offenders, [])

    def test_compiled_stylesheet_exists_and_has_the_palette(self):
        css = Path(settings.BASE_DIR, "static", "css", "tailwind.css")
        self.assertTrue(css.exists(), "run: npm run build")
        self.assertIn("bg-garden-700", css.read_text())

    def test_pages_link_the_compiled_stylesheet(self):
        self.assertContains(self.client.get("/promo/"), "css/tailwind.css")
