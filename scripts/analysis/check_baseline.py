#!/usr/bin/env python3
"""
check_baseline.py

Quality verification for baseline navigation experiments.

Metrics
-------
1. Successful runs
2. True Cross-Track Error (True CTE) - Distance to Ideal Path
3. Run-to-Run Trajectory Variance
4. Heading Error
5. Yaw Rate (Overall and Straight-line)
6. Abrupt Angular Corrections
7. Linear Velocity Profile

The reference trajectory is computed as the average of all interpolated
baseline runs, providing a robust estimate of the expected path.
"""

from pathlib import Path
import numpy as np
import pandas as pd
from scipy.interpolate import interp1d
from scipy.signal import find_peaks

# ==============================================================================
# CONFIGURATION
# ==============================================================================

DATA_DIR = Path("data/processed")
CONTROLLERS = ["DWB", "RPP"]

# Number of interpolated samples used to compare trajectories
N_POINTS = 300

# --------------------------
# Ideal Path Definitions
# --------------------------
START_X   = -2.0004353523254395
START_Y   =  5.971445560455322
WAYPOINT_1_X = -2.034727096557617
WAYPOINT_1_Y = -0.045293934643268585
WAYPOINT_2_X = 2.0069382190704346
WAYPOINT_2_Y = -0.0032528620213270187

IDEAL_PATH = [
    (START_X, START_Y),
    (WAYPOINT_1_X, WAYPOINT_1_Y),
    (WAYPOINT_2_X, WAYPOINT_2_Y)
]

# --------------------------
# Acceptance thresholds
# --------------------------
MAX_CTE_MEAN = 0.20          # meters
MAX_TRAJ_VARIANCE = 0.08     # meters
MAX_YAW_RATE = 0.15          # rad/s
YAW_RATE_PEAK = 0.50         # rad/s
CURVATURE_THRESHOLD = 0.10   # rad/m
MIN_EXPECTED_RUNS = 3        # Target repetitions

# ==============================================================================
# AUXILIARY FUNCTIONS
# ==============================================================================

def angle_wrap(angle):
    """Normalize angle to [-pi, pi]."""
    return np.arctan2(np.sin(angle), np.cos(angle))

def cumulative_distance(x, y):
    """Computes cumulative traveled distance along the trajectory."""
    dx = np.diff(x)
    dy = np.diff(y)
    dist = np.zeros(len(x))
    dist[1:] = np.cumsum(np.hypot(dx, dy))
    return dist

def load_run(csv_file):
    """Loads one trajectory CSV."""
    df = pd.read_csv(csv_file).dropna(how="all")
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df.reset_index(drop=True)

def load_meta(csv_file):
    """Loads one metadata file."""
    meta = pd.read_csv(csv_file).dropna(how="all")
    row = meta.iloc[0].copy()
    row["success"] = str(row["success"]).strip().lower() == "true"
    return row

def load_controller_runs(controller):
    """Loads every baseline run for one controller."""
    runs = []
    files = sorted(DATA_DIR.glob(f"{controller}-Baseline-R*.csv"))
    for file in files[:MIN_EXPECTED_RUNS]:
        if "_meta" in file.name:
            continue
        runs.append(load_run(file))
    return runs

def load_controller_meta(controller):
    """Loads metadata for every run."""
    metas = []
    files = sorted(DATA_DIR.glob(f"{controller}-Baseline-R*_meta.csv"))
    for file in files[:MIN_EXPECTED_RUNS]:
        metas.append(load_meta(file))
    return metas

# ==============================================================================
# TRAJECTORY INTERPOLATION
# ==============================================================================

def interpolate_run(df, n_points=N_POINTS):
    """
    Interpolates one trajectory using normalized traveled distance.
    Ensures spatial synchronization between trajectories of varying lengths.
    """
    x = df["x"].to_numpy()
    y = df["y"].to_numpy()
    yaw = np.unwrap(df["yaw"].to_numpy())
    linear_vel = df["linear_vel"].to_numpy()
    angular_vel = df["angular_vel"].to_numpy()

    s = cumulative_distance(x, y)
    s_norm = s / s[-1] if s[-1] > 0 else s
    s_new = np.linspace(0.0, 1.0, n_points)

    return pd.DataFrame({
        "x": interp1d(s_norm, x)(s_new),
        "y": interp1d(s_norm, y)(s_new),
        "yaw": interp1d(s_norm, yaw)(s_new),
        "linear_vel": interp1d(s_norm, linear_vel)(s_new),
        "angular_vel": interp1d(s_norm, angular_vel)(s_new),
    })

# ==============================================================================
# REFERENCE TRAJECTORY
# ==============================================================================

