import dpkt
import matplotlib.pyplot as plt
import numpy as np
import statsmodels.api as sm

class NetFlow:
    def __init__(self, timestamp, ip_src, ip_dst, dst_port, traffic):
        self.timestamp = timestamp
        self.ip_src = ip_src
        self.ip_dst = ip_dst
        self.traffic = traffic
        self.dst_port = dst_port
        self.hashable_obj = (ip_src, ip_dst, dst_port)

    def __hash__(self):
        return hash(self.ip_src) + hash(self.ip_dst)

    def __repr__(self):
        return f'({self.ip_src},{self.ip_dst},{self.dst_port})'
    
    def __eq__(self, other):
        if isinstance(other, NetFlow) and hash(other) == hash(self):
            return True
        if self.ip_dst == other.ip_src and self.ip_src == other.ip_dst:
            return True
        return False
        

class Filter:

    def is_arp_or_bytes(self, ip):
        return type(ip) == dpkt.arp.ARP or type(ip) == bytes
    
    def not_tcp_or_udp(self, data):
        if isinstance(data, dpkt.tcp.TCP) or isinstance(data, dpkt.udp.UDP):
            return False
        return True

    def is_IP6(self, ip):
        return type(ip) == dpkt.ip6.IP6

    def need_to_filter(self, ip):
        if self.is_arp_or_bytes(ip) or self.not_tcp_or_udp(ip.data) or self.is_IP6(ip):
            return True

from statsmodels.tsa.stattools import adfuller, kpss
import scipy

def ADF_test(x):
    # p-value小于0.05则证明序列平稳
    result = adfuller(x, autolag='AIC')
    print(f'ADF Statistic: {result[0]}')
    print(f'p-value: {result[1]}')
    for key, value in result[4].items():
        print('Critial Values:')
        print(f'   {key}, {value}')


def KPSS_test(x):
    # p-value大于0.05则证明序列平稳
    result = kpss(x, regression='c')
    print('\nKPSS Statistic: %f' % result[0])
    print('p-value: %f' % result[1])
    for key, value in result[3].items():
        print('Critial Values:')
        print(f'   {key}, {value}')
        
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf

def plot_ACF_and_PCAF(data, lags=10):
    fig, axes = plt.subplots(1,2,figsize=(16,3), dpi= 100)
    plot_acf(data, lags=lags, ax=axes[0])
    plot_pacf(data, lags=lags, ax=axes[1])
    

def pre_handle(timeseries):
    d_value = 0
    result = adfuller(timeseries)
    if result[1] >= 0.05:
        result_diff1 = adfuller(timeseries.diff().dropna())
#         print("1st Differencing")
        d_value = 1
        if result_diff1[1] >= 0.05 and len(timeseries.diff().diff().dropna())>3:
            d_value = 2
            result_diff2 = adfuller(timeseries.diff().diff().dropna())
            timeseries = timeseries.diff().diff().dropna()
#             print("2th Differencing")
        else:
            timeseries = timeseries.diff().dropna()
            d_value = 1
    result = adfuller(timeseries)   
#     print(f"ADF Statstic: {result[0]}")
#     print(f"p-value: {result[1]}")
    return timeseries, d_value

def split_data(timeseries, split_percent):
    # Create Training and Test
    data_list = timeseries
    print("len_data:",len(data_list))
    train_percent = split_percent/100
    split_index = int(train_percent * len(data_list))
    train = data_list[:split_index]
    test = data_list[split_index:]
    return train, test
 
from statsmodels.tsa.stattools import acf

def forecast_accuracy(forecast, actual):
    mape = np.mean(np.abs(forecast - actual)/np.abs(actual))  # MAPE
    me = np.mean(forecast - actual)             # ME
    mae = np.mean(np.abs(forecast - actual))    # MAE
    mpe = np.mean((forecast - actual)/actual)   # MPE
    rmse = np.mean((forecast - actual)**2)**.5  # RMSE
    corr = np.corrcoef(forecast, actual)[0,1]   # corr
    mins = np.amin(np.hstack([forecast[:,None], 
                              actual[:,None]]), axis=1)
    maxs = np.amax(np.hstack([forecast[:,None], 
                              actual[:,None]]), axis=1)
    minmax = 1 - np.mean(mins/maxs)             # minmax
    # acf1 = acf(forecast-actual)[1]                      # ACF1
    r2 = scipy.stats.linregress(forecast, actual).rvalue
    return({'mape':mape, 'r2': r2,'me':me, 'mae': mae, 
            'mpe': mpe, 'rmse':rmse, 
            # 'acf1':acf1, 
            'corr':corr, 'minmax':minmax})


def get_CDF_plot(data, X_label):
    font_size = 11
    plt.rc('font',family='Times New Roman')
    ecdf = sm.distributions.ECDF(data)
    #等差数列，用于绘制X轴数据
    x = np.linspace(min(data), max(data))
    # x轴数据上值对应的累计密度概率
    y = ecdf(x)
    #绘制阶梯图
    plt.plot(x, y,'-*', color='green')
    plt.xlabel(X_label, fontsize=font_size)
    plt.ylabel("CDF", fontsize=font_size)
    plt.grid()
    return plt
