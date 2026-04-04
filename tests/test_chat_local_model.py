import tempfile
import unittest
from pathlib import Path

from chat_local_model import TurboQuantNgramModel


class TurboModelTests(unittest.TestCase):
    def test_train_and_generate(self):
        model = TurboQuantNgramModel(order=3, turboquant=True, seed=1)
        model.train_text("bonjour le monde bonjour le chat")
        out = model.generate("bonjour le", max_new_tokens=5, temperature=0.7)
        self.assertTrue(len(out) > 0)

    def test_save_and_load_gzip(self):
        model = TurboQuantNgramModel(order=3, turboquant=True, seed=1)
        model.train_text("alpha beta gamma alpha beta delta")

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "model.json.gz"
            model.save(path)
            loaded = TurboQuantNgramModel.load(path)
            self.assertEqual(model.order, loaded.order)
            self.assertTrue(len(loaded.counts) > 0)


if __name__ == "__main__":
    unittest.main()