def build_reference(runs):
    """Builds the average reference trajectory from all runs."""
    interpolated = [interpolate_run(run) for run in runs]

    reference = pd.DataFrame({
        "x": np.mean([run["x"].values for run in interpolated], axis=0),
        "y": np.mean([run["y"].values for run in interpolated], axis=0),
        "yaw": np.mean([run["yaw"].values for run in interpolated], axis=0),
        "linear_vel": np.mean([run["linear_vel"].values for run in interpolated], axis=0),
        "angular_vel": np.mean([run["angular_vel"].values for run in interpolated], axis=0),
    })
    return reference, interpolated

# ==============================================================================
# METRIC COMPUTATION
# ==============================================================================

def compute_true_cte(interpolated_runs, ideal_path):
    """
    Calculates the true Cross-Track Error by finding the minimum distance 
    from each robot point to the line segments of the ideal geometric path.
    """
    all_distances = []
    
    for run in interpolated_runs:
        x_array = run["x"].values
        y_array = run["y"].values
        min_distances = np.full(len(x_array), np.inf)
        
        for i in range(len(ideal_path) - 1):
            p1 = np.array(ideal_path[i])
            p2 = np.array(ideal_path[i+1])
            
            segment_vec = p2 - p1
            segment_len_sq = np.dot(segment_vec, segment_vec)
            
            for j in range(len(x_array)):
                p3 = np.array([x_array[j], y_array[j]])
                
                if segment_len_sq == 0:
                    dist = np.linalg.norm(p3 - p1)
                else:
                    # Orthogonal projection of the point onto the segment
                    t = max(0, min(1, np.dot(p3 - p1, segment_vec) / segment_len_sq))
                    projection = p1 + t * segment_vec
                    dist = np.linalg.norm(p3 - projection)
                    
                if dist < min_distances[j]:
                    min_distances[j] = dist
                    
        all_distances.extend(min_distances)
        
    distances = np.asarray(all_distances)
    return {
        "mean": distances.mean(),
        "std": distances.std(),
        "max": distances.max(),
    }

def compute_trajectory_variance(interpolated_runs):
    """Computes spatial run-to-run variance across the route."""
    xs = np.stack([run["x"].values for run in interpolated_runs])
    ys = np.stack([run["y"].values for run in interpolated_runs])
    
    spatial_std = np.sqrt(xs.std(axis=0)**2 + ys.std(axis=0)**2)
    return {
        "mean": spatial_std.mean(),
        "max": spatial_std.max(),
    }

def compute_heading_error(reference, interpolated_runs):
    """Computes true orientation error using robot yaw vs reference yaw."""
    ref_yaw = reference["yaw"].values
    errors = []
    
    for run in interpolated_runs:
        err = angle_wrap(run["yaw"].values - ref_yaw)
        errors.extend(np.abs(err))
        
    errors = np.asarray(errors)
    return {
        "mean_deg": np.degrees(errors.mean()),
        "max_deg": np.degrees(errors.max()),
    }

def compute_yaw_rate(runs):
    """Extracts yaw rate metrics directly from angular_vel."""
    rates = np.concatenate([run["angular_vel"].to_numpy() for run in runs])
    return {
        "mean": np.mean(np.abs(rates)),
        "std": np.std(rates),
        "max": np.max(np.abs(rates)),
        "all": rates,
    }

def compute_linear_velocity(runs):
    """Extracts linear velocity metrics."""
    vels = np.concatenate([run["linear_vel"].to_numpy() for run in runs])
    return {
        "mean": np.mean(vels),
        "std": np.std(vels),
        "max": np.max(vels),
        "min": np.min(vels),
    }

def get_straight_mask(reference):
    """Generates a boolean mask for straight segments based on curvature threshold."""
    dx = np.gradient(reference["x"].values)
    dy = np.gradient(reference["y"].values)
    ds = np.hypot(dx, dy)
    
    heading = np.unwrap(np.arctan2(dy, dx))
    dheading = np.gradient(heading)
    
    with np.errstate(divide='ignore', invalid='ignore'):
        curvature = np.abs(dheading / ds)
        curvature[ds == 0] = 0.0

    return curvature < CURVATURE_THRESHOLD

def count_abrupt_corrections(straight_angular_vels):
    """Counts abrupt angular corrections exclusively on straight segments."""
    peaks, _ = find_peaks(np.abs(straight_angular_vels), height=YAW_RATE_PEAK)
    return {
        "count": len(peaks),
        "events_per_1000": (len(peaks) / len(straight_angular_vels)) * 1000 if len(straight_angular_vels) > 0 else 0,
    }

