import pandas as pd

import urllib.request as url
from bs4 import BeautifulSoup as bs
import re
import sys
from threading import Thread
from time import time
import os
from time import sleep
import shutil
import requests

headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}

def apply_fn_modify_localpath(Filename, local_path):
    temp_list = list(Filename.split('/'))
    CIK = temp_list[2]
    CODE = temp_list[3][0:-4]
    temp_local_path = local_path + '/' + CIK + '_' + CODE
    return temp_local_path

def apply_fn_modify_Filename(Filename):
    temp_list = list(Filename.split('/'))
    CIK = temp_list[2]
    CODE = temp_list[3][0:-4]
    return CIK + '_' + CODE + '.htm'


def build_masters(start_yr=2016, end_yr=2019, form_type='8-K'):
    master_cols = ['CIK', 'Company Name', 'Form Type', 'Date Filed', 'Filename']
    cols = master_cols
    yrs = range(int(start_yr), int(end_yr))
    qtrs = range(1,5)
    master = pd.DataFrame(columns=cols)
    
    for yr in yrs:
        if yr == 2022:
            qtrs = range(1,2)
        print(yr)
        yr = str(yr)
        local_path = './data/' + form_type + '/' + yr
        if(not os.path.isdir(local_path) ):
            os.mkdir(local_path)
        for qtr in qtrs:        
            print(qtr)
            qtr = str(qtr)
            master_url = 'https://www.sec.gov/Archives/edgar/full-index/' + yr + '/QTR' + qtr + '/master.idx'
            print(master_url)
            #url.urlretrieve(master_url, 'master.idx')
            r = requests.get(master_url, headers={'User-Agent': 'Agam Shah ashah482@gatech.edu'})
            r.raise_for_status()
            open('master.idx', 'wb').write(r.content)
            #r.close()
            sleep(0.1)
            try:
                master_df = pd.read_table('./master.idx', sep='|', skiprows=11, names=master_cols)
            except:
                master_df = pd.read_table('./master.idx', sep='|', skiprows=11, names=master_cols, encoding='latin-1')

            master_df = master_df[master_df['Form Type'] == form_type]   
            local_path_QTR = local_path + '/QTR' + qtr
            if(not os.path.isdir(local_path_QTR) ):
                os.mkdir(local_path_QTR)
            master_df['local_path'] = local_path_QTR
            print(master_df.shape)
            master = master.append(master_df, sort=False)
            #master = master.append(master_df[:10], sort=False)# change for downloading all files instead of just 10

    
    print(master.shape)
    ciks, filenames = master['CIK'], master['Filename']
    ciks = [str(cik) for cik in ciks]
    filings = [filename[11+len(cik)+1:-4] for (filename, cik) in zip(filenames, ciks)]
    prefix = 'https://www.sec.gov/Archives/edgar/data'
    urls = ['/'.join([prefix, cik, ''.join(filing.split('-')), filing + '-index.htm']) for (cik, filing) in zip(ciks, filings)]

    master['SEC_url'] = pd.Series(urls, index=master.index)

    master['local_path'] = master.apply(lambda x: apply_fn_modify_localpath(x['Filename'], x['local_path']), axis=1)
    master['Filename'] = master.apply(lambda x: apply_fn_modify_Filename(x['Filename']), axis=1)
    master.to_csv('./data/masters/master_' + form_type +'.csv', index=False)

