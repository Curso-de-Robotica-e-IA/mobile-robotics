## Experimental Protocol — Simulation Calibration

### Goal

Evaluate how different configurations of the Nav2 local controllers (DWB and Regulated Pure Pursuit) affect:

- trajectory reproducibility;
- path tracking accuracy;
- velocity stability;
- angular stability;
- execution time;
- suitability for controlled wireless data collection.

All experiments use the same map, robot platform, localization method and predefined route.
Only one parameter is modified at a time.

### Fixed Configuration

Robot:
- TurtleBot 4

Operating System:
- Ubuntu 22.04
- ROS2 Humble
- Nav2

Localization:
- AMCL

Planner:
- Smac Planner Hybrid

Behavior Tree:
- NavigateThroughPoses

Map:
- maze.yaml (TurtleBot4 Navigation package)

Route:
- Start -> go_to_start.py
- Goal -> go_to_goal.py

Controller Frequency:
- 20 Hz

Velocity Limits:
- max_vel_x: 0.26 m/s
- max_vel_theta: 1.0 rad/s

Number of repetitions:
- 3 runs per configuration

### Experiment ID Structure

```
[CONTROLLER]-[PARAMETER]-[VALUE]-[RUN]
Ex: DWB-PathDist-32-R01
    RPP-Lookahead-0.6-R01
```
---

## Parameters tested

### DWB

#### Path following

**1. `PathDist.scale`**

It is the critic that penalizes lateral distance from the path. Increasing it reduces cross-track error (CTE) but may cause oscillation; decreasing it allows the robot to be more "free".

| ID | Value |
|---|---|
| DWB-PathDist-2 | 2.0 | 
| DWB-PathDist-4 | 4.0 | 
| DWB-PathDist-8 | 8.0 | 
| DWB-PathDist-16 | 16.0 | 
| DWB-PathDist-32 **Baseline** | 32.0 | 
| DWB-PathDist-64 | 64.0 | 
| DWB-PathDist-128 | 128.0 | 
| DWB-PathDist-256 | 256.0 |

**2. `PathAlign.scale`**

Controls angular alignment with the path, not just lateral distance. Directly affects yaw rate and, consequently, antenna orientation.

| ID | Value | 
|---|---|
| DWB-PathAlign-2 | 2.0 |
| DWB-PathAlign-4 | 4.0 | 
| DWB-PathAlign-8 | 8.0 |
| DWB-PathAlign-16 | 16.0 |
| DWB-PathAlign-32 **Baseline** | 32.0 |
| DWB-PathAlign-64 | 64.0 |
| DWB-PathAlign-128 | 128.0 | 
| DWB-PathAlign-256 | 256.0 |

### RPP

#### Lookahead

**1. `lookahead_dist`**

Defines how far ahead the robot "looks". It is the main factor responsible for trajectory smoothness.

| ID | Value | 
|---|---|
| RPP-Lookahead-0.3 | 0.3m | 
| RPP-Lookahead-0.45 | 0.45m | 
| RPP-Lookahead-0.6 **Baseline** | 0.6m | 
| RPP-Lookahead-0.9 | 0.9m | 
| RPP-Lookahead-1.2 | 1.2m | 
| RPP-Lookahead-1.5 | 1.5m | 

**2. `use_regulated_linear_velocity_scaling` — ligar/desligar regulação**

Allows isolating the effect of curvature-based velocity regulation.

| ID | Value |
|---|---|
| RPP-RegVel-False | False | 
| RPP-RegVel-True **Baseline** | True |

---

## Selection Criteria

A configuration will be considered for real-world experiments if it satisfies:

- Low cross-track error.
- Low trajectory variance across runs.
- Stable linear velocity.
- Low yaw oscillation.
- Successful completion of all runs.
- No navigation failures.
- Smooth waypoint transitions.