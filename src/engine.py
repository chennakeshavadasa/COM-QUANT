import yfinance as yf
import numpy as np
import pandas as pd
import scipy
import scipy.stats
import statsmodels.api as sm
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.seasonal import seasonal_decompose
from sklearn.svm import SVR
import json
import sys
import datetime
import warnings
import time

warnings.filterwarnings('ignore')

COMMODITIES = {
    "GOLD":      {"ticker": "GC=F", "name": "Gold",          "unit": "USD/troy oz", "category": "precious_metals"},
    "SILVER":    {"ticker": "SI=F", "name": "Silver",        "unit": "USD/troy oz", "category": "precious_metals"},
    "PLATINUM":  {"ticker": "PL=F", "name": "Platinum",      "unit": "USD/troy oz", "category": "precious_metals"},
    "PALLADIUM": {"ticker": "PA=F", "name": "Palladium",     "unit": "USD/troy oz", "category": "precious_metals"},
    "COPPER":    {"ticker": "HG=F", "name": "Copper",        "unit": "USD/lb",      "category": "industrial_metals"},
    "ALUMINUM":  {"ticker": "ALI=F", "name": "Aluminum",     "unit": "USD/ton",     "category": "industrial_metals"},
    "ZINC":      {"ticker": "ZNC=F", "name": "Zinc",          "unit": "USD/ton",     "category": "industrial_metals"},
    "LEAD":      {"ticker": "LED=F", "name": "Lead",          "unit": "USD/ton",     "category": "industrial_metals"},
    "WTI":       {"ticker": "CL=F", "name": "WTI Crude Oil", "unit": "USD/barrel",  "category": "energy"},
    "BRENT":     {"ticker": "BZ=F", "name": "Brent Crude",   "unit": "USD/barrel",  "category": "energy"},
    "NATGAS":    {"ticker": "NG=F", "name": "Natural Gas",   "unit": "USD/MMBtu",   "category": "energy"},
    "GASOLINE":  {"ticker": "RB=F", "name": "RBOB Gasoline", "unit": "USD/gallon",  "category": "energy"},
    "HEATOIL":   {"ticker": "HO=F", "name": "Heating Oil",   "unit": "USD/gallon",  "category": "energy"},
    "WHEAT":     {"ticker": "ZW=F", "name": "Wheat",         "unit": "USD/bushel",  "category": "agriculture"},
    "CORN":      {"ticker": "ZC=F", "name": "Corn",          "unit": "USD/bushel",  "category": "agriculture"},
    "SOYBEAN":   {"ticker": "ZS=F", "name": "Soybean",       "unit": "USD/bushel",  "category": "agriculture"},
    "COFFEE":    {"ticker": "KC=F", "name": "Coffee",        "unit": "USD/lb",      "category": "agriculture"},
    "SUGAR":     {"ticker": "SB=F", "name": "Sugar",         "unit": "USD/lb",      "category": "agriculture"},
    "COTTON":    {"ticker": "CT=F", "name": "Cotton",        "unit": "USD/lb",      "category": "agriculture"},
    "COCOA":     {"ticker": "CC=F", "name": "Cocoa",         "unit": "USD/ton",     "category": "agriculture"},
    "OATS":      {"ticker": "OAT=F", "name": "Oats",          "unit": "USD/bushel",  "category": "agriculture"},
    "ROUGHRICE": {"ticker": "ZR=F",  "name": "Rough Rice",    "unit": "USD/cwt",     "category": "agriculture"},
    "LIVECATTLE":{"ticker": "LE=F", "name": "Live Cattle",   "unit": "USD/lb",      "category": "livestock"},
    "LEANHOGS":  {"ticker": "HE=F", "name": "Lean Hogs",     "unit": "USD/lb",      "category": "livestock"},
    "FEEDERCAT": {"ticker": "GF=F",  "name": "Feeder Cattle", "unit": "USD/lb",      "category": "livestock"},
}

CATEGORIES = {
    "precious_metals":   ["GOLD", "SILVER", "PLATINUM", "PALLADIUM"],
    "industrial_metals": ["COPPER", "ALUMINUM", "ZINC", "LEAD"],
    "energy":            ["WTI", "BRENT", "NATGAS", "GASOLINE", "HEATOIL"],
    "agriculture":       ["WHEAT", "CORN", "SOYBEAN", "COFFEE", "SUGAR", "COTTON", "COCOA", "OATS", "ROUGHRICE"],
    "livestock":         ["LIVECATTLE", "LEANHOGS", "FEEDERCAT"],
}

DXY_PROXY_TICKER = "EURUSD=X"

MODEL_WEIGHTS = {"arima": 0.25, "holt_winters": 0.25, "monte_carlo": 0.20, "ou_process": 0.15, "svr": 0.15}

WINDOWS = {
    "1W": {"forecast_days": 7,   "lookback_days": 180, "display_days": 7},
    "2W": {"forecast_days": 14,  "lookback_days": 365, "display_days": 14},
    "1M": {"forecast_days": 30,  "lookback_days": 365, "display_days": 30},
    "3M": {"forecast_days": 90,  "lookback_days": 730, "display_days": 90},
    "6M": {"forecast_days": 180, "lookback_days": 730, "display_days": 180},
}