def download_files(start, end, url_file):
    
    url_df = pd.read_csv(url_file).iloc[start:end,:]
    #url_df = pd.read_csv(url_file).iloc[0:10,:]
    local_paths, SEC_URLs, Filenames = list(url_df['local_path']), list(url_df['SEC_url']), list(url_df['Filename'])
    it = start
    errors = []

    for (local_path, SEC_URL, Filename) in zip(local_paths, SEC_URLs, Filenames):
        if not it % 100:
            print(it)
        if(not os.path.isdir(local_path) ):
            print(it)
            try:
                temp_local_path = local_path
                # based on local path create folder and create path accordingly to store the files
                os.mkdir(temp_local_path)

                req = url.Request(SEC_URL, headers={'User-Agent': 'Agam Shah ashah482@gatech.edu'})
                response = url.urlopen(req).read()
                sleep(0.1)
                soup = bs(response, 'html.parser')
                #response.close()
                #url.urlretrieve(SEC_URL, temp_local_path + '/' +  Filename)
                r = requests.get(SEC_URL, headers={'User-Agent': 'Agam Shah ashah482@gatech.edu'})
                r.raise_for_status()
                open(temp_local_path + '/' +  Filename, 'wb').write(r.content)
                
                sleep(0.1)

                tables = soup.findAll('table')
                for table in tables:
                    links = table.findAll('a')
                    for link in links:
                        temp_url = 'https://www.sec.gov' + link['href']
                        temp_list = list(temp_url.split('/'))
                        check_url = link['href']
                        check_url_list = list(check_url.split('/'))
                        if (len(check_url_list)>=7):
                            if(len(check_url_list[-1])>2):
                                try:
                                    #url.urlretrieve(temp_url, temp_local_path + '/' + temp_list[-1])
                                    r = requests.get(temp_url, headers={'User-Agent': 'Agam Shah ashah482@gatech.edu'})
                                    r.raise_for_status()
                                    open(temp_local_path + '/' + temp_list[-1], 'wb').write(r.content)
                                except:
                                    pass
                                sleep(0.2)
                        elif(temp_list[-1][-4:]==".txt"):
                            if(len(check_url_list[-1])>2):
                                #url.urlretrieve(temp_url, temp_local_path + '/' + temp_list[-1])
                                r = requests.get(temp_url, headers={'User-Agent': 'Agam Shah ashah482@gatech.edu'})
                                r.raise_for_status()
                                open(temp_local_path + '/' + temp_list[-1], 'wb').write(r.content)
                                sleep(0.2)
            except Exception as e: 
                shutil.rmtree(local_path)
                print(e)
                temp_error = [local_path, SEC_URL, Filename]
                errors.append(temp_error)
                print(temp_error)
                sleep(700.0)#sleep(2.0)#sleep(700.0)#sleep(60.0)
            

        it += 1

    error_df = pd.DataFrame(errors, columns =['local_path', 'SEC_URL', 'Filename'])
    error_df.to_csv('./error/errors_file_' + str(start) + '_' + str(end) + '.csv')

    return

def merge_error_logs(form_type='8-K'):
    cols = ['local_path', 'SEC_URL', 'Filename']
    combined_raw_results = pd.DataFrame(columns=cols)
    for file in os.listdir("./error"):
        file_path = os.path.join("error", file)
        temp_raw_result = pd.read_csv(file_path)
        combined_raw_results = combined_raw_results.append(temp_raw_result)
    combined_raw_results.to_csv('./data/error_logs/combined_error_log_' + form_type +'.csv', index=False)


def execute(start_yr=2016, end_yr=2019, n=4, form_type='8-K'):
    if(not os.path.isdir('data') ):
        os.mkdir('data')
    if(not os.path.isdir('data/masters') ):
        os.mkdir('data/masters')
    if(not os.path.isdir('data/' + form_type) ):
        os.mkdir('data/' + form_type)

    shutil.rmtree('./error')
    os.mkdir('error')


    n = int(n)
    build_masters(start_yr=start_yr, end_yr=end_yr, form_type=form_type)

    url_file = './data/masters/master_' + form_type + '.csv'
    url_df = pd.read_csv(url_file)
    start, end = 0, len(url_df.index)
    print('number of files:', end)
    if end % n:
        end = (int(end/n) + 1) * n

    threads = [ Thread(target = download_files, kwargs={'start':int(i), 'end':int(j), 'url_file':url_file}) for (i,j) in [((end-start)/n*k, (end-start)/n*(k+1)) for k in range(n)] ]
    [thread.start() for thread in threads]
    [thread.join() for thread in threads]

    merge_error_logs(form_type=form_type)
    

if __name__=='__main__':
    
    start = time()
    start_yr, end_yr, n_threads, form_type = sys.argv[1:]
    execute(start_yr=start_yr, end_yr=end_yr, n=n_threads, form_type=form_type)
    print((time() - start)/60.0)