def evaluate_metrics(reference, interpolated_runs, original_runs):
    # Get the mask for straight segments based on curvature
    straight_mask = get_straight_mask(reference)
    
    # Extract angular velocities only from straight segments for all runs
    straight_angular_vels = np.concatenate([run["angular_vel"].values[straight_mask] for run in interpolated_runs])
    
    yaw_rate = compute_yaw_rate(original_runs)
    yaw_rate["straight_mean"] = np.mean(np.abs(straight_angular_vels)) if len(straight_angular_vels) > 0 else 0.0
    
    return {
        "cte": compute_true_cte(interpolated_runs, IDEAL_PATH), # True CTE using absolute geometry
        "variance": compute_trajectory_variance(interpolated_runs),
        "heading": compute_heading_error(reference, interpolated_runs),
        "yaw_rate": yaw_rate,
        "corrections": count_abrupt_corrections(straight_angular_vels),
        "linear_vel": compute_linear_velocity(original_runs),
    }

def baseline_passed(successes, total_runs, metrics):
    if successes != total_runs or total_runs == 0:
        return False
    if metrics["cte"]["mean"] > MAX_CTE_MEAN:
        return False
    if metrics["variance"]["mean"] > MAX_TRAJ_VARIANCE:
        return False
    if metrics["yaw_rate"]["straight_mean"] > MAX_YAW_RATE:
        return False
    return True

# ==============================================================================
# REPORT
# ==============================================================================

def print_metric(name, value, unit="", passed=None):
    line = f"{name:.<35}"
    line += f"{value:.4f}" if isinstance(value, float) else str(value)
    if unit: line += f" {unit}"
    if passed is True: line += "   ✓"
    elif passed is False: line += "   ✗"
    print(line)

def evaluate_controller(controller):
    print(f"\n{'='*70}\n{controller} BASELINE (N={MIN_EXPECTED_RUNS})\n{'='*70}")
    
    runs = load_controller_runs(controller)
    metas = load_controller_meta(controller)

    if not runs:
        print("No baseline runs found.")
        return False

    success = sum(bool(m["success"]) for m in metas)
    total = len(metas)
    reference, interpolated = build_reference(runs)
    metrics = evaluate_metrics(reference, interpolated, runs)
    approved = baseline_passed(success, total, metrics)

    print("\nRUNS")
    print_metric("Successful runs", f"{success}/{total}", passed=(success == total))
    
    print("\nTRAJECTORY")
    print_metric("True Cross-Track Error (Mean)", metrics["cte"]["mean"], "m", metrics["cte"]["mean"] <= MAX_CTE_MEAN)
    print_metric("Maximum True CTE", metrics["cte"]["max"], "m")
    print_metric("Trajectory Variance", metrics["variance"]["mean"], "m", metrics["variance"]["mean"] <= MAX_TRAJ_VARIANCE)
    print_metric("Maximum Variance", metrics["variance"]["max"], "m")
    
    print("\nHEADING")
    print_metric("Mean Heading Error", metrics["heading"]["mean_deg"], "deg")
    print_metric("Maximum Heading Error", metrics["heading"]["max_deg"], "deg")
    
    print("\nLINEAR VELOCITY")
    print_metric("Mean Linear Velocity", metrics["linear_vel"]["mean"], "m/s")
    print_metric("Max Linear Velocity", metrics["linear_vel"]["max"], "m/s")
    print_metric("Min Linear Velocity", metrics["linear_vel"]["min"], "m/s")
    print_metric("Velocity Std Dev", metrics["linear_vel"]["std"], "m/s")

    print("\nANGULAR STABILITY")
    print_metric("Mean Yaw Rate (Straight)", metrics["yaw_rate"]["straight_mean"], "rad/s", metrics["yaw_rate"]["straight_mean"] <= MAX_YAW_RATE)
    print_metric("Mean Yaw Rate (Overall)", metrics["yaw_rate"]["mean"], "rad/s")
    print_metric("Maximum Yaw Rate", metrics["yaw_rate"]["max"], "rad/s")
    print_metric("Abrupt Corrections (Events)", metrics["corrections"]["count"])
    
    print(f"\n{'✓ BASELINE APPROVED' if approved else '✗ BASELINE FAILED'}\n")
    return approved

def main():
    print(f"\n{'='*70}\nBASELINE QUALITY CHECK\n{'='*70}")
    results = [evaluate_controller(ctrl) for ctrl in CONTROLLERS]
    print("=" * 70)
    
    if all(results):
        print("\nRESULT\n------\n✓ ALL BASELINES PASSED\nThe experiment is ready to proceed to Round A.\n")
        return 0
    else:
        print("\nRESULT\n------\n✗ BASELINE VALIDATION FAILED\nCheck initial pose, localization, and controller behavior.\nDo NOT continue to parameter tuning.\n")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())