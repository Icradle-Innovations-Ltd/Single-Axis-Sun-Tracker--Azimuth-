# Single-Axis Sun Tracker (Azimuth)

A complete simulation and control system for a vertical-axis solar tracker that follows the sun's azimuth angle throughout the day. This project implements a PID controller with custom RK4 numerical integration, demonstrating advanced control techniques including anti-windup and torque saturation handling.

[![Status](https://img.shields.io/badge/status-complete-success)](.) 
[![Python](https://img.shields.io/badge/python-3.13+-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## 🎯 Project Overview

This project models a single-axis solar tracker that rotates a panel around the vertical axis (azimuth only) to always face the sun. The system features:

- **Custom RK4 Integrator**: 4th-order Runge-Kutta implemented from scratch (no `scipy.solve_ivp`)
- **PID Controller**: Tuned controller with anti-windup for optimal tracking
- **Torque Saturation**: Realistic motor limitations
- **Performance Validation**: Meets strict tracking requirement (≤0.5° error after 10s)
- **Energy Analysis**: Quantified benefits vs. fixed panels
- **Visual Output**: Comprehensive plots and animated visualization

### Physical System

The tracker is modeled as a 2nd-order rotational system:

```
I·ϕ̈ + b·ϕ̇ = τ    with   |τ| ≤ τ_max
```

Where:
- `I` = Moment of inertia (2.0 kg·m²)
- `b` = Damping coefficient (0.5 N·m·s/rad)
- `τ_max` = Maximum motor torque (20.0 N·m)
- `ϕ` = Panel azimuth angle
- `τ` = Applied control torque

## ✅ Requirements Met

- ✅ Custom RK4 integrator (no external ODE solvers)
- ✅ PID controller with anti-windup
- ✅ Tracking error ≤ 0.5° after 10 seconds
- ✅ Energy comparison (tracker vs. fixed panels)
- ✅ 25-second MP4 animation with compass view
- ✅ Comprehensive performance plots
- ✅ Technical documentation and report

## 🚀 Quick Start

### Prerequisites

- Python 3.13+ (tested on 3.13.5)
- FFmpeg (for MP4 animation generation)

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/Icradle-Innovations-Ltd/Single-Axis-Sun-Tracker--Azimuth-.git
cd Single-Axis-Sun-Tracker--Azimuth-
```

2. **Install Python dependencies:**
```bash
pip install numpy matplotlib
```

3. **Install FFmpeg** (if not already installed):

**Windows:**
```bash
# Using Chocolatey
choco install ffmpeg

# Or using winget
winget install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt-get install ffmpeg  # Debian/Ubuntu
sudo yum install ffmpeg      # RHEL/CentOS
```

### Running the Simulation

Simply execute the main script:

```bash
python solar_tracker_simulation.py
```

**Expected Runtime:** ~30-60 seconds (depending on system performance)

### Output Files

After running the simulation, the following files will be generated:

- `tracker_performance.png` - Comprehensive time-series plots showing:
  - Panel angle vs. sun reference
  - Tracking error over time
  - Control torque with saturation
  - Steady-state error analysis

- `tracker_animation.mp4` - 25-second animated visualization featuring:
  - Polar compass view with sun and panel directions
  - Real-time error plot
  - Time annotation

## 📊 Performance Results

### Tracking Accuracy

All test cases **PASS** the ≤0.5° requirement after 10 seconds:

| Initial Angle φ(0) | Max Error After 10s | Status |
|-------------------|---------------------|---------|
| 0° | 0.0151° | ✅ PASS |
| -45° | 0.4984° | ✅ PASS |
| +45° | 0.3965° | ✅ PASS |

### Energy Performance

| Configuration | Energy | Improvement |
|--------------|--------|-------------|
| **Tracker (This System)** | **120.00** | **Baseline** |
| Fixed at 0° | 102.20 | +17.42% |
| Best Fixed (30°) | 116.50 | +3.01% |

**Key Insight:** The tracker achieves 17.42% more energy capture compared to a fixed panel at 0°, and 3.01% more than the optimally-oriented fixed panel.

### Controller Parameters (Tuned)

```python
Kp = 16.5  # Proportional gain
Ki = 4.8   # Integral gain  
Kd = 4.2   # Derivative gain
```

## 📁 Project Structure

```
Single-Axis-Sun-Tracker--Azimuth-/
├── solar_tracker_simulation.py    # Main simulation code (580 lines)
├── tracker_performance.png         # Generated performance plots
├── tracker_animation.mp4           # Generated animation
├── SIMULATION_REPORT.md           # Detailed technical report
├── README.md                      # This file
└── .github/
    └── copilot-instructions.md    # AI agent guidance
```

## 🔬 Technical Details

### Sun Reference Trajectory

The sun follows a sinusoidal path from -45° to +45° over 120 seconds:

```python
φ_sun(t) = 45° · sin(πt/120)
```

This represents a time-compressed "day" (360x speed-up).

### RK4 Integration

Custom 4th-order Runge-Kutta integrator with time step `dt = 0.01s`:

```python
k1 = f(state, t, τ)
k2 = f(state + 0.5·dt·k1, t + 0.5·dt, τ)
k3 = f(state + 0.5·dt·k2, t + 0.5·dt, τ)
k4 = f(state + dt·k3, t + dt, τ)
state_new = state + (dt/6)·(k1 + 2k2 + 2k3 + k4)
```

Total integration steps: **12,000** over 120 seconds.

### PID Controller with Anti-Windup

Control law:
```
e(t) = φ_sun(t) - φ(t)
τ = sat(Kp·e + Ki·∫e dt + Kd·ė, ±τ_max)
```

**Anti-windup (Clamping Method):**
- When `|τ| > τ_max`, stop integrating the error
- Prevents integral windup during saturation
- Ensures smooth recovery when saturation ends

### Energy Calculation

Energy proxy based on Lambert's cosine law:

```
E = ∫₀¹²⁰ cos(φ_sun(t) - φ(t)) dt
```

Computed using trapezoidal integration (`np.trapezoid`).

## 📖 Documentation

- **[SIMULATION_REPORT.md](SIMULATION_REPORT.md)** - Comprehensive technical report covering:
  - System modeling
  - Controller design and tuning process
  - Performance analysis
  - Energy comparison
  - Mathematical derivations
  - Appendices with sensitivity analysis

- **[.github/copilot-instructions.md](.github/copilot-instructions.md)** - Guidelines for AI coding agents working on this project

## 🎓 Educational Value

This project demonstrates:

1. **Control Theory Concepts:**
   - PID controller design and tuning
   - Anti-windup strategies
   - Saturation handling
   - Steady-state error elimination

2. **Numerical Methods:**
   - Custom RK4 implementation
   - State-space representation
   - Numerical integration accuracy

3. **System Modeling:**
   - 2nd-order dynamics
   - Friction/damping effects
   - Torque limitations

4. **Software Engineering:**
   - Clean, modular code structure
   - Comprehensive visualization
   - Automated testing (multiple initial conditions)

## 🛠️ Customization

You can modify the simulation parameters in `solar_tracker_simulation.py`:

### Physical Parameters (Lines 24-31)
```python
I = 2.0          # Moment of inertia [kg·m²]
b = 0.5          # Damping coefficient [N·m·s/rad]
tau_max = 20.0   # Maximum motor torque [N·m]
T_sim = 120.0    # Simulation time [s]
dt = 0.01        # Integration time step [s]
```

### Controller Gains (Lines 499-503)
```python
Kp = 16.5   # Proportional gain
Ki = 4.8    # Integral gain
Kd = 4.2    # Derivative gain
```

**Note:** If you change physical parameters, you'll need to re-tune the controller gains to maintain the ≤0.5° performance requirement.

## 🔍 Troubleshooting

### Common Issues

**1. Import Error: `ModuleNotFoundError: No module named 'matplotlib'`**
```bash
pip install matplotlib numpy
```

**2. Animation fails to save**
- Ensure FFmpeg is installed and in your PATH
- Fallback: The script will attempt to save as `.gif` instead

**3. Unicode errors in terminal output (Windows)**
- This is expected on some Windows terminals
- All functionality works correctly; only display characters are affected

**4. Performance issues / slow execution**
- Reduce time step: Change `dt = 0.01` to `dt = 0.02` (faster but less accurate)
- Reduce simulation time: Change `T_sim = 120.0` to `T_sim = 60.0`

## 📝 Citation

If you use this code in your research or project, please cite:

```bibtex
@software{single_axis_tracker_2025,
  title = {Single-Axis Sun Tracker (Azimuth) Simulation},
  author = {Icradle Innovations Ltd},
  year = {2025},
  url = {https://github.com/Icradle-Innovations-Ltd/Single-Axis-Sun-Tracker--Azimuth-}
}
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Ideas for Enhancement:
- Dual-axis tracking (add elevation angle)
- Wind disturbance modeling
- Power consumption analysis
- Real-time hardware implementation guide
- Model Predictive Control (MPC) implementation
- Adaptive gain scheduling

## 📧 Contact

**Icradle Innovations Ltd**
- GitHub: [@Icradle-Innovations-Ltd](https://github.com/Icradle-Innovations-Ltd)
- Repository: [Single-Axis-Sun-Tracker--Azimuth-](https://github.com/Icradle-Innovations-Ltd/Single-Axis-Sun-Tracker--Azimuth-)

## 🙏 Acknowledgments

- Inspired by real-world solar tracking systems
- Built with modern Python scientific computing stack
- Validated against control theory best practices

---

**Star ⭐ this repository if you found it helpful!**
