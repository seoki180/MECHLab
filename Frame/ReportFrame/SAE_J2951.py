import numpy as np
import pandas as pd
import os

class SAE_J2951:
    @staticmethod
    def calculate(time, Vr_kph, Vs_kph, ABCs_SI, Mass_kg, self=None):
        time = np.asarray(time, dtype=float)
        Vr_kph = np.asarray(Vr_kph, dtype=float)
        Vs_kph = np.asarray(Vs_kph, dtype=float)
        ABCs_SI = np.asarray(ABCs_SI, dtype=float)

        n = len(time)
        if not (len(Vr_kph) == len(Vs_kph) == n):
            raise ValueError("time, Vr_kph, Vs_kph must have the same length.")
        if n < 5:
            raise ValueError("Need ≥5 samples for the 5-point moving average.")

        # kph → m/s
        Vroll = Vr_kph / 3.6
        Vsched = Vs_kph / 3.6

        # Dyno coefficients
        F0_N = ABCs_SI[0]
        F1_N_per_kph = ABCs_SI[1]
        F2_N_per_kph2 = ABCs_SI[2]

        F1 = F1_N_per_kph * 3.6
        F2 = F2_N_per_kph2 * (3.6 * 3.6)
        F0 = F0_N

        ETW = Mass_kg
        Me = 1.015 * ETW

        Vd = SAE_J2951.five_point_ma_with_zero_ends(Vroll)
        Vt = SAE_J2951.five_point_ma_with_zero_ends(Vsched)
        Vd = SAE_J2951.five_point_ma_with_zero_ends(Vd)
        Vt = SAE_J2951.five_point_ma_with_zero_ends(Vt)

        Vd[Vd <= 0.03] = 0.0
        Vt[Vt <= 0.03] = 0.0

        # Accelerations
        ad = np.zeros(n)
        at = np.zeros(n)
        if n >= 3:
            ad[1:-1] = (Vd[2:] - Vd[:-2]) / 0.2
            at[1:-1] = (Vt[2:] - Vt[:-2]) / 0.2

        # Distances
        dd = np.zeros(n)
        dtm = np.zeros(n)
        if n >= 2:
            dd[1:] = Vd[1:] * 0.1
            dtm[1:] = Vt[1:] * 0.1
        Dd = np.cumsum(dd)
        Dt = np.cumsum(dtm)

        # Forces
        Frld = F0 + F1 * Vd + F2 * (Vd ** 2)
        Frlt = F0 + F1 * Vt + F2 * (Vt ** 2)
        Fid = Me * ad
        Fit = Me * at

        # Engine force
        Fengd = np.where(Frld + Fid >= 0.0, Frld + Fid, 0.0)
        Fengt = np.where(Frlt + Fit >= 0.0, Frlt + Fit, 0.0)

        # Work
        Wengd = Fengd * dd
        Wengt = Fengt * dtm

        # Cycle energy
        CEd = np.cumsum(Wengd)
        CEt = np.cumsum(Wengt)

        # Ratings
        ER = (CEd[-1] - CEt[-1]) / CEt[-1] * 100.0 if CEt[-1] != 0 else np.nan
        DR = (Dd[-1] - Dt[-1]) / Dt[-1] * 100.0 if Dt[-1] != 0 else np.nan
        EER = (1.0 - (((DR/100.0) + 1.0) / ((ER/100.0) + 1.0))) * 100.0 \
              if ((ER/100.0) + 1.0) != 0 else np.nan

        # ASC & ASCR
        ASCd = np.sum(np.abs(ad)) * 0.1
        ASCt = np.sum(np.abs(at)) * 0.1
        ASCR = (ASCd - ASCt) / ASCt * 100.0 if ASCt != 0 else np.nan

        # Inertial work
        IWd = np.sum(np.maximum(Fid, 0.0) * dd)
        IWt = np.sum(np.maximum(Fit, 0.0) * dtm)
        IWR = (IWd - IWt) / IWt * 100.0 if IWt != 0 else np.nan

        # RMS speed error
        spd_error = (Vd - Vt) ** 2
        RMSSE_mps = np.sqrt(np.mean(spd_error))
        RMSSE_mph = 2.237 * RMSSE_mps

        results = {
            "ER_pct": ER,
            "DR_pct": DR,
            "EER_pct": EER,
            "ASCR_pct": ASCR,
            "IWR_pct": IWR,
            "RMSSE_mph": RMSSE_mph,
        }

        # DQM
        keys = ["ER_pct", "DR_pct", "EER_pct", "ASCR_pct", "IWR_pct", "RMSSE_mph"]
        values = [abs(results[k]) for k in keys if k in results and pd.notna(results[k])]
        if len(values) == 6:
            results['DQM'] = sum(values) / 6
        else:
            results['DQM'] = np.nan

        return results

    @staticmethod
    def five_point_ma_with_zero_ends(x):
        x = np.asarray(x, dtype=float)
        y = np.zeros_like(x)
        if len(x) >= 2:
            y[1] = 0.0
        for i in range(2, len(x) - 2):
            y[i] = (x[i - 2] + x[i - 1] + x[i] + x[i + 1] + x[i + 2]) / 5.0
        if len(x) >= 2:
            y[-2] = 0.0
        y[-1] = 0.0
        return y


