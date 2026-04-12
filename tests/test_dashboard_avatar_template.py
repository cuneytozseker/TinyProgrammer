import re
import unittest

from web.app import create_app


class DashboardAvatarTemplateTest(unittest.TestCase):
    def setUp(self):
        self.client = create_app().test_client()

    def test_dashboard_embeds_avatar_payload(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

        html = response.get_data(as_text=True)

        self.assertIn("const AVATAR_EXPRESSIONS =", html)
        self.assertIn("const BLINK_PIXELS =", html)
        self.assertRegex(html, r'"hopeful"\s*:\s*\[')
        self.assertRegex(html, r'"determined"\s*:\s*\[')
        self.assertNotRegex(html, r'\bhopeful\s*:\s*new Set\s*\(')


if __name__ == "__main__":
    unittest.main()
