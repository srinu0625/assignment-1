import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import time
from colorama import Fore, Style, init

# ==================== INIT ====================
init(autoreset=True)

# ---- User I/O (unchanged) ----
file1 = r"D:\Data\BR Jun25_15min.csv"
file2 = r"D:\Data\CL Jun25_15min.csv"

# NOTE: Your comments said ES/NQ earlier; that was wrong.
# BR (Brent) & CL (WTI) both have 1,000-barrel contract multipliers.
contract_size_br = 1000
contract_size_cl = 1000

# ---- Strategy params ----
window_rank = 120          # lookback for pseudo-observations (ranks)
entry_thresh = 2.5         # enter when copula Z exceeds this
exit_thresh  = 0.0         # exit around mean
stop_thresh  = 4.0         # hard stop
use_logret   = True        # use log returns for copula fit

# ==================== HELPERS ====================
def norm_ppf(u):
    """
    Inverse standard normal CDF (Φ^-1) using Acklam's rational approximation.
    Vectorized for numpy arrays. Works well for u in (0,1).
    """
    u = np.asarray(u)
    # Guard against 0/1 (clip into open interval)
    u = np.clip(u, 1e-12, 1 - 1e-12)

    # Coefficients for central region
    a = [ -3.969683028665376e+01,  2.209460984245205e+02,
          -2.759285104469687e+02,  1.383577518672690e+02,
          -3.066479806614716e+01,  2.506628277459239e+00 ]
    b = [ -5.447609879822406e+01,  1.615858368580409e+02,
          -1.556989798598866e+02,  6.680131188771972e+01,
          -1.328068155288572e+01 ]
    # Coefficients for tails
    c = [ -7.784894002430293e-03, -3.223964580411365e-01,
          -2.400758277161838e+00, -2.549732539343734e+00,
           4.374664141464968e+00,  2.938163982698783e+00 ]
    d = [  7.784695709041462e-03,  3.224671290700398e-01,
           2.445134137142996e+00,  3.754408661907416e+00 ]

    plow  = 0.02425
    phigh = 1 - plow
    x = np.empty_like(u)

    # Lower tail
    mask = u < plow
    if mask.any():
        q = np.sqrt(-2*np.log(u[mask]))
        x[mask] = (((((c[0]*q + c[1])*q + c[2])*q + c[3])*q + c[4])*q + c[5]) / \
                   ((((d[0]*q + d[1])*q + d[2])*q + d[3])*q + 1)

    # Central region
    mask = (u >= plow) & (u <= phigh)
    if mask.any():
        q = u[mask] - 0.5
        r = q*q
        x[mask] = (((((a[0]*r + a[1])*r + a[2])*r + a[3])*r + a[4])*r + a[5]) * q / \
                   (((((b[0]*r + b[1])*r + b[2])*r + b[3])*r + b[4])*r + 1)

    # Upper tail
    mask = u > phigh
    if mask.any():
        q = np.sqrt(-2*np.log(1 - u[mask]))
        x[mask] = -(((((c[0]*q + c[1])*q + c[2])*q + c[3])*q + c[4])*q + c[5]) / \
                    ((((d[0]*q + d[1])*q + d[2])*q + d[3])*q + 1)

    return x

def rolling_rank_pseudo_obs(s: pd.Series, win: int) -> pd.Series:
    """
    For each time t, compute the rank of the *current* value within the last `win` values,
    then map to (0,1) via (rank) / (win + 1). This gives PIT-like pseudo-observations.
    """
    def rank_last(window_vals):
        x = pd.Series(window_vals)
        return x.rank(method='average').iloc[-1]  # rank of the last element within window

    r = s.rolling(win, min_periods=win).apply(rank_last, raw=False)
    return r / (win + 1.0)

def print_entry(t, z, side, BR, CL):
    side_colored = side.replace("LONG", f"{Fore.GREEN}LONG{Style.RESET_ALL}") \
                       .replace("SHORT", f"{Fore.RED}SHORT{Style.RESET_ALL}")
    print(f"{t} | ENTRY ({side_colored}) | CopulaZ = {z:.2f}")
    if "LONG BR" in side:
        print(f"   BR: {Fore.GREEN}{BR:.2f}{Style.RESET_ALL}")
        print(f"   CL: {Fore.RED}{CL:.2f}{Style.RESET_ALL}")
    else:
        print(f"   BR: {Fore.RED}{BR:.2f}{Style.RESET_ALL}")
        print(f"   CL: {Fore.GREEN}{CL:.2f}{Style.RESET_ALL}")
    print("-" * 60)

def print_exit(t, z, side, e_br, x_br, e_cl, x_cl, pnl):
    side_colored = side.replace("LONG", f"{Fore.GREEN}LONG{Style.RESET_ALL}") \
                       .replace("SHORT", f"{Fore.RED}SHORT{Style.RESET_ALL}")
    print(f"{t} | EXIT ({side_colored}) | CopulaZ = {z:.2f}")
    print(f"   BR: {e_br:.2f} → {x_br:.2f}")
    print(f"   CL: {e_cl:.2f} → {x_cl:.2f}")
    pnl_color = Fore.GREEN if pnl > 0 else Fore.RED
    print(f"   PnL: {pnl_color}{pnl:.2f}{Style.RESET_ALL}")
    print("=" * 60)

# ==================== LOAD & PREP ====================
df1 = pd.read_csv(file1)
df2 = pd.read_csv(file2)

df1.columns = df1.columns.str.strip()
df2.columns = df2.columns.str.strip()

# parse your timestamp format dd-mm-YYYY HH.MM
df1['Date(GMT)'] = pd.to_datetime(df1['Date(GMT)'], format='%d-%m-%Y %H.%M')
df2['Date(GMT)'] = pd.to_datetime(df2['Date(GMT)'], format='%d-%m-%Y %H.%M')

