import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

# --- Kalman Filter Core Functions ---
def kf_predict(x_prev, P_prev, F, Q, B=None, u=None):
    """
    Kalman Filter Prediction Step
    x_prev: Previous state estimate (n x 1)
    P_prev: Previous error covariance (n x n)
    F: State transition matrix (n x n)
    Q: Process noise covariance (n x n)
    B: Control input matrix (n x k) - Optional
    u: Control input vector (k x 1) - Optional
    """
    if B is not None and u is not None:
        x_pred = F @ x_prev + B @ u
    else:
        x_pred = F @ x_prev
    P_pred = F @ P_prev @ F.T + Q
    return x_pred, P_pred

def kf_update(x_pred, P_pred, z, H, R):
    """
    Kalman Filter Update Step
    x_pred: Predicted state estimate (n x 1)
    P_pred: Predicted error covariance (n x n)
    z: Measurement (m x 1)
    H: Measurement matrix (m x n)
    R: Measurement noise covariance (m x m)
    """
    y = z - H @ x_pred  # Innovation or measurement residual
    S = H @ P_pred @ H.T + R  # Innovation covariance
    K = P_pred @ H.T @ np.linalg.inv(S)  # Kalman gain
    
    x_updated = x_pred + K @ y
    P_updated = (np.eye(x_pred.shape[0]) - K @ H) @ P_pred
    return x_updated, P_updated, K, y, S

# --- Experiment Definitions ---
EXPERIMENTS = [
    {
        "name": "1. Track Constant Value (Good Q, R)",
        "description": (
            "Objective: Estimate a nearly constant value from noisy measurements.\n"
            "The true value drifts slightly over time (process noise).\n"
            "The filter is given fairly accurate Q and R values.\n"
            "Observe: How well the filter tracks the true value and smooths the measurements."
        ),
        "params": {
            "F": "1.0", "H": "1.0", "Q": "0.01", "R": "0.25",
            "x0_hat": "0.0", "P0_hat": "1.0", "num_steps": "100"
        },
        "true_system": {
            "initial_true_state": 10.0,
            "true_F": 1.0, # How true state evolves (can be same as filter F)
            "true_Q_stddev": 0.1, # Actual process noise standard deviation
            "true_H": 1.0, # How true state is measured (can be same as filter H)
            "true_R_stddev": 0.5, # Actual measurement noise standard deviation
        }
    },
    {
        "name": "2. Track Constant Value (Filter Q too small)",
        "description": (
            "Objective: See the effect of underestimating process noise.\n"
            "The true value drifts, but the filter assumes very little drift (small Q).\n"
            "Observe: The filter might be too 'confident' and slow to adapt to changes, "
            "potentially lagging behind the true state."
        ),
        "params": {
            "F": "1.0", "H": "1.0", "Q": "0.0001", "R": "0.25", # Filter's Q is very small
            "x0_hat": "0.0", "P0_hat": "1.0", "num_steps": "100"
        },
        "true_system": {
            "initial_true_state": 10.0,
            "true_F": 1.0,
            "true_Q_stddev": 0.1, # True process has more noise
            "true_H": 1.0,
            "true_R_stddev": 0.5,
        }
    },
    {
        "name": "3. Track Constant Value (Filter Q too large)",
        "description": (
            "Objective: See the effect of overestimating process noise.\n"
            "The true value drifts moderately, but the filter assumes a lot of drift (large Q).\n"
            "Observe: The filter might be too responsive to measurements, leading to a noisy estimate "
            "that doesn't smooth the data as much as it could."
        ),
        "params": {
            "F": "1.0", "H": "1.0", "Q": "1.0", "R": "0.25", # Filter's Q is large
            "x0_hat": "0.0", "P0_hat": "1.0", "num_steps": "100"
        },
        "true_system": {
            "initial_true_state": 10.0,
            "true_F": 1.0,
            "true_Q_stddev": 0.1, # True process has less noise
            "true_H": 1.0,
            "true_R_stddev": 0.5,
        }
    },
    {
        "name": "4. Track Constant Value (Filter R too small)",
        "description": (
            "Objective: See the effect of underestimating measurement noise.\n"
            "The measurements are noisy, but the filter assumes they are very precise (small R).\n"
            "Observe: The filter will trust the noisy measurements too much, leading to an estimate "
            "that closely follows the noisy data rather than smoothing it."
        ),
        "params": {
            "F": "1.0", "H": "1.0", "Q": "0.01", "R": "0.01", # Filter's R is small
            "x0_hat": "0.0", "P0_hat": "1.0", "num_steps": "100"
        },
        "true_system": {
            "initial_true_state": 10.0,
            "true_F": 1.0,
            "true_Q_stddev": 0.1,
            "true_H": 1.0,
            "true_R_stddev": 0.5, # True measurements are noisier
        }
    },
        {
        "name": "5. Track Constant Value (Filter R too large)",
        "description": (
            "Objective: See the effect of overestimating measurement noise.\n"
            "The measurements are fairly precise, but the filter assumes they are very noisy (large R).\n"
            "Observe: The filter will distrust the measurements, relying more on its prediction. "
            "The estimate might be overly smooth and slow to respond to actual changes if Q is also small."
        ),
        "params": {
            "F": "1.0", "H": "1.0", "Q": "0.01", "R": "5.0", # Filter's R is large
            "x0_hat": "0.0", "P0_hat": "1.0", "num_steps": "100"
        },
        "true_system": {
            "initial_true_state": 10.0,
            "true_F": 1.0,
            "true_Q_stddev": 0.1,
            "true_H": 1.0,
            "true_R_stddev": 0.5, # True measurements are less noisy
        }
    },
]

