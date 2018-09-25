# encoding: UTF-8

"""
感谢Darwin Quant贡献的策略思路。
知乎专栏原文：https://zhuanlan.zhihu.com/p/24448511

策略逻辑：
1. 布林通道（信号）
2. CCI指标（过滤）
3. ATR指标（止损）

适合品种：螺纹钢
适合周期：15分钟

这里的策略是作者根据原文结合vn.py实现，对策略实现上做了一些修改，仅供参考。

"""

from __future__ import division
import numpy as np
from datetime import datetime
import talib as ta
from var_dump import var_dump
from vnpy.trader.vtObject import VtBarData
from vnpy.trader.vtConstant import EMPTY_STRING
from vnpy.trader.app.ctaStrategy.ctaTemplate import (CtaTemplate, 
                                                     BarGenerator, 
                                                     ArrayManager)
import requests
import os
import csv
import smtplib
from email.mime.text import MIMEText
import time
########################################################################
class WHMikeStrategy(CtaTemplate):
    """基于布林通道的交易策略"""
    className = 'WHMikeStrategy'
    author = u'用Python的交易员'

    # 策略参数
    bollWindow = 18                     # 布林通道窗口数
    bollDev = 3.4                       # 布林通道的偏差
    cciWindow = 10                      # CCI窗口数
    atrWindow = 30                      # ATR窗口数
    slMultiplier = 5.2                  # 计算止损距离的乘数
    initDays = 30                       # 初始化数据所用的天数
    fixedSize = 1                       # 每次交易的数量

    # 策略变量
    bollUp = 0                          # 布林通道上轨
    bollDown = 0                        # 布林通道下轨
    cciValue = 0                        # CCI指标数值
    atrValue = 0                        # ATR指标数值
    
    intraTradeHigh = 0                  # 持仓期内的最高点
    intraTradeLow = 0                   # 持仓期内的最低点
    longStop = 0                        # 多头止损
    shortStop = 0                       # 空头止损

    firstN1 = 0                         #找到第一个n1
    firstN2 = 0                         #找到第一个n2
    firstN3 = 0                         #找到第一个n3
    firstC  = 0                         #找到第一个c
    bkprice = 0                         #返回最近一次模型买开位置的买开信号价位。
    skprice = 0                         #返回最近一次模型卖开位置的卖开信号价位。
    barssk = 0                          #返回上一次卖开仓的K线距离当前K线的周期数（不包含出现SK信号的那根K线）；发出SK信号的当根k线BARSSK返回空值
    barsbk = 0                          #返回上一次买开仓的K线距离当前K线的周期数（不包含出现BK信号的那根K线）；发出BK信号的当根k线BARSBK返回空值
    bkhigh  = 0                         #BKHIGH 买开仓以来的最高价
    sklow  = 0                          #卖开仓以来最低值
    line143 = []                        #143均线追述
    nowline143 = 0                      #最后一个143的值
    nowdate = ''                        #当前时间
    coarray = []                        #co的array
    carray = []                         #c的array
    csvfile="csvfile.csv"               #历史存储csv
    future_code = 'M0'                  #历史的品种
    hisbar = []                            #历史
    isinit = 0                          #0not init 1 initing

    # 参数列表，保存了参数的名称
    paramList = ['name',
                 'className',
                 'author',
                 'vtSymbol',
                 'bollWindow',
                 'bollDev',
                 'cciWindow',
                 'atrWindow',
                 'slMultiplier',
                 'initDays',
                 'fixedSize']    

    # 变量列表，保存了变量的名称
    varList = ['inited',
               'trading',
               'pos',
               'firstN1',
               'firstN2',
               'firstN3',
               'firstC',
               'bkprice',
               'skprice',
               'barssk',
               'barsbk',
               'bkhigh',
               'nowdate',
               'bollUp',
               'bollDown',
               'cciValue',
               'atrValue',
               'intraTradeHigh',
               'intraTradeLow',
               'longStop',
               'shortStop']  
    
    # 同步列表，保存了需要保存到数据库的变量名称
    syncList = ['pos',
                'intraTradeHigh',
                'intraTradeLow']    

    #----------------------------------------------------------------------
    def __init__(self, ctaEngine, setting):
        """Constructor"""
        super(WHMikeStrategy, self).__init__(ctaEngine, setting)
        
        self.bg = BarGenerator(self.onBar, 15, self.onXminBar)        # 创建K线合成器对象
        self.bg30 = BarGenerator(self.onBar, 30, self.on30minBar)
        self.am = ArrayManager()


        gg = os.path.exists(self.future_code + self.csvfile)
        gg = False
        if gg:
            with open(self.future_code + self.csvfile) as cf:
                lines = csv.reader(cf)
                for line in lines:
                    vv=(float(line[4])+float(line[1]))/2
                    self.coarray.insert(0,vv)
                    self.line143.insert(0, line[4])
                self.writeCtaLog(u'%s装载历史数据成功' % self.name)
                print(self.coarray)
        else:
           # os.remove(self.future_code + self.csvfile)
            #self.future_code = 'M0'
            url_str = ('http://stock2.finance.sina.com.cn/futures/api/json.php/IndexService.getInnerFuturesMiniKLine15m?symbol=' + self.future_code)
            r = requests.get(url_str)
            # http://stock2.finance.sina.com.cn/futures/api/json.php/IndexService.getInnerFuturesMiniKLine15m?symbol=M0
            r_json = r.json()
            r_lists = list(r_json)
            f = open(self.future_code + self.csvfile, 'a+')
            wf = csv.writer(f)
            wf.writerows(r_lists)
            f.close()
            self.writeCtaLog(u'%s装载历史数据失败重新拉取数据' % self.name)

        #get history data
        with open(self.future_code + self.csvfile) as cf:
            lines = csv.reader(cf)
            for line in lines:
                vv=(float(line[4])+float(line[1]))/2
                #self.coarray.insert(0, vv)
                #self.line143.insert(0, line[4])
                #self.hisbar.insert(0, line)
            self.writeCtaLog(u'%s装载历史数据成功' % self.name)
            print(self.coarray.__len__())
            # http://stock2.finance.sina.com.cn/futures/api/json.php/IndexService.getInnerFuturesMiniKLine5m?symbol=M0
        #self.sendQmail("strategy whmike start","strategy whmike start")
        #self.writeCtaLog(u'%s发送邮件成功' % self.name)



    #----------------------------------------------------------------------
    def on30minBar(self, bar):
        """"""
        
        
    #----------------------------------------------------------------------
    def onInit(self):
        """初始化策略（必须由用户继承实现）"""
        self.writeCtaLog(u'%s策略初始化' %self.name)
        self.isinit=1
        # 载入历史数据，并采用回放计算的方式初始化策略数值
        initData = self.loadBar(self.initDays)
        for bar in initData:
            self.onBar(bar)

        self.putEvent()
        self.isinit = 0
        self.writeCtaLog(u'%s策略初始化OK!!!!!!!' % self.name)

    def sendQmail(self,subject,msg):
        """发送邮件"""
        _user = "gongkai1000@qq.com"
        _pwd = "mmrphtjvhvetbjij"
        _to = "gongkai@dachuizichan.com"

        msg = MIMEText(msg)
        msg["Subject"] = subject + " "+ time.strftime('%Y-%m-%d %H:%M:%S',time.localtime())
        msg["From"] = _user
        msg["To"] = _to

        try:
            s = smtplib.SMTP_SSL("smtp.qq.com", 465)
            s.login(_user, _pwd)
            s.sendmail(_user, _to, msg.as_string())
            s.quit()
            #print("Success!")
        except smtplib.SMTPException, e:
            print ("Falied,%s" % e)

    #----------------------------------------------------------------------
    def onStart(self):
        """启动策略（必须由用户继承实现）"""
        self.writeCtaLog(u'%s策略启动' %self.name)
        self.putEvent()

    #----------------------------------------------------------------------
    def onStop(self):
        """停止策略（必须由用户继承实现）"""
        self.writeCtaLog(u'%s策略停止' %self.name)
        self.putEvent()

    #----------------------------------------------------------------------
    def onTick(self, tick):
        """收到行情TICK推送（必须由用户继承实现）""" 
        self.bg.updateTick(tick)

    #----------------------------------------------------------------------
    def onBar(self, bar):
        """收到Bar推送（必须由用户继承实现）"""
        self.bg.updateBar(bar)
    
    #----------------------------------------------------------------------
    def onXminBar(self, bar):
        self.writeCtaLog(u'%s onXminBar成功1' % self.name)
        #self.sendQmail("15 min ok ",  "ok")
        """收到X分钟K线"""

        # 全撤之前发出的委托
        self.cancelAll()
    
        # 保存K线数据
        am = self.am
        
        am.updateBar(bar)
        #print(231)
        out = "init: " + str(am.count) + " line: " + str(self.line143.__len__()) + " coarray: " + str(self.coarray.__len__())
        self.writeCtaLog(u'%s' % out)
        if self.line143.__len__() > 300:
            del (self.line143[0])
            del (self.coarray[0])
            return
        #self.nowline143 = self.line143[-1]
        self.line143.append(float(bar.close))
        self.coarray.append((bar.close + bar.open) / 2)

        if not am.inited:
            return
        #var_dump(self)
        #var_dump(111111111111111111111111111111111111111111111111111111111111111111111111111111111111111)
        #var_dump(bar)
        #exit()
        # 计算指标数值
        self.bollUp, self.bollDown = am.boll(self.bollWindow, self.bollDev)
        self.cciValue = am.cci(self.cciWindow)
        self.atrValue = am.atr(self.atrWindow)
        #print(242)

        # 判断是否要进行交易



        cop = np.array(self.coarray)
        # mike add sma #
        # NN1:=VALUEWHEN(DATE<>REF(DATE,1),REF(MA(KK,47),1));#
        #nn1=am.smaco(47)
        nn1array=ta.SMA(cop, 47)
        nn1=nn1array[-1]
        self.firstN1=nn1
        #NN2:=VALUEWHEN(DATE<>REF(DATE,1),REF(MA(KK,31),1));#
        #nn2=am.smaco(31)
        nn2array = ta.SMA(cop, 31)
        nn2 = nn2array[-1]
        self.firstN2=nn2
        #NN3:=VALUEWHEN(DATE<>REF(DATE,1),REF(MA(KK,34),1));
        #nn3=am.smaco(34)
        nn3array = ta.SMA(cop, 34)
        nn3 = nn3array[-1]
        self.firstN3=nn3
        #print(264)
        #
        #MAXM:=MAX(NN1, NN2);
        #MAX0:=MAX(MAXM, NN3);
        #
        max0=[nn1,nn2,nn3]
        maxa=max(max0)
        #
        #MINM:=MIN(NN1,NN2);
        #MIN0:=MIN(MINM,NN3);
        #
        min0=[nn1,nn2,nn3]
        mina=min(min0)
        #KEY:=(MAX0+MIN0)/2;//
        mkey=(maxa-mina)/2
        #MA1:=MA(C,143);
        # if bar.close>0:
        #   self.line143.append(bar.close)

        self.nowdate = bar.datetime
        #self.writeCtaLog(u'% Len 143' % self.line143.__len__())
