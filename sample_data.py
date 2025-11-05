from db import get_conn
from datetime import datetime, date

def seed():
    conn = get_conn(); c = conn.cursor()
    now = datetime.utcnow().isoformat()
    rows = [
        ("SN-ABC12345", "1TB", "TEAM1", "Premise A", date.today().isoformat(), date.today().isoformat(), "Case data A", "admin", now, "SN-ABC12345", "available"),
        ("SN-XYZ67890", "2TB", "TEAM2", "Premise B", date.today().isoformat(), date.today().isoformat(), "Case data B", "admin", now, "SN-XYZ67890", "sealed"),
    ]
    for r in rows:
        c.execute('INSERT INTO hdd_records (serial_no, unit_space, team_code, premise_name, date_search, date_seized, data_details, created_by, created_on, barcode_value, status) VALUES (?,?,?,?,?,?,?,?,?,?,?)', r)
    conn.commit(); conn.close()

if __name__ == "__main__":
    seed()
