"""from selenium import webdriver
from selenium.webdriver.chrome.service import Service

chrome_driver_path = './chromedriver'

chrome_driver_service = Service(chrome_driver_path)

driver = webdriver.Chrome(service=chrome_driver_service)
"""
from selenium import webdriver
from bs4 import BeautifulSoup
import string
import pandas as pd
import idx2numpy
import unicodedata
import time


driver = webdriver.Chrome()
sectionDf = pd.DataFrame() 
def getReportUrlFromIndexFile(fileName, filingType,section, urlFilingFileName):
    file = open(fileName, "r")
    #file = f.read()
    mySectionArr = []
    for line in file.readlines():
        if line.find(filingType) == -1:
            continue
        splitLine = line.split("|")
        filingDetailBaseURL = "https://www.sec.gov/Archives/"
        edgarFilingCode = splitLine[4]
        endPosition = edgarFilingCode.find(".")
        edgarFilingCode = edgarFilingCode[:endPosition]
        endOfURL = "-index.htm"
        filingDetailURL = filingDetailBaseURL + edgarFilingCode + endOfURL
        #print("filing detail url ", filingDetailURL)
        reportURL = checkIfSectionExists(section,filingDetailURL)
        #print("URL 8-K report ", reportURL)
        if reportURL != None:
            companyName = splitLine[1]
            date = splitLine[3]
            mySectionArr.append((companyName, date, reportURL))
            writer = open(urlFilingFileName,'a')
            outputString = companyName + "|" + date + "|" + reportURL + '\n'
            writer.write(outputString)
            writer.close()
    print(mySectionArr)
    file.close()
    




#driver.get('https://www.sec.gov/Archives/edgar/data/1000045/0000950170-23-001040-index.htm')
#soup = BeautifulSoup(driver.page_source, "html.parser")
#print(soup)

def checkIfSectionExists(section, url):
    driver.get(url)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    possible_table_of_contents = soup.find_all("div", class_="info")
    #finds if section 2.03 exists
    item203Exists = False
    for toc in possible_table_of_contents:
        if toc.text.find(section) > 0:
            item203Exists = True
            break

    #gets url of the 8k
    baseURL = "https://www.sec.gov"
    URL8K = None
    if item203Exists:
        possible_tables = soup.find_all("table", class_="tableFile")
        targetTable = None
        for table in possible_tables:
            if table['summary'] == "Document Format Files":
                targetTable = table
                break
        if targetTable != None:
            #assumes the find row in the table has the 8k html link
            URL8K = baseURL + targetTable.findChild("a")['href']
        #else:
            #print("table not found")
    #else:
        #print("item 2.03 does not exist")
    return URL8K

def getSectionInfoFromReportUrlFile(fileName,sectionName, topicSentence, csvName):
    reportUrlFile = open(fileName, "r")
    companyNames = []
    dates = []
    sectionInfo = []
    for line in reportUrlFile.readlines():
        splitLines = line.split("|")
        companyNames.append(splitLines[0])
        dates.append(splitLines[1])
        url = splitLines[2]
        currentSectionText = getSectionInfoFromUrl(url, sectionName, topicSentence)
        sectionInfo.append(currentSectionText)
    sectionDf["Company Name"] = companyNames
    sectionDf["Date"] = dates
    sectionDf[sectionName] = sectionInfo
    sectionDf.to_csv(csvName, index=False)
    
