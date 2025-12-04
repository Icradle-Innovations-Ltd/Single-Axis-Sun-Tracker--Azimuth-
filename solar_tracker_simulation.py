"""
Single-Axis Solar Tracker (Azimuth) Simulation
================================================
Models a vertical-axis solar tracker with PI controller, torque saturation,
and friction. Demonstrates tracking performance and energy benefits.

Requirements:
- Custom RK4 integration (no scipy.solve_ivp)
- PI controller with anti-windup
- Tracking error ≤ 0.5° after 10s
- Energy comparison vs fixed panels
- 20-30s animation output
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.patches import Wedge, Circle
import matplotlib.patches as mpatches

# ============================================================================
# PHYSICAL PARAMETERS
# ============================================================================
# Moment of inertia (kg·m²) - typical for small solar panel
I = 2.0

# Damping coefficient (N·m·s/rad)
b = 0.5

# Maximum motor torque (N·m)
tau_max = 20.0

# Simulation parameters
T_sim = 120.0  # Total simulation time (seconds)
dt = 0.01      # Time step for RK4 integration

# ============================================================================
# SUN REFERENCE TRAJECTORY
# ============================================================================
def phi_sun(t):
    """
    Sun azimuth angle as function of time.
    Smooth sinusoidal trajectory from -45° to +45° over 120s.
    
    Args:
        t: Time in seconds
    
    Returns:
        Azimuth angle in degrees
    """
    # Angular range: -45° to +45° (90° total)
    amplitude = 45.0  # degrees
    period = T_sim
    
    # Sinusoidal motion: φ_sun(t) = 45*sin(π*t/120)
    phi = amplitude * np.sin(np.pi * t / period)
    return phi


def phi_sun_dot(t):
    """
    Derivative of sun azimuth angle (angular velocity).
    
    Args:
        t: Time in seconds
    
    Returns:
        Angular velocity in degrees/second
    """
    amplitude = 45.0
    period = T_sim
    
    # d/dt[45*sin(π*t/120)] = 45*(π/120)*cos(π*t/120)
    phi_dot = amplitude * (np.pi / period) * np.cos(np.pi * t / period)
    return phi_dot


# ============================================================================
# RK4 INTEGRATOR
# ============================================================================
def rk4_step(state, t, dt, controller_func, tau_max, I, b):
    """
    Single RK4 integration step for 2nd-order system.
    
    State: [φ, ω] where φ is angle (deg), ω is angular velocity (deg/s)
    
    Dynamics:
        φ̇ = ω
        ω̇ = (τ - b*ω) / I
    
    Args:
        state: [φ, ω] current state
        t: Current time
        dt: Time step
        controller_func: Function(φ, ω, t, integral) -> (τ, integral_new)
        tau_max: Maximum torque limit
        I: Moment of inertia
        b: Damping coefficient
    
    Returns:
        new_state: [φ_new, ω_new]
        torque_applied: Actual torque applied (after saturation)
        integral_new: Updated integral term
    """
    phi, omega = state
    
    # Define state derivative function
    def f(state, t, tau):
        phi, omega = state
        phi_dot = omega
        omega_dot = (tau - b * omega) / I
        return np.array([phi_dot, omega_dot])
    
    # Get control torque at current state
    tau, integral = controller_func(phi, omega, t)
    
    # Apply saturation
    tau_sat = np.clip(tau, -tau_max, tau_max)
    
    # RK4 coefficients
    k1 = f(state, t, tau_sat)
    k2 = f(state + 0.5 * dt * k1, t + 0.5 * dt, tau_sat)
    k3 = f(state + 0.5 * dt * k2, t + 0.5 * dt, tau_sat)
    k4 = f(state + dt * k3, t + dt, tau_sat)
    
    # Update state
    new_state = state + (dt / 6.0) * (k1 + 2*k2 + 2*k3 + k4)
    
    return new_state, tau_sat, integral


# ============================================================================
# PI CONTROLLER WITH ANTI-WINDUP
# ============================================================================
class PIController:
    """
    PI Controller with anti-windup (clamping method).
    
    Control law:
        e(t) = φ_sun(t) - φ(t)
        τ = Kp * e + Ki * ∫e dt
    
    Anti-windup: Stop integrating when torque is saturated.
    """
    
    def __init__(self, Kp, Ki, Kd=0.0, tau_max=tau_max):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.tau_max = tau_max
        self.integral = 0.0
        self.prev_error = 0.0
        
    def compute(self, phi, omega, t):
        """
        Compute control torque.
        
        Args:
            phi: Current angle (degrees)
            omega: Current angular velocity (deg/s)
            t: Current time
        
        Returns:
            tau: Control torque (before saturation)
            integral: Updated integral term
        """
        # Tracking error
        error = phi_sun(t) - phi
        
        # Proportional term
        p_term = self.Kp * error
        
        # Integral term (will be updated after checking saturation)
        i_term = self.Ki * self.integral
        
        # Derivative term (optional)
        d_term = -self.Kd * omega  # Negative feedback on velocity
        
        # Total control signal (before saturation)
        tau = p_term + i_term + d_term
        
        # Check if saturated
        tau_sat = np.clip(tau, -self.tau_max, self.tau_max)
        is_saturated = (abs(tau) > self.tau_max)
        
        # Anti-windup: only integrate if not saturated
        # or if integration would help (error and integral have opposite signs)
        if not is_saturated or (error * self.integral < 0):
            self.integral += error * dt
        
        self.prev_error = error
        
        return tau_sat, self.integral
    
    def reset(self):
        """Reset controller state."""
        self.integral = 0.0
        self.prev_error = 0.0


# ============================================================================
# SIMULATION FUNCTION
# ============================================================================
def simulate_tracker(phi_0, Kp, Ki, Kd=0.0):
    """
    Run complete simulation of solar tracker.
    
    Args:
        phi_0: Initial angle (degrees)
        Kp: Proportional gain
        Ki: Integral gain
        Kd: Derivative gain (optional)
    
    Returns:
        t_array: Time points
        phi_array: Tracker angles
        omega_array: Angular velocities
        tau_array: Applied torques
        error_array: Tracking errors
    """
    # Initialize controller
    controller = PIController(Kp, Ki, Kd, tau_max)
    
    # Initial state
    state = np.array([phi_0, 0.0])  # [angle, angular_velocity]
    
    # Time array
    N_steps = int(T_sim / dt)
    t_array = np.linspace(0, T_sim, N_steps)
    
    # Storage arrays
    phi_array = np.zeros(N_steps)
    omega_array = np.zeros(N_steps)
    tau_array = np.zeros(N_steps)
    error_array = np.zeros(N_steps)
    
    # Simulation loop
    for i, t in enumerate(t_array):
        # Store current state
        phi_array[i] = state[0]
        omega_array[i] = state[1]
        error_array[i] = phi_sun(t) - state[0]
        
        # Compute control and integrate
        tau, _ = controller.compute(state[0], state[1], t)
        tau_array[i] = tau
        
        # RK4 step
        if i < N_steps - 1:
            state, _, _ = rk4_step(
                state, t, dt,
                lambda p, o, t: controller.compute(p, o, t),
                tau_max, I, b
            )
    
    return t_array, phi_array, omega_array, tau_array, error_array


# ============================================================================
# ENERGY CALCULATION
# ============================================================================
def calculate_energy(t_array, phi_array):
    """
    Calculate energy captured (proportional to cos(angle_diff)).
    
    Energy proxy: E = ∫ cos(φ_sun - φ) dt
    
    Args:
        t_array: Time points
        phi_array: Panel angles (degrees)
    
    Returns:
        energy: Total energy captured
    """
    # Sun angles at each time
    phi_sun_array = phi_sun(t_array)
    
    # Angle difference (convert to radians for cosine)
    angle_diff = np.deg2rad(phi_sun_array - phi_array)
    
    # Energy is proportional to cos(difference)
    energy = np.trapezoid(np.cos(angle_diff), t_array)
    
    return energy


def energy_comparison(t_array, phi_tracker):
    """
    Compare tracker energy vs fixed panels.
    
    Returns:
        Dictionary with energy values and ratios
    """
    # Tracker energy
    E_tracker = calculate_energy(t_array, phi_tracker)
    
    # Fixed panel at 0°
    phi_fixed_0 = np.zeros_like(t_array)
    E_fixed_0 = calculate_energy(t_array, phi_fixed_0)
    
    # Best fixed panel (optimized angle)
    # For symmetric trajectory -45° to +45°, best is at 0°
    # But let's check a few angles
    angles_to_test = np.linspace(-45, 45, 19)
    energies = []
    for angle in angles_to_test:
        phi_fixed = np.full_like(t_array, angle)
        energies.append(calculate_energy(t_array, phi_fixed))
    
    E_fixed_best = max(energies)
    best_angle = angles_to_test[np.argmax(energies)]
    
    results = {
        'E_tracker': E_tracker,
        'E_fixed_0': E_fixed_0,
        'E_fixed_best': E_fixed_best,
        'best_fixed_angle': best_angle,
        'ratio_vs_0': E_tracker / E_fixed_0,
        'ratio_vs_best': E_tracker / E_fixed_best
    }
    
    return results


# ============================================================================
# VISUALIZATION
# ============================================================================
def plot_results(t_array, phi_array, tau_array, error_array, Kp, Ki, Kd):
    """
    Generate comprehensive time-domain plots.
    """
    phi_sun_array = phi_sun(t_array)
    
    fig, axes = plt.subplots(4, 1, figsize=(12, 10))
    fig.suptitle(f'Solar Tracker Performance (Kp={Kp}, Ki={Ki}, Kd={Kd})', 
                 fontsize=14, fontweight='bold')
    
    # Plot 1: Angles
    axes[0].plot(t_array, phi_sun_array, 'r--', label='Sun Position φ_sun', linewidth=2)
    axes[0].plot(t_array, phi_array, 'b-', label='Tracker Angle φ', linewidth=1.5)
    axes[0].set_ylabel('Angle (degrees)', fontsize=11)
    axes[0].legend(loc='upper left')
    axes[0].grid(True, alpha=0.3)
    axes[0].set_title('Tracking Performance')
    
    # Plot 2: Tracking Error
    axes[1].plot(t_array, error_array, 'g-', linewidth=1.5)
    axes[1].axhline(y=0.5, color='r', linestyle='--', label='±0.5° tolerance', alpha=0.7)
    axes[1].axhline(y=-0.5, color='r', linestyle='--', alpha=0.7)
    axes[1].axvline(x=10, color='orange', linestyle=':', label='t=10s', alpha=0.7)
    axes[1].set_ylabel('Error (degrees)', fontsize=11)
    axes[1].legend(loc='upper right')
    axes[1].grid(True, alpha=0.3)
    axes[1].set_title('Tracking Error (φ_sun - φ)')
    
    # Plot 3: Control Torque
    axes[2].plot(t_array, tau_array, 'purple', linewidth=1.5)
    axes[2].axhline(y=tau_max, color='r', linestyle='--', label=f'τ_max = ±{tau_max} N·m', alpha=0.7)
    axes[2].axhline(y=-tau_max, color='r', linestyle='--', alpha=0.7)
    axes[2].set_ylabel('Torque (N·m)', fontsize=11)
    axes[2].legend(loc='upper right')
    axes[2].grid(True, alpha=0.3)
    axes[2].set_title('Applied Motor Torque')
    
    # Plot 4: Error after 10s (zoomed)
    t_mask = t_array >= 10
    axes[3].plot(t_array[t_mask], error_array[t_mask], 'g-', linewidth=1.5)
    axes[3].axhline(y=0.5, color='r', linestyle='--', label='±0.5° requirement', alpha=0.7)
    axes[3].axhline(y=-0.5, color='r', linestyle='--', alpha=0.7)
    axes[3].fill_between(t_array[t_mask], -0.5, 0.5, alpha=0.2, color='green')
    axes[3].set_ylabel('Error (degrees)', fontsize=11)
    axes[3].set_xlabel('Time (seconds)', fontsize=11)
    axes[3].legend(loc='upper right')
    axes[3].grid(True, alpha=0.3)
    axes[3].set_title('Steady-State Error (t ≥ 10s)')
    axes[3].set_ylim([-1.5, 1.5])
    
    plt.tight_layout()
    plt.savefig('tracker_performance.png', dpi=300, bbox_inches='tight')
    print("✓ Saved: tracker_performance.png")
    
    return fig


def create_animation(t_array, phi_array, error_array, filename='tracker_animation.mp4'):
    """
    Create 20-30s animation showing compass view and error subplot.
    """
    # Subsample for animation (aim for 30 fps, ~25s duration)
    fps = 30
    duration = 25  # seconds
    total_frames = fps * duration
    
    # Sample indices
    step = max(1, len(t_array) // total_frames)
    t_anim = t_array[::step]
    phi_anim = phi_array[::step]
    error_anim = error_array[::step]
    phi_sun_anim = phi_sun(t_anim)
    
    # Setup figure
    fig = plt.figure(figsize=(14, 6))
    
    # Left subplot: Compass view
    ax1 = plt.subplot(1, 2, 1, projection='polar')
    ax1.set_theta_zero_location('N')
    ax1.set_theta_direction(-1)
    
    # Right subplot: Error vs time
    ax2 = plt.subplot(1, 2, 2)
    
    # Initialize plot elements
    sun_marker = ax1.plot([], [], 'yo', markersize=20, label='Sun', zorder=5)[0]
    tracker_line = ax1.plot([], [], 'b-', linewidth=4, label='Tracker')[0]
    error_line = ax2.plot([], [], 'g-', linewidth=2)[0]
    time_marker = ax2.plot([], [], 'ro', markersize=8)[0]
    
    # Setup compass
    ax1.set_ylim(0, 1)
    ax1.set_title('Azimuth Tracking', fontsize=14, fontweight='bold', pad=20)
    ax1.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
    
    # Setup error plot
    ax2.axhline(y=0.5, color='r', linestyle='--', alpha=0.5, label='±0.5° limit')
    ax2.axhline(y=-0.5, color='r', linestyle='--', alpha=0.5)
    ax2.axvline(x=10, color='orange', linestyle=':', alpha=0.5, label='t=10s')
    ax2.fill_between([0, T_sim], -0.5, 0.5, alpha=0.1, color='green')
    ax2.set_xlim(0, T_sim)
    ax2.set_ylim(-3, 3)
    ax2.set_xlabel('Time (s)', fontsize=12)
    ax2.set_ylabel('Error (degrees)', fontsize=12)
    ax2.set_title('Tracking Error', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.legend(loc='upper right')
    
    # Animation function
    def animate(frame):
        # Convert angles to radians for polar plot
        theta_sun = np.deg2rad(phi_sun_anim[frame])
        theta_tracker = np.deg2rad(phi_anim[frame])
        
        # Update sun position
        sun_marker.set_data([theta_sun], [0.9])
        
        # Update tracker direction (line from center)
        tracker_line.set_data([theta_tracker, theta_tracker], [0, 0.7])
        
        # Update error plot
        error_line.set_data(t_anim[:frame+1], error_anim[:frame+1])
        time_marker.set_data([t_anim[frame]], [error_anim[frame]])
        
        # Add time annotation
        ax1.set_title(f'Azimuth Tracking (t = {t_anim[frame]:.1f} s)', 
                     fontsize=14, fontweight='bold', pad=20)
        
        return sun_marker, tracker_line, error_line, time_marker
    
    # Create animation
    anim = FuncAnimation(fig, animate, frames=len(t_anim), 
                        interval=1000/fps, blit=True, repeat=True)
    
    # Save animation
    try:
        anim.save(filename, writer='ffmpeg', fps=fps, dpi=150)
        print(f"✓ Saved: {filename}")
    except Exception as e:
        print(f"✗ Could not save animation: {e}")
        print("  (Make sure ffmpeg is installed)")
        # Try GIF as fallback
        try:
            gif_name = filename.replace('.mp4', '.gif')
            anim.save(gif_name, writer='pillow', fps=fps)
            print(f"✓ Saved GIF instead: {gif_name}")
        except:
            print("  Could not save GIF either. Animation will be skipped.")
    
    plt.close(fig)


# ============================================================================
# MAIN EXECUTION
# ============================================================================
if __name__ == "__main__":
    print("=" * 70)
    print("SINGLE-AXIS SOLAR TRACKER SIMULATION")
    print("=" * 70)
    
    # Display parameters
    print(f"\nPhysical Parameters:")
    print(f"  Inertia (I):        {I} kg*m^2")
    print(f"  Damping (b):        {b} N*m*s/rad")
    print(f"  Max Torque (tau_max): {tau_max} N*m")
    print(f"  Simulation time:    {T_sim} s")
    print(f"  Time step:          {dt} s")
    
    # Controller tuning
    # Optimized to meet ≤0.5° requirement after 10s for ALL initial conditions
    Kp = 16.5  # High proportional gain for fast error correction
    Ki = 4.8   # Strong integral action to eliminate steady-state error
    Kd = 4.2   # Derivative gain to dampen oscillations
    
    print(f"\nController Gains:")
    print(f"  Kp = {Kp}")
    print(f"  Ki = {Ki}")
    print(f"  Kd = {Kd}")
    
    # Test initial conditions
    initial_angles = [0.0, -45.0, 45.0]
    
    print(f"\n{'='*70}")
    print("RUNNING SIMULATIONS...")
    print(f"{'='*70}\n")
    
    # Main simulation with φ(0) = 0°
    phi_0 = 0.0
    print(f"Simulating with phi(0) = {phi_0} degrees...")
    t, phi, omega, tau, error = simulate_tracker(phi_0, Kp, Ki, Kd)
    
    # Check performance requirement
    print(f"\nPerformance Check:")
    t_mask = t >= 10.0
    max_error_after_10s = np.max(np.abs(error[t_mask]))
    print(f"  Max |error| after 10s: {max_error_after_10s:.4f} deg")
    if max_error_after_10s <= 0.5:
        print("  [PASS] Requirement (<= 0.5 deg)")
    else:
        print("  [FAIL] Requirement (> 0.5 deg)")
        print("  -> Consider increasing Ki or adjusting Kp/Kd")
    
    # Energy comparison
    print(f"\nEnergy Analysis:")
    energy_results = energy_comparison(t, phi)
    print(f"  Tracker energy:       {energy_results['E_tracker']:.2f}")
    print(f"  Fixed at 0 deg:       {energy_results['E_fixed_0']:.2f}")
    print(f"  Best fixed angle:     {energy_results['best_fixed_angle']:.1f} deg")
    print(f"  Best fixed energy:    {energy_results['E_fixed_best']:.2f}")
    print(f"  Tracker vs 0 deg:     {energy_results['ratio_vs_0']:.2%}")
    print(f"  Tracker vs best:      {energy_results['ratio_vs_best']:.2%}")
    
    if energy_results['ratio_vs_best'] >= 1.30:
        print(f"  ✓ Good energy benefit (≥ 30% improvement)")
    
    # Generate plots
    print(f"\n{'='*70}")
    print("GENERATING OUTPUTS...")
    print(f"{'='*70}\n")
    
    plot_results(t, phi, tau, error, Kp, Ki, Kd)
    
    # Create animation
    print("\nCreating animation (this may take a minute)...")
    create_animation(t, phi, error, 'tracker_animation.mp4')
    
    # Test robustness with different initial conditions
    print(f"\n{'='*70}")
    print("ROBUSTNESS TESTING")
    print(f"{'='*70}\n")
    
    for phi_init in initial_angles:
        if phi_init == phi_0:
            continue  # Already tested
        print(f"\nTesting phi(0) = {phi_init} deg...")
        _, _, _, _, err = simulate_tracker(phi_init, Kp, Ki, Kd)
        max_err = np.max(np.abs(err[t >= 10.0]))
        status = "✓ PASS" if max_err <= 0.5 else "✗ FAIL"
        print(f"  Max |error| after 10s: {max_err:.4f} deg [{status}]")
    
    print(f"\n{'='*70}")
    print("SIMULATION COMPLETE")
    print(f"{'='*70}")
    print("\nOutputs generated:")
    print("  • tracker_performance.png")
    print("  • tracker_animation.mp4 (or .gif)")
    print("\nNext steps:")
    print("  1. Review plots to assess tracking performance")
    print("  2. If error > 0.5 deg after 10s, tune Kp/Ki/Kd")
    print("  3. Check animation for visual validation")
    print("  4. Document results in final report")
    print()
