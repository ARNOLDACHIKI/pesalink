import logging
import numpy as np
from sklearn.ensemble import IsolationForest

def detect_anomalies(records):
    """
    Detect anomalies among account records using an Isolation Forest.
    Expects records to be a list of dict with at least 'balance' and 'recent_transactions' fields.
    Returns a list of indices of records flagged as anomalies.
    """
    n = len(records)
    if n == 0:
        return []
    if n < 5:
        # Not enough data to reliably detect anomalies
        logging.warning("Not enough records to perform anomaly detection.")
        return []
    # Prepare feature matrix
    balances = []
    num_txns = []
    avg_txn_amounts = []
    for rec in records:
        # Balance might be string or numeric
        try:
            bal = float(rec.get("balance", 0))
        except:
            bal = 0.0
        balances.append(bal)
        # Recent transactions: parse string of amounts
        txns_str = rec.get("recent_transactions", "")
        txns = []
        if txns_str:
            # The transactions are assumed separated by ';'
            try:
                txns = [float(x) for x in str(txns_str).split(';') if x]
            except:
                txns = []
        count = len(txns)
        num_txns.append(count)
        if count > 0:
            avg_txn_amounts.append(sum(txns) / count)
        else:
            avg_txn_amounts.append(0.0)
    # Convert to numpy array of shape (n_samples, n_features)
    X = np.column_stack((balances, num_txns, avg_txn_amounts))
    # Train Isolation Forest
    try:
        iso = IsolationForest(n_estimators=100, contamination=0.02, random_state=42)
        preds = iso.fit_predict(X)
    except Exception as e:
        logging.error(f"Anomaly detection model failed: {e}")
        return []
    # IsolationForest returns -1 for anomaly, 1 for normal
    anomalies = [idx for idx, pred in enumerate(preds) if pred == -1]
    logging.info(f"Anomaly detection complete: flagged {len(anomalies)} out of {n} records as suspicious.")
    return anomalies
