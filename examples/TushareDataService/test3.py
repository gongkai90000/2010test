# encoding: UTF-8

import requests
import sys
import csv
import csv
import os

'''
future_code = 'M0'
url_str = ('http://stock2.finance.sina.com.cn/futures/api/json.php/IndexService.getInnerFuturesMiniKLine15m?symbol=' + future_code)
r = requests.get(url_str)

#http://stock2.finance.sina.com.cn/futures/api/json.php/IndexService.getInnerFuturesMiniKLine15m?symbol=M0
r_json = r.json()
r_lists = list(r_json)
#print('future_code,date,open,high,low,close,vol')

headers=['id','username','password','age','country']
rows=[(1001,'qiye','qiye_pass',20,'china'),(1002,'mary','mary_pass',23,'usa')]
f=open("csvfile.csv",'a+')
wf =csv.writer(f)
#wf.writerow(headers)
wf.writerows(r_lists)
f.close()
'''
with open("csvfile.csv") as cf:
    lines = csv.reader(cf)
    for line in lines:
        print(line)

gg=os.path.exists("csvfile.csv")
print gg

ty=[1,2,3,4,5,6,7]
print ty
del(ty[0])
print ty
#http://stock2.finance.sina.com.cn/futures/api/json.php/IndexService.getInnerFuturesMiniKLine5m?symbol=M0