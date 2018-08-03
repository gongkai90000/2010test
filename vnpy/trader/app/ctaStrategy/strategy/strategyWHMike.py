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
from var_dump import var_dump
from vnpy.trader.vtObject import VtBarData
from vnpy.trader.vtConstant import EMPTY_STRING
from vnpy.trader.app.ctaStrategy.ctaTemplate import (CtaTemplate, 
                                                     BarGenerator, 
                                                     ArrayManager)


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
    initDays = 10                       # 初始化数据所用的天数
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
        
    #----------------------------------------------------------------------
    def on30minBar(self, bar):
        """"""
        
        
    #----------------------------------------------------------------------
    def onInit(self):
        """初始化策略（必须由用户继承实现）"""
        self.writeCtaLog(u'%s策略初始化' %self.name)
        
        # 载入历史数据，并采用回放计算的方式初始化策略数值
        initData = self.loadBar(self.initDays)
        for bar in initData:
            self.onBar(bar)

        self.putEvent()

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
        """收到X分钟K线"""
        # 全撤之前发出的委托
        self.cancelAll()
    
        # 保存K线数据
        am = self.am
        
        am.updateBar(bar)
        
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
        
        # 判断是否要进行交易
        # mike add sma #
        # NN1:=VALUEWHEN(DATE<>REF(DATE,1),REF(MA(KK,47),1));#
        nn1=am.smaco(47)
        #NN2:=VALUEWHEN(DATE<>REF(DATE,1),REF(MA(KK,31),1));#
        nn2=am.smaco(31)
        #NN3:=VALUEWHEN(DATE<>REF(DATE,1),REF(MA(KK,34),1));
        nn3=am.smaco(34)
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
        ma1=am.sma(143,1)
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

        diffma1=max(xarr)-min(marr)
        #AA:=C>KEY AND C>VALUEWHEN(DATE<>REF(DATE,1),C);
        if [self.am.close>mkey]:
            aa=True
        else:
            aa=False
        #BB:=C<KEY AND C<VALUEWHEN(DATE<>REF(DATE,1),C);
        if [self.am.close<mkey]:
            bb=True
        else:
            bb=False





        # 当前无仓位，发送开仓委托
        if self.pos == 0:
            self.intraTradeHigh = bar.high
            self.intraTradeLow = bar.low            
            
            if self.cciValue > 0:
                self.buy(self.bollUp, self.fixedSize, True)
                
            elif self.cciValue < 0:
                self.short(self.bollDown, self.fixedSize, True)
    
        # 持有多头仓位
        elif self.pos > 0:
            self.intraTradeHigh = max(self.intraTradeHigh, bar.high)
            self.intraTradeLow = bar.low
            self.longStop = self.intraTradeHigh - self.atrValue * self.slMultiplier
            
            self.sell(self.longStop, abs(self.pos), True)
    
        # 持有空头仓位
        elif self.pos < 0:
            self.intraTradeHigh = bar.high
            self.intraTradeLow = min(self.intraTradeLow, bar.low)
            self.shortStop = self.intraTradeLow + self.atrValue * self.slMultiplier
            
            self.cover(self.shortStop, abs(self.pos), True)
            
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
    
