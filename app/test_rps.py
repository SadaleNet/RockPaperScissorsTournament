import unittest
import unittest.mock
import datetime
import sqlite3
import rps
import captcha
import flask
import os
import shutil
import time
import PIL
import PIL.Image
import tempfile
import xml.etree.ElementTree as ET
import functools

class FlaskTemplateMocker:
    def __enter__(self):
        self.original_render_template = flask.render_template
        flask.render_template = unittest.mock.Mock(wraps=self.original_render_template)
        return flask.render_template
    def __exit__(self, exc_type, exc_val, exc_tb):
        flask.render_template = self.original_render_template

flaskTemplateMocker = FlaskTemplateMocker()

def lookForCallKey(call_args, target_key):
    for value in call_args:
        if type(value) != dict:
            continue
        return value[target_key ]
    return None

class TestRps(unittest.TestCase):
    """
    Test cases for testing the functionality of rps module
    """
    def check_template_generated_by_get_request(self, client, path, expectedTemplate):
        response = client.get(path)
        templateCalled, = flask.render_template.call_args[0]
        self.assertEqual(templateCalled, expectedTemplate)
    def play(self, client, nick, country, played, captchaText=None):
        response = client.get('/join')
        captcha_id = lookForCallKey(flask.render_template.call_args, 'captcha_id')
        for i in response.get_data().decode('utf-8').split('\n'):
            if 'csrf_token' in i:
                root = ET.fromstring(i)
                break
        csrf_token = root.attrib['value']

        return client.post('/action',
            data={
            'csrf_token': csrf_token,
            'nick': nick,
            'country': country,
            'played': played,
            'captcha': captcha.fetch_captcha_answer(captcha_id) if captchaText == None else captchaText,
            'captcha_id': str(captcha_id)
            }
        )
    def setUp(self):
        if os.path.exists(rps.app.config['DATABASE_NAME']):
            os.remove(rps.app.config['DATABASE_NAME'])
        rps.setup_db()
    def test_setup_db(self):
        #Delete the database file and check
        os.remove(rps.app.config['DATABASE_NAME'])
        self.assertFalse(os.path.exists(rps.app.config['DATABASE_NAME']))
        #Create the database file and check
        rps.setup_db()
        self.assertTrue(os.path.exists(rps.app.config['DATABASE_NAME']))
        #Check if the columes exists. If not, it'll raise an exception and this test case will fail
        conn = sqlite3.connect(rps.app.config['DATABASE_NAME'])
        conn.execute("SELECT pk, nick, country, played, cheat, timestamp, score used FROM game")
        conn.close()
    def test_page_routing_before_event(self):
        """
            Test if template routing is working correctly before the event had started
        """
        rps.app.config['START_TIME'] = (datetime.datetime.now()+datetime.timedelta(days=1))
        rps.app.config['END_TIME'] = (datetime.datetime.now()+datetime.timedelta(days=2))
        with rps.app.test_client() as client:
            with flaskTemplateMocker:
                self.check_template_generated_by_get_request(client, '/', 'index.html')
                self.check_template_generated_by_get_request(client, '/about', 'about.html')
                self.check_template_generated_by_get_request(client, '/join', 'join_not_started.html')
                self.check_template_generated_by_get_request(client, '/result', 'result_not_ended.html')
                #Ensure that POSTing to /action during the event won't return HTTP 200
                response = client.post('/action')
                self.assertNotEqual(response.status_code, 200)
                #Ensure that POSTing to /done before the event won't return HTTP 200
                response = client.get('/done')
                self.assertNotEqual(response.status_code, 200)
    def test_page_routing_during_event(self):
        """
            Test if template routing is working correctly during the event
        """
        rps.app.config['START_TIME'] = (datetime.datetime.now()+datetime.timedelta(days=-1))
        rps.app.config['END_TIME'] = (datetime.datetime.now()+datetime.timedelta(days=1))
        with rps.app.test_client() as client:
            with flaskTemplateMocker:
                self.check_template_generated_by_get_request(client, '/', 'index.html')
                self.check_template_generated_by_get_request(client, '/about', 'about.html')
                self.check_template_generated_by_get_request(client, '/join', 'join.html')
                self.check_template_generated_by_get_request(client, '/result', 'result_not_ended.html')
                #We're saving /action for another test case.
                #response = client.post('/action')
                #self.assertNotEqual(response.status_code, 200)
                #Ensure that POSTing to /done during the event will return HTTP 200
                response = client.get('/done')
                self.assertEqual(response.status_code, 200)
    def test_page_routing_after_event(self):
        """
            Test if template routing is working correctly after the event had ended
        """
        rps.app.config['START_TIME'] = (datetime.datetime.now()+datetime.timedelta(days=-2))
        rps.app.config['END_TIME'] = (datetime.datetime.now()+datetime.timedelta(days=-1))
        with rps.app.test_client() as client:
            with flaskTemplateMocker:
                self.check_template_generated_by_get_request(client, '/', 'index.html')
                self.check_template_generated_by_get_request(client, '/about', 'about.html')
                self.check_template_generated_by_get_request(client, '/join', 'join_ended.html')
                self.check_template_generated_by_get_request(client, '/result', 'result.html')
                #Ensure that POSTing to /action after the event won't return HTTP 200
                response = client.post('/action')
                self.assertNotEqual(response.status_code, 200)
                #Ensure that POSTing to /done after the event won't return HTTP 200
                response = client.get('/done')
                self.assertNotEqual(response.status_code, 200)
    def test_page_simulate_event_without_players(self):
        """
            Simulate an event without any player and check the result
        """
        EVENT_DURATION = 5
        rps.app.config['START_TIME'] = (datetime.datetime.now())
        rps.app.config['END_TIME'] = (datetime.datetime.now()+datetime.timedelta(seconds=EVENT_DURATION))
        startTime = time.time()
        with rps.app.test_client() as client:
            with flaskTemplateMocker as functionCalled:
                #We've got no players. So we just wait.
                #Wait for the completion of the event
                time.sleep(EVENT_DURATION-(time.time()-startTime))
                client.get('/result')
                players = lookForCallKey(functionCalled.call_args, 'players')
                self.assertEqual(players, [])
    def test_page_play_simple(self):
        """
            Ensure that self.play() is working correctly
        """
        rps.app.config['START_TIME'] = (datetime.datetime.now())
        rps.app.config['END_TIME'] = (datetime.datetime.now()+datetime.timedelta(days=1))
        with rps.app.test_client() as client:
            with flaskTemplateMocker as functionCalled:
                response = self.play(client, 'test', 'us', 'pspprprpsrrrpsprppspsrsspprsssprrrpsrprrsspprrprrs')
                self.assertTrue(response.headers.get('Location').endswith('done'))
    def test_page_play_duplicated_name(self):
        """
            Ensure that the website does not allow duplicate of player name
        """
        rps.app.config['START_TIME'] = (datetime.datetime.now())
        rps.app.config['END_TIME'] = (datetime.datetime.now()+datetime.timedelta(days=1))
        with rps.app.test_client() as client:
            with flaskTemplateMocker as functionCalled:
                self.play(client, 'test', 'us', 'pspprprpsrrrpsprppspsrsspprsssprrrpsrprrsspprrprrs')
                self.play(client, 'test', 'cn', 'ssssrrrppsrrspsrpprssssprprsrprpsprrrpprsrppssrrpp')
                self.assertEqual(functionCalled.call_args[0][0], 'join.html')
    def test_page_play_wrong_captcha(self):
        """
            Ensure that the website requires a correct captcha
        """
        rps.app.config['START_TIME'] = (datetime.datetime.now())
        rps.app.config['END_TIME'] = (datetime.datetime.now()+datetime.timedelta(days=1))
        with rps.app.test_client() as client:
            with flaskTemplateMocker as functionCalled:
                self.play(client, 'test', 'us', 'pspprprpsrrrpsprppspsrsspprsssprrrpsrprrsspprrprrs', '12345678')
                self.assertEqual(functionCalled.call_args[0][0], 'join.html')
    def test_page_play_invalid_country(self):
        """
            Ensure that the website requires a valid country code
        """
        rps.app.config['START_TIME'] = (datetime.datetime.now())
        rps.app.config['END_TIME'] = (datetime.datetime.now()+datetime.timedelta(days=1))
        with rps.app.test_client() as client:
            with flaskTemplateMocker as functionCalled:
                self.play(client, 'test', 'xx', 'pspprprpsrrrpsprppspsrsspprsssprrrpsrprrsspprrprrs')
                self.assertEqual(functionCalled.call_args[0][0], 'join.html')
    def test_page_play_invalid_hands(self):
        """
            Ensure that the website disallows playing of invalid hands
        """
        rps.app.config['START_TIME'] = (datetime.datetime.now())
        rps.app.config['END_TIME'] = (datetime.datetime.now()+datetime.timedelta(days=1))
        with rps.app.test_client() as client:
            with flaskTemplateMocker as functionCalled:
                #Too many consequtive hands
                self.play(client, 'test', 'us', 'pppppprpsrrrpsprppspsrsspprsssprrrpsrprrsspprrprrs')
                self.assertEqual(functionCalled.call_args[0][0], 'join.html')
                self.play(client, 'test', 'us', 'sssssrrpsrrrpsprppspsrsspprsssprrrpsrprrsspprsssss')
                self.assertEqual(functionCalled.call_args[0][0], 'join.html')
                self.play(client, 'test', 'us', 'pspprprpsrrrrrrsppspsrsspprsssprrrpsrprrsspprrprrs')
                self.assertEqual(functionCalled.call_args[0][0], 'join.html')
                #Too many hands played
                self.play(client, 'test', 'us', 'pspprprpsrrrpsprppspsrsspprsssprrrpsrprrsspprrprrsr')
                #Not enough hands played
                self.play(client, 'test', 'us', 'pspprprpsrrrpsprppspsrsspprsssprrrpsrprrsspprrprr')
                self.assertEqual(functionCalled.call_args[0][0], 'join.html')
    def test_page_simulate_event_with_players(self):
        return
        """
            Simulate an event with a few players and check the result
        """
        EVENT_DURATION = 5
        rps.app.config['START_TIME'] = (datetime.datetime.now())
        rps.app.config['END_TIME'] = (datetime.datetime.now()+datetime.timedelta(seconds=EVENT_DURATION))
        startTime = time.time()
        time.sleep(EVENT_DURATION-(time.time()-startTime))
        with rps.app.test_client() as client:
            with flaskTemplateMocker as functionCalled:
                #Simulate playing the game
                
                #Wait for the completion of the event
                time.sleep(EVENT_DURATION-(time.time()-startTime)+1)
                client.get('/result')
                players = lookForCallKey(functionCalled.call_args, 'players')
                self.assertEqual(players,
                [
                {'i': 1, 'country': 'us', 'nick': 'test', 'score': 7, 'cheat': 0, 'played': 'pspprprpsrrrpsprppspsrsspprsssprrrpsrprrsspprrprrs'},
                {'i': 2, 'country': 'uy', 'nick': 'bar', 'score': 0, 'cheat': 0, 'played': 'ssssrrrppsrrspsrpprssssprprsrprpsprrrpprsrppssrrpp'},
                {'i': 3, 'country': 'hk', 'nick': 'foo', 'score': -3, 'cheat': 0, 'played': 'rssrsrrrrsppsppsprsrpppppsspprrsrpsrspppsprsrprpss'},
                {'i': 4, 'country': 'se', 'nick': 'baz', 'score': -4, 'cheat': 0, 'played': 'prsrpsrrrsrpprspppprppspsprprssprspppppspssrpsrrsp'}
                ]
                )
                
                #TODO: also view the cert

if __name__ == '__main__':
    unittest.main()
