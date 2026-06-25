# Experimental Plan — DWB vs RPP Controller Comparison

## Overview

This document describes the planned experiments for comparing local navigation controllers in the ROS 2 Navigation Stack (Nav2) using a TurtleBot 4 platform. The objective is to evaluate how controller selection affects trajectory reproducibility and the quality of wireless data collection during autonomous navigation.

The study will compare:

* DWB (Dynamic Window Approach)
* RPP (Regulated Pure Pursuit)

under same navigation conditions and route configurations.

---

# Research Question

**RQ1:** How does the choice of local navigation controller affect the reproducibility of robot trajectories in indoor environments?
**RQ2:** How does the choice of local navigation controller affect the quality and consistency of BLE signal measurements collected during robot navigation?

---

# Hypothesis

The Regulated Pure Pursuit (RPP) controller is expected to produce:

* Lower cross-track error;
* Lower trajectory variability across runs;
* Smoother velocity profiles;
* Lower angular oscillation;
* More consistent RSSI measurements.

compared to the Dynamic Window Approach (DWB) controller.

---

# Experimental Platform

## Robot

* TurtleBot 4
* Differential-drive mobile robot

## Software

* ROS 2 Humble
* Nav2
* AMCL
* RViz

## Environment

* Indoor university corridor
* Previously mapped environment (`hall_cin_v3 and hall_cin_v4`)
* Static environment without dynamic obstacles

---

# Route Definition

The route will be defined using fixed waypoints.

Example:

Start → W1 → W2 → Goal

The same route must be used for all experimental runs.

---

# Experimental Factors

## Independent Variable

Navigation controller:

* DWB
* RPP

## Controlled Variables

* Robot platform
* Map
* Route
* Initial pose
* Goal pose
* Localization method
* BLE device placement
* Environment conditions

---

# Experiment 1 — Trajectory Reproducibility

## Objective

Evaluate how consistently each controller reproduces the same trajectory.

## Procedure

1. Set robot initial pose.
2. Load selected controller.
3. Execute predefined route.
4. Record navigation data.
5. Repeat N times.
6. Change controller.
7. Repeat same procedure.

## Planned Repetitions

* 10 runs using DWB
* 10 runs using RPP

---

# Experiment 2 — BLE Data Collection

## Objective

Evaluate whether controller behavior impacts BLE signal measurements.

## Procedure

1. Fixed BLE device remains stationary.
2. Mobile BLE device is mounted on the robot.
3. Establish BLE connection.
4. Execute navigation route.
5. Collect:

   * RSSI
   * Robot position
   * Robot orientation
   * Robot velocity
6. Repeat for both controllers.

---

# Metrics

## Trajectory Metrics

### Cross-Track Error (CTE)

Distance between executed trajectory and reference path.

Desired value:

* Lower is better.

### Run-to-Run Trajectory Variance

Spatial dispersion between repeated executions.

Desired value:

* Lower is better.

### Heading Error

Difference between robot orientation and path direction.

Desired value:

* Lower is better.

---

## Velocity Metrics

### Velocity Variance

Variance of linear velocity during navigation.

Desired value:

* Lower is better.

### Minimum Velocity at Waypoints

Lowest speed reached during waypoint transitions.

Desired value:

* Closer to nominal velocity.

---

## Angular Stability Metrics

### Yaw Rate Variance

Variance of angular velocity.

Desired value:

* Lower is better.

### Abrupt Angular Corrections

Number of peaks above a predefined threshold.

Desired value:

* Lower is better.

---

## BLE Metrics

### RSSI Variance per Segment

RSSI variability within spatial route segments.

Desired value:

* Lower is better.

### RSSI Coefficient of Variation

Computed for repeated measurements at similar positions.

Desired value:

* Lower is better.

### Correlation Between Yaw Rate and RSSI

Pearson correlation between robot rotation and signal strength.

Desired value:

* Lower is better.

---

# Data Collection

## ROS Topics

* /amcl_pose
* /odom
* /cmd_vel

## BLE Data

Current options:

### Option A — Bleak

* Native BLE collection
* ROS integration possible

### Option B — ADB + nRF Connect

* Current working solution
* Uses Android device logs
* Requires synchronization with navigation logs

---

# Scripts

## Navigation

### set_initial_pose.py

Publishes a fixed initial pose to `/initialpose`.

Status:

* Testing

### record_trajectory.py

Records reference trajectory.

Status:

* Testing

### replay_trajectory.py

Executes predefined route.

Status:

* Testing

---

## BLE

### ble_rssi_collector.py (bleak)

Collects BLE RSSI data.

Status:

* Under development

---

## Analysis

### compare_trajectories.py

Computes:

* Cross-track error
* Trajectory overlap
* Spatial variance

Status:

* Planned

### compare_rssi.py

Computes:

* RSSI variance
* RSSI heatmaps
* Correlation analyses

Status:

* Planned

---

# Expected Outputs

## Figures

* Overlapped trajectories
* CTE boxplots
* Velocity profiles
* Yaw rate profiles
* RSSI heatmaps
* RSSI variance comparison

## Tables

* Controller parameter summary
* Navigation metrics summary
* BLE metrics summary

---

# Extensions

* Navigation repeatability benchmarking
* Different waypoint densities
* Different robot velocities
* Obstacle environments

## Future:

* Dynamic obstacles
* Multi-floor navigation
* Wi-Fi signal collection
* Full wireless coverage mapping
* Long-term controller stability analysis
