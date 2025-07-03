from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime, timedelta
from utils.rotation_manager import get_standby_person, load_roster, save_roster
from utils.overtime_logger import load_overtime_logs, validate_overtime_entry, save_overtime_entry
from config import config, ensure_directories

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

# Ensure required directories exist
ensure_directories()

@app.route('/')
def index():
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    # For now, assume current user is 'errol'
    current_user = 'errol'
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
    overtime_logs = load_overtime_logs(current_user, year, month)
    total_overtime_hours = sum(float(log.get('duration_hours', 0)) for log in overtime_logs)
    
    # Load roster data for team members and overrides
    roster_data = load_roster()
    team_members = [m for m in roster_data.get('team_members', []) if m.get('active', True)]
    overrides = roster_data.get('overrides', {})
    
    # Sort overrides by date descending, get 5 most recent
    sorted_overrides = sorted(overrides.items(), key=lambda x: x[0], reverse=True)
    recent_overrides = [
        {'date': date, 'person': person}
        for date, person in sorted_overrides[:5]
    ]
    
    # Get recent overtime activity (last 5 entries across all team members)
    recent_overtime = []
    for member in team_members:
        member_logs = load_overtime_logs(member['name'], year, month)
        recent_overtime.extend(member_logs[:2])  # Get 2 most recent per member
    
    # Sort by start time and get 5 most recent
    recent_overtime.sort(key=lambda x: x.get('start_time', ''), reverse=True)
    recent_overtime = recent_overtime[:5]
    
    # Generate notifications
    notifications = []
    if current_standby == current_user:
        notifications.append("You are currently on standby duty")
    if next_standby == current_user:
        notifications.append("You will be on standby next week")
    if total_overtime_hours > config.OVERTIME_WARNING_THRESHOLD:
        notifications.append(f"High overtime this month: {total_overtime_hours:.1f} hours")
    
    # Monthly overtime limit from config
    monthly_overtime_limit = config.MONTHLY_OVERTIME_LIMIT
    
    return render_template(
        'dashboard.html',
        current_user=current_user,
        current_standby=current_standby,
        next_standby=next_standby,
        today=today,
        next_week=next_week,
        total_overtime_hours=total_overtime_hours,
        month_name=month_name,
        year=year,
        recent_overrides=recent_overrides,
        recent_overtime=recent_overtime,
        team_members=team_members,
        today_dt=today_dt,
        get_standby_person=get_standby_person,
        timedelta=timedelta,
        notifications=notifications,
        monthly_overtime_limit=monthly_overtime_limit,
        config=config
    )

@app.route('/calendar')
def calendar():
    try:
        # Determine current month and year
        today = datetime.today()
        year = request.args.get('year', today.year, type=int)
        month = request.args.get('month', today.month, type=int)
        
        # Validate year and month
        if year < 1900 or year > 2100:
            year = today.year
        if month < 1 or month > 12:
            month = today.month
        
        # First and last day of the month
        first_day = datetime(year, month, 1)
        if month == 12:
            next_month = datetime(year + 1, 1, 1)
        else:
            next_month = datetime(year, month + 1, 1)
        num_days = (next_month - first_day).days
        
        # Load roster data for colors
        roster_data = load_roster()
        team_members = {m['name']: m.get('color', '#6c757d') for m in roster_data.get('team_members', [])}
        person_colors = {**config.DEFAULT_PERSON_COLORS, **team_members}
        
        events = []
        today_str = today.strftime('%Y-%m-%d')
        
        for i in range(num_days):
            day = first_day + timedelta(days=i)
            date_str = day.strftime('%Y-%m-%d')
            person = get_standby_person(date_str)
            
            if person:
                # Determine if this is today, past, or future
                is_today = date_str == today_str
                is_past = date_str < today_str
                
                event_data = {
                    'title': person,
                    'start': date_str,
                    'end': date_str,  # single-day event
                    'color': person_colors.get(person, '#6c757d'),
                    'extendedProps': {
                        'isToday': is_today,
                        'isPast': is_past,
                        'isOverride': date_str in roster_data.get('overrides', {})
                    }
                }
                
                # Add special styling for today
                if is_today:
                    event_data['classNames'] = ['fc-event-today']
                
                events.append(event_data)
        
        return render_template('calendar.html', events=events, config=config)
        
    except Exception as e:
        # Log the error for debugging
        print(f"Calendar error: {e}")
        # Return a minimal template with error handling
        return render_template('calendar.html', events=[], config=config)

