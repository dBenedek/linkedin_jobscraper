# LinkedIn JobScraper

## The main idea & code backbone is from Matan Freemdan's [medium article](https://medium.com/nerd-for-tech/linked-in-web-scraper-using-selenium-15189959b3ba).

***

This Python script performs automatic job search on LinkedIn, based on the specified keyword(s) and location. After the search performed, it exports the results into an Excel table.

### Instructions

First, you need Chrome driver (preferably version 98) which you can download [here](https://chromedriver.chromium.org/downloads). The driver should be added to your PATH.
To install the required Python packages, you need to run the following command:

```bash
pip install -r requirements.txt

```

After installing the packages, you can run the LinkedIn bot:

```bash
./linkedin_scraper.py
```

Once the job scraping has been finished, a directory will be created: `linkedin_data`.
This folder contains an Excel file together with the jobs data with the following columns: `Position`, `Location`, `Job_type`, `Posted`, `Number_of_applicant`, and `Job_insight`.
