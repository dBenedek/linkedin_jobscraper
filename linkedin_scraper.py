#!/usr/bin/env python3

# Benedek Dankó
# Created on: 2022-02-06

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import time
import logging
import pickle
import os
import re
import pandas as pd
import numpy as np
import getpass


def safe_send_keys(driver, input_selector: str, input_text: str, selector_type = By.ID):
    driver.find_element(selector_type, input_selector).click()
    action = ActionChains(driver)
    action.send_keys(input_text)
    action.perform()

class LinkedInBot:
    def __init__(self, delay=5):
        if not os.path.exists("linkedin_data"):
            os.makedirs("linkedin_data")
        log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        logging.basicConfig(level=logging.INFO, format=log_fmt)
        self.delay=delay
        logging.info("Starting driver")
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--headless')
        self.driver = webdriver.Chrome(options=chrome_options)

    def login(self, email, password):
        """Go to linkedin and login"""
        # Go to linkedin:
        logging.info("Logging in")
        self.driver.maximize_window()
        self.driver.get('https://www.linkedin.com/login')
        time.sleep(self.delay)
        # Fill username:
        self.driver.find_element(By.ID, 'username').click()
        action = ActionChains(self.driver)
        action.send_keys(email)
        action.perform()
        # Fill pasword:
        self.driver.find_element(By.ID, 'password').click()
        action = ActionChains(self.driver)
        action.send_keys(password)
        action.perform()
        # Press enter:
        self.driver.find_element(By.ID, 'password').send_keys(Keys.RETURN)
        time.sleep(self.delay)

    def save_cookie(self, path):
        with open(path, 'wb') as filehandler:
            pickle.dump(self.driver.get_cookies(), filehandler)

    def load_cookie(self, path):
        with open(path, 'rb') as cookiesfile:
            cookies = pickle.load(cookiesfile)
            for cookie in cookies:
                self.driver.add_cookie(cookie)

    def search_linkedin(self, keywords, location):
        """Enter keywords into search bar
        """
        logging.info("Searching jobs page")
        self.driver.get("https://www.linkedin.com/jobs/")
        # search based on keywords and location and hit enter
        self.wait_for_element_ready(By.CLASS_NAME, 'jobs-search-box__text-input')
        time.sleep(self.delay)
        search_bars = self.driver.find_elements(By.CLASS_NAME, 'jobs-search-box__text-input')
        # Keywords and locations searchbars:
        search_bar_keywords = search_bars[0]
        search_bar_location = search_bars[3]
        # Fill them:
        search_bar_keywords.send_keys(keywords)
        search_bar_location.send_keys(location)
        time.sleep(self.delay)
        # Perform search:
        search_bar_location.send_keys(Keys.RETURN)
        logging.info("Keyword search successful")
        time.sleep(self.delay)
    
    def wait(self, t_delay=None):
        """Just easier to build this in here.
        Parameters
        ----------
        t_delay [optional] : int
            seconds to wait.
        """
        delay = self.delay if t_delay == None else t_delay
        time.sleep(delay)

    def scroll_to(self, job_list_item, job_title):
        """Just a function that will scroll to the list item in the column 
        """
        self.driver.execute_script("arguments[0].scrollIntoView(true);", job_list_item)
        job_title.click()
        time.sleep(self.delay)
    
    def get_position_data(self, job):
        """Gets the position data for a posting.

        Parameters
        ----------
        job : Selenium webelement

        Returns
        -------
        list of strings : [position, company, location, job_type, 
                           posted_time, n_applicants, job_insight, details]
        """
        summary_info = job.text.split('\n')
        try:
            [position, company, location, job_type] = summary_info[:4]
        except ValueError:
            return [np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan]
        except NoSuchElementException:
            n_applicants = 0
        try:
            n_applicants = self.driver.find_element(By.CLASS_NAME, "jobs-unified-top-card__applicant-count").text
            if summary_info[-1] != 'Easy Apply':
                posted_time = summary_info[-1]
            else:
                posted_time = summary_info[-2]
            pass
        except NoSuchElementException:
            n_applicants = self.driver.find_elements(By.CLASS_NAME, "jobs-unified-top-card__bullet")[1].text
            posted_time = summary_info[-2]
            pass
        else:
            posted_time = self.driver.find_element(By.CLASS_NAME, "jobs-unified-top-card__posted-date").text
            
        details = self.driver.find_element(By.ID, "job-details").text
        job_insight = self.driver.find_element(By.CLASS_NAME, "jobs-unified-top-card__job-insight").text.replace(' · ', ', ')
        if n_applicants in ['', ' ']:
            n_applicants = 0
        else:
            n_applicants = re.sub('\sapplicant.*', '', n_applicants)
        if job_type in ['Hide job', 'Actively recruiting']:
                job_type = 'NA'
        return [position, company, location, job_type, 
                posted_time, n_applicants, job_insight, details]

    def wait_for_element_ready(self, by, text):
        try:
            WebDriverWait(self.driver, self.delay).until(EC.presence_of_element_located((by, text)))
        except TimeoutException:
            logging.debug("wait_for_element_ready TimeoutException")
            pass

    def close_session(self):
        """This function closes the actual session"""
        logging.info("Closing session")
        self.driver.close()

    def run(self, email, password, keywords, location):
        if os.path.exists("linkedin_data/cookies.txt"):
            self.driver.get("https://www.linkedin.com/")
            self.load_cookie("linkedin_data/cookies.txt")
            self.driver.get("https://www.linkedin.com/")
        else:
            self.login(email=email, password=password)
            self.save_cookie("linkedin_data/cookies.txt")
        logging.info("Begin linkedin keyword search")
        self.search_linkedin(keywords, location)
        self.wait()
        # Stores jobs data:
        data = []
        # scrape pages, only do first 8 pages since after that the data isn't 
        # well suited for me anyways:  
        for page in range(2, 8):
            # get the jobs list items to scroll through:
            jobs = self.driver.find_elements(By.CLASS_NAME, "occludable-update")
            for idx, job in enumerate(jobs):
                # get job titles:
                jobs_title = self.driver.find_elements(By.CLASS_NAME, "job-card-list__title") 
                if idx < len(jobs_title):
                    self.scroll_to(job, jobs_title[idx])
                    # Get the data:
                    [position, company, location, job_type, 
                    posted_time, n_applicants, job_insight, details] = self.get_position_data(job)
                    # Store data:
                    if not pd.isnull(pd.unique([position, company, location, job_type, 
                                                posted_time, n_applicants, job_insight])).all():
                        data.append([position, company, location, job_type, 
                                     posted_time, n_applicants, job_insight])
                        # Print to command line:
                        print('==========================================')
                        print('\nPosition:', position, '\nCompany:', company, '\nLocation:', location, 
                              '\nJob type:', job_type, '\nPosted:', posted_time, 
                              '\nNumber of applicants:', n_applicants, '\nJob insight:', job_insight)
                        print('\n==========================================')
                else:
                    break
            # go to next page:
            try:
                bot.driver.find_element(By.XPATH, f"//button[@aria-label='Page {page}']").click()
                bot.wait()
            # End of the results:
            except NoSuchElementException:
                break
        # Create data frame:
        data_df = pd.DataFrame(data, columns=['Position', 'Company', 'Location', 'Job_type',
                                              'Posted', 'Number_of_applicants', 'Job_insight']).sort_values('Company')
        current_time = time.strftime("%Y_%m_%d_%H_%M_%S", time.gmtime())
        # Export data:
        data_df.to_excel('linkedin_data/linkedin_positions_' + current_time + '.xlsx',
                         index=False)
        logging.info("Data exported to Excel.")
        logging.info("Done scraping.")
        logging.info("Closing DB connection.")
        bot.close_session()


if __name__ == "__main__":
    print('\nLogging in to LinkedIn.\n')
    email = str(input('Your e-mail address: '))
    password = getpass.getpass()
    keyword = str(input('Keyword(s) - space separated: '))
    location = str(input('Location: '))
    bot = LinkedInBot()
    bot.run(email, password, keyword, location)
