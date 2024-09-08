from flask import request, render_template, redirect, url_for, flash, session
from main import users_collection, events_collection
from datetime import datetime
from app import server
from app.routes2 import (
    find_user_by_username,
    find_user_by_email,
    find_events_by_creator,
    find_events_by_participant,
    find_all_events,
    perform_search,
    find_event_by_name,
    update_event,
    delete_event,
    add_participation,
    update_participation,
    find_all_users,
    delete_user
)

server.secret_key = 'a_random_key'

# Set Login page
@server.route('/', methods=['GET'])
def login():
    return render_template('login.html')  # Set up page

# Login the system
@server.route('/login', methods=['POST'])
def login_action():
    username = request.form.get('username')
    password = request.form.get('password')
    
    if not username or not password:
        flash('Missing parameters.')
        return redirect(url_for('login'))
    
    role = authenticate_user(username, password)

    if role == 'administrator':
        session['username'] = username
        session['role'] = 'administrator'
        return redirect('/admin_role')
    elif role == 'user':
        session['username'] = username
        session['role'] = 'user'
        return redirect('/user')
    else:
        flash('Invalid credentials.')
        return redirect(url_for('login'))
    
# Identifies the user's role
def authenticate_user(username, password):
    if username == 'admin' and password == 'admin321':
        return 'administrator'
    
    user = find_user_by_username(username)
    if user and user.get('password') == password:
        return 'user'
    
    return None

# Logout of system
@server.route('/logout', methods=['POST'])
def logout():
    # Clear the session
    session.pop('username', None)
    session.pop('role', None)
    
    return redirect(url_for('login'))

# Set Register page
@server.route('/register', methods=['GET'])
def show_register():
    return render_template('register.html')  # Set up page

# User registry
@server.route('/register_action', methods=['POST'])
def register():
    # Get data from form
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    email = request.form.get('email')
    username = request.form.get('username')
    password = request.form.get('password')

    # Check for missing data
    if not all([first_name, last_name, email, username, password]):
        flash('All fields are required.')
        return redirect('/register')

    # Check if the username or email are used
    if find_user_by_username(username):
        flash('Username is already taken.')
        return redirect('/register')
    if find_user_by_email(email):
        flash('Email is already registered.')
        return redirect('/register')

    # Create a new user
    new_user = {'first_name' : first_name, 'last_name' : last_name, 'email' : email, 'username' : username, 'password' : password}

    # Save the user to the database
    users_collection.insert_one(new_user)

    # Flash success message and redirect to login
    flash('User registered successfully. Please log in.')
    return redirect('/')

# Set User page
@server.route('/user', methods=['GET'])
def show_user():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('user.html')

# Set Admin role menu
@server.route('/admin_role', methods=['GET'])
def admin_role():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if session['role'] != 'administrator':
        return redirect(url_for('show_user'))
    return render_template('admin_role.html')

# Set Admin page
@server.route('/admin', methods=['GET'])
def show_admin():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if session['role'] != 'administrator':
        return redirect(url_for('show_user'))
    return render_template('admin.html')

event_types = ["meet up", "conference", "party", "festival"]

# Set Create event page
@server.route('/create_event', methods=['GET'])
def show_create_event():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('create_event.html', event_types=event_types)

# User creates event
@server.route('/create_event_action', methods=['POST'])
def create_event():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # Get data from form
    name = request.form.get('name')
    description = request.form.get('description')
    date = request.form.get('date')
    time = request.form.get('time')
    place = request.form.get('place')
    type_ = request.form.get('type')

    # Check for missing data
    if not all([name, description, date, time, place, type_]):
        flash("All fields are required.", "error")
        return render_template('create_event.html', event_types=event_types)

    # Validate event type
    if type_ not in event_types:
        flash("Invalid event type.", "error")
        return render_template('create_event.html', event_types=event_types)

    # Validate date and time formats
    try:
        event_date = datetime.strptime(date, "%Y-%m-%d").date()
        event_time = datetime.strptime(time, "%H:%M").time()
    except ValueError:
        flash("Invalid date or time format.", "error")
        return render_template('create_event.html', event_types=event_types)
    
    # Ensure event date is in the future
    if event_date <= datetime.now().date():
        flash("Event date must be in the future.", "error")
        return render_template('create_event.html', event_types=event_types)
    
    # Store the username of the creator
    creator_ = session['username']

    # Convert date and time to strings for storage
    event_date_str = event_date.strftime("%Y-%m-%d")  # Convert date to string
    event_time_str = event_time.strftime("%H:%M")     # Convert time to string

    # Create a new event
    new_event = {'name' : name, 'description' : description, 'date' : event_date_str, 'time' : event_time_str, 'place' : place, 'type' : type_, 'creator' : creator_}
    
    # Save to the database
    events_collection.insert_one(new_event)

    # Return a success response
    flash("Event created successfully!", "success")
    return redirect('/create_event')

def filter_future_events(events):
    current_date = datetime.now().date()
    return [event for event in events if event['date'] >= current_date]

