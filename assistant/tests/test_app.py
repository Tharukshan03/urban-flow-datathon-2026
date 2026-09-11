import unittest

from streamlit.testing.v1 import AppTest


class AssistantAppTests(unittest.TestCase):
    def test_app_renders(self):
        app = AppTest.from_file('../app.py').run(timeout=30)
        self.assertEqual([e.message for e in app.exception], [])
        self.assertTrue(app.get('text_input'))
        self.assertTrue(app.get('button'))


if __name__ == '__main__':
    unittest.main()
