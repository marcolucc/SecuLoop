from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity, get_raw_jwt, unset_jwt_cookies, jwt_optional
import sqlite3
import datetime
import traceback    

# Initialize the Flask app
app = Flask(__name__)

# Set the secret key for JWT
app.config['JWT_SECRET_KEY'] = 'secret'

# Initialize the JWTManager
jwt = JWTManager(app)

# Connect to the database
conn = sqlite3.connect('devices.db', check_same_thread=False)
cursor = conn.cursor()

# DEBUG Create the devices table if it does not exist
cursor.execute("""CREATE TABLE IF NOT EXISTS devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    status TEXT NOT NULL,
    owner TEXT NOT NULL,
    added_by_ip TEXT NOT NULL,
    date_added TEXT NOT NULL
)
""")

# DEBUG
conn.commit()

# DEBUG Create the devices table if it does not exist
cursor.execute("""CREATE TABLE IF NOT EXISTS devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    status TEXT NOT NULL,
    owner TEXT NOT NULL,
    added_by_ip TEXT NOT NULL,
    date_added TEXT NOT NULL
)
""")

# DEBUG
conn.commit()

# DEBUG Create the users table if it does not exist
cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL
    );
""")

# DEBUG
conn.commit()

# DEBUG: Define a list of users
users = [
    {
        'username': 'user1',
        'password': 'pass1'
    },
    {
        'username': 'user2',
        'password': 'pass2'
    }
]

# DEBUG: Define a list of monitored devices
devices = [
    {
        'device_id': 'd1',
        'device_name': 'Device 1',
        'device_status': 'Online'
    },
    {
        'device_id': 'd2',
        'device_name': 'Device 2',
        'device_status': 'Offline'
    }
]

#function to get all devices
def get_all_devices():
    cursor.execute("SELECT * FROM devices")
    devices = cursor.fetchall()
    return devices

#function to get a device by id 
def get_device_by_id(device_id):    
    cursor.execute("SELECT * FROM devices WHERE id=?", (device_id,))
    device = cursor.fetchone()
    return device

#function to get a device by name
def get_device_by_name(device_name):
    cursor.execute("SELECT * FROM devices WHERE name=?", (device_name,))
    device = cursor.fetchone()
    return device

#function to add a new device
def add_device(device_name, device_status, owner, added_by_ip, date_added):
    cursor.execute("INSERT INTO devices (name, status, owner, added_by_ip, date_added) VALUES (?, ?, ?, ?, ?)", (device_name, device_status, owner, added_by_ip, date_added))
    conn.commit()
    # Close the database connection
    conn.close()

#function to update a device
def update_device(device_id, device_name, device_status, owner, added_by_ip, date_added):
    cursor.execute("UPDATE devices SET name=?, status=?, owner=?, added_by_ip=?, date_added=? WHERE id=?", (device_name, device_status, owner, added_by_ip, date_added, device_id))
    conn.commit()
    # Close the database connection
    conn.close()

#function to delete a device
def delete_device(device_id):
    cursor.execute("DELETE FROM devices WHERE id=?", (device_id,))
    conn.commit()
    # Close the database connection
    conn.close()


# Define the login endpoint
@app.route('/login', methods=['POST'])
def login():
    # Get the username and password from the request body
    username = request.json.get('username', None)
    password = request.json.get('password', None)

    # DEBUG Loop through the users to find a match
    for user in users:
        # If the username and password match with a user
        if username == user['username'] and password == user['password']:
            # Create a JWT access token
            access_token = create_access_token(identity=username)
            # Return the access token in the response
            return jsonify(access_token=access_token), 200

    # Check if the required parameters are present
    if username is None or password is None:
        return jsonify({"error": "Missing required parameters"}), 400

    # Connect to the database
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Execute the SELECT statement to retrieve the user
    cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = cursor.fetchone()

    # Close the database connection
    conn.close()

    # Check if a user was found with the given credentials
    if user is None:
        return jsonify({"error": "Incorrect username or password"}), 401

    # Create the JSON Web Token and return it in the response
    access_token = create_access_token(identity=username)
    return jsonify(access_token=access_token), 200

# endpoint to reset the password of the user making the request
@app.route('/reset_password', methods=['POST'])
@jwt_required
def reset_password():
    # Get the current user from the JWT
    current_user = get_jwt_identity()
    # Get the new password from the request body
    new_password = request.json.get('new_password', None)
    # Validate the new password
    if not new_password:
        return jsonify({"msg": "New password is required"}), 400
    # Loop through the users to find a match
    for user in users:
        # If the username and password match with a user
        if current_user == user['username']:
            # Update the user's password
            user['password'] = new_password
            # Return a success message
            return jsonify({"msg": "Password reset successful"}), 200

    # If no match is found, return an error message
    return jsonify({"msg": "Error resetting password"}), 500

# TODO endpoint to reset the password of a user by token
@app.route('/reset_password_by_token', methods=['POST'])
@jwt_required
def reset_password_by_token():

# TODO endpoint to logout the user making the request
# Route for logout, which revokes the JWT token and returns a success message
@app.route('/logout', methods=['DELETE'])
@jwt_optional
def logout():
    current_user = get_jwt_identity()
    if current_user:
        # Revoke the JWT token
        unset_jwt_cookies(app, access_token_name="access_token")
        return jsonify({"msg": "Successfully logged out"}), 200
    else:
        # No JWT token found, return a message indicating that the user was not logged in
        return jsonify({"msg": "User was not logged in"}), 400


# Define a protected endpoint that requires JWT
@app.route('/protected', methods=['GET'])
@jwt_required
def protected():
    # Get the current user from the JWT
    current_user = get_jwt_identity()
    # Return the current user in the response
    return jsonify(logged_in_as=current_user), 200

# TODO endpoint for loading the dashboard
@app.route('/dashboard', methods=['GET'])
@jwt_required
def load_dashboard():
    return jsonify(monitored_devices=monitored_devices), 200

# endpoint for adding a new device
@app.route('/add_device', methods=['POST'])
@jwt_required
def add_device():
    # Get the device name and status from the request body
    device_name = request.json.get('device_name', None)
    device_status = request.json.get('device_status', None)
    owner = get_jwt_identity()
    added_by_ip = request.remote_addr
    date_added = str(datetime.datetime.now())

    # Validate the device information
    if not device_name:
        return jsonify({"msg": "Device name is required"}), 400
    if not device_status:
        return jsonify({"msg": "Device status is required"}), 400

    # DEBUG: Add the device to the list of devices
    devices.append({
        'device_id': 'd3',
        'device_name': device_name,
        'device_status': device_status
    })

    try:
        # Insert the device in the sqlite3 database
        cursor.execute("""
            INSERT INTO devices (name, status, owner, added_by_ip, date_added)
            VALUES (?, ?, ?, ?, ?)
        """, (device_name, device_status, owner, added_by_ip, date_added))
        conn.commit()

        # Return a success message
        return jsonify({"msg": "Device added successfully"}), 201
    
    except Exception as e:
        return jsonify({"msg": f"Error adding device: {e}"}), 500

# endpoint for deleting a device
@app.route('/delete_device', methods=['DELETE'])
@jwt_required
def delete_device():
    # Get the JWT identity (username) of the user making the request
    user = get_jwt_identity()
    # Get the device_id and owner of the device to be deleted from the request data
    device_id = request.json.get('device_id', None)
    device_owner = request.json.get('device_owner', None)
    
    try:
        # Check that the device_id and owner were provided in the request
        if device_id is None or device_owner is None:
            return jsonify({"msg": "Device ID and owner must be provided"}), 400
        
        # Check that the device exists in the database
        device = get_device_by_id(device_id)
        if device is None:
            return jsonify({"msg": "Device not found"}), 404
        
        # Check that the user making the request is the owner of the device
        if device_owner != user:
            return jsonify({"msg": "Unauthorized - only the owner can delete the device"}), 401
        
        # Delete the device from the devices table
        cursor.execute("DELETE FROM devices WHERE device_id=%s", (device_id,))
        conn.commit()
        
        # Add the device information to the deviceCancelled table
        #deleted_device = {"device_id": device_id, "owner": device_owner, "deleted_by": user, "deleted_at": str(datetime.datetime.now())}
        cursor.execute("INSERT INTO deviceCancelled (device_id, owner, deleted_by, deleted_at) VALUES (%s, %s, %s, %s)", 
                       (device_id, device_owner, user, str(datetime.datetime.now())))
        conn.commit()
        
        return jsonify({"msg": "Device successfully deleted"}), 200
    except Exception as e:
        # Log the error and return a 500 Internal Server Error
        traceback.print_exc()
        return jsonify({"msg": "An error occurred while deleting the device"}), 500

# endpoint for updating a device
@app.route('/update_device', methods=['PUT'])
@jwt_required
def update_device():
    # Get the JWT identity (username) of the user making the request
    user = get_jwt_identity()
    # Get the device_id and owner of the device to be updated from the request data
    device_id = request.json.get('device_id', None)
    device_owner = request.json.get('device_owner', None)
    device_name = request.json.get('device_name', None)
    device_status = request.json.get('device_status', None)
    
    try:
        # Check that the device_id and owner were provided in the request
        if device_id is None or device_owner is None:
            return jsonify({"msg": "Device ID and owner must be provided"}), 400
        
        # Check that the device exists in the database
        device = get_device_by_id(device_id)
        if device is None:
            return jsonify({"msg": "Device not found"}), 404
        
        # Check that the user making the request is the owner of the device
        if device_owner != user:
            return jsonify({"msg": "Unauthorized - only the owner can update the device"}), 401
        
        # Update the device in the devices table
        cursor.execute("UPDATE devices SET name=%s, status=%s WHERE device_id=%s", (device_name, device_status, device_id))
        conn.commit()
        
        return jsonify({"msg": "Device successfully updated"}), 200
    except Exception as e:
        # Log the error and return a 500 Internal Server Error
        traceback.print_exc()
        return jsonify({"msg": "An error occurred while updating the device"}), 500

# endpoint for getting a device by ID
@app.route('/get_device_by_id', methods=['GET'])
@jwt_required
def get_device_by_id():
    # Get the JWT identity (username) of the user making the request
    user = get_jwt_identity()
    # Get the device_id and owner of the device to be updated from the request data
    device_id = request.json.get('device_id', None)
    device_owner = request.json.get('device_owner', None)
    
    try:
        # Check that the device_id and owner were provided in the request
        if device_id is None or device_owner is None:
            return jsonify({"msg": "Device ID and owner must be provided"}), 400
        
        # Check that the device exists in the database
        device = get_device_by_id(device_id)
        if device is None:
            return jsonify({"msg": "Device not found"}), 404
        
        # Check that the user making the request is the owner of the device
        if device_owner != user:
            return jsonify({"msg": "Unauthorized - only the owner can get the device"}), 401
        
        # Get the device from the devices table
        cursor.execute("SELECT * FROM devices WHERE device_id=%s", (device_id,))
        device = cursor.fetchone()
        
        return jsonify({"device": device}), 200
    except Exception as e:
        # Log the error and return a 500 Internal Server Error
        traceback.print_exc()
        return jsonify({"msg": "An error occurred while getting the device"}), 500


# endpoint for getting all devices owned by the user making the request
@app.route('/get_all_devices', methods=['GET'])
@jwt_required
def get_all_devices():
    # Get the JWT identity (username) of the user making the request
    user = get_jwt_identity()
    
    try:
        # Get all devices from the devices table
        cursor.execute("SELECT * FROM devices WHERE owner=%s", (user,))
        devices = cursor.fetchall()
        
        return jsonify({"devices": devices}), 200
    except Exception as e:
        # Log the error and return a 500 Internal Server Error
        traceback.print_exc()
        return jsonify({"msg": "An error occurred while getting the devices"}), 500


# endpoint for getting all devices cancelled ADMIN ONLY
@app.route('/get_all_devices_cancelled', methods=['GET'])
@jwt_required
def get_all_devices_cancelled():
    # Get the JWT identity (username) of the user making the request
    user = get_jwt_identity()
    
    try:
        # Check that the user making the request is an admin
        if user != 'admin':
            return jsonify({"msg": "Unauthorized - only an admin can get all cancelled devices"}), 401
        
        # Get all devices from the devices table
        cursor.execute("SELECT * FROM deviceCancelled")
        devices = cursor.fetchall()
        
        return jsonify({"devices": devices}), 200
    except Exception as e:
        # Log the error and return a 500 Internal Server Error
        traceback.print_exc()
        return jsonify({"msg": "An error occurred while getting all devices"}), 500

# endpoint for getting all devices by owner ADMIN ONLY
@app.route('/get_all_devices_by_owner', methods=['GET'])
@jwt_required
def get_all_devices_by_owner():
    # Get the JWT identity (username) of the user making the request
    user = get_jwt_identity()
    # Get the device_id and owner of the device to be updated from the request data
    device_owner = request.json.get('device_owner', None)
    
    try:
        # Check that the device_id and owner were provided in the request
        if device_owner is None:
            return jsonify({"msg": "Device owner must be provided"}), 400
        
        # Check that the user making the request is an admin
        if user != 'admin':
            return jsonify({"msg": "Unauthorized - only an admin can get all devices by owner"}), 401
        
        # Get all devices from the devices table
        cursor.execute("SELECT * FROM devices WHERE owner=%s", (device_owner,))
        devices = cursor.fetchall()
        
        return jsonify({"devices": devices}), 200
    except Exception as e:
        # Log the error and return a 500 Internal Server Error
        traceback.print_exc()
        return jsonify({"msg": "An error occurred while getting all devices"}), 500

# endpoint for getting all devices by status ADMIN ONLY
@app.route('/get_all_devices_by_status', methods=['GET'])
@jwt_required
def get_all_devices_by_status():
    # Get the JWT identity (username) of the user making the request
    user = get_jwt_identity()
    # Get the device_id and owner of the device to be updated from the request data
    device_status = request.json.get('device_status', None)
    
    try:
        # Check that the device_id and owner were provided in the request
        if device_status is None:
            return jsonify({"msg": "Device status must be provided"}), 400
        
        # Check that the user making the request is an admin
        if user != 'admin':
            return jsonify({"msg": "Unauthorized - only an admin can get all devices by status"}), 401
        
        # Get all devices from the devices table
        cursor.execute("SELECT * FROM devices WHERE status=%s", (device_status,))
        devices = cursor.fetchall()
        
        return jsonify({"devices": devices}), 200
    except Exception as e:
        # Log the error and return a 500 Internal Server Error
        traceback.print_exc()
        return jsonify({"msg": "An error occurred while getting all devices"}), 500


# Run the app if it is the main module
if __name__ == '__main__':
    app.run()
