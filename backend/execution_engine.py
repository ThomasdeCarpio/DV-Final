import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
import traceback
import matplotlib

# Use 'Agg' backend so matplotlib doesn't try to open pop-up windows on the server
matplotlib.use('Agg')

def execute_and_capture_chart(code: str, dataset_path: str) -> dict:
    try:
        # 1. Clear any existing plots in memory
        plt.clf()
        plt.close('all')
        
        # 2. Load the specific dataset
        df = pd.read_csv(dataset_path)
        
        # 3. Define the local namespace for the exec() function
        # This provides the AI's code access to df, pd, plt, and sns
        local_vars = {
            'df': df,
            'pd': pd,
            'plt': plt,
            'sns': sns
        }
        
        # Set default seaborn theme for better looking charts
        sns.set_theme(style="whitegrid")
        
        # 4. Execute the human-approved code
        exec(code, {}, local_vars)
        
        # 5. Capture the output figure into a buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        
        # 6. Convert to Base64 to send via API
        image_base64 = base64.b64encode(buf.read()).decode('utf-8')
        
        # Close the plot to free memory
        plt.close()
        
        return {"status": "success", "image": image_base64}
        
    except Exception as e:
        # Capture the exact error so the user/frontend knows what went wrong
        error_traceback = traceback.format_exc()
        return {"status": "error", "error": str(e) + "\n\n" + error_traceback}