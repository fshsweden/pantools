import re
from datetime import datetime

def generate_filename_with_datetime(prefix, extension):
    today = datetime.now()
    today = today.strftime("%Y%m%d-%H%M%S")
    return f"{prefix}-{today}.{extension}"

def clean_name(tkr):
    # clean name!
    return re.sub('[^\w\-_\. ]', '_', tkr)

