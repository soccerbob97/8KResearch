from selenium import webdriver
from bs4 import BeautifulSoup
import string
import pandas as pd
import idx2numpy
import unicodedata
import time

driver = webdriver.Chrome()
sectionDf = pd.DataFrame() 

# Creates .txt file with 8-Ks containing your section, txt file contains name, date, and url of 8-K
def getReportUrlFromIndexFile(fileName, filingType,section, urlFilingFileName):
    file = open(fileName, "r")
    mySectionArr = []
    #reads through the file line by line
    for line in file.readlines():
        # skip line if it does not contain 8K info
        if line.find(filingType) == -1:
            continue
        # Create Url for 8-K base Info
        splitLine = line.split("|")
        filingDetailBaseURL = "https://www.sec.gov/Archives/"
        edgarFilingCode = splitLine[4]
        endPosition = edgarFilingCode.find(".")
        edgarFilingCode = edgarFilingCode[:endPosition]
        endOfURL = "-index.htm"
        filingDetailURL = filingDetailBaseURL + edgarFilingCode + endOfURL
        # checks if your section exists
        reportURL = checkIfSectionExists(section,filingDetailURL)
        #if section exists, store 8-K info in txt file
        if reportURL != None:
            companyName = splitLine[1]
            date = splitLine[3]
            mySectionArr.append((companyName, date, reportURL))
            writer = open(urlFilingFileName,'a')
            outputString = companyName + "|" + date + "|" + reportURL + '\n'
            print("Text file line: ", outputString)
            writer.write(outputString)
            writer.close()
    #print(mySectionArr)
    file.close()

#checks if section number exists
def checkIfSectionExists(section, url):
    driver.get(url)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    #finds all divs
    possible_table_of_contents = soup.find_all("div", class_="info")
    item203Exists = False
    for toc in possible_table_of_contents:
        if toc.text.find(section) > 0:
            item203Exists = True
            break

    #gets url of the 8k
    baseURL = "https://www.sec.gov"
    URL8K = None
    if item203Exists:
        #finds table with link to 8-K
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

# gets section info text and stores company info to csv
def getSectionInfoFromReportUrlFile(fileName,sectionName, topicSentence, csvName):
    reportUrlFile = open(fileName, "r")
    companyNames = []
    dates = []
    sectionInfo = []
    # creates arrays of company name, dates, and section info
    for line in reportUrlFile.readlines():
        splitLines = line.split("|")
        companyNames.append(splitLines[0])
        dates.append(splitLines[1])
        url = splitLines[2]
        currentSectionText = getSectionInfoFromUrl(url, sectionName, topicSentence)
        print("company and section info ", splitLines[0], currentSectionText)
        sectionInfo.append(currentSectionText)
    #stores data in csv
    sectionDf["Company Name"] = companyNames
    sectionDf["Date"] = dates
    sectionDf[sectionName] = sectionInfo
    sectionDf.to_csv(csvName, index=False)

# returns section info from given 8-K url
def getSectionInfoFromUrl(url, sectionName, topicSentence):
    driver.get(url)
    # sleeps for 2 to let the page reload
    time.sleep(2)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    targetIndex = -1
    # create array with all text
    htmlArr = soup.html.findAll(string=True, recursive=True)
    tableOfContentExists = False
    for index in range(len(htmlArr)):
        element = unicodedata.normalize('NFKD', htmlArr[index]).strip()
        element = element.replace("\n", " ")
        if element.lower().find("table of contents") >= 0:
            tableOfContentExists = True
        elif element.lower().find(sectionName.lower()) == 0 and not tableOfContentExists:
            targetIndex = index + 1
            break
        elif element.lower().find(sectionName.lower()) == 0 and tableOfContentExists:
            tableOfContentExists = False

    avoidCharactersSet = {'\xa0','\n'}
    currSectionText = ""
    #print("htmlArr ", htmlArr)
    #print("targetindex ", targetIndex)
    #print("url ", url)
    #print("arr ", htmlArr[targetIndex:])
    if targetIndex >= 0:
        while targetIndex < len(htmlArr) and htmlArr[targetIndex].strip().lower().find("item") != 0:
            # Remove punctuation
            #print("target index ", targetIndex)
            text = htmlArr[targetIndex]
            # (targetIndex > 0 and text == '\n' and htmlArr[targetIndex - 1] == '\n'
            #print("text in loop ", text)
            # Break clauses, ex: if end of page occurs
            if text == "SIGNATURE" or text == "SIGNATURES" or text == "Forward Looking Statements":
                break
            # text cannot be new line, space, and section text
            targetText = text.strip().lower()
            if text not in avoidCharactersSet and (topicSentence.lower().find(targetText) == -1 and len(text) > 0):
                #print("text ", text)
                #print("topicSetence in index ", topicSentence.find(text))
                #print("topic sentence found ", topicSentence.find(text) >= 0 and len(text) > 0)
                # add text to current section text
                content = htmlArr[targetIndex]
                if content != "\n":
                    content = htmlArr[targetIndex].replace("\n", " ")
                currSectionText += content
                #print("curr section ", currSectionText)
            targetIndex += 1
    print("current text ", currSectionText)
    print(" ")
    return currSectionText

# Parameters needed for the file, 
indexFileName = "EdgarCodesMarch.idx"
fileType = "8-K"
sectionName = "Item 2.03"
reportUrlFile = "SavedFiles/Item2.03/March2023/March2023ReportUrlSavedInfo.txt"
csvFilename = "SavedFiles/Item2.03/March2023/March2023Item2.03SectionInfo.csv"

#getReportUrlFromIndexFile(indexFileName,fileType,sectionName,reportUrlFile)
#change to your title section, this should not be included csv file
topicSentence = 'Creation of a Direct Financial Obligation or an Obligation under an Off-Balance Sheet Arrangement of a Registrant.'
getSectionInfoFromReportUrlFile(reportUrlFile, sectionName,topicSentence.lower(),csvFilename)
driver.quit()