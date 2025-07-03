from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime, timedelta
from utils.rotation_manager import get_standby_person, load_roster, save_roster
from utils.overtime_logger import load_overtime_logs, validate_overtime_entry, save_overtime_entry
import os

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'super-secret-key-change-this')

@app.route('/dashboard')
def dashboard():
    # For now, assume current user is 'errol'
    person = 'errol'
    today_dt = datetime.today()
    today = today_dt.strftime('%Y-%m-%d')
    next_week_dt = today_dt + timedelta(days=7)
    next_week = next_week_dt.strftime('%Y-%m-%d')
    current_standby = get_standby_person(today)
    next_standby = get_standby_person(next_week)
    year = today_dt.year
    month = today_dt.month
    month_name = today_dt.strftime('%B')
    # Load and sum overtime logs for this month
    overtime_logs = load_overtime_logs(person, year, month)
    total_overtime_hours = sum(float(log.get('duration_hours', 0)) for log in overtime_logs)
    # Load overrides from roster.json
    roster_data = load_roster()
    overrides = roster_data.get('overrides', {})
    # Sort overrides by date descending, get 5 most recent
    sorted_overrides = sorted(overrides.items(), key=lambda x: x[0], reverse=True)
    recent_overrides = [
        {'date': date, 'person': person}
        for date, person in sorted_overrides[:5]
    ]
    return render_template(
        'dashboard.html',
        current_standby=current_standby,
        next_standby=next_standby,
        today=today,
        next_week=next_week,
        total_overtime_hours=f"{total_overtime_hours:.2f}",
        month_name=month_name,
        year=year,
        recent_overrides=recent_overrides
    )

@app.route('/calendar')
def calendar():
    # Determine current month and year
    today = datetime.today()
    year = request.args.get('year', today.year, type=int)
    month = request.args.get('month', today.month, type=int)
    # First and last day of the month
    first_day = datetime(year, month, 1)
    if month == 12:
        next_month = datetime(year + 1, 1, 1)
    else:
        next_month = datetime(year, month + 1, 1)
    num_days = (next_month - first_day).days
    # Hardcoded color mapping for demonstration
    person_colors = {
        'Alice': '#007bff',
        'Bob': '#28a745',
        'Charlie': '#ffc107',
        'Diana': '#dc3545'
    }
    events = []
    for i in range(num_days):
        day = first_day + timedelta(days=i)
        date_str = day.strftime('%Y-%m-%d')
        person = get_standby_person(date_str)
        if person:
            events.append({
                'title': person,
                'start': date_str,
                'end': date_str,  # single-day event
                'color': person_colors.get(person, '#6c757d')
            })
    return render_template('calendar.html', events=events)

@app.route('/roster', methods=['GET'])
def roster():
    roster_data = load_roster()
    team_members = roster_data.get('team_members', [])
    overrides = roster_data.get('overrides', {})
    rotation = roster_data.get('rotation', [])
    return render_template('roster.html', team_members=team_members, overrides=overrides, rotation=rotation)

@app.route('/roster/add_member', methods=['POST'])
def add_member():
    roster_data = load_roster()
    team_members = roster_data.get('team_members', [])
    name = request.form.get('name')
    color = request.form.get('color')
    active = bool(request.form.get('active'))
    # Prevent duplicate names
    if any(m.get('name') == name for m in team_members):
        flash('Member with this name already exists.', 'warning')
        return redirect(url_for('roster'))
    team_members.append({'name': name, 'color': color, 'active': active})
    roster_data['team_members'] = team_members
    save_roster(roster_data)
    flash('Team member added!', 'success')
    return redirect(url_for('roster'))

@app.route('/roster/add_override', methods=['POST'])
def add_override():
    roster_data = load_roster()
    overrides = roster_data.get('overrides', {})
    date = request.form.get('override_date')
    person = request.form.get('override_person')
    if not date or not person:
        flash('Date and person are required for override.', 'warning')
        return redirect(url_for('roster'))
    overrides[date] = person
    roster_data['overrides'] = overrides
    save_roster(roster_data)
    flash('Override added!', 'success')
    return redirect(url_for('roster'))

@app.route('/roster/update_rotation', methods=['POST'])
def update_rotation():
    roster_data = load_roster()
    # Always get the current rotation order from the form
    rotation = request.form.getlist('rotation[]')

    # Handle add person (only if not already in rotation)
    add_person = request.form.get('add')
    if add_person:
        if add_person not in rotation:
            rotation.append(add_person)
            roster_data['rotation'] = rotation
            save_roster(roster_data)
            flash(f'{add_person} added to rotation!', 'success')
        else:
            flash(f'{add_person} is already in rotation.', 'warning')
        return redirect(url_for('roster'))

    # Handle move action
    move = request.form.get('move')
    if move:
        direction, index = move.split(':')
        index = int(index)
        if direction == 'up' and index > 0:
            rotation[index], rotation[index - 1] = rotation[index - 1], rotation[index]
            flash(f"Moved {rotation[index]} up!", 'success')
        elif direction == 'down' and index < len(rotation) - 1:
            rotation[index], rotation[index + 1] = rotation[index + 1], rotation[index]
            flash(f"Moved {rotation[index]} down!", 'success')
        roster_data['rotation'] = rotation
        save_roster(roster_data)
        return redirect(url_for('roster'))

    # Handle removal
    remove = request.form.get('remove')
    if remove:
        if remove in rotation:
            rotation.remove(remove)
            roster_data['rotation'] = rotation
            save_roster(roster_data)
            flash(f'Removed {remove} from rotation!', 'success')
        else:
            flash(f'{remove} not found in rotation.', 'warning')
        return redirect(url_for('roster'))

    # Save on explicit save click
    if request.form.get('save'):
        roster_data['rotation'] = rotation
        save_roster(roster_data)
        flash('Rotation updated!', 'success')
        return redirect(url_for('roster'))

    # Default: just redirect
    return redirect(url_for('roster'))

@app.route('/overtime', methods=['GET', 'POST'])
def overtime():
    # For now, assume current user is 'errol'
    person = 'errol'
    now = datetime.now()
    year = now.year
    month = now.month
    if request.method == 'POST':
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')
        issue_description = request.form.get('issue_description', '')
        resolution_notes = request.form.get('resolution_notes', '')
        valid, duration_or_msg = validate_overtime_entry(start_time, end_time)
        if not valid:
            flash(duration_or_msg, 'danger')
        else:
            entry = {
                'start_time': start_time,
                'end_time': end_time,
                'duration_hours': f"{duration_or_msg:.2f}",
                'issue_description': issue_description,
                'resolution_notes': resolution_notes
            }
            save_overtime_entry(person, year, month, entry)
            flash('Overtime entry saved!', 'success')
        # After POST, reload logs and show page
    overtime_logs = load_overtime_logs(person, year, month)
    return render_template('overtime.html', overtime_logs=overtime_logs)

if __name__ == '__main__':
    app.run(debug=True) 