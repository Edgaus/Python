import numpy as np
from scipy.interpolate import UnivariateSpline
import os # <--- NEW IMPORT FOR MANAGING PATHS DIRECTLY

def smooth_and_interpolate_txt(input_filename, output_filename, x_initial, x_final, num_points, smoothing_factor=0.05, degree=2):
    
    # -----------------------------------------------------------------
    # PATH FIX: Get the absolute path to the directory of THIS script.
    # This prevents FileNotFoundError regardless of your terminal location.
    # -----------------------------------------------------------------
    script_dir = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(script_dir, 'Data_to_interpolate', input_filename)
    
    # Also build an absolute output filepath if it isn't one already
    if not os.path.isabs(output_filename):
        output_filename = os.path.join(script_dir, 'Data_now_interpolated', output_filename)
        
    # Ensure the output directory exists so it doesn't crash on saving
    os.makedirs(os.path.dirname(output_filename), exist_ok=True)
    
    # 1. Load the data with the usecols=(0, 1) fix
    try:
        data = np.loadtxt(filepath, usecols=(0, 1))
    except ValueError:
        try:
            data = np.loadtxt(filepath, skiprows=1, usecols=(0, 1))
        except Exception as e:
            print(f"Error loading '{filepath}' after skipping header: {e}")
            return
    except Exception as e:
        print(f"Unexpected error loading the file '{filepath}': {e}")
        return

    # Extract and Sort X and Y columns
    x_original = data[:, 0]
    y_original = data[:, 1]
    
    sort_indices = np.argsort(x_original)
    x_original = x_original[sort_indices]
    y_original = y_original[sort_indices]

    # 2. Create the Smoothing Spline
    spline_func = UnivariateSpline(x_original, y_original, k=degree, s=smoothing_factor)

    # 3. Generate the new X array and calculate new Y values
    x_new = np.linspace(x_initial, x_final, num_points)
    y_new = spline_func(x_new)

    # 4. Save the data
    new_data = np.column_stack((x_new, y_new))
    np.savetxt(output_filename, new_data, fmt='%.8f', delimiter='\t', 
               header='X_Interpolated\tY_Interpolated', comments='')

    print(f"Success! Saved to:\n'{output_filename}'\nusing degree {degree} with smoothing factor {smoothing_factor}.")

if __name__ == "__main__":
    
    # The name of your file exactly as it is saved on your computer
    name = 'm925_Sanatana_01'
    INPUT_FILE = f'{name}.txt'
    OUTPUT_FILE = f'{name}_fitted.txt'
    
    X_START = 350
    X_END = 700
    POINTS = 700-349
    
    smooth_and_interpolate_txt(
        input_filename=INPUT_FILE, 
        output_filename=OUTPUT_FILE, 
        x_initial=X_START, 
        x_final=X_END, 
        num_points=POINTS, 
        smoothing_factor=0.01,  
        degree=2                
    )