@app.route('/api/calendar/<int:year>/<int:month>')
def api_calendar(year, month):
    """API endpoint for calendar data"""
    try:
        # Validate year and month
        if year < 1900 or year > 2100 or month < 1 or month > 12:
            return {'error': 'Invalid year or month'}, 400
        
        # First and last day of the month
        first_day = datetime(year, month, 1)
        if month == 12:
            next_month = datetime(year + 1, 1, 1)
        else:
            next_month = datetime(year, month + 1, 1)
        num_days = (next_month - first_day).days
        
        # Load roster data for colors
        roster_data = load_roster()
        team_members = {m['name']: m.get('color', '#6c757d') for m in roster_data.get('team_members', [])}
        person_colors = {**config.DEFAULT_PERSON_COLORS, **team_members}
        
        events = []
        today = datetime.today()
        today_str = today.strftime('%Y-%m-%d')
        
        for i in range(num_days):
            day = first_day + timedelta(days=i)
            date_str = day.strftime('%Y-%m-%d')
            person = get_standby_person(date_str)
            
            if person:
                is_today = date_str == today_str
                is_past = date_str < today_str
                
                event_data = {
                    'title': person,
                    'start': date_str,
                    'end': date_str,
                    'color': person_colors.get(person, '#6c757d'),
                    'extendedProps': {
                        'isToday': is_today,
                        'isPast': is_past,
                        'isOverride': date_str in roster_data.get('overrides', {})
                    }
                }
                
                if is_today:
                    event_data['classNames'] = ['fc-event-today']
                
                events.append(event_data)
        
        return {'events': events, 'month': month, 'year': year}
        
    except Exception as e:
        print(f"API Calendar error: {e}")
        return {'error': 'Failed to load calendar data'}, 500

@app.route('/roster', methods=['GET'])
def roster():
    roster_data = load_roster()
    team_members = roster_data.get('team_members', [])
    overrides = roster_data.get('overrides', {})
    rotation = roster_data.get('rotation', [])
    today = datetime.today().strftime('%Y-%m-%d')
    return render_template('roster.html', team_members=team_members, overrides=overrides, rotation=rotation, today=today)

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
    start_date = request.form.get('override_start_date')
    end_date = request.form.get('override_end_date')
    person = request.form.get('override_person')
    
    if not start_date or not end_date or not person:
        flash('Start date, end date, and person are required for override.', 'warning')
        return redirect(url_for('roster'))
    
    # Add overrides for each date in the range
    from datetime import datetime, timedelta
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    
    current = start
    while current <= end:
        date_str = current.strftime('%Y-%m-%d')
        overrides[date_str] = person
        current += timedelta(days=1)
    
    roster_data['overrides'] = overrides
    save_roster(roster_data)
    flash(f'Override added for {start_date} to {end_date}!', 'success')
    return redirect(url_for('roster'))

@app.route('/roster/remove_override', methods=['POST'])
def remove_override():
    roster_data = load_roster()
    date = request.form.get('date')
    overrides = roster_data.get('overrides', {})
    if date in overrides:
        overrides.pop(date)
        roster_data['overrides'] = overrides
        save_roster(roster_data)
        flash(f'Override for {date} removed.', 'success')
    else:
        flash('Override not found.', 'warning')
    return redirect(url_for('roster'))

@app.route('/roster/toggle_member', methods=['POST'])
def toggle_member():
    roster_data = load_roster()
    name = request.form.get('name')
    for member in roster_data.get('team_members', []):
        if member.get('name') == name:
            member['active'] = not member.get('active', True)
            break
    save_roster(roster_data)
    flash(f'{name} status toggled.', 'success')
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
    now = datetime.now()
    year, month = now.year, now.month
    roster_data = load_roster()
    team_members = [m for m in roster_data.get('team_members', []) if m.get('active', True)]

    # For GET
    selected_person = request.args.get('person')
    if not selected_person:
        today_str = now.strftime('%Y-%m-%d')
        selected_person = get_standby_person(today_str)

    if request.method == 'POST':
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')
        issue_description = request.form.get('issue_description', '')
        resolution_notes = request.form.get('resolution_notes', '')

        start_date = start_time[:10]
        person = get_standby_person(start_date)

        valid, duration_or_msg = validate_overtime_entry(start_time, end_time)
        if valid:
            entry = {
                'person': person,
                'start_time': start_time,
                'end_time': end_time,
                'duration_hours': f"{duration_or_msg:.2f}",
                'issue_description': issue_description,
                'resolution_notes': resolution_notes
            }
            save_overtime_entry(person, year, month, entry)
            flash('Overtime entry saved!', 'success')
        else:
            flash(duration_or_msg, 'danger')

        return redirect(url_for('overtime', person=person))

    overtime_logs = load_overtime_logs(selected_person, year, month)
    return render_template('overtime.html',
                           overtime_logs=overtime_logs,
                           team_members=team_members,
                           selected_person=selected_person)

@app.route('/roster/edit_member', methods=['POST'])
def edit_member():
    roster_data = load_roster()
    name_original = request.form.get('name_original')
    name = request.form.get('name')
    color = request.form.get('color')
    active = bool(request.form.get('active'))
    
    # Find and update the member
    for member in roster_data.get('team_members', []):
        if member.get('name') == name_original:
            member['name'] = name
            member['color'] = color
            member['active'] = active
            break
    
    save_roster(roster_data)
    flash(f'Team member {name_original} updated!', 'success')
    return redirect(url_for('roster'))

if __name__ == '__main__':
    app.run(debug=True) 