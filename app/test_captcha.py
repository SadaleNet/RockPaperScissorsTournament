import unittest
import sqlite3
import captcha
import os
import shutil
import PIL
import PIL.Image
import tempfile

class TestCaptcha(unittest.TestCase):
    """
    Test cases for testing the functionality of captcha module
    """
    def setUp(self):
        #Start test cases with a clean environment
        if os.path.exists(captcha.DATABASE_NAME):
            os.remove(captcha.DATABASE_NAME)
        if os.path.exists(captcha.CAPTCHA_DIR):
            shutil.rmtree(captcha.CAPTCHA_DIR)
        captcha.setup_db()
        
        self.captcha_id_list = []
        for i in range(16):
            self.captcha_id_list.append(captcha.generate_new_captcha())
    def test_initialization(self):
        """
            Test if captcha.setup_db() is working correctly
        """
        #Simulate an uninitialized environment
        os.remove(captcha.DATABASE_NAME)
        shutil.rmtree(captcha.CAPTCHA_DIR)
        self.assertFalse(os.path.exists(captcha.DATABASE_NAME))
        self.assertFalse(os.path.exists(captcha.CAPTCHA_DIR))

        #Ensure that captcha.setup_db() is creating the files
        captcha.setup_db()
        self.assertTrue(os.path.exists(captcha.DATABASE_NAME))
        self.assertTrue(os.path.exists(captcha.CAPTCHA_DIR))

        #Check if the columes exists. If not, it'll raise an exception and this test case will fail
        conn = sqlite3.connect(captcha.DATABASE_NAME)
        conn.execute("SELECT pk, answer, used FROM captcha")
        conn.close()
    def test_captcha_image_generation(self):
        """
        Ensure that the captcha system is generating the correct image
        """
        for i in self.captcha_id_list:
            self.assertTrue(os.path.exists(captcha.get_captcha_path(i)))
            with PIL.Image.open(captcha.get_captcha_path(i)) as im:
                im.load() #Will raise an exception if it fails

        #Ensure that image error detection code is working by using an invalid image file
        #In this case, we try loading the database as an image
        with tempfile.NamedTemporaryFile("w") as f:
            fileName = f.name
            f.write("dummy file content that isn't an image")
        with self.assertRaises(Exception):
            with PIL.Image.open(fileName) as im:
                im.load() #Will raise an exception if it fails
    def test_captcha_fetch_answer(self):
        """
        Ensure that the answer of existing captcha is fetchable, and the non-existing one isn't
        """
        #Ensure answer is fetchable and is in a correct format
        for i in self.captcha_id_list:
            self.assertIsNotNone(captcha.fetch_captcha_answer(i))
            self.assertTrue(type(captcha.fetch_captcha_answer(i))==str)
        #Ensure answer is not fetchable after the deletion of the captcha
        for i in self.captcha_id_list:
            captcha.invalidate(i)
            self.assertIsNone(captcha.fetch_captcha_answer(i))
    def test_captcha_delete_image_file(self):
        """
        Ensure that the captcha system will delete the invalidated images
        """
        for i in self.captcha_id_list:
            captcha.invalidate(i)
            self.assertFalse(os.path.exists(captcha.get_captcha_path(i)))
    def test_captcha_cannot_invalidate_deleted_captcha(self):
        """
        Ensure that one cannot invalidate a deleted captcha
        """
        for i in self.captcha_id_list:
            captcha.invalidate(i)
            with self.assertRaises(Exception):
                captcha.invalidate(i)
        

if __name__ == '__main__':
    captcha.setup_db()
    unittest.main()
