import numpy as np
import pandas as pd
from pathlib import Path

# ---------- documentary inputs (US$ million) ----------
C_HOME = 20_000                 # incremental 2-nm node in Taiwan
C_HOST = 65_000                 # Arizona complex cap-ex
L_DAY  = 48                     # 2 m $ / h downtime
S_BASE = 6_600 + 0.25 * C_HOST  # grant + full 25 % ITC  = 22 850

# Five-year PV of node revenue with 10 % growth, 8 % discount
disc = 1.08
growth = 1.10
R_g = sum((growth**t) / (disc**t) for t in range(1, 6)) * 10_000  # ≈ 64 367

pi_stay = lambda p: R_g - (p * L_DAY * 365) - C_HOME
pi_move = lambda p, b, s: b * R_g - (C_HOST - s)

# ---------- deterministic baseline ----------
baseline = pd.DataFrame({
    "P_dis": [0.10, 0.25],
    "Profit_Stay": [pi_stay(0.10), pi_stay(0.25)],
    "Profit_Move": [pi_move(0.10, 1.10, S_BASE), pi_move(0.25, 1.10, S_BASE)]
})
print("\nBaseline profits\n", baseline)

# ---------- Monte-Carlo over widened ranges ----------
N = 10_000
rng = np.random.default_rng(42)
P_sim   = rng.uniform(0.05, 0.40,  N)       # disruption 5–40 %
β_sim   = rng.uniform(1.05, 1.15,  N)       # cost premium 5–15 %
S_sim   = rng.uniform(S_BASE, 35_000, N)    # subsidy 22.85–35 bn

mc_df = pd.DataFrame({"P_dis": P_sim, "Beta": β_sim, "Subsidy": S_sim})
mc_df["Profit_Stay"] = pi_stay(mc_df["P_dis"])
mc_df["Profit_Move"] = pi_move(mc_df["P_dis"], mc_df["Beta"], mc_df["Subsidy"])
mc_df["Stay_Better"] = mc_df["Profit_Stay"] > mc_df["Profit_Move"]

threshold = (
    mc_df.groupby(pd.cut(mc_df["P_dis"], bins=np.linspace(0.05, 0.40, 8)))
         .mean()["Stay_Better"]
         .reset_index()
         .rename(columns={"Stay_Better": "Share_Stay_Better"})
)
print("\nThreshold summary\n", threshold)

# ---------- save to Excel ----------
out_xlsx = Path("chicken_game_results_v3.xlsx")
with pd.ExcelWriter(out_xlsx, engine="openpyxl") as xl:
    baseline.to_excel(xl, sheet_name="Baseline",  index=False)
    threshold.to_excel(xl, sheet_name="Thresholds", index=False)

print("\n Results saved to", out_xlsx.resolve())