class KalmanFilterApp:
    def __init__(self, master):
        self.master = master
        master.title("Kalman Filter Educational Simulator (1D)")
        master.geometry("1000x750")

        self.param_vars = {}
        self.experiment_data = None

        self._setup_gui()
        self._load_experiment_data(0) # Load first experiment by default

    def _setup_gui(self):
        # Main PanedWindow
        main_pane = ttk.PanedWindow(self.master, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True)

        # --- Left Pane (Controls) ---
        left_frame = ttk.Frame(main_pane, padding="10")
        main_pane.add(left_frame, weight=1)

        # Experiment Selection
        ttk.Label(left_frame, text="Select Experiment:", font=("Arial", 12, "bold")).pack(pady=(0,5), anchor="w")
        self.exp_combo = ttk.Combobox(left_frame, values=[exp["name"] for exp in EXPERIMENTS], state="readonly", width=40)
        self.exp_combo.pack(fill=tk.X, pady=(0,10))
        self.exp_combo.bind("<<ComboboxSelected>>", self._on_experiment_select)

        # Parameter Configuration
        param_frame = ttk.LabelFrame(left_frame, text="Kalman Filter Parameters (1D)", padding="10")
        param_frame.pack(fill=tk.X, pady=10)

        params_to_show = ["F", "H", "Q", "R", "x0_hat", "P0_hat", "num_steps"]
        labels = ["State Transition (F):", "Measurement Matrix (H):", "Process Noise Cov (Q):",
                  "Measurement Noise Cov (R):", "Initial State Est (x̂₀):", "Initial Error Cov (P₀):",
                  "Number of Time Steps:"]

        for i, param_key in enumerate(params_to_show):
            row_frame = ttk.Frame(param_frame)
            row_frame.pack(fill=tk.X, pady=2)
            ttk.Label(row_frame, text=labels[i], width=22).pack(side=tk.LEFT)
            self.param_vars[param_key] = tk.StringVar()
            entry = ttk.Entry(row_frame, textvariable=self.param_vars[param_key], width=15)
            entry.pack(side=tk.LEFT, padx=5)
        
        # Buttons
        button_frame = ttk.Frame(left_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        self.run_button = ttk.Button(button_frame, text="Run Simulation", command=self._run_simulation)
        self.run_button.pack(side=tk.LEFT, padx=5)
        
        self.reset_button = ttk.Button(button_frame, text="Reset Parameters", command=self._reset_parameters)
        self.reset_button.pack(side=tk.LEFT, padx=5)

        # Teacher's Notes / Message Area
        msg_frame = ttk.LabelFrame(left_frame, text="Experiment Info & Messages", padding="10")
        msg_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        self.message_text = tk.Text(msg_frame, wrap=tk.WORD, height=10, relief=tk.SOLID, borderwidth=1)
        self.message_text.pack(fill=tk.BOTH, expand=True)
        self.message_text.config(state=tk.DISABLED) # Read-only

        # --- Right Pane (Plot) ---
        right_frame = ttk.Frame(main_pane, padding="10")
        main_pane.add(right_frame, weight=3)
        
        plot_container_frame = ttk.LabelFrame(right_frame, text="Simulation Results", padding="10")
        plot_container_frame.pack(fill=tk.BOTH, expand=True)

        self.fig, self.ax = plt.subplots(2, 1, figsize=(7, 6), gridspec_kw={'height_ratios': [3, 1]}, sharex=True)
        plt.subplots_adjust(hspace=0.1) # Reduce space between subplots

        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_container_frame)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill=tk.BOTH, expand=True)
        
        self.toolbar = NavigationToolbar2Tk(self.canvas, plot_container_frame)
        self.toolbar.update() # Important for displaying it

    def _update_message_area(self, text, append=False, level="info"):
        self.message_text.config(state=tk.NORMAL)
        if not append:
            self.message_text.delete("1.0", tk.END)
        
        prefix = ""
        if level == "error":
            prefix = "ERROR: "
        elif level == "warning":
            prefix = "WARNING: "
            
        self.message_text.insert(tk.END, prefix + text + "\n")
        self.message_text.config(state=tk.DISABLED)

    def _on_experiment_select(self, event=None):
        selected_index = self.exp_combo.current()
        if selected_index >= 0:
            self._load_experiment_data(selected_index)

    def _load_experiment_data(self, index):
        self.experiment_data = EXPERIMENTS[index]
        self.exp_combo.current(index) # Ensure combobox reflects this
        
        for key, value in self.experiment_data["params"].items():
            if key in self.param_vars:
                self.param_vars[key].set(value)
        
        self._update_message_area(self.experiment_data["description"])
        self._clear_plot()

    def _reset_parameters(self):
        if self.experiment_data:
            current_index = self.exp_combo.current()
            self._load_experiment_data(current_index) # Reload current experiment's defaults
            self._update_message_area(f"Parameters reset to defaults for '{self.experiment_data['name']}'.\n" + self.experiment_data["description"])
        else:
            self._update_message_area("No experiment selected to reset.", level="warning")
            
    def _clear_plot(self):
        self.ax[0].clear()
        self.ax[1].clear()
        self.ax[0].set_ylabel("Value")
        self.ax[0].grid(True)
        self.ax[1].set_xlabel("Time Step")
        self.ax[1].set_ylabel("Error (True-Est)")
        self.ax[1].grid(True)
        self.ax[0].set_title("Kalman Filter Simulation")
        self.canvas.draw_idle()

    def _get_params_from_gui(self):
        try:
            params = {}
            # For 1D, F, H, Q, R, x0_hat, P0_hat are scalars
            params['F'] = np.array([[float(self.param_vars['F'].get())]])
            params['H'] = np.array([[float(self.param_vars['H'].get())]])
            params['Q'] = np.array([[float(self.param_vars['Q'].get())]])
            params['R'] = np.array([[float(self.param_vars['R'].get())]])
            params['x0_hat'] = np.array([[float(self.param_vars['x0_hat'].get())]])
            params['P0_hat'] = np.array([[float(self.param_vars['P0_hat'].get())]])
            params['num_steps'] = int(self.param_vars['num_steps'].get())
            
            if params['num_steps'] <= 0:
                raise ValueError("Number of time steps must be positive.")
            if params['Q'][0,0] < 0 or params['R'][0,0] < 0 or params['P0_hat'][0,0] < 0:
                raise ValueError("Covariance values (Q, R, P0) cannot be negative.")

            return params
        except ValueError as e:
            self._update_message_area(f"Invalid parameter input: {e}", level="error", append=True)
            return None

    def _run_simulation(self):
        if not self.experiment_data:
            self._update_message_area("Please select an experiment first.", level="error")
            return

        kf_params = self._get_params_from_gui()
        if not kf_params:
            return

        self._update_message_area("Running simulation...", append=True)

        # Get true system parameters
        true_sys = self.experiment_data["true_system"]
        num_steps = kf_params['num_steps']

        # --- Simulate True System and Measurements ---
        x_true = np.zeros((1, num_steps))
        z_measured = np.zeros((1, num_steps))
        
        current_x_true = np.array([[true_sys["initial_true_state"]]])
        true_F_matrix = np.array([[true_sys["true_F"]]])
        true_H_matrix = np.array([[true_sys["true_H"]]])

        for t in range(num_steps):
            # True process noise (w_t)
            process_noise_w = np.random.normal(0, true_sys["true_Q_stddev"])
            current_x_true = true_F_matrix @ current_x_true + np.array([[process_noise_w]])
            x_true[:, t] = current_x_true.flatten()

            # True measurement noise (v_t)
            measurement_noise_v = np.random.normal(0, true_sys["true_R_stddev"])
            z_measured[:, t] = (true_H_matrix @ current_x_true + np.array([[measurement_noise_v]])).flatten()
        # --- Kalman Filter Estimation ---
        x_estimated = np.zeros((1, num_steps))
        P_covariance = np.zeros((1, 1, num_steps)) # Store P_t|t (scalar for 1D)
        
        x_hat_t = kf_params['x0_hat']
        P_t = kf_params['P0_hat']

        for t in range(num_steps):
            # Predict
            x_hat_pred, P_pred = kf_predict(x_hat_t, P_t, kf_params['F'], kf_params['Q'])
            
            # Update
            z_t = np.array([[z_measured[0, t]]])
            x_hat_t, P_t, _, _, _ = kf_update(x_hat_pred, P_pred, z_t, kf_params['H'], kf_params['R'])
            
            x_estimated[:, t] = x_hat_t.flatten()
            P_covariance[:, :, t] = P_t

        # --- Plot Results ---
        self._plot_results(x_true, z_measured, x_estimated, P_covariance)
        self._update_message_area("Simulation complete.", append=True)

    def _plot_results(self, x_true, z_measured, x_estimated, P_covariance):
        self.ax[0].clear()
        self.ax[1].clear()
        
        time_steps = np.arange(x_true.shape[1])

        # Top plot: States
        self.ax[0].plot(time_steps, x_true[0, :], 'k-', label='True State ($x_t$)', linewidth=2, alpha=0.7)
        self.ax[0].plot(time_steps, z_measured[0, :], 'rx', label='Measurements ($z_t$)', markersize=4, alpha=0.6)
        self.ax[0].plot(time_steps, x_estimated[0, :], 'b--', label='KF Estimate ($\hat{x}_{t|t}$)', linewidth=2)
        
        # Plot +/- 2 sigma bounds for 1D case
        std_dev_P = np.sqrt(P_covariance[0, 0, :])
        self.ax[0].fill_between(time_steps, x_estimated[0, :] - 2*std_dev_P, 
                                x_estimated[0, :] + 2*std_dev_P, color='blue', alpha=0.2, label='$\pm 2\sigma$ Bounds')

        self.ax[0].set_ylabel("Value")
        self.ax[0].legend(loc='upper right')
        self.ax[0].grid(True)
        self.ax[0].set_title(f"Kalman Filter Simulation: {self.experiment_data['name']}")

        # Bottom plot: Estimation Error
        estimation_error = x_true[0, :] - x_estimated[0, :]
        self.ax[1].plot(time_steps, estimation_error, 'g-', label='Error ($x_t - \hat{x}_{t|t}$)')
        self.ax[1].fill_between(time_steps, -2*std_dev_P, 2*std_dev_P, color='gray', alpha=0.3, label='$\pm 2\sigma$ (from $P_{t|t}$)')
        self.ax[1].plot(time_steps, np.zeros_like(time_steps), 'k:', alpha=0.5) # Zero line

        self.ax[1].set_xlabel("Time Step")
        self.ax[1].set_ylabel("Error")
        self.ax[1].legend(loc='upper right')
        self.ax[1].grid(True)
        
        self.canvas.draw_idle()

if __name__ == '__main__':
    root = tk.Tk()
    app = KalmanFilterApp(root)
    root.mainloop()