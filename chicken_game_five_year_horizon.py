import numpy as np
import pandas as pd
from pathlib import Path

# -------- adjusted documentary inputs (US$ million) -------------
# 1. five-year PV of revenue at 8 % discount:
five_year_factor = sum((1/1.08)**t for t in range(1,6))   # ≈ 3.992
R = 10_000 * five_year_factor     # ≈ 39 920

# 2. incremental cap-ex for an additional 2-nm node in Taiwan
C_HOME = 20_000

# 3. Arizona cap-ex unchanged, but subsidy now includes 25 % ITC
C_HOST = 65_000
S_BASE = 6_600 + 0.25 * C_HOST     # 22 850

# 4. Other parameters
BETA   = 1.10                      # wafer cost premium
L_DAY  = 24                        # downtime loss per day

# -------- payoff functions ---------------------------------------
pi_stay = lambda p: R - (p * L_DAY * 365) - C_HOME
pi_move = lambda p, b=BETA, s=S_BASE: b * R - (C_HOST - s)

# -------- deterministic baseline at P=0.10 and 0.25 --------------
baseline_df = pd.DataFrame({
    "P_dis":       [0.10, 0.25],
    "Profit_Stay": [pi_stay(0.10), pi_stay(0.25)],
    "Profit_Move": [pi_move(0.10), pi_move(0.25)]
})
print("\nBaseline profits\n", baseline_df)

# -------- Monte-Carlo sensitivity --------------------------------
N       = 10_000
rng     = np.random.default_rng(42)
P_sim   = rng.uniform(0.05, 0.40, N)           # disruption 5-40 %
beta_sim= rng.uniform(1.10, 1.20, N)           # cost premium 10-20 %
S_sim   = rng.uniform(S_BASE, 30_000, N)       # subsidy 22.85-30 bn

mc_df = pd.DataFrame({"P_dis": P_sim, "Beta": beta_sim, "Subsidy": S_sim})
mc_df["Profit_Stay"] = pi_stay(mc_df["P_dis"])
mc_df["Profit_Move"] = mc_df["Beta"] * R - (C_HOST - mc_df["Subsidy"])
mc_df["Stay_Better"] = mc_df["Profit_Stay"] > mc_df["Profit_Move"]

threshold_df = (
    mc_df.groupby(pd.cut(mc_df["P_dis"], bins=np.linspace(0.05, 0.40, 8)))
         .mean()["Stay_Better"]
         .reset_index()
         .rename(columns={"Stay_Better": "Share_Stay_Better"})
)
print("\nThreshold summary\n", threshold_df)

# -------- save both tables to Excel ------------------------------
out_xlsx = Path("chicken_game_results_v2.xlsx")
with pd.ExcelWriter(out_xlsx, engine="openpyxl") as writer:
    baseline_df.to_excel(writer, sheet_name="Baseline", index=False)
    threshold_df.to_excel(writer, sheet_name="Thresholds", index=False)

print("\n Results saved to", out_xlsx.resolve())
