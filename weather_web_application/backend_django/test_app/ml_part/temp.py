import datetime

import pandas as pd
import numpy as np

from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_absolute_error

import pmdarima as pm
import statsmodels.api as sm
from scipy.optimize import minimize


def sarima_and_es(series: pd.Series, test_size=7):
    future_dates = pd.date_range(
        start=series.index[-1] + datetime.timedelta(days=1), 
        end=series.index[-1] + datetime.timedelta(days=test_size), 
        freq='D'
    )
    empty_ser = pd.Series(
        np.full(test_size, fill_value=np.NaN), index=future_dates
    )
    series = pd.concat([series, empty_ser])

    four_terms = pm.preprocessing.FourierFeaturizer(m=365.25, k=1)
    y_orig, exog_feats = four_terms.fit_transform(series)
    exog_feats['date'] = y_orig.index 
    exog_feats = exog_feats.set_index('date')
    
    y_train = y_orig.iloc[:(len(y_orig)-test_size)]
    y_test =  y_orig.iloc[(len(y_orig)-test_size):]
    exog_train = exog_feats.iloc[:(len(exog_feats)-test_size)]
    exog_test = exog_feats.iloc[(len(exog_feats)-test_size):]
    
    # We do next two actions because there will be ValueWarning otherwise 
    y_train.index = pd.DatetimeIndex(
        y_train.index.values, freq=y_train.index.inferred_freq
    )
    exog_train.index = pd.DatetimeIndex(
        exog_train.index.values, freq=exog_train.index.inferred_freq
    )
    
    sarima = sm.tsa.statespace.SARIMAX(
        y_train, exog=exog_train, freq='D',
        order=(3, 0, 1), seasonal_order=(2, 1, 0, 7)
    ).fit(disp=-1)
    es = fitting(series, test_size=test_size, n_preds=0, verbose=False)
    
    sarima_fc = sarima.predict(
        start=y_test.index[0], end=y_test.index[-1], exog=exog_test
    )
    es_fc = pd.Series(
        es.result[-test_size:], index=y_test.index
    )
    comb_fc = (sarima_fc + es_fc) / 2
    
    return list(np.around(comb_fc.values))
    



