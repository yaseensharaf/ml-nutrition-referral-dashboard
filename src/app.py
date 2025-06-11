import csv
import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_socketio import SocketIO, emit
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.pipeline import make_pipeline
import json
from werkzeug.utils import secure_filename
from datetime import date

app = Flask(__name__)
socketio = SocketIO(app)
app.secret_key = '123456'

data_folder = 'data'
UPLOAD_FOLDER = 'data'  # Specify your uploads directory
ALLOWED_EXTENSIONS = {'csv'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def recent_file(): 
    # Get all files in the folder
    files_in_folder = os.listdir(data_folder)

    # Filter out only CSV files
    csv_files = [file for file in files_in_folder if file.endswith('.csv')]

    # Check if there are any CSV files in the folder
    if csv_files:
        # Assume the first CSV file is the most recent initially
        data_recent_file_name = csv_files[0]
        # Fetch the creation time (or the closest equivalent) of the first file
        most_recent_file_time = os.path.getctime(os.path.join(data_folder, data_recent_file_name))

        # Loop through the CSV files to find the most recent
        for file in csv_files:
            file_path = os.path.join(data_folder, file)
            # Use getctime() to get the file creation time
            file_time = os.path.getctime(file_path)

            # Update if this file's creation time is more recent
            if file_time > most_recent_file_time:
                most_recent_file_time = file_time
                data_recent_file_name = file

        return data_recent_file_name
    else:
        print("No CSV files found in the folder.")

def allowed_file(filename):
    return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_data_by_encounter_id(encounter_id):
    data = []
    with open('data\FeedingDashboardData.csv', 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['encounterId'] == encounter_id:
                data.append(row)
                break  # Assuming encounter_id is unique, break after finding the match
    return data

def get_filtered_results(update_data, results, confidence_scores):
    lower = update_data.get('lower', 0)
    upper = update_data.get('upper', 100)
    referral_filter = update_data.get('referral', None)

    filtered_results = []
    for result, confidence_score in zip(results, confidence_scores):
        if lower <= confidence_score <= upper:
            if referral_filter == "1" and result['needs_referral'] == "Yes":
                filtered_results.append(result)
            elif referral_filter == "2" and result['needs_referral'] == "No":
                filtered_results.append(result)
            elif referral_filter == "None":
                filtered_results.append(result)
    return filtered_results


@app.route('/')
@app.route('/index.html')
def index():
    data_file = recent_file()
    if data_file is None:
        flash("No CSV files found in the folder.")
        return redirect(url_for('upload'))
    
    try:
        with open('update_data.json', 'r') as f:
            update_data = json.load(f)
    except FileNotFoundError:
        update_data = {'lower': 0, 'upper': 100, 'referral': "None"}

    # Load data
    df = pd.read_csv(f"data/{data_file}")

    # Columns for the new algorithm
    X = df[['end_tidal_co2','feed_vol','feed_vol_adm','fio2','fio2_ratio','insp_time', 'oxygen_flow_rate','peep','pip', 'resp_rate','sip','tidal_vol','tidal_vol_actual','tidal_vol_kg','tidal_vol_spon', 'bmi']]
    y = df['referral']

    # Pipeline for imputation, normalization, and model training
    pipeline = make_pipeline(
        SimpleImputer(strategy='median'),
        StandardScaler(),
        SVC(probability=True, random_state=42)
    )

    # Train model on the entire dataset
    pipeline.fit(X, y)

    # Predict and calculate confidence scores
    predicted_referrals = pipeline.predict(X)
    probabilities = pipeline.predict_proba(X)
    confidence_scores = probabilities.max(axis=1) * 100

    # Prepare initial output for results
    initial_results = [{
        'patient_number': i + 1,
        'encounter_id': int(row['encounterId']),
        'referral_probability': f"{conf_score:.2f}",  # This is already formatted to 2 decimal places
        'needs_referral': "Yes" if pred_referral else "No",
        'color': "red" if pred_referral else "green",
        'end_tidal_co2': f"{row['end_tidal_co2']:.2f}",
        'feed_vol': f"{row['feed_vol']:.2f}",
        'feed_vol_adm': f"{row['feed_vol_adm']:.2f}",
        'fio2': f"{row['fio2']:.2f}",
        'fio2_ratio': f"{row['fio2_ratio']:.2f}",
        'insp_time': f"{row['insp_time']:.2f}",
        'oxygen_flow_rate': f"{row['oxygen_flow_rate']:.2f}",
        'peep': f"{row['peep']:.2f}",
        'pip': f"{row['pip']:.2f}",
        'resp_rate': f"{row['resp_rate']:.2f}",
        'sip': f"{row['sip']:.2f}",
        'tidal_vol': f"{row['tidal_vol']:.2f}",
        'tidal_vol_actual': f"{row['tidal_vol_actual']:.2f}",
        'tidal_vol_kg': f"{row['tidal_vol_kg']:.2f}",
        'tidal_vol_spon': f"{row['tidal_vol_spon']:.2f}",
        'bmi': f"{row['bmi']:.2f}",
        'referral': row['referral']  # Assuming 'referral' is a string and doesn't need formatting
        } for i, (row, pred_referral, conf_score) in enumerate(zip(df.to_dict('records'), predicted_referrals, confidence_scores))]

    # Filter results based on update_data criteria
    results = get_filtered_results(update_data, initial_results, confidence_scores)


    referrals = sum(res['needs_referral'] == "Yes" for res in results)
    count_no_referral = len(results) - referrals
    Today = date.today().strftime("%B %d, %Y")
    dark_mode = 'dark' if session.get('dark_mode') else ''

    # Render the HTML template with the filtered results and patient data
    return render_template('index.html', results=results, count=referrals, sum=len(results), today=Today, dark_mode=dark_mode)

@app.route('/updateAll', methods=['POST'])
def update_all():
    data = request.get_json()  # Get JSON data sent from the client

    # Process the data as before
    # Example: Update 'update_data.json' with the received data
    with open('update_data.json', 'w') as f:
        json.dump(data, f)

    # Correctly emit an event to all clients
    socketio.emit('data_updated', data, room=None)  # Correct use of emit for broadcasting

    return jsonify({'status': 'success'})

@app.route('/toggle-dark-mode', methods=['POST'])
def toggle_dark_mode():
    # Toggle the dark mode state in the session
    session['dark_mode'] = not session.get('dark_mode', False)
    # Return a 204 no content response, as we only need to toggle the state
    return ('', 204)

@app.route('/upload', methods=['POST'])
def upload_file():
    # Check if the post request has the file part
    if 'file' not in request.files:
        flash('No file part')
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        jsonify ({'success': 'File uploaded successfully'})
        return redirect(url_for('index'))

        
    else:
        flash('File type not supported. Please upload a CSV file.', 'error')
        return jsonify({'error': 'File type not supported. Please upload a CSV file.'}), 400
        
@app.route('/graphs.html')
def graphs():
    data_file = recent_file() 
    if data_file is None:
        flash("No CSV files found in the folder.")
        return redirect(url_for('upload'))
    # Load data
    df = pd.read_csv(f"data/{data_file}")

    # Columns for the new algorithm
    X = df[['end_tidal_co2','feed_vol','feed_vol_adm','fio2','fio2_ratio','insp_time', 'oxygen_flow_rate','peep','pip', 'resp_rate','sip','tidal_vol','tidal_vol_actual','tidal_vol_kg','tidal_vol_spon', 'bmi']]
    y = df['referral']

    # Pipeline for imputation, normalization, and model training
    pipeline = make_pipeline(
        SimpleImputer(strategy='median'),
        StandardScaler(),
        SVC(probability=True, random_state=42)
    )

    # Train model on the entire dataset
    pipeline.fit(X, y)

    # Predict and calculate confidence scores
    predicted_referrals = pipeline.predict(X)
    probabilities = pipeline.predict_proba(X)
    confidence_scores = probabilities.max(axis=1) * 100

    # Prepare output
    results = [{
        'patient_number': i + 1,
        'encounter_id': int(row['encounterId']),
        'referral_probability': f"{conf_score:.2f}",
        'needs_referral': "Yes" if pred_referral else "No",
        'color': "red" if pred_referral else "green"
    } for i, (row, pred_referral, conf_score) in enumerate(zip(df.to_dict('records'), predicted_referrals, confidence_scores))]

    referrals = sum(res['needs_referral'] == "Yes" for res in results)
    count_no_referral = len(results) - referrals
    Today = date.today().strftime("%B %d, %Y")
    dark_mode = 'dark' if session.get('dark_mode') else ''

        # Prepare data for pie chart
    needs_referral_count = sum(predicted_referrals)
    no_referral_count = len(predicted_referrals) - needs_referral_count
    pie_data = [needs_referral_count, no_referral_count]

    # Prepare data for histogram
    histogram_data = list(confidence_scores)

    # Convert data to JSON for JavaScript
    pie_data_json = json.dumps(pie_data)
    histogram_data_json = json.dumps(histogram_data)
    
    # Calculate complete and incomplete data counts
    complete_data_count = (df.isnull().sum(axis=1) == 0).sum()
    incomplete_data_count = len(df) - complete_data_count

    # Convert int64 to native Python int for JSON serialization
    complete_data_count = int(complete_data_count)
    incomplete_data_count = int(incomplete_data_count)

    # Prepare data for box plot (Tidal Volume)
    tidal_vol_actual_data = df['tidal_vol_actual'].dropna().tolist()
    tidal_vol_kg_data = df['tidal_vol_kg'].dropna().tolist()

    # Serialize data to JSON
    complete_data_json = json.dumps([complete_data_count, incomplete_data_count])
    tidal_volume_data_json = json.dumps([tidal_vol_actual_data, tidal_vol_kg_data])


    # Render the HTML template with the results
    return render_template('graphs.html',results=results,count=referrals,sum=len(results),today=date.today().strftime("%B %d, %Y"),dark_mode='dark' if session.get('dark_mode') else '',pie_data=pie_data_json,histogram_data=histogram_data_json,complete_data=complete_data_json,tidal_volume_data=tidal_volume_data_json)

@app.route('/data.html')
def data():
    #today's date
    Today = date.today().strftime("%B %d, %Y")
    encounter_id = request.args.get('encounterId')
    data = get_data_by_encounter_id(encounter_id)
    dark_mode = 'dark' if session.get('dark_mode') else ''
    return render_template('data.html', today = Today, data=data, dark_mode=dark_mode)

@app.route('/upload.html', methods=['GET'])
def upload():
    #today's date
    Today = date.today().strftime("%B %d, %Y")
    encounter_id = request.args.get('encounterId')
    data = get_data_by_encounter_id(encounter_id)
    dark_mode = 'dark' if session.get('dark_mode') else ''
    return render_template('upload.html', today = Today, data=data, dark_mode=dark_mode)

@app.route('/help.html')
def help():
    Today = date.today().strftime("%B %d, %Y")
    dark_mode = 'dark' if session.get('dark_mode') else ''
    return render_template('help.html', today = Today, dark_mode=dark_mode)

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5001)