# User finds the events they created
@server.route('/created_events', methods=['GET'])
def created_events():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    creator_username = session['username']

    # Retrieve events
    events = find_events_by_creator(creator_username)

    # Transform date and time
    for event in events:
        try:
            # Convert date from string to date object
            event['date'] = datetime.strptime(event['date'], "%Y-%m-%d").date()

            # Convert time from string to time object
            event['time'] = datetime.strptime(event['time'], "%H:%M").time()
        except ValueError:
            flash(f"Invalid date or time format for event: {event['name']}", "error")
            return render_template('created_events.html', events=[])

    # Filter future events
    future_events = filter_future_events(events)

    if not future_events:
        flash("No events found.")
        return render_template('created_events.html', events=[])
    
    return render_template('created_events.html', events=future_events)

# User finds the events they are participating in
@server.route('/participated_events', methods=['GET'])
def participated_events():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']

    # Retrieve events where the user is a participant
    events = find_events_by_participant(username)

    # Transform date and time
    for event in events:
        try:
            # Convert date from string to date object
            event['date'] = datetime.strptime(event['date'], "%Y-%m-%d").date()

            # Convert time from string to time object
            event['time'] = datetime.strptime(event['time'], "%H:%M").time()
        except ValueError:
            flash(f"Invalid date or time format for event: {event['name']}", "error")
            return render_template('participated_events.html', events=[])

    # Filter future events
    future_events = filter_future_events(events)

    if not future_events:
        flash("No events found.", "error")
        return render_template('participated_events.html', events=None)

    # Render the page with events
    return render_template('participated_events.html', events=future_events)

# User finds all events
@server.route('/all_events', methods=['GET'])
def all_events():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # Retrieve all events
    events = find_all_events()

    # Transform date and time
    for event in events:
        try:
            # Convert date from string to date object
            event['date'] = datetime.strptime(event['date'], "%Y-%m-%d").date()

            # Convert time from string to time object
            event['time'] = datetime.strptime(event['time'], "%H:%M").time()
        except ValueError:
            flash(f"Invalid date or time format for event: {event['name']}", "error")
            return render_template('all_events.html', events=[])

    # Filter future events
    future_events = filter_future_events(events)

    if not future_events:
        flash("No events found.", "error")
        return render_template('all_events.html', events=[])

    # Render the events in the HTML template
    return render_template('all_events.html', events=future_events)

# Render the search events page
@server.route('/search_events', methods=['GET'])
def show_search_events():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('search_events.html', events=[], search_term='')

# User searches for events
@server.route('/search_events_action', methods=['GET'])
def search_events():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # Get the search term from the request
    search_term = request.args.get('search_term', '').strip()

    # Retrieve events based on the search term
    events = perform_search(search_term=search_term)

    # Transform date and time
    for event in events:
        try:
            # Convert date from string to date object
            event['date'] = datetime.strptime(event['date'], "%Y-%m-%d").date()

            # Convert time from string to time object
            event['time'] = datetime.strptime(event['time'], "%H:%M").time()
        except ValueError:
            flash(f"Invalid date or time format for event: {event['name']}", "error")
            return render_template('search_events.html', events=[])

    # Filter future events
    future_events = filter_future_events(events)

    # Render the search results page
    return render_template(
        'search_events.html',
        events=future_events,
        search_term=search_term
    )

# User views an event
@server.route('/view_event/<event_name>', methods=['GET'])
def view_event(event_name: str):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # Retrieve the event by its name
    event = find_event_by_name(event_name)

    # Prepare participants list with their responses
    participants = [
        {"username": participant["username"], "status": participant["status"]}
        for participant in event.get("participants", [])
    ]

    # Transform date and time
    try:
        # Convert date from string to date object
        event['date'] = datetime.strptime(event['date'], "%Y-%m-%d").date()

        # Convert time from string to time object
        event['time'] = datetime.strptime(event['time'], "%H:%M").time()
    except ValueError:
        flash(f"Invalid date or time format for event: {event['name']}", "error")
        return render_template('all_events.html', events=[])


    # Return the event details
    return render_template(
        'event_details.html',
        name=event.get("name"),
        description=event.get("description"),
        date=event['date'],
        time=event['time'],
        place=event.get("place"),
        type=event.get("type"),
        creator=event.get("creator"),
        participants=participants
    )

# Show the update event page
@server.route('/update_event/<event_name>', methods=['GET'])
def show_update_event(event_name):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    event = find_event_by_name(event_name)

    if not event:
        flash("Event not found.")
        return redirect('/created_events')
    
    # Ensure the current user is the creator of the event
    if event.get("creator") != session['username']:
        flash("You do not have permission to update this event.", "error")
        return redirect('/created_events')
    
    return render_template('update_event.html', event=event)