class HoltWinters:
    
    """
    Holt-Winters model with the anomalies detection using Brutlag method
    
    # series - initial time series
    # slen - length of a season
    # alpha, beta, gamma - Holt-Winters model coefficients
    # n_preds - predictions horizon
    # scaling_factor - sets the width of the confidence interval by Brutlag (usually takes values from 2 to 3)
    
    """
    
    
    def __init__(
        self, series, slen, alpha, beta, gamma, n_preds, test_size,
        scaling_factor=2.5
    ):
        self.series = series
        self.slen = slen
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.n_preds = n_preds
        self.test_size = test_size
        self.scaling_factor = scaling_factor
        
        
    def initial_trend(self):
        sum = 0.0
        for i in range(self.slen):
            sum += float(self.series[i+self.slen] - self.series[i]) / self.slen
        return sum / self.slen  
    

    def initial_seasonal_components(self):
        seasonals = {}
        season_averages = []
        n_seasons = int(len(self.series)/self.slen)
        # let's calculate season averages
        for j in range(n_seasons):
            season_averages.append(
                sum(self.series[self.slen*j:self.slen*j+self.slen]) / \
                float(self.slen)
            )
        # let's calculate initial values
        for i in range(self.slen):
            sum_of_vals_over_avg = 0.0
            for j in range(n_seasons):
                sum_of_vals_over_avg += self.series[self.slen*j+i]-season_averages[j]
            seasonals[i] = sum_of_vals_over_avg/n_seasons
        return seasonals   

          
    def triple_exponential_smoothing(self):
        self.result = []
        self.Smooth = []
        self.Season = []
        self.Trend = []
        self.PredictedDeviation = []
        self.UpperBond = []
        self.LowerBond = []
        
        seasonals = self.initial_seasonal_components()
        
        for i in range(len(self.series)+self.n_preds):
            if i == 0: # components initialization
                smooth = self.series[0]
                trend = self.initial_trend()
                self.result.append(self.series[0])
                self.Smooth.append(smooth)
                self.Trend.append(trend)
                self.Season.append(seasonals[i%self.slen])
                
                self.PredictedDeviation.append(0)
                
                self.UpperBond.append(self.result[0] + 
                                      self.scaling_factor * 
                                      self.PredictedDeviation[0])
                
                self.LowerBond.append(self.result[0] - 
                                      self.scaling_factor * 
                                      self.PredictedDeviation[0])
                continue
                
            if i >= len(self.series): # predicting
                m = i - len(self.series) + 1
                self.result.append((smooth + m*trend) + seasonals[i%self.slen])
                
                # when predicting we increase uncertainty on each step
                self.PredictedDeviation.append(self.PredictedDeviation[-1]*1.01) 
                
            else:
                val = self.series[i]
                last_smooth, smooth = smooth, self.alpha*(val-seasonals[i%self.slen]) + (1-self.alpha)*(smooth+trend)
                trend = self.beta * (smooth-last_smooth) + (1-self.beta)*trend
                seasonals[i%self.slen] = self.gamma*(val-smooth) + (1-self.gamma)*seasonals[i%self.slen]
                self.result.append(smooth+trend+seasonals[i%self.slen])
                
                # Deviation is calculated according to Brutlag algorithm.
                self.PredictedDeviation.append(self.gamma * np.abs(self.series[i] - self.result[i]) 
                                               + (1-self.gamma)*self.PredictedDeviation[-1])
                     
            self.UpperBond.append(self.result[-1] + 
                                  self.scaling_factor * 
                                  self.PredictedDeviation[-1])

            self.LowerBond.append(self.result[-1] - 
                                  self.scaling_factor * 
                                  self.PredictedDeviation[-1])

            self.Smooth.append(smooth)
            self.Trend.append(trend)
            self.Season.append(seasonals[i%self.slen])


def timeseriesCVscore(
    params, series, loss_function=mean_absolute_error, test_size=10, slen=365
):
    """
        Returns error on CV  
        
        params - vector of parameters for optimization
        series - dataset with timeseries
        slen - season length for Holt-Winters model
    """
    # errors array
    errors = []
    
    values = series.values
    alpha, beta, gamma = params
    
    # set the number of folds for cross-validation
    tscv = TimeSeriesSplit(n_splits=3) 
    
    # iterating over folds, train model on each, forecast and calculate error
    for train, test in tscv.split(values):

        model = HoltWinters(
            series=values[train], slen=slen, 
            alpha=alpha, beta=beta, gamma=gamma, 
            n_preds=len(test), test_size=test_size
        )
        model.triple_exponential_smoothing()
        
        predictions = model.result[-len(test):]
        actual = values[test]
        error = loss_function(predictions, actual)
        errors.append(error)
        
    return np.mean(np.array(errors))


def fitting(series, n_preds=10, test_size=10, slen=365, verbose=True):
    data = series.copy()
    train_data = data[:-test_size]

    # initializing model parameters alpha, beta and gamma
    x = [0, 0, 0]

    # Minimizing the loss function
    opt = minimize(
        timeseriesCVscore, x0=x, 
        args=(train_data, mean_absolute_error, test_size, slen), 
        method="TNC", bounds = ((0, 1), (0, 1), (0, 1))  # bounds for params
    )

    # Take optimal values...
    alpha_final, beta_final, gamma_final = opt.x
    if verbose:
        print("alpha=%f, beta=%f, gamma=%f" % (
            alpha_final, beta_final, gamma_final
        ))

    # ...and train the model with them, forecasting for a week
    model = HoltWinters(
        train_data, slen = slen, n_preds = n_preds + test_size, 
        alpha=alpha_final, beta = beta_final, gamma = gamma_final,
        test_size=test_size
    )
    model.triple_exponential_smoothing()
    return model