def json_safe(obj):
    if isinstance(obj, float):
        if np.isnan(obj) or np.isinf(obj):
            return None
        return obj
    elif isinstance(obj, (np.float64, np.float32)):
        val = float(obj)
        if np.isnan(val) or np.isinf(val):
            return None
        return val
    elif isinstance(obj, (np.int64, np.int32, np.integer)):
        return int(obj)
    elif isinstance(obj, np.ndarray):
        return json_safe(obj.tolist())
    elif isinstance(obj, dict):
        return {k: json_safe(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [json_safe(x) for x in obj]
    else:
        return obj

def download_data(ticker, lookback_days):
    for attempt in range(3):
        try:
            df = yf.download(ticker, period=f"{lookback_days}d", auto_adjust=True)
            if df is None or df.empty:
                time.sleep(2)
                continue
            
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            df = df.ffill()
            
            req_cols = ["Open", "High", "Low", "Close", "Volume"]
            for c in req_cols:
                if c not in df.columns:
                    if c == "Volume":
                        df["Volume"] = 0
                    else:
                        df[c] = df["Close"] if "Close" in df.columns else np.nan
            
            if ticker in ["ZW=F", "ZC=F", "ZS=F"]:
                if df["Close"].iloc[-1] > 2000:
                    for c in ["Open", "High", "Low", "Close"]:
                        if c in df.columns:
                            df[c] = df[c] / 100.0
            
            return df
        except Exception as e:
            time.sleep(2)
    print(f"Failed to download data for {ticker}", file=sys.stderr)
    return None

def fit_arima(prices, forecast_days):
    n = forecast_days
    try:
        log_prices = np.log(prices)
        best_aic = np.inf
        best_model = None
        best_order = (1, 1, 1)
        for p in [0, 1, 2, 3]:
            for q in [0, 1, 2, 3]:
                try:
                    model = ARIMA(log_prices, order=(p, 1, q))
                    res = model.fit()
                    if res.aic < best_aic:
                        best_aic = res.aic
                        best_model = res
                        best_order = (p, 1, q)
                except:
                    continue
        
        if best_model is None:
            raise Exception("ARIMA failed")
            
        fc = best_model.get_forecast(steps=n)
        mean_fc = fc.predicted_mean
        conf_int = fc.conf_int(alpha=0.05)
        var_fc = fc.var_pred
        
        forecast_prices = np.exp(mean_fc + var_fc / 2.0)
        ci_lower = np.exp(conf_int.iloc[:, 0] if isinstance(conf_int, pd.DataFrame) else conf_int[:, 0])
        ci_upper = np.exp(conf_int.iloc[:, 1] if isinstance(conf_int, pd.DataFrame) else conf_int[:, 1])
        
        return {
            "forecast": forecast_prices.tolist(),
            "ci_lower": ci_lower.tolist(),
            "ci_upper": ci_upper.tolist(),
            "order": best_order,
            "aic": float(best_aic)
        }
    except:
        return {"forecast": [None]*n, "ci_lower": [None]*n, "ci_upper": [None]*n, "order": (1,1,1), "aic": None}

def fit_holt_winters(prices, forecast_days):
    n = forecast_days
    seasonal_periods = 5 if n <= 14 else 22
    try:
        try:
            model = ExponentialSmoothing(prices, trend='add', seasonal='add', seasonal_periods=seasonal_periods, initialization_method='estimated')
            res = model.fit()
        except:
            model = ExponentialSmoothing(prices, trend='add', seasonal=None, initialization_method='estimated')
            res = model.fit()
            
        fc = res.forecast(n)
        alpha = res.params.get('smoothing_level')
        beta = res.params.get('smoothing_trend')
        gamma = res.params.get('smoothing_seasonal')
        return {
            "forecast": fc.tolist(),
            "alpha": float(alpha) if alpha is not None else None,
            "beta": float(beta) if beta is not None else None,
            "gamma": float(gamma) if gamma is not None else None
        }
    except:
        return {"forecast": [None]*n, "alpha": None, "beta": None, "gamma": None}

def fit_monte_carlo(prices, forecast_days, n_sims=5000):
    n = forecast_days
    try:
        r = np.diff(np.log(prices))
        sigma = np.std(r) * np.sqrt(252)
        mu_ann = np.mean(r) * 252 + (sigma**2) / 2
        
        dt = 1/252
        S0 = prices[-1]
        
        paths = np.zeros((n_sims, n))
        Z = np.random.randn(n_sims, n)
        
        drift = (mu_ann - (sigma**2)/2) * dt
        vol = sigma * np.sqrt(dt)
        
        for t in range(n):
            if t == 0:
                paths[:, t] = S0 * np.exp(drift + vol * Z[:, t])
            else:
                paths[:, t] = paths[:, t-1] * np.exp(drift + vol * Z[:, t])
        
        p5 = np.percentile(paths, 5, axis=0)
        p25 = np.percentile(paths, 25, axis=0)
        p50 = np.percentile(paths, 50, axis=0)
        p75 = np.percentile(paths, 75, axis=0)
        p95 = np.percentile(paths, 95, axis=0)
        
        return {
            "p5": p5.tolist(), "p25": p25.tolist(), "p50": p50.tolist(), 
            "p75": p75.tolist(), "p95": p95.tolist(), "mu": float(mu_ann), "sigma": float(sigma)
        }
    except:
        return {"p5": [None]*n, "p25": [None]*n, "p50": [None]*n, "p75": [None]*n, "p95": [None]*n, "mu": None, "sigma": None}

def fit_ou_process(prices, forecast_days, n_sims=1000, is_natgas=False):
    n = forecast_days
    current_price = prices[-1]
    dt = 1.0 / 252.0
    try:
        S_t = prices[1:]
        S_t_minus_1 = prices[:-1]
        dS = S_t - S_t_minus_1
        
        X = sm.add_constant(S_t_minus_1)
        model = sm.OLS(dS, X)
        res = model.fit()
        alpha, beta = res.params[0], res.params[1]
        
        if beta >= 0:
            theta = 0.1
            mu_eq = current_price
            resid = dS - (alpha + beta * S_t_minus_1)
            sigma = np.std(resid) / np.sqrt(dt) if len(resid) > 0 else current_price * 0.05
        else:
            theta = -beta / dt
            mu_eq = -alpha / beta
            resid = res.resid
            sigma = np.std(resid) / np.sqrt(dt)
        
        theta = np.clip(theta, 0.001, 50.0)
        mu_eq = np.clip(mu_eq, 0.1 * current_price, 10.0 * current_price)
        sigma = np.clip(sigma, 1e-4, current_price * 0.5)
        
        half_life_days = (np.log(2) / theta) * 252.0
        
        paths = np.zeros((n_sims, n))
        for i in range(n_sims):
            S = current_price
            for t in range(n):
                eps = np.random.randn()
                S = S + theta * (mu_eq - S) * dt + sigma * np.sqrt(dt) * eps
                max_S = 5.0 * current_price if is_natgas else 10.0 * current_price
                S = np.clip(S, 0.001, max_S)
                paths[i, t] = S
        
        forecast = np.median(paths, axis=0)
        return {
            "forecast": forecast.tolist(),
            "theta": float(theta),
            "mu_eq": float(mu_eq),
            "sigma": float(sigma),
            "half_life_days": float(half_life_days)
        }
    except:
        return {"forecast": [None]*n, "theta": None, "mu_eq": None, "sigma": None, "half_life_days": None}

def fit_svr(prices, forecast_days):
    n = forecast_days
    try:
        X = np.arange(len(prices)).reshape(-1, 1)
        y = np.array(prices)
        from sklearn.preprocessing import StandardScaler
        scaler_X = StandardScaler()
        scaler_y = StandardScaler()
        X_scaled = scaler_X.fit_transform(X)
        y_scaled = scaler_y.fit_transform(y.reshape(-1, 1)).flatten()
        
        model = SVR(kernel='rbf', C=10, gamma='scale', epsilon=0.1)
        model.fit(X_scaled, y_scaled)
        
        X_pred = np.arange(len(prices), len(prices) + n).reshape(-1, 1)
        X_pred_scaled = scaler_X.transform(X_pred)
        forecast_scaled = model.predict(X_pred_scaled)
        forecast = scaler_y.inverse_transform(forecast_scaled.reshape(-1, 1)).flatten()
        
        return {"forecast": forecast.tolist()}
    except:
        return {"forecast": [None]*n}

def fit_random_forest(prices, forecast_days):
    n = forecast_days
    try:
        from sklearn.ensemble import RandomForestRegressor
        X = np.arange(len(prices)).reshape(-1, 1)
        y = np.array(prices)
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X, y)
        X_pred = np.arange(len(prices), len(prices) + n).reshape(-1, 1)
        forecast = model.predict(X_pred)
        # Smooth the RF forecast slightly so it's not totally flat
        smoothed = pd.Series(forecast).ewm(span=5).mean().values
        return {"forecast": smoothed.tolist()}
    except:
        return {"forecast": [None]*n}

MODEL_WEIGHTS = {"arima": 0.20, "holt_winters": 0.20, "monte_carlo": 0.20, "ou_process": 0.15, "svr": 0.15, "rf": 0.10}

def compute_ensemble(arima_fc, hw_fc, mc_p50, ou_fc, svr_fc, rf_fc, weights):
    n = len(arima_fc)
    ensemble = []
    for i in range(n):
        vals = []
        wts = []
        if arima_fc[i] is not None:
            vals.append(arima_fc[i])
            wts.append(weights["arima"])
        if hw_fc[i] is not None:
            vals.append(hw_fc[i])
            wts.append(weights["holt_winters"])
        if mc_p50[i] is not None:
            vals.append(mc_p50[i])
            wts.append(weights["monte_carlo"])
        if ou_fc[i] is not None:
            vals.append(ou_fc[i])
            wts.append(weights["ou_process"])
        if svr_fc and svr_fc[i] is not None:
            vals.append(svr_fc[i])
            wts.append(weights.get("svr", 0.0))
        if rf_fc and rf_fc[i] is not None:
            vals.append(rf_fc[i])
            wts.append(weights.get("rf", 0.0))
        
        if sum(wts) > 0:
            ensemble.append(float(np.average(vals, weights=wts)))
        else:
            ensemble.append(None)
    return ensemble

def find_optimal_entry(ensemble, forecast_dates, current_price):
    valid_pairs = [(v, i) for i, v in enumerate(ensemble) if v is not None]
    if not valid_pairs:
        return {"optimal_date": None, "optimal_price": None, "optimal_horizon_days": None, "potential_gain_pct": None}
    
    best_val, best_idx = min(valid_pairs, key=lambda x: x[0])
    gain_pct = abs(current_price - best_val) / current_price * 100
    
    return {
        "optimal_date": forecast_dates[best_idx],
        "optimal_price": float(best_val),
        "optimal_horizon_days": best_idx + 1,
        "potential_gain_pct": float(gain_pct)
    }

def compute_technical_indicators(close, high=None, low=None):
    close = np.array(close)
    if high is None: high = close
    else: high = np.array(high)
    if low is None: low = close
    else: low = np.array(low)
    
    def calc_rsi(c, period=14):
        if len(c) <= period: return 50.0
        diff = np.diff(c)
        gains = np.where(diff > 0, diff, 0)
        losses = np.where(diff < 0, -diff, 0)
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        if avg_loss == 0: return 100.0
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
        
    rsi14 = np.clip(calc_rsi(close), 0, 100)
    
    def ema(c, period):
        return pd.Series(c).ewm(span=period, adjust=False).mean().values
    
    if len(close) > 26:
        ema12 = ema(close, 12)
        ema26 = ema(close, 26)
        macd_line = ema12 - ema26
        signal_line = ema(macd_line, 9)
        macd = macd_line[-1]
        macd_signal = signal_line[-1]
        macd_hist = macd - macd_signal
    else:
        macd, macd_signal, macd_hist = 0.0, 0.0, 0.0
        
    if len(close) >= 20:
        sma20 = np.mean(close[-20:])
        std20 = np.std(close[-20:])
        boll_u = sma20 + 2 * std20
        boll_l = sma20 - 2 * std20
        pct_b = (close[-1] - boll_l) / (boll_u - boll_l) if boll_u != boll_l else 0.5
        pct_b = np.clip(pct_b, -0.5, 1.5)
    else:
        boll_u, boll_l, pct_b = close[-1], close[-1], 0.5
        
    if len(close) >= 14:
        min14 = np.min(low[-14:])
        max14 = np.max(high[-14:])
        if max14 != min14:
            k_line = (close[-14:] - min14) / (max14 - min14) * 100
        else:
            k_line = np.full(14, 50.0)
        stoch_k = k_line[-1]
        stoch_d = np.mean(k_line[-3:]) if len(k_line) >= 3 else stoch_k
        stoch_d = np.clip(stoch_d, 0, 100)
    else:
        stoch_k, stoch_d = 50.0, 50.0
        
    if len(close) >= 14:
        min14 = np.min(low[-14:])
        max14 = np.max(high[-14:])
        if max14 != min14:
            will_r = (max14 - close[-1]) / (max14 - min14) * -100
        else:
            will_r = -50.0
        will_r = np.clip(will_r, -100, 0)
    else:
        will_r = -50.0
        
    if len(close) >= 14:
        tr = np.maximum(high[1:] - low[1:], 
                        np.maximum(np.abs(high[1:] - close[:-1]), 
                                   np.abs(low[1:] - close[:-1])))
        atr14 = np.mean(tr[-14:]) if len(tr) >= 14 else np.mean(tr)
    else:
        atr14 = 0.0
        
    if len(close) >= 20:
        sma20 = np.mean(close[-20:])
        mad = np.mean(np.abs(close[-20:] - sma20))
        cci20 = (close[-1] - sma20) / (0.015 * mad) if mad != 0 else 0.0
    else:
        cci20 = 0.0
        
    if len(close) >= 20:
        sma20 = np.mean(close[-20:])
        std20 = np.std(close[-20:])
        zscore20 = (close[-1] - sma20) / std20 if std20 != 0 else 0.0
    else:
        zscore20 = 0.0
        
    scores = []
    
    if rsi14 < 30: scores.append(85)
    elif rsi14 <= 50: scores.append(65)
    elif rsi14 <= 70: scores.append(35)
    else: scores.append(15)
    
    if macd_hist > 0 and macd > macd_signal: scores.append(75)
    elif macd > macd_signal: scores.append(55)
    else: scores.append(30)
    
    if pct_b < 0.2: scores.append(80)
    elif pct_b <= 0.4: scores.append(65)
    elif pct_b <= 0.6: scores.append(50)
    elif pct_b <= 0.8: scores.append(35)
    else: scores.append(20)
    
    if stoch_k < 20: scores.append(80)
    elif stoch_k <= 50: scores.append(60)
    elif stoch_k <= 80: scores.append(40)
    else: scores.append(20)
    
    if will_r < -80: scores.append(80)
    elif will_r <= -50: scores.append(60)
    elif will_r <= -20: scores.append(40)
    else: scores.append(20)
    
    if cci20 < -100: scores.append(80)
    elif cci20 <= 0: scores.append(60)
    elif cci20 <= 100: scores.append(40)
    else: scores.append(20)
    
    if zscore20 < -2: scores.append(85)
    elif zscore20 <= -1: scores.append(65)
    elif zscore20 <= 1: scores.append(50)
    elif zscore20 <= 2: scores.append(35)
    else: scores.append(15)
    
    comp_score = np.mean(scores)
    
    if comp_score < 25: comp_signal = "Bearish"
    elif comp_score < 40: comp_signal = "Mildly Bearish"
    elif comp_score < 60: comp_signal = "Neutral"
    elif comp_score < 75: comp_signal = "Mildly Bullish"
    else: comp_signal = "Bullish"
    
    return {
        "rsi14": float(rsi14),
        "macd": float(macd),
        "macd_signal": float(macd_signal),
        "macd_hist": float(macd_hist),
        "bollinger_upper": float(boll_u),
        "bollinger_lower": float(boll_l),
        "bollinger_pct_b": float(pct_b),
        "stochastic_k": float(stoch_k),
        "stochastic_d": float(stoch_d),
        "williams_r": float(will_r),
        "atr14": float(atr14),
        "cci20": float(cci20),
        "zscore20": float(zscore20),
        "composite_score": float(comp_score),
        "composite_signal": comp_signal
    }

def compute_statistics(close):
    r = np.diff(np.log(close))
    
    hursts = []
    for tau in [10, 20, 40, 80, 160]:
        if len(r) > tau:
            num_blocks = len(r) // tau
            rs_vals = []
            for i in range(num_blocks):
                block = r[i*tau : (i+1)*tau]
                mean_adj = block - np.mean(block)
                cumdev = np.cumsum(mean_adj)
                R = np.max(cumdev) - np.min(cumdev)
                S = np.std(block)
                if S > 0:
                    rs_vals.append(R/S)
            if rs_vals:
                hursts.append((tau, np.mean(rs_vals)))
    
    if len(hursts) > 1:
        log_taus = np.log([x[0] for x in hursts])
        log_rs = np.log([x[1] for x in hursts])
        H = np.polyfit(log_taus, log_rs, 1)[0]
    else:
        H = 0.5
        
    H = np.clip(H, 0.01, 0.99)
    if H < 0.45: h_regime = "Mean-Reverting"
    elif H <= 0.55: h_regime = "Random Walk"
    else: h_regime = "Trending"
    
    skewness = scipy.stats.skew(r) if len(r) > 0 else 0.0
    kurt = scipy.stats.kurtosis(r) if len(r) > 0 else 0.0
    
    if len(r) > 5:
        try:
            adf = adfuller(r, maxlag=5)
            adf_stat, adf_p = adf[0], adf[1]
            adf_stat_flag = bool(adf_p < 0.05)
        except:
            adf_stat, adf_p, adf_stat_flag = None, None, None
    else:
        adf_stat, adf_p, adf_stat_flag = None, None, None
        
    if len(r) > 0:
        try:
            jb = scipy.stats.jarque_bera(r)
            jb_stat, jb_p = jb.statistic, jb.pvalue
        except:
            jb_stat, jb_p = None, None
    else:
        jb_stat, jb_p = None, None
        
    vols = {}
    for n in [10, 20, 30]:
        if len(r) >= n:
            vols[f"annualized_vol_{n}d"] = float(np.std(r[-n:]) * np.sqrt(252) * 100)
        else:
            vols[f"annualized_vol_{n}d"] = None
            
    return {
        "hurst": float(H),
        "hurst_regime": h_regime,
        "skewness": float(skewness),
        "kurtosis_excess": float(kurt),
        "adf_statistic": float(adf_stat) if adf_stat is not None else None,
        "adf_pvalue": float(adf_p) if adf_p is not None else None,
        "adf_stationary": adf_stat_flag,
        "jarque_bera_statistic": float(jb_stat) if jb_stat is not None else None,
        "jarque_bera_pvalue": float(jb_p) if jb_p is not None else None,
        **vols,
        "mean_daily_return_pct": float(np.mean(r) * 100) if len(r) > 0 else 0.0
    }

def compute_risk_metrics(close):
    r = np.diff(np.log(close))
    
    var_95_pct = float(-np.percentile(r, 5) * 100) if len(r) > 0 else 0.0
    var_99_pct = float(-np.percentile(r, 1) * 100) if len(r) > 0 else 0.0
    
    if len(r) > 0:
        cvar_mask = r < np.percentile(r, 5)
        cvar_95_pct = float(-np.mean(r[cvar_mask]) * 100) if np.sum(cvar_mask) > 0 else var_95_pct
    else:
        cvar_95_pct = 0.0
    
    peak = np.maximum.accumulate(close)
    drawdowns = (peak - close) / peak
    max_drawdown_pct = float(np.max(drawdowns) * 100) if len(drawdowns) > 0 else 0.0
    
    dca_5d_avg = float(np.mean(close[-5:])) if len(close) >= 5 else float(np.mean(close))
    dca_10d_avg = float(np.mean(close[-10:])) if len(close) >= 10 else float(np.mean(close))
    
    std_r = np.std(r)
    sharpe_ratio = float(np.mean(r) / std_r * np.sqrt(252)) if std_r > 0 else 0.0
    
    downside = r[r < 0]
    std_down = np.std(downside)
    sortino_ratio = float(np.mean(r) * 252 / (std_down * np.sqrt(252))) if len(downside) > 0 and std_down > 0 else None
    
    return {
        "var_95_pct": var_95_pct,
        "var_99_pct": var_99_pct,
        "cvar_95_pct": cvar_95_pct,
        "max_drawdown_pct": max_drawdown_pct,
        "dca_5d_avg": dca_5d_avg,
        "dca_10d_avg": dca_10d_avg,
        "sharpe_ratio": sharpe_ratio,
        "sortino_ratio": sortino_ratio
    }

def compute_seasonality(close_series, date_index):
    r = pd.Series(np.diff(np.log(close_series.values)), index=date_index[1:])
    
    dow = r.groupby(r.index.weekday).mean()
    day_names = {0:"Monday", 1:"Tuesday", 2:"Wednesday", 3:"Thursday", 4:"Friday"}
    day_of_week = {day_names.get(k, str(k)): float(v) for k, v in dow.items() if k < 5}
    
    mon = r.groupby(r.index.month).mean()
    month_names = {1:"Jan", 2:"Feb", 3:"Mar", 4:"Apr", 5:"May", 6:"Jun", 7:"Jul", 8:"Aug", 9:"Sep", 10:"Oct", 11:"Nov", 12:"Dec"}
    monthly = {month_names.get(k, str(k)): float(v) for k, v in mon.items()}
    
    qtr = r.groupby(r.index.quarter).mean()
    quarterly = {f"Q{k}": float(v) for k, v in qtr.items()}
    
    best_day = max(day_of_week.items(), key=lambda x: x[1])[0] if day_of_week else None
    worst_day = min(day_of_week.items(), key=lambda x: x[1])[0] if day_of_week else None
    best_month = max(monthly.items(), key=lambda x: x[1])[0] if monthly else None
    worst_month = min(monthly.items(), key=lambda x: x[1])[0] if monthly else None
    
    trend, seasonal, resid = [], [], []
    if len(close_series) >= 44:
        try:
            decomp = seasonal_decompose(close_series, model='multiplicative', period=22, extrapolate_trend='freq')
            trend = [float(x) if not np.isnan(x) else None for x in decomp.trend.tolist()]
            seasonal = [float(x) if not np.isnan(x) else None for x in decomp.seasonal.tolist()]
            resid = [float(x) if not np.isnan(x) else None for x in decomp.resid.tolist()]
        except:
            pass
            
    return {
        "day_of_week": day_of_week,
        "monthly": monthly,
        "quarterly": quarterly,
        "best_day": best_day,
        "worst_day": worst_day,
        "best_month": best_month,
        "worst_month": worst_month,
        "decomposition_trend": trend,
        "decomposition_seasonal": seasonal,
        "decomposition_residual": resid
    }

def compute_spreads(all_close_dict):
    df_all = pd.DataFrame(all_close_dict).dropna(how='all')
    df_all = df_all.ffill()
    
    gold_silver_ratio = None
    if "GOLD" in df_all.columns and "SILVER" in df_all.columns:
        df_pair = df_all[["GOLD", "SILVER"]].dropna()
        if len(df_pair) > 0:
            ratio = df_pair["GOLD"] / df_pair["SILVER"]
            ratio_dates = [d.strftime("%Y-%m-%d") for d in ratio.index[-180:]]
            ratio_vals = ratio.values[-180:]
            
            n_1y = min(252, len(ratio))
            mean_1y = np.mean(ratio.values[-n_1y:])
            std_1y = np.std(ratio.values[-n_1y:])
            
            curr = ratio_vals[-1]
            z_score = (curr - mean_1y) / std_1y if std_1y > 0 else 0.0
            
            if z_score > 1.0: interp = "Silver cheap vs gold"
            elif z_score < -1.0: interp = "Gold cheap vs silver"
            else: interp = "Near historical mean"
            
            gold_silver_ratio = {
                "dates": ratio_dates,
                "values": [round(float(x), 4) for x in ratio_vals],
                "current": float(curr),
                "mean_1y": float(mean_1y),
                "z_score": float(z_score),
                "interpretation": interp
            }
            
    brent_wti_spread = None
    if "BRENT" in df_all.columns and "WTI" in df_all.columns:
        df_pair = df_all[["BRENT", "WTI"]].dropna()
        if len(df_pair) > 0:
            spread = df_pair["BRENT"] - df_pair["WTI"]
            spread_dates = [d.strftime("%Y-%m-%d") for d in spread.index[-180:]]
            spread_vals = spread.values[-180:]
            
            n_1y = min(252, len(spread))
            mean_1y = np.mean(spread.values[-n_1y:])
            std_1y = np.std(spread.values[-n_1y:])
            
            curr = spread_vals[-1]
            z_score = (curr - mean_1y) / std_1y if std_1y > 0 else 0.0
            
            brent_wti_spread = {
                "dates": spread_dates,
                "values": [round(float(x), 4) for x in spread_vals],
                "current": float(curr),
                "mean_1y": float(mean_1y),
                "z_score": float(z_score)
            }
            
    precious_energy_corr_3m = None
    if "GOLD" in df_all.columns and "WTI" in df_all.columns:
        df_pair = df_all[["GOLD", "WTI"]].dropna()
        if len(df_pair) >= 64:
            g_r = np.diff(np.log(df_pair["GOLD"].values[-64:]))
            w_r = np.diff(np.log(df_pair["WTI"].values[-64:]))
            precious_energy_corr_3m = float(scipy.stats.pearsonr(g_r, w_r)[0])
            
    return {
        "gold_silver_ratio": gold_silver_ratio,
        "brent_wti_spread": brent_wti_spread,
        "precious_energy_corr_3m": precious_energy_corr_3m
    }

def compute_correlations(all_close_dict, dxy_series):
    df_all = pd.DataFrame(all_close_dict)
    if dxy_series is not None:
        df_all["DXY_PROXY"] = dxy_series
    
    df_all = df_all.dropna(how='all').ffill().dropna()
    correlations = {}
    
    df_comm = df_all.drop(columns=["DXY_PROXY"], errors='ignore')
    cids = df_comm.columns
    
    if len(df_all) >= 64:
        df_64 = df_all.iloc[-64:]
        for cid1 in cids:
            correlations[cid1] = {}
            r1 = np.diff(np.log(df_64[cid1].values))
            for cid2 in cids:
                r2 = np.diff(np.log(df_64[cid2].values))
                if np.std(r1) == 0 or np.std(r2) == 0:
                    correlations[cid1][cid2] = 0.0
                else:
                    correlations[cid1][cid2] = float(scipy.stats.pearsonr(r1, r2)[0])
                
        correlations["dxy_proxy"] = {}
        if "DXY_PROXY" in df_all.columns:
            dxy_r = -np.diff(np.log(df_64["DXY_PROXY"].values))
            for cid in cids:
                r = np.diff(np.log(df_64[cid].values))
                if np.std(r) == 0 or np.std(dxy_r) == 0:
                    correlations["dxy_proxy"][cid] = 0.0
                else:
                    correlations["dxy_proxy"][cid] = float(scipy.stats.pearsonr(r, dxy_r)[0])
    
    return correlations

def compute_commodity_specific(close, dates, commodity_id, gold_close, dxy_corr):
    category = COMMODITIES[commodity_id]["category"]
    
    if commodity_id == "GOLD":
        inf_score = 1.0
    else:
        if len(close) >= 64 and len(gold_close) >= 64:
            r_comm = np.diff(np.log(close[-64:]))
            r_gold = np.diff(np.log(gold_close[-64:]))
            corr = scipy.stats.pearsonr(r_comm, r_gold)[0]
            inf_score = max(0.0, min(1.0, float(corr)))
        else:
            inf_score = 0.0
            
    n_1y = min(252, len(close))
    if n_1y > 0:
        mean_1y = np.mean(close[-n_1y:])
        std_1y = np.std(close[-n_1y:])
        p_pct = (close[-1] - mean_1y) / mean_1y * 100
        p_z = (close[-1] - mean_1y) / std_1y if std_1y > 0 else 0.0
    else:
        p_pct, p_z = 0.0, 0.0
        
    if category == "agriculture":
        contango = "N/A"
    else:
        if p_z > 1.5: contango = "Backwardation Likely"
        elif p_z > 0.5: contango = "Slight Backwardation"
        elif p_z < -1.5: contango = "Contango Likely"
        elif p_z < -0.5: contango = "Slight Contango"
        else: contango = "Normal"
        
    q_seas = None
    if category == "agriculture":
        close_series = pd.Series(close, index=dates)
        seas = compute_seasonality(close_series, dates)
        q_seas = seas["quarterly"]
        
    return {
        "inflation_hedge_score": float(inf_score),
        "dxy_correlation_3m": float(dxy_corr),
        "price_vs_1y_mean_pct": float(p_pct),
        "price_vs_1y_mean_zscore": float(p_z),
        "contango_indicator": contango,
        "quarterly_seasonality": q_seas
    }

def main():
    import time
    start = time.time()
    print("COM-QUANT Engine — starting...")

    raw_data = {}
    for cid, info in COMMODITIES.items():
        df = download_data(info["ticker"], 730)
        if df is not None and len(df) >= 60:
            raw_data[cid] = df
            print(f"  ✓ {cid}: {len(df)} rows")
        else:
            print(f"  ✗ {cid}: failed or insufficient data", file=sys.stderr)

    if not raw_data:
        print("Failed to download any data. Exiting.", file=sys.stderr)
        sys.exit(1)

    dxy_df = download_data(DXY_PROXY_TICKER, 730)
    dxy_series = dxy_df["Close"] if dxy_df is not None else None

    all_close = {cid: raw_data[cid]["Close"] for cid in raw_data}
    spreads      = compute_spreads(all_close)
    correlations = compute_correlations(all_close, dxy_series)

    data_out = {}
    gold_close_full = raw_data.get("GOLD", list(raw_data.values())[0])["Close"].values

    for cid, info in COMMODITIES.items():
        if cid not in raw_data:
            continue
        df_full = raw_data[cid]
        data_out[cid] = {}

        for win_id, wp in WINDOWS.items():
            df = df_full.iloc[-wp["lookback_days"]:]
            if len(df) < 30:
                continue

            close = df["Close"].values
            high  = df["High"].values  if "High"  in df.columns else None
            low   = df["Low"].values   if "Low"   in df.columns else None
            disp  = wp["display_days"]

            current_price = float(close[-1])
            change_1d = (close[-1]/close[-2] - 1)*100 if len(close)>=2 else 0.0
            change_5d = (close[-1]/close[-6] - 1)*100 if len(close)>=6 else 0.0

            last_date = df.index[-1]
            forecast_dates = []
            d = last_date + pd.Timedelta(days=1)
            while len(forecast_dates) < wp["forecast_days"]:
                if d.weekday() < 5:
                    forecast_dates.append(d.strftime("%Y-%m-%d"))
                d += pd.Timedelta(days=1)

            n = wp["forecast_days"]
            arima_r  = fit_arima(close, n)
            hw_r     = fit_holt_winters(close, n)
            mc_r     = fit_monte_carlo(close, n)
            ou_r     = fit_ou_process(close, n, is_natgas=(cid=="NATGAS"))
            svr_r    = fit_svr(close, n)
            rf_r     = fit_random_forest(close, n)
            ensemble = compute_ensemble(arima_r["forecast"], hw_r["forecast"], mc_r["p50"], ou_r["forecast"], svr_r["forecast"], rf_r["forecast"], MODEL_WEIGHTS)
            optimal  = find_optimal_entry(ensemble, forecast_dates, current_price)

            indicators  = compute_technical_indicators(close, high, low)
            statistics  = compute_statistics(close)
            risk        = compute_risk_metrics(close)
            close_s     = pd.Series(close, index=df.index)
            seasonality = compute_seasonality(close_s, df.index)

            dxy_corr = correlations["dxy_proxy"].get(cid, 0.0) if correlations else 0.0
            gold_arr = gold_close_full[-len(close):]
            if len(gold_arr) < len(close):
                gold_arr = np.concatenate([np.full(len(close)-len(gold_arr), gold_arr[0]), gold_arr])
            commodity_specific = compute_commodity_specific(close, df.index, cid, gold_arr, dxy_corr)

            data_out[cid][win_id] = {
                "meta": {
                    "id": cid, "name": info["name"], "ticker": info["ticker"],
                    "unit": info["unit"], "category": info["category"],
                    "current_price": round(current_price, 4),
                    "price_change_1d_pct": round(change_1d, 3),
                    "price_change_5d_pct": round(change_5d, 3),
                },
                "history": {
                    "dates": [d.strftime("%Y-%m-%d") for d in df.index[-disp:]],
                    "close":  [round(float(x),4) for x in close[-disp:]],
                    "open":   [round(float(x),4) for x in df["Open"].values[-disp:]],
                    "high":   [round(float(x),4) for x in df["High"].values[-disp:]] if "High" in df.columns else [],
                    "low":    [round(float(x),4) for x in df["Low"].values[-disp:]]  if "Low"  in df.columns else [],
                    "volume": [int(x) for x in df["Volume"].values[-disp:]]           if "Volume" in df.columns else [],
                },
                "forecast": {
                    "dates": forecast_dates,
                    "arima":            arima_r["forecast"],
                    "holt_winters":     hw_r["forecast"],
                    "monte_carlo_p5":   mc_r["p5"],
                    "monte_carlo_p25":  mc_r["p25"],
                    "monte_carlo_p50":  mc_r["p50"],
                    "monte_carlo_p75":  mc_r["p75"],
                    "monte_carlo_p95":  mc_r["p95"],
                    "ou_process":       ou_r["forecast"],
                    "svr":              svr_r["forecast"],
                    "rf":               rf_r["forecast"],
                    "ensemble":         ensemble,
                    "arima_ci_lower":   arima_r["ci_lower"],
                    "arima_ci_upper":   arima_r["ci_upper"],
                    **optimal,
                    "model_weights": MODEL_WEIGHTS,
                },
                "indicators":         indicators,
                "statistics":         statistics,
                "risk":               risk,
                "seasonality":        seasonality,
                "commodity_specific": commodity_specific,
            }
            print(f"  ✓ {cid}/{win_id}")

    output = {
        "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
        "categories":   CATEGORIES,
        "data":         data_out,
        "spreads":      spreads,
        "correlations": correlations,
    }

    with open("multi_data.json", "w") as f:
        json.dump(json_safe(output), f, indent=2)

    print(f"\nDone in {time.time()-start:.1f}s → multi_data.json written.")

if __name__ == "__main__":
    main()