#        self.writeCtaLog(u'% min0' % min0)
#        self.writeCtaLog(u'% max0' % max0)
#        self.writeCtaLog(u'% bar close' % bar.close)

        #print(self.line143.__len__())
        self.writeCtaLog(u'%sonXminBar成功2' % self.name)
        #del self.line143[0]



        p=np.array(self.line143)
        ma1 = ta.SMA(p, 143)
      #  ma1 = ta.SMA(self.line143, 143)


        #ma1=am.sma(143,1)
        xnum=7
        mnum=2

        if (len(ma1)<xnum):
            return
        #DIFF:=HHV(MA1,7)-LLV(MA1,2);
        xarr=[]
        xarr.append(ma1[-1])
        xarr.append(ma1[-2])
        xarr.append(ma1[-3])
        xarr.append(ma1[-4])
        xarr.append(ma1[-5])
        xarr.append(ma1[-6])
        xarr.append(ma1[-7])

        marr=[]
        marr.append(ma1[-1])
        marr.append(ma1[-2])
        print("max: " + str(round(max(xarr),2)) + " min: " + str(round(min(marr),2)) + " mkey: "+ str(mkey) + " firstC:" + str(self.firstC) + " bc: "+ str(bar.close))

        diffma1=round(max(xarr),2)-round(min(marr),2)
        diffma2=float(diffma1)
        if [self.firstC<1]:
            self.firstC=bar.close

        #AA:=C>KEY AND C>VALUEWHEN(DATE<>REF(DATE,1),C);
        if [bar.close>mkey and bar.close>self.firstC]:
            aa=True
        else:
            aa=False
        #BB:=C<KEY AND C<VALUEWHEN(DATE<>REF(DATE,1),C);
        if [bar.close<mkey and bar.close<self.firstC]:
            bb=True
        else:
            bb=False
        if self.isinit>0:
            print("init trade " + str(self.isinit))
            return
        else:
            print("start trade "+ str(self.isinit))
        # 当前无仓位，发送开仓委托
        if self.pos == 0:
            self.intraTradeHigh = bar.high
            self.intraTradeLow = bar.low            

            #if self.cciValue > 0:
            #    self.buy(self.bollUp, self.fixedSize, True)
                
            #elif self.cciValue < 0:
            #    self.short(self.bollDown, self.fixedSize, True)

            #AA && C-KEY<0.01*208*C/100 && DIFF<0.01*72*C/1000,BK;
            #BB && KEY-C<0.01*49*C/100 && DIFF<0.01*N5*C/1000,SK;

            ifbuyb=bar.close-mkey<0.01*208*bar.close/100
            ifbuyc=diffma1<0.01*72*bar.close/1000
            ifbuyd=self.barsbk < 1

            ifsellb=mkey-bar.close<0.01*49*bar.close/100
            ifsellc=diffma1<0.01*555*bar.close/1000
            ifselld=self.barssk < 1
            if aa and ifbuyb and ifbuyc:
                self.buy(self.bollUp, self.fixedSize, True)
                self.bkprice=bar.close
                self.barsbk = 1
                self.sendQmail("没有仓位buy ok " + str(self.bollUp), "ok ")


            elif bb and ifsellb and ifsellc:
                self.short(self.bollDown, self.fixedSize, True)
                self.skprice=bar.close
                self.barssk = 1
                self.sendQmail("没有仓位sell ok " + str(self.bollDown), "ok")


        #用法:BKPRICE返回最近一次模型买开位置的买开信号价位。
        #SKPRICE返回最近一次模型卖开位置的卖开信号价位。

