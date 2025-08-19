import itertools
from typing import NamedTuple
import pandas as pd

# --- Fallback so the script works in any environment -----------------
try:                     
    from IPython.display import display
except ImportError:      
    def display(obj):
        if isinstance(obj, pd.DataFrame):
            print(obj.to_string(index=False))
        else:
            print(obj)
# --------------------------------------------------------------------

class Params(NamedTuple):
    grant: float
    itc_pv: float
    delta_LC: float
    delta_HC: float
    npv_node: float
    signal_cost: float
    clawback: float
    prior_LC: float
    state_security_value: float
    state_budget_cost: float
    credibility: float

p = Params(
    grant=6.6e9,            # Biden-Harris Admin., 2024
    itc_pv=5.0e9,           # PV of 25 % ITC
    delta_LC=0.05,          # TechInsights, 2025
    delta_HC=0.15,
    npv_node=40e9,          # 5-yr node NPV (internal estimate)
    signal_cost=3.5e8,      # Tom’s Hardware, 2024
    clawback=2.0e9,         # CSIS, 2023
    prior_LC=0.4,           # share of genuine low-cost movers
    state_security_value=3.0e9,
    state_budget_cost=1.0,  # 1 $ fiscal disutility per 1 $
    credibility=0.9         # milestone risk
)

def subsidy_value(params):        # expected value to firm
    return params.credibility * (params.grant + params.itc_pv)

SUBSIDY = subsidy_value(p)

def firm_payoff(params, firm_type, signal):
    delta = params.delta_LC if firm_type == "LC" else params.delta_HC
    guard = 0.0 if firm_type == "LC" else params.clawback
    relocation_penalty = delta * params.npv_node if signal else 0.0
    cost = params.signal_cost if signal else 0.0
    return lambda subsid: subsid - relocation_penalty - cost - guard

def state_payoff(params, giving_subsidy, sec_val):
    fiscal = params.grant + params.itc_pv if giving_subsidy else 0.0
    return sec_val - params.state_budget_cost * fiscal

def solve_game(params):
    firm_strats = list(itertools.product(("S", "W"), repeat=2))   # (LC, HC)
    state_strats = list(itertools.product(("H", "St"), repeat=2)) # (after S, after W)
    rows = []

    for fs in firm_strats:
        for ss in state_strats:
            a_LC, a_HC = fs
            a_S, a_W = ss

            prob_S = params.prior_LC*(a_LC=="S") + (1-params.prior_LC)*(a_HC=="S")
            prob_W = 1 - prob_S

            if prob_S:
                mu_LC_S = params.prior_LC*(a_LC=="S")/prob_S
            if prob_W:
                mu_LC_W = params.prior_LC*(a_LC=="W")/prob_W

            def state_act(obs):    # H or St
                return a_S if obs=="S" else a_W

            subsid_if_S = SUBSIDY if state_act("S")=="H" else 0.0
            subsid_if_W = SUBSIDY if state_act("W")=="H" else 0.0

            u_LC = firm_payoff(p,"LC",a_LC=="S")(subsid_if_S if a_LC=="S" else subsid_if_W)
            u_HC = firm_payoff(p,"HC",a_HC=="S")(subsid_if_S if a_HC=="S" else subsid_if_W)

            # unilateral deviations
            dev_LC = firm_payoff(p,"LC",a_LC!="S")(subsid_if_W if a_LC=="S" else subsid_if_S)
            dev_HC = firm_payoff(p,"HC",a_HC!="S")(subsid_if_W if a_HC=="S" else subsid_if_S)
            firm_BR = (u_LC >= dev_LC) and (u_HC >= dev_HC)

            # State best-response check
            def state_expected(obs, mu_LC):
                sec_val = p.state_security_value if obs=="S" else 0.0
                return (state_payoff(p, True,  sec_val),
                        state_payoff(p, False, sec_val))

            state_BR = True
            if prob_S:
                uH,uSt = state_expected("S",mu_LC_S)
                if (a_S=="H" and uH < uSt) or (a_S=="St" and uSt < uH): state_BR=False
            if prob_W:
                uH,uSt = state_expected("W",mu_LC_W)
                if (a_W=="H" and uH < uSt) or (a_W=="St" and uSt < uH): state_BR=False

            if firm_BR and state_BR:
                rows.append(dict(firm_strategy=fs,
                                 state_strategy=ss,
                                 payoff_LC=round(u_LC/1e9,2),
                                 payoff_HC=round(u_HC/1e9,2)))
    return pd.DataFrame(rows)

df = solve_game(p)
display(df)
