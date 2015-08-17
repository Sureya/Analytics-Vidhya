import urllib2, sys
from bs4 import BeautifulSoup
import unicodedata
import sqlite3
import os
import pdfkit

def getSoup(url):
    header = {'User-Agent': 'Mozilla/5.0'}
    request = urllib2.Request(url,headers=header)
    page = urllib2.urlopen(request)
    soup = BeautifulSoup(page,from_encoding="UTF-8")
    return soup


def MostRecentBlog():
    soup = getSoup("http://www.analyticsvidhya.com/blog/page/1/")
    
    BlogList = soup.find("div",{"class":"cur-page-item row block-streams el-block-3"})
    blogs = BlogList.findAll("div")
    finalBlog = [x for x in blogs if "up-up-child" in x.attrs['class'] ]
    
    MostRecentBlog = finalBlog[0]
    
    #Scraping the Blog related details from the DIV content
    _name = MostRecentBlog.find("h3",{"itemprop":"name"})
    
    blogLink = _name.find("a").attrs["href"]
    blogTitle = unicodedata.normalize('NFKD', _name.getText()).encode('ascii','ignore').replace("\n","").replace("\t"," ")
    
    allCat = MostRecentBlog.find("div",{"class":"meta-count"}).find("span",{"class","i-category"}).findAll("a")
    
    tags =[]
    
    for _x_ in allCat:
        tags.append(unicodedata.normalize('NFKD', _x_.getText()).encode('ascii','ignore').replace("\n","").replace("\t"," "))
        
            
        
    meta = MostRecentBlog.find("div",{"class":"meta-info no-bottom"})
    _auth = meta.find("span",{"itemprop":"author"}).getText()
    
    author_name =unicodedata.normalize('NFKD', _auth).encode('ascii','ignore').replace("\n","").replace("\t"," ")
    
    _on = meta.find("time",{"itemprop":"dateCreated"})
    
    posted_on = unicodedata.normalize('NFKD', _on.getText()).encode('ascii','ignore').replace("\n","").replace("\t","") 
    
    pagination =  map(int,unicodedata.normalize('NFKD',soup.find("div",{"class":"pagination"}).find("span").getText() ).encode('ascii','ignore').replace(" Page ","").split("of"))
    pages = [i for i in xrange(pagination[0],pagination[1]+1) ]
    return blogTitle,blogLink,tags,author_name,posted_on,pages
    

def ScrapeBlogs(url):
    soup = getSoup(url)
    BlogList = soup.find("div",{"class":"cur-page-item row block-streams el-block-3"})
    blogs = BlogList.findAll("div")
    finalBlog = [x for x in blogs if "up-up-child" in x.attrs['class'] ]
    
    for thisBlog in finalBlog:
        #Scraping the Blog related details from the DIV content
        _name = thisBlog.find("h3",{"itemprop":"name"})
        
        blogLink = _name.find("a").attrs["href"]
        blogTitle = unicodedata.normalize('NFKD', _name.getText()).encode('ascii','ignore').replace("\n","").replace("\t"," ")
        
        allCat = thisBlog.find("div",{"class":"meta-count"}).find("span",{"class","i-category"}).findAll("a")
        
        tags = []
        
        for _x_ in allCat:

            tags.append(unicodedata.normalize('NFKD', _x_.getText()).encode('ascii','ignore').replace("\n","").replace("\t"," "))
                        
        meta = thisBlog.find("div",{"class":"meta-info no-bottom"})
        _auth = meta.find("span",{"itemprop":"author"}).getText()
        
        author_name =unicodedata.normalize('NFKD', _auth).encode('ascii','ignore').replace("\n","").replace("\t"," ")
        
        _on = meta.find("time",{"itemprop":"dateCreated"})
        
        posted_on = unicodedata.normalize('NFKD', _on.getText()).encode('ascii','ignore') .replace("\n","").replace("\t"," ")
        
    return blogTitle,blogLink,tags,author_name,posted_on