def getSectionInfoFromUrl(url, sectionName, topicSentence):
    #time.sleep(10)
    #driver = webdriver.Chrome()
    driver.get(url)
    time.sleep(2)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    #possible_paragraphs = soup.find_all("div")
    targetIndex = -1
    #time.sleep(5)
    htmlArr = soup.html.findAll(string=True, recursive=True)
    tableOfContentExists = False
    #print("html arr ", htmlArr)
    for index in range(len(htmlArr)):
        element = unicodedata.normalize('NFKD', htmlArr[index]).strip()
        element = element.replace("\n", " ")
        #print("element ", element)
        #print("eleemnt find ", element.find(sectionName))

        #print("element", element)
        #print("section Name ", sectionName)
        #if len(element) > 0:
        #    print("first element ", element[0])
        #print("equal ", element == sectionName)
        #print("len of element ", len(element))
        #print("len of section Name ", len(sectionName))
        #print("element ",element.translate(str.maketrans('', '', string.punctuation)).strip())
        if element.lower().find("table of contents") >= 0:
            tableOfContentExists = True
        elif element.lower().find(sectionName.lower()) == 0 and not tableOfContentExists:
            targetIndex = index + 1
            break
        elif element.lower().find(sectionName.lower()) == 0 and tableOfContentExists:
            tableOfContentExists = False

    # 'Creation of a Direct Financial Obligation or an Obligation under an Off-Balance Sheet Arrangement of a Registrant'
    avoidCharactersSet = {'\xa0','\n'}
    #avoidList.update(userAvoidSet)
    currSectionText = ""
    print("htmlArr ", htmlArr)
    print("targetindex ", targetIndex)
    print("url ", url)
    print("arr ", htmlArr[targetIndex:])
    if targetIndex >= 0:
        while targetIndex < len(htmlArr) and htmlArr[targetIndex].strip().lower().find("item") != 0:
            # Remove punctuation
            print("target index ", targetIndex)
            text = htmlArr[targetIndex]
            # Break clases, ex: if end of page occurs
            # (targetIndex > 0 and text == '\n' and htmlArr[targetIndex - 1] == '\n'
            print("text in loop ", text)
            if text == "SIGNATURE" or text == "SIGNATURES" or text == "Forward Looking Statements":
                break
            targetText = text.strip().lower()
            if text not in avoidCharactersSet and (topicSentence.lower().find(targetText) == -1 and len(text) > 0):
                #print("text ", text)
                #print("topicSetence in index ", topicSentence.find(text))
                #print("topic sentence found ", topicSentence.find(text) >= 0 and len(text) > 0)
                
                content = htmlArr[targetIndex]
                if content != "\n":
                    content = htmlArr[targetIndex].replace("\n", " ")
                currSectionText += content
                print("curr section ", currSectionText)
            targetIndex += 1
    #print("current text ", currSectionText)
    return currSectionText



# topic modeling: what is text discussing 
# tfid gives features, use svm to create classfication
# nmf, non negative matrix factorization 
# lda - latent data analysis 
# 
indexFileName = "EdgarCodesMarch.idx"
fileType = "8-K"
sectionName = "Item 2.03"
reportUrlFile = "SavedFiles/Item2.03/March2023/March2023ReportUrlSavedInfo.txt"
csvFilename = "SavedFiles/Item2.03/March2023/March2023Item2.03SectionInfo.csv"

#getReportUrlFromIndexFile(indexFileName,fileType,sectionName,reportUrlFile)
topicSentence = 'Creation of a Direct Financial Obligation or an Obligation under an Off-Balance Sheet Arrangement of a Registrant.'
#print("topic sentence find ", topicSentence.lower().find("SHEET ARRANGEMENT OF A REGISTRANT. "))
getSectionInfoFromReportUrlFile(reportUrlFile, sectionName,topicSentence.lower(),csvFilename)
#getSectionInfoFromUrl("https://www.sec.gov/ix?doc=/Archives/edgar/data/1000045/000095017023001040/nick-20230118.htm", "Item 2.03", avoidList)
#getSectionInfoFromUrl("https://www.sec.gov/ix?doc=/Archives/edgar/data/1000697/000119312523062099/d640177d8k.htm", "Item 2.03", avoidList)
#time.sleep(15)


        
#https://www.sec.gov/ix?doc=/Archives/edgar/data/1000228/000100022823000006/hsic-20230216.htm
#'https://www.sec.gov/ix?doc=/Archives/edgar/data/1000045/000095017023001040/nick-20230118.htm'
# https://www.sec.gov/ix?doc=/Archives/edgar/data/100378/000143774923004278/twin20230220_8k.htm

#soup = BeautifulSoup('<html>x<b>no</b>yes</html>',"html.parser")
#print("new soup ", soup.html.findAll(string=True, recursive=False))
#for element in soup:

#print(element.contents)



"""
found_item = False
target_index = 0
for index in range(0, len(possible_paragraphs)):
    paragraph = possible_paragraphs[index]
    #print("paragraph in loop ", paragraph)
    #print("index ", index)
    if paragraph.text.find("Item 2.02") >= 0:
        target_index = index + 2
        found_item = True
        break
if found_item:
    print(possible_paragraphs[target_index])
else:
    print("did not found 2.02")
"""
driver.quit()