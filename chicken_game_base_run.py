import numpy as np
import pandas as pd
from pathlib import Path

# --- baseline point estimates from documentary sources (values in US$ million) ---
C_home = 30_000     # Domestic cap-ex  (Taipei Times, 2024)
C_host = 65_000     # Arizona complex  (TSMC CHIPS term-sheet, 2024)
beta   = 1.10       # 10 % cost premium (TechInsights, 2025)
L_day  = 24         # Downtime loss     (Air Monitor, 2025)
R      = 10_000     # Normalised annual revenue
S      = 6_600      # CHIPS grant       (TSMC, 2024)

def π_stay(P_dis):
    return R - (P_dis * L_day * 365) - C_home          # EQ (1)

def π_move(P_dis, β=beta, sub=S):
    return β * R - (C_host - sub)                      # EQ (2)

# --- deterministic baseline at P_dis = 0.10 and 0.25 ---
for p in (0.10, 0.25):
    print(f"P_dis = {p:4.2f}  |  Stay: {π_stay(p):,.0f}   Move: {π_move(p):,.0f}")

# --- Monte-Carlo sensitivity ------------------------------------------------------
N = 10_000
rng = np.random.default_rng(42)

P_sim   = rng.uniform(0.1, 0.25,  N)      
β_sim   = np.full(N, 1.10)      
S_sim   = np.full(N, 6_600)    

stay = R - (P_sim * L_day * 365) - C_home
move = β_sim * R - (C_host - S_sim)

df = pd.DataFrame({"P_dis": P_sim, "StayBetter": stay > move})
threshold = df.groupby(pd.cut(df["P_dis"], bins=np.linspace(0.05, 0.40, 8))).mean()["StayBetter"]

print("\nShare of simulations where staying beats moving, by disruption-probability bin:")
print(threshold)

baseline_df = pd.DataFrame({
    "P_dis": [0.10, 0.25],
    "Profit_Stay": [π_stay(0.10), π_stay(0.25)],
    "Profit_Move": [π_move(0.10), π_move(0.25)]
})

threshold_df = threshold.reset_index().rename(
    columns={"P_dis": "P_dis_bin", 0: "Share_Stay_Better"}
)

out_xlsx = Path("chicken_game_results.xlsx")
with pd.ExcelWriter(out_xlsx, engine="xlsxwriter") as xl:
    baseline_df.to_excel(xl, sheet_name="Baseline", index=False)
    threshold_df.to_excel(xl, sheet_name="Thresholds", index=False)

print("\nResults saved to", out_xlsx.resolve())