#（1）当模型存在连续多个开仓信号(加仓)的情况下，该函数返回的是最后一次开仓信号的价格,而不是开仓均价。

#（2）模组运行环境，返回的是SK(SPK)信号发出时的行情的最新价（可以与模组运行界面中“信号记录”中的SK(SPK)信号对应的“当时最新价”比较）。SK信号发出并且已经确认固定后，SKPRICE的值更新为信号发出时的行情的最新价

#BARSSK返回上一次卖开仓的K线距离当前K线的周期数（不包含出现SK信号的那根K线）；发出SK信号的当根k线BARSSK返回空值

#BARSBK返回上一次买开仓的K线距离当前K线的周期数（不包含出现BK信号的那根K线）；发出BK信号的当根k线BARSBK返回空值

        # 持有多头仓位
        elif self.pos > 0:
            self.intraTradeHigh = max(self.intraTradeHigh, bar.high)
            self.intraTradeLow = bar.low
            self.bkhigh=self.intraTradeHigh
            self.sklow=self.intraTradeLow
            self.longStop = self.intraTradeHigh - self.atrValue * self.slMultiplier
            self.barsbk=self.barsbk+1
            # AA && (SKPRICE-C>0 OR SKPRICE-C<-1*(C/100)) AND BARSSK>1,BP;
            if [aa and (self.skprice - bar.close >0 or self.skprice-bar.close<-1*(bar.close/100)) and self.barssk>1]:
                self.sell(self.longStop, abs(self.pos), True)
                self.barsbk=0
                self.sendQmail("持有多头仓位买平1 " + str(self.longStop), "ok")
            # C > SKLOW * (1 + 0.001 * 35), BP;
            if [bar.close > self.sklow * (1 + 0.001 * 35)]:
                self.sell(self.longStop, abs(self.pos), True)
                self.barsbk = 0
                self.sendQmail("持有多头仓位买平2 " + str(self.longStop), "ok")
            #C < SKPRICE * (1 - 0.001 * 91), BP;
            if [bar.close < self.skprice * (1 - 0.001 * 91)]:
                self.sell(self.longStop, abs(self.pos), True)
                self.barsbk = 0
                self.sendQmail("持有多头仓位买平3 " + str(self.longStop), "ok")

        # 持有空头仓位
        elif self.pos < 0:
            self.intraTradeHigh = bar.high
            self.intraTradeLow = min(self.intraTradeLow, bar.low)
            self.bkhigh = self.intraTradeHigh
            self.sklow = self.intraTradeLow
            self.shortStop = self.intraTradeLow + self.atrValue * self.slMultiplier
            self.barssk=self.barssk+1
            # BB && (C-BKPRICE>0 OR C-BKPRICE<-1*(C/100)) AND BARSBK>37,SP;
            if [bb and (bar.close-self.bkprice>0 or bar.close-self.bkprice<-1*(bar.close/100)) and self.barsbk>37]:
                self.cover(self.shortStop, abs(self.pos), True)
                self.barssk = 0
                self.sendQmail("持有空头仓位买平3 " + str(self.longStop), "ok")
            # C < BKHIGH * (1 - 0.001 * 40), SP;
            if [bar.close < self.bkhigh * (1 - 0.001 * 40)]:
                self.cover(self.longStop, abs(self.pos), True)
                self.barssk = 0
                self.sendQmail("持有空头仓位买平3 " + str(self.longStop), "ok")
            # C > BKPRICE * (1 + 0.001 * 85), SP
            if [bar.close > self.bkprice * (1 + 0.001 * 85)]:
                self.cover(self.longStop, abs(self.pos), True)
                self.barssk = 0
                self.sendQmail("持有空头仓位买平3 " + str(self.longStop), "ok")
            #BKHIGH 买开仓以来的最高价
        #C >= SKPRICE * (1 + 0.0001 * 130), BP; //
        #C <= BKPRICE * (1 - 0.0001 * 185), SP; //



        #SETALLSIGPRICETYPE(PRICE) 市价委托



        # 同步数据到数据库
        self.saveSyncData()        
    
        # 发出状态更新事件
        self.putEvent()


    #----------------------------------------------------------------------
    def onOrder(self, order):
        """收到委托变化推送（必须由用户继承实现）"""
        pass

    #----------------------------------------------------------------------
    def onTrade(self, trade):
        # 发出状态更新事件
        self.putEvent()

    #----------------------------------------------------------------------
    def onStopOrder(self, so):
        """停止单推送"""
        pass
    