df1 = df1.set_index('Date(GMT)')[['Close']].rename(columns={'Close': 'BR'})
df2 = df2.set_index('Date(GMT)')[['Close']].rename(columns={'Close': 'CL'})

df = df1.join(df2, how='inner').dropna()

# For copula fitting we want something stationary -> returns.
if use_logret:
    df['r_br'] = np.log(df['BR']).diff()
    df['r_cl'] = np.log(df['CL']).diff()
else:
    df['r_br'] = df['BR'].pct_change()
    df['r_cl'] = df['CL'].pct_change()

df = df.dropna()

# ==================== COPULA FEATURES ====================
# 1) Pseudo-observations via rolling ranks on returns
u_br = rolling_rank_pseudo_obs(df['r_br'], window_rank)
u_cl = rolling_rank_pseudo_obs(df['r_cl'], window_rank)

# 2) Map uniforms to normal scores (Gaussian copula latent space)
x_br = pd.Series(norm_ppf(u_br.values), index=df.index, name='x_br')
y_cl = pd.Series(norm_ppf(u_cl.values), index=df.index, name='y_cl')

# 3) Rolling correlation between latent normals gives Gaussian copula rho
rho = x_br.rolling(window_rank, min_periods=window_rank).corr(y_cl)
rho = rho.clip(lower=-0.999, upper=0.999).shift(1)  # shift to avoid look-ahead

# 4) Copula-conditional Z for CL given BR:
#    Z_t = (y_t - rho_t * x_t) / sqrt(1 - rho_t^2)
den = np.sqrt(1 - rho*rho)
copula_z = (y_cl - rho * x_br) / den
df['copula_z'] = copula_z

# ==================== BACKTEST (same style as your script) ====================
position = 0      # +1: LONG BR/SHORT CL ; -1: SHORT BR/LONG CL ; 0: flat
entry_br = entry_cl = 0.0
total_pnl = 0.0
pnl_list = []

df['position'] = 0

for t, row in df.iterrows():
    z = row['copula_z']
    if np.isnan(z):
        continue

    br = row['BR']
    cl = row['CL']

    if position == 0:
        # If CL is "too high" relative to BR given the copula -> z large positive -> Short CL / Long BR
        if z > entry_thresh:
            position = -1
            entry_br, entry_cl = br, cl
            print_entry(t, z, "SHORT CL / LONG BR", br, cl)
            time.sleep(0.05)

        # If CL is "too low" relative to BR -> z very negative -> Long CL / Short BR
        elif z < -entry_thresh:
            position = +1
            entry_br, entry_cl = br, cl
            print_entry(t, z, "LONG CL / SHORT BR", br, cl)
            time.sleep(0.05)

    elif position == +1:  # LONG CL / SHORT BR
        if z >= exit_thresh or z <= -stop_thresh:
            pnl_br = -(br - entry_br) * contract_size_br
            pnl_cl =  (cl - entry_cl) * contract_size_cl
            pnl = pnl_br + pnl_cl
            total_pnl += pnl
            pnl_list.append(pnl)
            print_exit(t, z, "LONG CL / SHORT BR", entry_br, br, entry_cl, cl, pnl)
            position = 0

    elif position == -1:  # SHORT CL / LONG BR
        if z <= exit_thresh or z >=  stop_thresh:
            pnl_br =  (br - entry_br) * contract_size_br
            pnl_cl = -(cl - entry_cl) * contract_size_cl
            pnl = pnl_br + pnl_cl
            total_pnl += pnl
            pnl_list.append(pnl)
            print_exit(t, z, "SHORT CL / LONG BR", entry_br, br, entry_cl, cl, pnl)
            position = 0

    df.loc[t, 'position'] = position

# ==================== SUMMARY ====================
wins = sum(p > 0 for p in pnl_list)
losses = sum(p <= 0 for p in pnl_list)
total_trades = len(pnl_list)
win_rate = (wins / total_trades * 100) if total_trades else 0.0
loss_rate = 100 - win_rate


print("\n==== SUMMARY ====")
print(f"Total Trades            : {total_trades}")
print(f"Total PnL               : {total_pnl:.2f}")
print(f"Winning Trades          : {Fore.GREEN}{wins}{Style.RESET_ALL}")
print(f"Losing Trades           : {Fore.RED}{losses}{Style.RESET_ALL}")
print(f"Win Rate                : {Fore.GREEN}{win_rate:.2f}%{Style.RESET_ALL}")
print(f"Failure Rate            : {Fore.RED}{loss_rate:.2f}%{Style.RESET_ALL}")
if pnl_list:
    print(f"Max Profit Per trade    : {Fore.GREEN}{max(pnl_list):.2f}{Style.RESET_ALL}")
    print(f"Max Loss Per trade      : {Fore.RED}{min(pnl_list):.2f}{Style.RESET_ALL}")

# ==== Plot ====
plt.figure(figsize=(14, 6))

# Z-score plot
plt.subplot(2, 1, 1)
plt.plot(df['zscore'], label='Z-Score')
plt.axhline(entry_thresh, color='red', linestyle='--', label='Entry Threshold')
plt.axhline(-entry_thresh, color='green', linestyle='--')
plt.axhline(stop_thresh, color='darkred', linestyle=':')
plt.axhline(-stop_thresh, color='darkgreen', linestyle=':')
plt.axhline(0, color='black', linestyle='-')
plt.title('Z-Score')
plt.legend()

# Cumulative PnL plot
plt.subplot(2, 1, 2)
plt.plot(pd.Series(pnl_list).cumsum(), label='Cumulative PnL', color='blue')
plt.title('Cumulative PnL BR and CL')
plt.legend()

plt.tight_layout()
plt.show()
