"""
Loads the dofusdb.fr treasure hunt page to exploit its data.
Tad overcomplicated as they implement captcha verifications.
"""

import json
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from api import Direction, first

SITE_URL = 'https://dofusdb.fr/fr/tools/treasure-hunt'
DRIVER_URL = './webdriver/chromedriver'
RESPONSE_METHOD = 'Network.responseReceived'
RESPONSE_URL = 'https://api.dofusdb.fr/treasure-hunt?'
I_CLASS = 'q-select__dropdown-icon'
X_PATH = '//input[@placeholder=\'X\']'
Y_PATH = '//input[@placeholder=\'Y\']'
D_CLASS = {
    Direction.UP: 'fa-arrow-up',
    Direction.DOWN: 'fa-arrow-down',
    Direction.LEFT: 'fa-arrow-left',
    Direction.RIGHT: 'fa-arrow-right'
}        

class DofusDB:
    """
    Class to load and interact with dofusdb.fr.
    """

    def __init__(self):
        capabilities = DesiredCapabilities.CHROME
        capabilities['goog:loggingPrefs'] = {'performance': 'ALL'}

        service = Service(executable_path=DRIVER_URL)

        self.driver = Chrome(service=service, desired_capabilities=capabilities)
        self.wait = WebDriverWait(self.driver, 2)
        self.driver.get(SITE_URL)

    
    @staticmethod
    def filter_logs(logs):
        """
        Removes logs that we are not interested to.
        """
        for l in logs:
            log = json.loads(l['message'])['message']
            if (
                RESPONSE_METHOD in log['method'] and
                'response' in log['params'] and
                'requestId' in log['params'] and
                RESPONSE_URL in log['params']['response']['url']
            ):
                yield log


    @staticmethod
    def clear_and_set_field(element, value):
        """
        Clears the field element.
        """
        element.send_keys(Keys.CONTROL + 'a')
        element.send_keys(Keys.BACK_SPACE)
        element.send_keys(value)


    @staticmethod
    def format_hints(hints):
        """
        Formats hints to a readable format.
        """
        valid_hints = []
        hints = json.loads(hints)
        
        for h in hints['data']:
            for o in h['pois']:
                valid_hints.append({
                    'x': h['posX'],
                    'y': h['posY'],
                    'n': o['name']['fr']
                })

        return valid_hints


    def get_hints(self, x, y, d):
        """
        Get the elements in a dirtection from a position.
        """

        # Prepare the page
        DofusDB.clear_and_set_field(self.driver.find_element(By.XPATH, X_PATH), x)
        DofusDB.clear_and_set_field(self.driver.find_element(By.XPATH, Y_PATH), y)
        self.driver.find_element(By.CLASS_NAME, D_CLASS[d]).click()

        # Wait for the requests answer (await the elements update)
        self.wait.until(EC.invisibility_of_element_located((By.CLASS_NAME, I_CLASS)))
        self.wait.until(EC.visibility_of_element_located((By.CLASS_NAME, I_CLASS)))

        # Get the network logs to find the results
        logs = self.driver.get_log('performance')
        logs = DofusDB.filter_logs(logs)
        logs = sorted(logs, key=lambda log: log['params']['timestamp'], reverse=True)

        # Return the first valid log
        for l in logs:
            try:
                return DofusDB.format_hints(
                    self.driver.execute_cdp_cmd(
                        'Network.getResponseBody', 
                        {'requestId': l['params']['requestId']})['body'])
            except:
                pass
