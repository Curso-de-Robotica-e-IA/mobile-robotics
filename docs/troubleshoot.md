# Troubleshooting Guide
This document centralizes solutions for the most common issues encountered during communication, initialization, and navigation of the TurtleBot 4 running the Nav2 stack via Docker.

## ERROR 1: Transform Timeout (TF: base_link -> odom)

### Problem Statement
While running the **Nav2** stack inside a Docker container (configured with `--network host`), the `controller_server` failed to initialize, throwing the following error:
```bash
[local_costmap.local_costmap]: Timed out waiting for transform from base_link to odom to become available, tf error: Invalid frame ID "odom" passed to canTransform argument target_frame - frame does not exist
```
Despite the error, the `/odom` topic was visible in the topic list, but the **TF tree** was broken, with no link between the `odom` frame and the `base_link` frame.

### Diagnostic & Evidence
To isolate the issue, we performed the following checks:

- **TF Echo:** Running `ros2 run tf2_ros tf2_echo odom base_link` on the Raspberry Pi (RPi) returned a "Frame does not exist" error, confirming the issue was on the robot side, not just the Docker container.
- **Node Discovery:** `ros2 node list` did not show essential Create3 nodes (e.g., `/motion_control`, `/_internal/mobility`), indicating that the RPi was not discovering the base via DDS.
- **Networking:** `ip addr show` confirmed the USB-C link (`usb0`) was active at `192.168.186.3`, and the base was pingable at `192.168.186.2`. However, the RPi was prioritizing the WiFi interface (`wlan0`) for ROS 2 traffic.
    - wlan0 is still available at `/etc/turtlebot4/cyclonedds_rpi.xml` file
- **Topic Ownership:** `ros2 topic info /odom --verbose` showed that the `/odom` topic was being published by the `robot_state` node (a placeholder on the RPi) rather than the `motion_control` node (the actual base driver).

### Root Cause Analysis
The primary cause was a **Middleware (RMW) Mismatch/Misconfiguration**.

1. The robot was using **FastDDS** by default, which occasionally fails to bridge the USB-C internal connection between the RPi and the Create3 base when multiple network interfaces (WiFi + USB) are active.
2. The DDS configuration was not explicitly forcing communication over the `usb0` interface, causing the high-frequency TF data from the base to be lost or ignored.

### Solution 
The fix involved migrating the entire system to **CycloneDDS**, which provides more stable discovery over the TB4's internal USB link.

#### Step 1: Raspberry Pi Configuration
- Updated `/etc/turtlebot4/setup.bash` to switch the middleware:    
```bash
# run 
sudo nano /etc/turtlebot4/setup.bash 

# and update this line
export RMW_IMPLEMENTATION="rmw_cyclonedds_cpp"

# ctrl + S and ctrl + X to save and exit
```

#### Step 2: Network Interface Binding
- Modified the CycloneDDS configuration file at `/etc/turtlebot4/cyclonedds_rpi.xml` to explicitly enable the USB interface by uncommenting the relevant line:
```bash
# run 
sudo nano /etc/turtlebot4/cyclonedds_rpi.xml

# uncomment this line
# if it is commented it should look like this <!--NetworkInterface name="usb0" priority="default" multicast="default"/-->
<NetworkInterface name="usb0" priority="default" multicast="default"/>

# ctrl + S and ctrl + X to save and exit
``` 

#### Step 3: Create3 Base Update
- Accessed the Create3 Web Server (`http://192.168.158.251:8080/home` or `http://192.168.186.2:8080/home`) -> web interface of Softex_Conv - and navigated to **Application -> Configuration**:
    - Updated **RMW Implementation** to `rmw_cyclonedds_cpp`.
    - Saved and restarted the application.

#### Step 4: Service Restart
Restarted the TurtleBot4 main service on the RPi:
```bash
sudo systemctl restart turtlebot4.service
```

### Verification
After applying the changes, the following command was executed on the RPi and inside the Docker container:
```bash
ros2 run tf2_ros tf2_echo odom base_link
```

**Result:** The command successfully returned translation and rotation coordinates, confirming the `odom -> base_link` transform was being broadcast correctly. Nav2 was then able to initialize the costmaps without timing out.

### Lessons Learned

- **Topic vs. TF:** Seeing a topic in `ros2 topic list` does not mean the data is valid or that the TF tree is healthy. Always verify with `tf2_echo`.
- **Interface Priority:** On robots with multiple NICs (Network Interface Cards), always explicitly define which interface the DDS should use in the `.xml` profile to avoid "ghost" nodes or missing transforms.

---

## ERROR 2: Time Synchronization

### Problem Description
During Nav2 operation via Docker on the `softex_conv` network, the system experienced critical data drops. Diagnostics revealed significant **clock skew** between the Host PC (Docker), the Raspberry Pi (RPi), and the iRobot Create3 base. This skew prevented the Transform (TF) buffer from validating robot positioning in real-time, as sensor data appeared to arrive from the "past".

#### Possible solution
```bash
sudo timedatectl set-timezone America/Recife
```

### NTP Server Configuration (Chrony) on Raspberry Pi
To ensure the robot acts as a stable "source of truth" for the Create3 base, the `chrony` service on the Raspberry Pi was configured to function as a local NTP server.

- **File Path:** `/etc/chrony/chrony.conf`
- Applied Modifications:
```bash
# Allow devices on the internal network (usb0 interface) to query time
allow 192.168.186.0/24

# Force the robot to announce itself as a time server even without internet access
local stratum 10
```
- **Persistence:** These changes are saved directly to the RPi's filesystem and remain active after reboots.
- **Application:** The service was restarted using `sudo systemctl restart chrony` to apply the new rules.

### System Synchronization Hierarchy
A three-tier synchronization hierarchy was established to eliminate "timestamp earlier than data in cache" errors:

1. **Host PC -> Robot:** Manual synchronization via SSH to align the Raspberry Pi with the development computer's clock.
    - Run `ros2 topic delay /scan` to see if the `average rate` is low.
    - If it is high:
        - For synchronization, you will need permissions:
            ```bash
            # in the docker (if used)
            ssh-keygen -t ed25519
            ssh-copy-id ubuntu@<robot_ip>
            ```
        - Then, run:
            ```bash
             ssh ubuntu@<robot_ip> "sudo date -s '@$(date +%s.%N)'"
            ```

2. **Robot -> Create3 Base:** The Create3 base was configured (via its web interface) to seek time via NTP directly from the Raspberry Pi's USB-C IP address (**192.168.186.3**).
    - Run `ros2 topic delay /odom` to see if the `average rate` is low.
    - If it is high, reboot the robot ⇒ **Enter http://192.168.0.100:8080/home > Application > Reboot Robot**

### Results and Validation
Following the `chrony` configuration and the alignment of middlewares (CycloneDDS), the following improvements were observed:

- **Reduced Clock Offset:** The offset on the Create3 base dashboard reached negligible levels.
- **Stable TF Tree:** The `/tf` topic stabilized, allowing Nav2 to synchronize the `odom -> base_link` frames without timing out.
- **Clean Message Filters:** The AMCL node stopped dropping scan messages, as the laser timestamps now fall within the expected buffer window.

---

## ERROR 3: Bringup Fail (General)
Run
```bash
`ros2 launch turtlebot4_bringup standard.launch.py camera:=false`.
# or restart processes 
ros2 daemon stop` then `ros2 daemon start`
```
