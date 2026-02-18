import unittest

from universal_morse_decoder import decode, decode_continuous, decode_separated, encode


class UniversalMorseDecoderTests(unittest.TestCase):
    def test_encode(self):
        self.assertEqual(encode("SOS"), "... --- ...")

    def test_separated_decode(self):
        result = decode_separated(".... . .-.. .-.. --- / .-- --- .-. .-.. -..")
        self.assertEqual(result.text, "HELLO WORLD")

    def test_fuzzy_decode(self):
        result = decode("..- ..--", mode="separated", fuzzy=True)
        self.assertEqual(result.text[0], "U")

    def test_continuous_decode(self):
        # ".... . .-.. .-.. ---" بدون فاصله
        result = decode_continuous("......-...-..---")
        self.assertTrue(result.text == "HELLO" or "HELLO" in result.alternatives)
        self.assertGreater(result.confidence, 0)


if __name__ == "__main__":
    unittest.main()
