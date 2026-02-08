# SAE J2951 Calculations — SI internal units, RMSSE reported in mph
# Input CSV: time, Vsched, Vroll (sec, kph, kph)
# Internally: speeds in m/s, forces in N, mass in kg, work in J
# Output metrics: ER, DR, EER, ASCR, IWR in %, RMSSE in mph
### ACTYON2 ####

import numpy as np
import pandas as pd
import csv
import argparse
from typing import Dict, Optional

def sae_j2951_SI(
    time: np.ndarray,
    Vr_kph: np.ndarray,        # driven/actual [kph]
    Vs_kph: np.ndarray,        # scheduled     [kph]
    ABCs_SI: np.ndarray,       # [F0_N, F1_N_per_kph, F2_N_per_kph2]
    Mass_kg: float,            # ETW in kg
    Name: str = "",
    ID: str = "",
    NEC: Optional[float] = None,
    FC: Optional[float] = None,
    save_path: Optional[str] = None,   # e.g., 'trial.xls' (tab-delimited)
) -> Dict[str, float]:

    time = np.asarray(time, dtype=float)
    Vr_kph = np.asarray(Vr_kph, dtype=float)
    Vs_kph = np.asarray(Vs_kph, dtype=float)
    ABCs_SI = np.asarray(ABCs_SI, dtype=float)

    n = len(time)
    if not (len(Vr_kph) == len(Vs_kph) == n):
        raise ValueError("time, Vr_kph, Vs_kph must have the same length.")
    if n < 5:
        raise ValueError("Need ≥5 samples for the 5-point moving average.")

    # --- kph → m/s ---------------------------------------------------------
    Vroll  = Vr_kph / 3.6
    Vsched = Vs_kph / 3.6

    # --- Dyno coefficients in SI ------------------------------------------
    # User provides:
    #   F0_N          [N]
    #   F1_N_per_kph  [N/kph]
    #   F2_N_per_kph2 [N/kph^2]
    #
    # Convert F1, F2 to N/(m/s) and N/(m/s^2) since V is in m/s:
    #
    # 1 kph = (1/3.6) m/s  =>  dV_kph = 3.6 * dV_mps
    # F1 [N/kph] * dV_kph = F1 * 3.6 * dV_mps
    # => F1_mps = F1_kph * 3.6  [N/(m/s)]
    #
    # Similarly for F2:
    # F2 [N/kph^2] * (dV_kph)^2 = F2 * (3.6^2) * (dV_mps)^2
    # => F2_mps2 = F2_kph2 * (3.6^2) [N/(m/s^2)]
    F0_N          = ABCs_SI[0]
    F1_N_per_kph  = ABCs_SI[1]
    F2_N_per_kph2 = ABCs_SI[2]

    F1 = F1_N_per_kph  * 3.6            # N/(m/s)
    F2 = F2_N_per_kph2 * (3.6 * 3.6)    # N/(m/s^2)
    F0 = F0_N                            # N

    # --- Mass: kg; Effective test mass ------------------------------------
    ETW = Mass_kg
    Me  = 1.015 * ETW

    # --- Two-pass 5-point moving average with zeroed endpoints ------------
    def five_point_ma_with_zero_ends(x: np.ndarray) -> np.ndarray:
        x = np.asarray(x, dtype=float)
        y = np.zeros_like(x)
        if len(x) >= 2:
            y[1] = 0.0
        for i in range(2, len(x) - 2):
            y[i] = (x[i-2] + x[i-1] + x[i] + x[i+1] + x[i+2]) / 5.0
        if len(x) >= 2:
            y[-2] = 0.0
        y[-1] = 0.0
        return y

    Vd = five_point_ma_with_zero_ends(Vroll)
    Vt = five_point_ma_with_zero_ends(Vsched)
    Vd = five_point_ma_with_zero_ends(Vd)
    Vt = five_point_ma_with_zero_ends(Vt)

    # --- Truncate very low speeds (m/s) -----------------------------------
    Vd[Vd <= 0.03] = 0.0
    Vt[Vt <= 0.03] = 0.0

    # --- Accelerations (m/s^2), central diff, dt = 0.1 s ------------------
    ad = np.zeros(n)
    at = np.zeros(n)
    if n >= 3:
        ad[1:-1] = (Vd[2:] - Vd[:-2]) / 0.2
        at[1:-1] = (Vt[2:] - Vt[:-2]) / 0.2

    # --- Distances (m) with fixed dt = 0.1 s ------------------------------
    dd  = np.zeros(n)
    dtm = np.zeros(n)
    if n >= 2:
        dd[1:]  = Vd[1:] * 0.1
        dtm[1:] = Vt[1:] * 0.1
    Dd = np.cumsum(dd)
    Dt = np.cumsum(dtm)

    # --- Forces (N) --------------------------------------------------------
    Frld = F0 + F1 * Vd + F2 * (Vd ** 2)
    Frlt = F0 + F1 * Vt + F2 * (Vt ** 2)
    Fid = Me * ad
    Fit = Me * at

    # --- Engine force (positive-only) -------------------------------------
    Fengd = np.where(Frld + Fid >= 0.0, Frld + Fid, 0.0)
    Fengt = np.where(Frlt + Fit >= 0.0, Frlt + Fit, 0.0)

    # --- Work (J) ----------------------------------------------------------
    Wengd = Fengd * dd
    Wengt = Fengt * dtm

    # --- Cycle energy (J) --------------------------------------------------
    CEd = np.cumsum(Wengd)
    CEt = np.cumsum(Wengt)

    # --- Ratings -----------------------------------------------------------
    ER  = (CEd[-1] - CEt[-1]) / CEt[-1] * 100.0 if CEt[-1] != 0 else np.nan
    DR  = (Dd[-1] - Dt[-1]) / Dt[-1] * 100.0     if Dt[-1]  != 0 else np.nan
    EER = (1.0 - (((DR/100.0) + 1.0) / ((ER/100.0) + 1.0))) * 100.0 \
          if ((ER/100.0) + 1.0) != 0 else np.nan

    # --- ASC & ASCR --------------------------------------------------------
    ASCd = np.sum(np.abs(ad)) * 0.1
    ASCt = np.sum(np.abs(at)) * 0.1
    ASCR = (ASCd - ASCt) / ASCt * 100.0 if ASCt != 0 else np.nan
    ASCtime = ASCt / (n * 0.1) if n > 0 else np.nan  # not used in results

    # --- Inertial work & IWR (inertial-only, positive work portions) -------
    IWd = np.sum(np.maximum(Fid, 0.0) * dd)
    IWt = np.sum(np.maximum(Fit, 0.0) * dtm)
    IWR = (IWd - IWt) / IWt * 100.0 if IWt != 0 else np.nan

    # --- RMS speed error: J2951 requires mph -------------------------------
    # Internal speeds Vd, Vt are m/s.
    # RMSSE_mps = sqrt(mean((Vd - Vt)^2))
    # Convert to mph: 1 m/s = 2.237 mph
    spd_error = (Vd - Vt) ** 2
    RMSSE_mps = np.sqrt(np.mean(spd_error))
    RMSSE_mph = 2.237 * RMSSE_mps

    # --- More metrics (SI internal) ----------------------------------------
    CEdist = CEt[-1] / Dt[-1] if Dt[-1] != 0 else np.nan
    IWF    = IWt / CEt[-1] if CEt[-1] != 0 else np.nan
    RLWF   = 1.0 - IWF if np.isfinite(IWF) else np.nan

    # Power & APC
    Pt = np.zeros(n)
    if n >= 2:
        Pt[1:] = Fengt[1:] * Vt[1:]
    powert_deriv_tmp = np.zeros(n)
    if n >= 3:
        powert_deriv_tmp[1:-1] = np.abs((Pt[2:] - Pt[:-2]) / 0.2)
    powert_deriv_tmp[-1] = Pt[-1]
    APC = np.sum(powert_deriv_tmp) * 0.1
    APCtime = APC / (n * 0.1) if n > 0 else np.nan  # not used in results

    results = {
        "ER_pct":     ER,
        "DR_pct":     DR,
        "EER_pct":    EER,
        "ASCR_pct":   ASCR,
        "IWR_pct":    IWR,
        "RMSSE_mph":  RMSSE_mph,
        # You could also expose SI internals if you like:
        # "RMSSE_mps":  RMSSE_mps,
        # "CEdist_J_per_m": CEdist,
        # "IWF": IWF,
        # "RLWF": RLWF,
        # "ASCtime": ASCtime,
        # "APC": APC,
        # "APCtime": APCtime,
    }

    # Optional “trial.xls” append (tab-delimited)
    if save_path is not None:
        row = [
            str(Name), str(ID),
            f"{results['ER_pct']}",
            f"{results['DR_pct']}",
            f"{results['EER_pct']}",
            f"{results['ASCR_pct']}",
            f"{results['IWR_pct']}",
            f"{results['RMSSE_mph']}",
            "" if NEC is None else f"{NEC}",
            "" if FC  is None else f"{FC}",
            "",
        ]
        with open(save_path, "a", newline="") as f:
            csv.writer(f, delimiter="\t").writer.writerow(row)

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Run SAE J2951 (SI internal) from CSV: time, Vsched, Vroll (sec, kph, kph)."
    )
    parser.add_argument("--file", default="data.csv",
                        help="Input CSV (default: data.csv)")
    parser.add_argument("--name", default="ACTYON2?")
    parser.add_argument("--id", default="run-1")
    parser.add_argument("--save", default="",
                        help="Optional tab-delimited output (e.g., trial.xls).")

    # ABCs in SI: F0 [N], F1 [N/kph], F2 [N/kph^2]
    # Defaults taken from your comments: 21.098, 0.2823, 0.045611
    parser.add_argument("--F0_N", type=float, default=35.5)
    parser.add_argument("--F1_N_per_kph", type=float, default=1.453)
    parser.add_argument("--F2_N_per_kph2", type=float, default=0.03011)

    # Mass in kg
    parser.add_argument("--mass_kg", type=float, default=1726.9)

    args = parser.parse_args()

    # 1) Read CSV; auto-detect delimiter & tolerate header variants
    df = pd.read_csv(args.file, sep=None, engine="python")

    # Accept either ['Vsched','Vroll'] or ['Vnom','Vact'] as speed columns
    cols = {c.lower(): c for c in df.columns}
    # Required time column
    time_col = cols.get("time") or cols.get("t") or "time"
    # Scheduled speed
    vs_col = cols.get("vsched") or cols.get("vnom") or "Vsched"
    # Driven/actual speed
    vr_col = cols.get("vroll") or cols.get("vact") or "Vroll"

    time_s = pd.to_numeric(df[time_col], errors="coerce").to_numpy()
    Vs_kph = pd.to_numeric(df[vs_col],  errors="coerce").to_numpy()
    Vr_kph = pd.to_numeric(df[vr_col],  errors="coerce").to_numpy()

    # 2) Coeffs & mass (SI)
    ABCs_SI = np.array([args.F0_N,
                        args.F1_N_per_kph,
                        args.F2_N_per_kph2], dtype=float)
    Mass_kg = float(args.mass_kg)

    # 3) Run
    save_path = args.save if args.save.strip() else None
    out = sae_j2951_SI(time_s, Vr_kph, Vs_kph,
                       ABCs_SI, Mass_kg,
                       Name=args.name, ID=args.id,
                       save_path=save_path)

    # 4) Print results (values only, like your original)
    rounded = {k: (round(v, 6) if pd.notna(v) else None) for k, v in out.items()}
    for k, v in rounded.items():
        print(f"{v}")

    # 5) DQM calculation
    keys = ["ER_pct", "DR_pct", "EER_pct", "ASCR_pct", "IWR_pct", "RMSSE_mph"]
    values = [abs(out[k]) for k in keys if k in out and pd.notna(out[k])]
    if len(values) == 6:
        DQM = sum(values) / 6
    else:
        DQM = np.nan
    print(f"{DQM:.6f}")

    # Optional save of DQM as well
    if save_path is not None:
        header = ["ER_pct", "DR_pct", "EER_pct", "ASCR_pct", "RMSSE_mph", "IWR_pct", "DQM"]
        row = [args.name, args.id] + [out.get(k, "") for k in keys] + [DQM]
        with open(save_path, "a", newline="") as f:
            csv.writer(f, delimiter="\t").writer.writerow(row)


if __name__ == "__main__":
    main()
