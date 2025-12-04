# Copilot Instructions for Single-Axis Sun Tracker (Azimuth)

## Project Overview
This repository models and simulates a single-axis solar tracker that rotates a panel around the vertical (azimuth) axis to follow the sun. The system is subject to friction/damping (`b`) and limited motor torque (`τ_max`).

## Architecture & Key Components
- **Physical Model**: Simulates the tracker dynamics, including inertia (`I`), friction (`b`), and torque limits (`τ_max`).
- **Sun Reference Trajectory**: Implements a smooth, realistic sun path (typically sinusoidal or piecewise-sinusoidal) from –45° to +45° (or 0° → 90°) over 120 seconds.
- **Controller**: Uses a PI (optionally PID) controller with anti-windup (clamping) to maintain tracking accuracy. Tuning is critical to meet the requirement: after 10s, keep $|ϕ - ϕ_{sun}| \leq 0.5°$.
- **Integrator**: Custom RK4 (Runge-Kutta 4th order) implementation for state-space simulation. Do not use `scipy.solve_ivp`.
- **Energy Calculation**: Computes energy captured by the tracker vs. fixed panel for performance comparison.
- **Visualization**: Generates time plots and a 20–30s animation (matplotlib + FuncAnimation or manim). Save as `.mp4` (ffmpeg) or `.gif`.

## Developer Workflow
- **Code Format**: Use a single `.py` or `.ipynb` file that runs end-to-end, saving figures and video outputs.
- **Tuning**: Start with P-only control, reduce `Kp` to avoid oscillation, then increase `Ki` for steady-state error. Add `Kd` if needed for phase lag compensation.
- **Testing**: Validate robustness by initializing $ϕ(0)$ at –45°, +45°, and 0°.
- **Deliverables**: Ensure outputs include time plots (`ϕ`, `ϕ_{sun}`, error, torque), energy table, and animation. Include a brief report/memo summarizing model, controller, tuning, results, and energy benefit.

## Project-Specific Patterns
- **Anti-windup**: When torque saturates, stop integrating the I term (clamping method).
- **Parameter Sweeps**: Test multiple values for `I`, `b`, and `τ_max` to ensure realistic and challenging tuning.
- **No External ODE Solvers**: RK4 must be implemented manually.

## Key Files & Directories
- `README.md`: Contains requirements, architecture, and workflow details.
- Main code file: Should be a single `.py` or `.ipynb` implementing all logic and outputs.

## Example Workflow
1. Pick plant parameters (`I`, `b`, `τ_max`).
2. Write sun reference function.
3. Implement RK4 integrator.
4. Simulate open-loop response.
5. Add PI controller and tune.
6. Generate plots and animation.
7. Compare energy results.

## Integration Points
- **Visualization**: Use matplotlib and ffmpeg for animation output.
- **No external simulation libraries**: All numerical integration and control logic must be custom.

---
For questions or unclear conventions, refer to `README.md` or ask for clarification.