# User updates one of their events
@server.route('/update_event_action', methods=['POST'])
def update_event_action():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # Get data
    event_name = request.form.get('event_name')
    attribute = request.form.get('attribute')
    new_value = request.form.get('new_value')

    # Validate input
    if not all([event_name, attribute, new_value]):
        flash("All fields are required.")
        return redirect(f'/update_event/{event_name}')

    # Ensure the attribute is valid
    if attribute not in ['name', 'description', 'place', 'type']:
        flash("Invalid attribute specified.")
        return redirect(f'/update_event/{event_name}')
    
    # If the attribute is 'type', validate the new_value
    if attribute == 'type':
        if new_value not in event_types:
            flash("Invalid event type specified. Choose from: meet up, conference, party, festival.")
            return redirect(f'/update_event/{event_name}')

    # Prepare update dictionary
    updates = {attribute: new_value}

    # Update the event
    success = update_event(event_name, updates)
    if success:
        flash("Event updated successfully.")
    else:
        flash("Event update failed. The event might not exist.")

    return redirect(f'/update_event/{event_name}')

#User deletes one of their events
@server.route('/delete_event_action', methods=['POST'])
def delete_event_action():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # Get data from form
    event_name = request.form.get('event_name')

    # Validate input
    if not event_name:
        flash("Event name is required.")
        return redirect('/created_events')

    # Find the event by name
    event = find_event_by_name(event_name)
    if not event:
        flash("Event not found.")
        return redirect('/created_events')

    # Ensure the current user is the creator of the event
    if event.get("creator") != session['username']:
        flash("You are not authorized to delete this event.")
        return redirect('/created_events')

    # Attempt to delete the event
    success = delete_event(event_name)
    if success:
        flash("Event deleted successfully.")
    else:
        flash("Failed to delete event.")

    return redirect('/created_events')

# User participates in an event
@server.route('/participate_event/<event_name>', methods=['POST'])
def participate_event(event_name: str):
    if 'username' not in session:
        return redirect(url_for('login'))

    # Ensure the event exists
    event = find_event_by_name(event_name)
    if not event:
        flash("Event not found.", "error")
        return redirect('/all_events')

    # Get the participation status from form data
    status = request.form.get('status')
    if status not in ['yes', 'maybe']:
        flash("Invalid status. Must be 'yes' or 'maybe'.", "error")
        return render_template('event_details.html', event_name=event_name)

    # Safely get the participants list (empty if not found)
    participants = event.get('participants', [])

    # Check if the user is already participating
    existing_participant = next((p for p in participants if p['username'] == session['username']), None)

    if existing_participant:
        # Update existing participation
        result = update_participation(event_name, session['username'], status)
    else:
        # Add new participation
        result = add_participation(event_name, session['username'], status)

    if result:
        flash("Participation status updated successfully.", "success")
    else:
        flash("Failed to update participation status.", "error")

    return redirect(url_for('view_event', event_name=event_name))

# Admin views all events
@server.route('/admin/view_all_events', methods=['GET'])
def admin_view_all_events():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if session['role'] != 'administrator':
        return redirect('/user')

    # Retrieve all events
    events = find_all_events()

    # Transform date and time
    for event in events:
        try:
            # Convert date from string to date object
            event['date'] = datetime.strptime(event['date'], "%Y-%m-%d").date()

            # Convert time from string to time object
            event['time'] = datetime.strptime(event['time'], "%H:%M").time()
        except ValueError:
            flash(f"Invalid date or time format for event: {event['name']}", "error")
            return render_template('admin_all_events.html', events=[])

    # Filter future events if necessary
    future_events = filter_future_events(events)

    # Render the page with events
    return render_template('admin_all_events.html', events=future_events)

# Admin deletes an event
@server.route('/admin/delete_event', methods=['POST'])
def admin_delete_event():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if session['role'] != 'administrator':
        return redirect('/user')

    # Get event name from form data
    event_name = request.form.get('event_name')
    if not event_name:
        flash("Event name is required.", "error")
        return redirect('/admin/view_all_events')

    # Ensure the event exists
    event = find_event_by_name(event_name)
    if not event:
        flash("Event not found.", "error")
        return redirect('/admin/view_all_events')

    # Attempt to delete the event
    success = delete_event(event_name)
    if success:
        flash("Event deleted successfully.", "success")
    else:
        flash("Failed to delete event. It might not exist or an error occurred.", "error")
    
    return redirect('/admin/view_all_events')

# Admin views all users
@server.route('/admin/view_all_users', methods=['GET'])
def admin_view_all_users():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if session['role'] != 'administrator':
        return redirect('/user')

    # Retrieve all users
    users = find_all_users()

    # Render the page with users
    return render_template('admin_all_users.html', users=users)

# Admin deletes a user
@server.route('/admin/delete_user', methods=['POST'])
def admin_delete_user():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if session['role'] != 'administrator':
        return redirect('/user')

    # Get username from form data
    username = request.form.get('username')
    if not username:
        flash("Username is required.", "error")
        return redirect('/admin/view_all_users')

    # Ensure the user exists
    user = find_user_by_username(username)
    if not user:
        flash("User not found.", "error")
        return redirect('/admin/view_all_users')

    # Attempt to delete the user
    if delete_user(username):
        flash("User deleted successfully.", "success")
    else:
        flash("Failed to delete user.", "error")

    return redirect('/admin/view_all_users')