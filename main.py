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
            #print("Text file line: ", outputString)
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
def getSectionInfoFromReportUrlFile(fileName,sectionNames, topicSentence, csvName):
    companyNames = []
    dates = []
    sectionInfo = [[] for i in range(len(sectionNames))]
    reportUrlFile = open(fileName, "r")
    #print("sectionInfo start ", sectionInfo)
    # creates arrays of company name, dates, and section info
    for line in reportUrlFile.readlines():
        splitLines = line.split("|")
        companyNames.append(splitLines[0])
        dates.append(splitLines[1])
        url = splitLines[2]
        for index in range(len(sectionNames)):
            currentSectionText = getSectionInfoFromUrl(url, sectionNames[index], topicSentence[index])
            sectionInfo[index].append(currentSectionText)
    #stores data in csv
    #print("company names ", len(companyNames))
    #print("date ", len(dates))
    sectionDf["Company Name"] = companyNames
    sectionDf["Date"] = dates
    #print("sectionInfo after ", sectionInfo)
    for index in range(len(sectionNames)):
        sectionName = sectionNames[index]
        #print("section Name ", sectionName)
        currentSectionInfo = sectionInfo[index]
        #print("seciton info ", currentSectionInfo)
        sectionDf[sectionName] = currentSectionInfo
    sectionDf.to_csv(csvName, index=False)

# returns section info from given 8-K url
def getSectionInfoFromUrl(url, sectionName, topicSentence):
    #print("first tp ", topicSentence)
    driver.get(url)
    # sleeps for 2 to let the page reload
    time.sleep(2)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    targetIndex = -1
    # create array with all text
    htmlArr = soup.html.findAll(string=True, recursive=True)
    tableOfContentExists = False
    pastTableOfContentNumber = True
    for index in range(len(htmlArr)):
        #print("element before ", htmlArr[index])
        # unicodedata.normalize('NFKD', htmlArr[index]).strip()
        element = htmlArr[index].strip()
        #print("element after ", element)
        #print("remove punc ", element.translate(str.maketrans('', '', string.punctuation)))
        element = element.replace("\n", " ")
        # remove spaces in between words
        element = " ".join(element.split())
        #print("element ", element)
        if element.lower().find("table of contents") >= 0 and not tableOfContentExists:
            tableOfContentExists = True
            pastTableOfContentNumber = False
            #print("table of contents exists")
        elif element.lower().find(sectionName.lower()) == 0 and pastTableOfContentNumber:
            targetIndex = index + 1
            #print("found correct 2.03")
            break
        elif element.lower().find(sectionName.lower()) == 0 and tableOfContentExists:
            pastTableOfContentNumber = True
            #print("found one 2.03")

    avoidCharactersSet = set(['\xa0','\n', 'table of contents'])
    currSectionText = ""
    #print("htmlArr ", htmlArr)
    #print("targetindex ", targetIndex)
    #print("url ", url)
    #print("arr ", htmlArr[targetIndex:])
    if targetIndex >= 0:
        while targetIndex < len(htmlArr) and htmlArr[targetIndex].strip().lower().find("item") != 0:
            # Remove punctuation
            #print("target index ", targetIndex)
            targetText = htmlArr[targetIndex].strip()
            # (targetIndex > 0 and text == '\n' and htmlArr[targetIndex - 1] == '\n'
            # Break clauses, ex: if end of page occurs
            if targetText == "SIGNATURE" or targetText == "SIGNATURES" or targetText == "Forward Looking Statements":
                break
            # text cannot be new line, space, and section text
            #targetText = text.translate(str.maketrans('', '', string.punctuation))
            targetText = " ".join(targetText.split()).lower()
            # some title statements do not have the -
            topicSenetenceComparsion = targetText.replace("-"," ").replace(".", "")
            #print("Topic S ", topicSentence)
            #print("Targe S ", topicSenetenceComparsion)
            #print("find targetText ", topicSentence.find(topicSenetenceComparsion))
            if targetText not in avoidCharactersSet and (topicSentence.find(topicSenetenceComparsion) == -1 and len(targetText) > 0):
                #print("text approved ", text)
                #print("topicSetence in index ", topicSentence.find(text))
                #print("topic sentence found ", topicSentence.find(text) >= 0 and len(text) > 0)
                # add text to current section text
                content = htmlArr[targetIndex].strip()
                if content != "\n":
                    content = htmlArr[targetIndex].replace("\n", " ")
                # remove spaces in between words
                content = " ".join(content.split())
                currSectionText += content
                #print("curr section ", currSectionText)
            targetIndex += 1
    #print("final current text ", currSectionText)
    #print(" ")
    return currSectionText

# Parameters needed for the file, 
indexFileName = "EdgarCodesMarch.idx"
fileType = "8-K"
sectionNames = ["Item 2.03", "Item 1.01"]
#change to your title sections, this should not be included csv file
topicSentence = ['creation of a direct financial obligation or an obligation under an off balance sheet arrangement of a registrant', 'entry into a material definitive agreement']
reportUrlFile = "SavedFiles/Item2.03/March2023/March2023ReportUrlSavedInfo.txt"
csvFilename = "SavedFiles/Item2.03/March2023/March2023Item2.03SectionInfo.csv"
getSectionInfoFromReportUrlFile(reportUrlFile, sectionNames,topicSentence,csvFilename)
driver.quit()