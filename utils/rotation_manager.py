import json
import os
from datetime import datetime, timedelta

ROSTER_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'roster.json')

def load_roster():
    """Load the roster from the JSON file."""
    with open(ROSTER_PATH, 'r') as f:
        return json.load(f)

def is_active(person_name):
    """Check if a person is active in the roster."""
    roster_data = load_roster()
    for member in roster_data.get('team_members', []):
        if member.get('name') == person_name:
            return member.get('active', True)
    return False

def get_standby_person(date: str):
    """
    Get the standby person for a given date (YYYY-MM-DD).
    Checks overrides first, else cycles the rotation pattern weekly.
    Returns the standby person's name.
    """
    roster = load_roster()
    rotation = roster.get('rotation', [])
    overrides = roster.get('overrides', {})
    
    # Filter rotation to only include active members
    active_rotation = [p for p in rotation if is_active(p)]
    
    if not active_rotation:
        return None
    # Check overrides
    if date in overrides:
        return overrides[date]
    # Cycle rotation weekly
    # Find the first Monday in the rotation (or use a fixed epoch)
    epoch = roster.get('epoch', '2024-01-01')
    d = datetime.strptime(date, '%Y-%m-%d')
    epoch_date = datetime.strptime(epoch, '%Y-%m-%d')
    weeks_since = (d - epoch_date).days // 7
    idx = weeks_since % len(active_rotation)
    return active_rotation[idx]

def test_rotation_manager():
    """Test function: print standby person for a list of dates."""
    test_dates = [
        '2024-06-03', '2024-06-10', '2024-06-17', '2024-06-24',
        '2024-07-01', '2024-07-08', '2024-07-15', '2024-07-22',
    ]
    for date in test_dates:
        person = get_standby_person(date)
        print(f"{date}: {person}")

def save_roster(roster):
    """Save the roster to the JSON file."""
    with open(ROSTER_PATH, 'w') as f:
        json.dump(roster, f, indent=2)

if __name__ == "__main__":
    test_rotation_manager() 