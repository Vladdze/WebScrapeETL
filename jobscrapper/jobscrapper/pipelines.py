
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

from itemadapter import ItemAdapter
import mysql.connector

## CONSOLIDATES DATA INTO ONE TABLE
class JobscrapperPipeline:
    def __init__(self):
        self.conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='******',
            database='Scrapped_Jobs'
        )
        self.cur = self.conn.cursor()

        # Create Jobs table if it doesn't exist
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS Jobs(
                id INT AUTO_INCREMENT PRIMARY KEY,
                position TEXT,
                location TEXT,
                company_name VARCHAR(255),
                details TEXT
            )
        """)

    def process_item(self, item, spider):
        if spider.name == 'linkedin_spider':
            details = item.get("detail_url", "")
            company_name = item.get("company_name", "")
        elif spider.name == 'indeed_spider':
            details = item.get("jobDescription", "")
            company_name = item.get("company", "")

        position = item.get("title") or item.get("jobTitle", "")
        location = item.get("location", "")
        
        # Insert data into the Jobs table
        self.cur.execute("""INSERT INTO Jobs (position, location, company_name, details)
                            VALUES (%s, %s, %s, %s)""", (
            position,
            location,
            company_name,
            details
        ))

        # Execute insert of data into database
        self.conn.commit()

    def close_spider(self, spider):
        # Close cursor & connection to the database
        self.cur.close()
        self.conn.close()
