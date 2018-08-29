data = dataClass()
data.__dict__ = {'high': d['high'], 'low': d['low'], 'open': d['open'], 'close': d['close'], 'volume': d['volume'],
                 'datetime': d.name.to_pydatetime()}