def main():
    """메인 테스트 함수"""
    print("=" * 60)
    print("SAE J2951 Calculator Test")
    print("=" * 60)

    # CSV 파일 읽기
    try:
        print(os.getcwd())
        df = pd.read_csv("./ReportFrame/data.csv", sep=None, engine="python")
        print(f"✓ CSV file loaded: {len(df)} rows")
    except FileNotFoundError:
        print("✗ Error: data.csv not found")
        return
    except Exception as e:
        print(f"✗ Error reading CSV: {e}")
        return

    # 컬럼 매핑
    cols = {c.lower(): c for c in df.columns}
    time_col = cols.get("time") or cols.get("t") or "time"
    vs_col = cols.get("vsched") or cols.get("vnom") or "Vsched"
    vr_col = cols.get("vroll") or cols.get("vact") or "Vroll"

    print(f"✓ Columns mapped: {time_col}, {vs_col}, {vr_col}")

    # 데이터 추출
    try:
        time_s = pd.to_numeric(df[time_col], errors="coerce").to_numpy()
        Vs_kph = pd.to_numeric(df[vs_col], errors="coerce").to_numpy()
        Vr_kph = pd.to_numeric(df[vr_col], errors="coerce").to_numpy()
        print(f"✓ Data extracted: {len(time_s)} points")
    except KeyError as e:
        print(f"✗ Error: Column not found - {e}")
        print(f"Available columns: {list(df.columns)}")
        return

    # 파라미터 설정
    F0_N = 35.5
    F1_N = 1.453
    F2_N = 0.03011
    mass_kg = 1726.9

    ABCs_SI = np.array([F0_N, F1_N, F2_N], dtype=float)
    Mass_kg = float(mass_kg)

    print(f"\n✓ Parameters:")
    print(f"  Mass: {Mass_kg} kg")
    print(f"  F0: {F0_N} N")
    print(f"  F1: {F1_N} N/kph")
    print(f"  F2: {F2_N} N/kph²")

    # 계산 수행
    print(f"\n⚙ Calculating SAE J2951 metrics...")
    try:
        results = SAE_J2951.calculate(time_s, Vr_kph, Vs_kph, ABCs_SI, Mass_kg)

        print("\n" + "=" * 60)
        print("RESULTS")
        print("=" * 60)

        print(f"\nEnergy Rating (ER):          {results['ER_pct']:8.4f} %")
        print(f"Distance Rating (DR):        {results['DR_pct']:8.4f} %")
        print(f"Energy Economy Rating (EER): {results['EER_pct']:8.4f} %")
        print(f"ASC Rating (ASCR):           {results['ASCR_pct']:8.4f} %")
        print(f"Inertial Work Rating (IWR):  {results['IWR_pct']:8.4f} %")
        print(f"RMS Speed Error (RMSSE):     {results['RMSSE_mph']:8.4f} mph")
        print(f"\n{'─' * 60}")
        print(f"Data Quality Metric (DQM):   {results['DQM']:8.4f}")

        # 품질 평가
        dqm = results['DQM']
        if dqm < 1.0:
            quality = "Excellent"
        elif dqm < 2.0:
            quality = "Good"
        else:
            quality = "Poor"

        print(f"Quality Assessment:          {quality}")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ Calculation error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()