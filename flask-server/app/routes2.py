from main import users_collection, events_collection

def find_user_by_username(username):
    return users_collection.find_one({"username": username})

def find_user_by_email(email):
    return users_collection.find_one({"email": email})

def find_events_by_creator(username):
    return list(events_collection.find({"creator": username}))

def find_events_by_participant(username):
    return list(events_collection.find({"participants.username": username}))

def find_all_events():
    return list(events_collection.find())

def perform_search(search_term):
    search_term = search_term.strip()
    query = {
        '$or': [
            {'name': {'$regex': search_term, '$options': 'i'}},
            {'description': {'$regex': search_term, '$options': 'i'}},
            {'type': {'$regex': search_term, '$options': 'i'}},
            {'place': {'$regex': search_term, '$options': 'i'}}
        ]
    }
    return list(events_collection.find(query))

def find_event_by_name(event_name):
    return events_collection.find_one({"name": event_name})

def update_event(event_name, updates):
    result = events_collection.update_one({"name": event_name}, {"$set": updates})
    return result.modified_count > 0

def delete_event(event_name):
    result = events_collection.delete_one({"name": event_name})
    return result.deleted_count > 0

def add_participation(event_name, username, status):
    result = events_collection.update_one(
        {"name": event_name},
        {"$push": {"participants": {"username": username, "status": status}}}
    )
    return result.modified_count > 0

def update_participation(event_name, username, status):
    result = events_collection.update_one(
        {"name": event_name, "participants.username": username},
        {"$set": {"participants.$.status": status}}
    )
    return result.modified_count > 0

def find_all_users():
    return list(users_collection.find())

def delete_user(username):
    result = users_collection.delete_one({"username": username})
    return result.deleted_count > 0