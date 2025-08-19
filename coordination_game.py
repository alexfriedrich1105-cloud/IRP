from itertools import product
from math import exp, log

# ----- Parameters -----
N_PLAYERS = 5
R = 40.0             # $bn PV over 5 years
s = 1.0              # $bn per firm (site-specific), excludes supplier subsidies
delta0 = 0.10
alpha = log(2) / 4.0 # ≈ 0.173286795, ensures delta(4) = 0.05
c0 = 3               # complements currently present (chemicals, gases, EUV support)
C_MAX = 5            # total complements when fully built out

# ----- Core functions -----
def delta(c: int) -> float:
    """Host-site operating premium as a function of complements c (0..C_MAX)."""
    return delta0 * exp(-alpha * c)

def complements(movers: int) -> int:
    """Available complements as a function of number of movers."""
    c = c0 + movers
    return C_MAX if c > C_MAX else c

def payoff_H(movers_other: int) -> float:
    """Payoff to a player if they choose H, given number of OTHER players choosing H."""
    # If I move, movers_total = movers_other + 1
    c = complements(movers_other + 1)
    return R - delta(c) * R + s

def payoff_T(movers_other: int) -> float:
    """Payoff to a player if they choose T, given number of OTHER players choosing H."""
    return R

def best_response_is_H(movers_other: int) -> bool:
    """Whether H is (weakly) a best response against 'movers_other' others choosing H."""
    return payoff_H(movers_other) >= payoff_T(movers_other)

# ----- Enumerate pure-strategy NE -----
def find_pure_NE():
    """
    Enumerate all 2^N profiles.
    A profile is a tuple of 0/1 with 1=H (move), 0=T (stay).
    Check that each player's action is a best response to others.
    """
    NE = []
    for profile in product([0, 1], repeat=N_PLAYERS):
        # Count others choosing H for each player
        is_NE = True
        total_H = sum(profile)
        for i, a in enumerate(profile):
            others_H = total_H - a
            wants_H = best_response_is_H(others_H)
            if a == 1 and not wants_H:
                is_NE = False; break
            if a == 0 and wants_H:
                is_NE = False; break
        if is_NE:
            NE.append(profile)
    return NE

def critical_mass():
    """
    Compute complements threshold c* solving delta(c*) = s/R.
    Then translate to movers m* = max(0, c* - c0). This may exceed C_MAX - c0.
    """
    delta_star = s / R
    # Solve delta0 * e^{-alpha c*} = delta_star => c* = (ln(delta0) - ln(delta_star)) / alpha
    c_star = (log(delta0) - log(delta_star)) / alpha
    m_star = max(0.0, c_star - c0)
    return delta_star, c_star, m_star

def main():
    print("="*72)
    print("Coordination Game — Semiconductor Cluster (Calibrated)")
    print("="*72)
    print(f"N={N_PLAYERS}, R={R:.2f} bn (PV 5y), s={s:.2f} bn, delta0={delta0:.3f}, alpha={alpha:.6f}")
    print(f"c0={c0}, C_MAX={C_MAX}")
    print(f"delta(3)={delta(3):.4%}, delta(4)={delta(4):.4%}, delta(5)={delta(5):.4%}")
    ds, c_star, m_star = critical_mass()
    print(f"Indifference premium delta* = s/R = {ds:.4%}")
    print(f"Complement threshold c* ≈ {c_star:.2f} -> movers needed m* ≈ {m_star:.2f} (cap {C_MAX - c0})")
    print("-"*72)
    NE = find_pure_NE()
    if not NE:
        print("No pure-strategy Nash equilibria found.")
    else:
        print(f"Pure-strategy Nash equilibria (1=H, 0=T), count={len(NE)}:")
        for prof in NE:
            print("  ", prof)
    print("-"*72)
    # Sanity: show best responses by # of others moving
    print("Best response map (others moving -> choose H?):")
    for others in range(N_PLAYERS):
        print(f"  others={others}: {'H' if best_response_is_H(others) else 'T'} "
              f"(pi_H={payoff_H(others):.2f}, pi_T={payoff_T(others):.2f})")

if __name__ == "__main__":
    main()
