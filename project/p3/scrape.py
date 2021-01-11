# project: p3
# submitter: zdai38
# partner: none

from collections import deque
import time
import pandas as pd

class Scraper:
    # required
    def __init__(self, driver, home_url):
        self.driver = driver
        self.home_url = home_url

    # you can do these three with your group
    def easter_egg(self):
        self.driver.get(self.home_url)
        txt = str()
        content = self.driver.find_elements_by_tag_name("span")
        for word in content:
            txt += word.text
        return txt

    def dfs_pass(self):
        self.password = str()
        self.btn = "DFS"
        self.children = []
        
        self.driver.get(self.home_url)
        link = self.driver.find_element_by_tag_name("a")
        url = link.get_attribute("href")
        self.added = {url,}
        
        entrance_btn = self.driver.find_element_by_id("maze-entrance")
        entrance_btn.click()
        
        self.find(url)
        
        return self.password
        
    def find(self,url): # DFS: depth first search
        # click DFS button and get letter
        self.driver.get(url)
        btn = self.driver.find_element_by_id(self.btn)
        btn.click()
        letter = self.driver.find_element_by_id(self.btn)
        self.password += letter.text
        
        # get hyperlinks
        links = self.driver.find_elements_by_tag_name("a")
        hyperlinks = [link.get_attribute("href") for link in links]
        
        for hyperlink in hyperlinks:
            if not hyperlink in self.added:
                self.added.add(hyperlink)
                self.find(hyperlink)
    
    def visit_page(self, url):
        self.driver.get(url)
        links = self.driver.find_elements_by_tag_name("a")
        return [link.get_attribute("href") for link in links]                

    def visit_next(self):
        # 1. do the first thing on TODO list
        url = self.todo.popleft()
        children_urls = self.visit_page(url)

        # 2. add new urls to the end of TODO list
        for child_url in children_urls:
            if not child_url in self.added:
                self.todo.append(child_url)
                self.added.add(child_url)
                
        # click the BFS button, get letter
        btn = self.driver.find_element_by_id(self.btn)
        btn.click()
        letter = self.driver.find_element_by_id(self.btn)
        
        return letter.text

    def bfs_pass(self):
        self.password = str()
        self.btn = "BFS"
        
        self.driver.get(self.home_url)
        link = self.driver.find_element_by_tag_name("a")
        url = link.get_attribute("href")
        
        self.todo = deque([url])
        self.added = {url,}
        
        entrance_btn = self.driver.find_element_by_id("maze-entrance")
        entrance_btn.click()    
        
        while len(self.todo) > 0:
            self.password += self.visit_next()
        return self.password
        
    # write the code for this one individually
    def protected_df(self, password):
        self.driver.get(self.home_url)
        pwd = self.driver.find_element_by_id("password-input")
        pwd.clear()
        pwd.send_keys(password)
        btn = self.driver.find_element_by_id("attempt-button")
        btn.click()
                         
        x = -1
        while len(self.driver.find_elements_by_tag_name("tr")) > x:
            x = len(self.driver.find_elements_by_tag_name("tr"))
            time.sleep(1)
            try:
                btn = self.driver.find_element_by_id("more-locations-button")
                btn.click()
            except:
                continue
                
        return pd.read_html(self.driver.page_source)[0]