if __name__ == '__main__':

    BLOG_URL = "http://www.analyticsvidhya.com/blog/page/{P.NO}/"
    conn = sqlite3.connect('AnVid.db')
    counter = 0
    cursor = conn.execute("select name from sqlite_master where type = 'table';")
    
    for row in cursor:
        counter = counter +1

    if counter ==0:

        #setup file location.
        exit = False
        flag = 0

        while exit == False:
            if flag==0:
                location = raw_input("Enter file location \t OR press 0 to terminate : ")
            elif flag==-1:
                location = raw_input("Invalid file path found, Try again \t OR press 0 to terminate : ")

            if os.path.exists(location) :
                exit = True
                flag = 1

            else:
                flag =-1

        #configure database.
        
        temp_location = location.replace("/","_")
        conn.execute("CREATE TABLE config  (location text NOT NULL) ; ")
        query = "INSERT INTO config (location) VALUES ('{s}') ;".replace("{s}",temp_location)
        print query
        conn.execute(query)

        #first time running
        conn.execute("CREATE TABLE most_recent_blog (ID INT PRIMARY KEY     NOT NULL, name TEXT NOT NULL, url TEXT NOT NULL, author TEXT NOT NULL, posted_on TEXT NOT NULL, tags TEXT NOT NULL ) ;")

        blogTitle,blogLink,tags,author_name,posted_on,pages = MostRecentBlog()
        
        for page in pages:
            _url = BLOG_URL.replace("{P.NO}",str(page))
            temp_blogTitle,temp_blogLink,temp_tags,temp_author_name,temp_posted_on = ScrapeBlogs(_url)
            pdfkit.from_url(temp_blogLink, location+temp_blogTitle+".pdf")
            print "Downloaded : "+ temp_blogTitle 
            
            new_query = "INSERT INTO most_recent_blog (id,name,author,posted_on,tags,url) VALUES (1,'_name_','_author_','_postedOn_','_tags_','_url_') ; "
            new_query = new_query.replace("_name_",temp_blogTitle)
            new_query = new_query.replace("_author_",temp_author_name)
            new_query = new_query.replace("_postedOn_",temp_posted_on)
            new_query = new_query.replace("_tags_",", ".join(tags))
            new_query = new_query.replace("_url_",temp_blogLink)

            print new_query
            conn.execute("DELETE FROM most_recent_blog")
            conn.execute(new_query)
    
    else:
        print "else part triggered."
        location_cursor = conn.execute("select  location from  config ;")
        counter = 0
        location =""
        for row in location_cursor:
            location = row[0]
            counter = counter +1
            break

        location = location.replace("_","/")
        print location
        if os.path.exists(location):
            print "Path validated..."
            blog_cursor = conn.execute("SELECT url FROM most_recent_blog")
            url = ""
            for row in blog_cursor:
                url = row[0]
                counter = counter +1
                break

            blogTitle,blogLink,tags,author_name,posted_on,pages = MostRecentBlog()

            if url == blogLink :
                print "Up-to-date"

            else:
                for page in pages:
                    _url = BLOG_URL.replace("{P.NO}",str(page))
                    temp_blogTitle,temp_blogLink,temp_tags,temp_author_name,temp_posted_on = ScrapeBlogs(_url)
                    
                    pdfkit.from_url(temp_blogLink, location+"/"+temp_blogTitle+".pdf")
                    
                    print "Downloaded : "+ temp_blogTitle 
                    new_query = "INSERT INTO most_recent_blog (id,name,author,posted_on,tags,url) VALUES (1,'_name_','_author_','_postedOn_','_tags_','_url_') ; "
                    new_query = new_query.replace("_name_",temp_blogTitle)
                    new_query = new_query.replace("_author_",temp_author_name)
                    new_query = new_query.replace("_postedOn_",temp_posted_on)
                    new_query = new_query.replace("_tags_",", ".join(tags))
                    new_query = new_query.replace("_url_",temp_blogLink)

                    print new_query
                    conn.execute("DELETE FROM most_recent_blog")
                    conn.execute(new_query)
           

                    if url == temp_blogLink:
                        print "Updated succesfully."
                        break

    


