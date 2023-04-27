from selenium import webdriver
from bs4 import BeautifulSoup
import string
import pandas as pd
import idx2numpy

"""
f_read = open('master.idx', 'rb')
ndarr = idx2numpy.convert_from_file(f_read)
print("indexfile ", ndarr)
"""

file = open("master.idx", "r")
#file = f.read()
for line in file.readlines():
    if line.find("8-K") == -1:
        continue
    splitLine = line.split("|")
    print(splitLine)
    print(line)
    print("split line link ", splitLine[4])
    
    