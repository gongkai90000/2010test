import tushare as ts
import os

filename = 'c:/day/bigfile.csv'
for code in ['CU1801']:
    #df = ts.get_hist_data(code)
    #print df
    cons=ts.get_apis()
    #df = ts.bar(code,conn=cons, freq='1min', asset='X' ,start_date='2017-10-01', end_date='')
    df = ts.tick(code, conn=cons, asset='X')
    df.head(5)
   # df = df.sort_index()
    print df
    if os.path.exists(filename):
        df.to_csv(filename, mode='a', header=None)
    else:
        df.to_csv(filename)

ts.close_apis(cons)

#http://www.360doc.com/content/17/1030/16/14934540_699467341.shtml
#https://github.com/waditu/tushare/tree/master/test