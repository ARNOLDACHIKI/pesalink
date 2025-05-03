import logging
import random

# Define known valid bank codes for simulation
VALID_BANK_CODES = {"ABC", "DEF", "GHI", "JKL", "XYZ"}

def mask_account_number(acc_num):
    """Mask an account number for security: reveal only last 4 digits."""
    if acc_num is None:
        return None
    # Convert to string in case it's numeric type
    s = str(acc_num)
    if len(s) <= 4:
        return ""
    return "*" * (len(s) - 4) + s[-4:]

def simulate_bank_api(account_number, bank_code):
    """
    Simulate an external bank API call to validate an account.
    Returns (True, None) if account is valid, or (False, reason_code) if invalid.
    May raise an exception to simulate API errors.
    """
    # Simulate network issues randomly (e.g., 5% chance)
    if random.random() < 0.05:
        raise Exception("Network timeout")
    # Simulate account validation logic:
    # For simplicity, use the last digit of account number to decide outcome
    try:
        last_digit = int(str(account_number)[-1])
    except Exception:
        # If account_number is not numeric, consider it invalid
        return False, "AC01"
    # If last digit is 0 or 1, simulate account not found (invalid account)
    if last_digit in [0, 1]:
        return False, "AC01"
    # If last digit is 2, simulate account closed
    if last_digit == 2:
        return False, "AC04"
    # If last digit is 3, simulate account blocked
    if last_digit == 3:
        return False, "AC06"
    # Otherwise, account is valid
    return True, None

def validate_record(record):
    """
    Validate a single account record. Returns (is_valid, reason_code).
    If valid, reason_code will be None. If invalid, is_valid will be False with a reason code.
    """
    acc_num = record.get("account_number", "")
    bank_code = record.get("bank_code", "")
    status = record.get("status", "").lower()
    account_type = record.get("account_type", "")
    # Basic checks for account number format
    if  not acc_num.isdigit():
        # Account number missing or contains non-digit characters
        return False, "AC01"
    # Check account number length (simulate expected length of 10 digits)
    if len(acc_num) != 10:
        return False, "AC01"
    # Check bank code validity
    if bank_code not in VALID_BANK_CODES:
        return False, "BANK_CODE_INVALID"
    # Check account status
    if status != "active":
        # If account is closed or inactive, mark accordingly
        if status == "closed":
            return False, "AC04"
        else:
            # Any other statu treat as closed 
            return False, "AC04"
    # (Optional) Check account type if needed (e.g., if certain types are not allowed)
    # For example, if account_type is "Loan", mark as invalid account type (AC13)
    if account_type.lower() == "loan":
        return False, "AC13"
    # If basic checks passed, simulate external API validation
    try:
        api_ok, reason = simulate_bank_api(acc_num, bank_code)
    except Exception as e:
        # Log the API error with masked account number
        logging.error(f"API validation error for account {mask_account_number(acc_num)}: {e}")
        return False, "API_ERROR"
    if not api_ok:
        # If API said invalid, propagate the reason code from API
        return False, reason
    # If all checks pass and API returned valid
    return True, None

def validate_accounts(records):
    """
    Validate a list of account records using multiprocessing for parallelism.
    Returns a tuple (valid_accounts_list, invalid_accounts_list).
    Each account in the invalid list will include a 'reason' code.
    """
    from multiprocessing import Pool, cpu_count
    results = []
    try:
        # Use a pool of workers to validate in parallel
        pool_size = min(4, cpu_count())  # limit pool size to 4 or CPU count, whichever is smaller
        with Pool(processes=pool_size) as pool:
            results = pool.map(validate_record, records)
    except Exception as e:
        # If any issue with parallel processing, fallback to sequential
        logging.error(f"Multiprocessing validation failed, falling back to sequential: {e}")
        results = list(map(validate_record, records))
    valid_accounts = []
    invalid_accounts = []
    for record, (is_valid, reason) in zip(records, results):
        if is_valid:
            # Keep valid record
            valid_accounts.append(record)
        else:
            # Add reason code to the record and collect as invalid
            record_copy = dict(record)
            record_copy["reason"] = reason
            invalid_accounts.append(record_copy)
    # Log summary
    logging.info(f"Validation completed: {len(valid_accounts)} valid, {len(invalid_accounts)} invalid.")
    return valid_accounts, invalid_accounts