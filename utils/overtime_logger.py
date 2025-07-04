import os
import csv
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import uuid

LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')

FIELDNAMES = [
    'id',
    'person',
    'start_time',
    'end_time',
    'duration_hours',
    'issue_description',
    'resolution_notes'
]

def get_log_path(person, year, month):
    person_dir = os.path.join(LOGS_DIR, person)
    os.makedirs(person_dir, exist_ok=True)
    filename = f"{year:04d}-{month:02d}.csv"
    return os.path.join(person_dir, filename)

def load_overtime_logs(person, year, month):
    path = get_log_path(person, year, month)
    logs = []
    if os.path.exists(path):
        with open(path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if 'id' not in row or not row['id']:
                    row['id'] = str(uuid.uuid4())
                logs.append(row)
    return logs

def validate_overtime_entry(start_str, end_str):
    try:
        start = datetime.fromisoformat(start_str)
        end = datetime.fromisoformat(end_str)
    except Exception:
        return False, 'Invalid date format.'
    if end <= start:
        return False, 'End time must be after start time.'
    duration = (end - start).total_seconds() / 3600.0
    return True, duration

def save_overtime_entry(person, year, month, entry):
    path = get_log_path(person, year, month)
    file_exists = os.path.exists(path)
    if 'id' not in entry or not entry['id']:
        entry['id'] = str(uuid.uuid4())
    with open(path, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if not file_exists:
            writer.writeheader()
        writer.writerow(entry)

def update_overtime_entry(person, year, month, entry_id, updated_entry):
    path = get_log_path(person, year, month)
    logs = []
    updated = False
    if os.path.exists(path):
        with open(path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('id') == entry_id:
                    row.update(updated_entry)
                    updated = True
                logs.append(row)
        with open(path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()
            writer.writerows(logs)
    return updated

def export_logs_to_pdf(person, year, month, output_pdf_path):
    """
    Export the overtime logs for a given user and month to a PDF file.
    """
    logs = load_overtime_logs(person, year, month)
    c = canvas.Canvas(output_pdf_path, pagesize=letter)
    width, height = letter
    c.setFont("Helvetica", 12)
    y = height - 40
    c.drawString(40, y, f"Overtime Logs for {person} - {year}-{month:02d}")
    y -= 30
    headers = FIELDNAMES
    c.setFont("Helvetica-Bold", 10)
    for i, header in enumerate(headers):
        c.drawString(40 + i*120, y, header)
    c.setFont("Helvetica", 10)
    y -= 20
    for log in logs:
        for i, header in enumerate(headers):
            value = str(log.get(header, ""))
            c.drawString(40 + i*120, y, value)
        y -= 18
        if y < 40:
            c.showPage()
            y = height - 40
    c.save()

def archive_old_csvs(person, current_year, current_month):
    """
    Move all CSVs for the user that are not for the current month to logs/_archive/.
    """
    person_dir = os.path.join(LOGS_DIR, person)
    archive_dir = os.path.join(LOGS_DIR, "_archive", person)
    os.makedirs(archive_dir, exist_ok=True)
    for fname in os.listdir(person_dir):
        if fname.endswith(".csv"):
            try:
                year, month = map(int, fname[:-4].split("-"))
                if year != current_year or month != current_month:
                    src = os.path.join(person_dir, fname)
                    dst = os.path.join(archive_dir, fname)
                    os.rename(src, dst)
            except Exception:
                continue 