import numpy as np
import talib as ta

o= [1.0, 321.0, 231.0, 321.0, 45.0, 46.0, 57.0, 897.0, 987.0, 64.0, 78987.0, 31.0, 32.0, 654.0, 5.0]
print o.__len__()
print o
del o[0]
o.append(666.66)
print o
print o[0]
p = np.array(o)
s = ta.SMA(p, 5)
k = s[-1]
print(s)
print(k)