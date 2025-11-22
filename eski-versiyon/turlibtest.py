# -*- coding: utf-8 -*-
import unittest
import turlib
import time

class TurlibTest(unittest.TestCase):
    def test_get_base_url(self):
        url ="http://www.gamet.com.tr/gelecege-donus/"
        base_url = "http://www.gamet.com.tr"
        self.assertEqual(base_url, turlib.get_base_url(url))
        self.assertEqual("gelecege-donus",turlib.get_path1(url))
        url2="http://www.google.com/testing/retesting/x/"
        self.assertEqual("http://www.google.com",turlib.get_base_url(url2))
        self.assertEqual("testing",turlib.get_path1(url2))
        self.assertEqual("1:00:00:00",turlib.gecen_sure(int(time.time())-86400))
        self.assertEqual("0:01:00:00",turlib.gecen_sure(int(time.time())-3600))
        self.assertEqual("0:00:01:00",turlib.gecen_sure(int(time.time())-60))
        self.assertEqual("0:00:00:00",turlib.gecen_sure(int(time.time())-0))
        self.assertFalse(turlib.hepsi_turkce("Tequila"))
        self.assertFalse(turlib.hepsi_turkce("Washington Post"))
        self.assertTrue(turlib.hepsi_turkce("Bu Türkçe bir cümledir."))

if __name__ == "__main__":
    unittest.main()

