import logging
from datetime import datetime
import pandas as pd
from flask import Flask, request, render_template

from validation import validate_accounts, mask_account_number
from anomaly import detect_anomalies
from scheduler import start_validation_scheduler

app = Flask(__name__)

# Configure logging at module import
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

# Global variables to hold state
current_data_file = 'data/sample_accounts.csv'
last_valid_results = []
last_invalid_results = []
last_run_time = None

def validate_all():
    """Read the current data file, run validation and anomaly detection, update global results."""
    global last_valid_results, last_invalid_results, last_run_time
    logging.info(f"Starting validation for data file: {current_data_file}")
    try:
        df = pd.read_csv(current_data_file, dtype=str)
    except Exception as e:
        logging.error(f"Failed to read data file {current_data_file}: {e}")
        return
    records = df.to_dict(orient='records')
    # Performance of validation
    valid_accounts, invalid_accounts = validate_accounts(records)
    # Performing anomaly detection on valid accounts
    suspicious_indices = detect_anomalies(valid_accounts)
    # Mark suspicious accounts in the valid list
    for rec in valid_accounts:
        rec['suspicious'] = False
    for idx in suspicious_indices:
        if 0 <= idx < len(valid_accounts):
            valid_accounts[idx]['suspicious'] = True
    # Mask account numbers for output security
    for rec in valid_accounts:
        rec['account_number'] = mask_account_number(rec.get('account_number'))
    for rec in invalid_accounts:
        rec['account_number'] = mask_account_number(rec.get('account_number'))
    # Updating the global results
    last_valid_results = valid_accounts
    last_invalid_results = invalid_accounts
    last_run_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logging.info(f"Validation run complete at {last_run_time}: "
                 f"{len(valid_accounts)} valid, {len(invalid_accounts)} invalid, {len(suspicious_indices)} suspicious.")

@app.route('/', methods=['GET', 'POST'])
def index():
    global current_data_file
    if request.method == 'POST':
        file = request.files.get('file')
        if file and file.filename.endswith('.csv'):
            upload_path = 'data/uploaded_accounts.csv'
            try:
                file.save(upload_path)
                current_data_file = upload_path
                logging.info(f"New file uploaded and saved to {upload_path}.")
                # Run validation on the new file immediately
                validate_all()
            except Exception as e:
                logging.error(f"Error saving uploaded file: {e}")
        else:
            logging.warning("No file uploaded or file type is not CSV.")
    # For GET request or after processing POST, render the dashboard
    return render_template('dashboard.html',
                           valid_accounts=last_valid_results,
                           invalid_accounts=last_invalid_results,
                           last_run_time=last_run_time)

if __name__ == '__main__':
    # Start scheduler for periodic validation every hour
    start_validation_scheduler(validate_all, interval_hours=1)
    # Perform an initial validation run at startup
    try:
        validate_all()
    except Exception as e:
        logging.error(f"Initial validation run failed: {e}")
    # Run the Flask development server
    app.run(host='0.0.0.0', port=5000)
