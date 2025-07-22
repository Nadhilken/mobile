from flask import Flask, request, render_template, jsonify
import pandas as pd
import uuid
import os
from werkzeug.utils import secure_filename
import numpy as np
import time

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

# Ensure upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def safe_remove(file_path, retries=3, delay=0.5):
    """Attempt to remove a file with retries to handle PermissionError."""
    for _ in range(retries):
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            return True
        except PermissionError:
            time.sleep(delay)
    return False

def find_column(columns, target):
    """Find a column name case-insensitively, ignoring spaces and special characters."""
    target = target.lower().replace(' ', '').replace('(%', '').replace(')', '')
    for col in columns:
        if col and isinstance(col, str) and col.lower().replace(' ', '').replace('(%', '').replace(')', '') == target:
            return col
    return None

def find_header_row(df, required_columns, max_rows=10):
    """Find the row containing the header by checking for required columns."""
    for i in range(max_rows):
        try:
            temp_df = pd.read_excel(df, sheet_name='Emotion Summary', header=i)
            columns = temp_df.columns
            found_columns = [find_column(columns, col) for col in required_columns]
            if all(found_columns):
                return i, {rc: fc for rc, fc in zip(required_columns, found_columns)}
        except:
            continue
    return None, None

def analyze_emotions(df, is_summary_format=False):
    if is_summary_format:
        # Handle try_emotions.xlsx format (Emotion Summary sheet)
        required_columns = ['Emotion', 'Average (%)']
        header_row, column_map = find_header_row(df, required_columns)
        if header_row is None:
            columns = pd.read_excel(df, sheet_name='Emotion Summary').columns
            return None, f"Could not find header row with required columns in Emotion Summary: {', '.join(required_columns)}. Found columns: {', '.join([str(c) for c in columns])}"
        
        # Read with correct header row
        emotion_summary = pd.read_excel(df, sheet_name='Emotion Summary', header=header_row)
        emotion_summary = emotion_summary.dropna(subset=[column_map['Emotion'], column_map['Average (%)']])
        
        # Map columns
        columns_to_use = [column_map['Emotion'], column_map['Average (%)']]
        max_conf_col = find_column(emotion_summary.columns, 'Max (%)')
        min_conf_col = find_column(emotion_summary.columns, 'Min (%)')
        if max_conf_col:
            columns_to_use.append(max_conf_col)
        if min_conf_col:
            columns_to_use.append(min_conf_col)
        
        # Extract relevant columns
        emotion_summary = emotion_summary[columns_to_use].copy()
        emotion_summary.columns = ['Emotion', 'Avg Confidence'] + (['Max Confidence', 'Min Confidence'] if max_conf_col and min_conf_col else ['Max Confidence', 'Min Confidence'][:len(columns_to_use)-2])
        emotion_summary['Frequency'] = 1  # Assume equal weight for summary data
        if max_conf_col and min_conf_col:
            emotion_summary['Std Confidence'] = emotion_summary['Max Confidence'] - emotion_summary['Min Confidence']
        else:
            emotion_summary['Std Confidence'] = 0
        
        # Normalize proportions
        total_confidence = emotion_summary['Avg Confidence'].sum()
        if total_confidence > 0:
            emotion_summary['Proportion'] = emotion_summary['Avg Confidence'] / total_confidence * 100
        else:
            emotion_summary['Proportion'] = 0
    else:
        # Handle original n_a_dh_l_emotions.xlsx format
        required_columns = ['Session ID', 'Timestamp', 'Emotion', 'Confidence']
        columns = df.columns
        # Map required columns case-insensitively
        session_id_col = find_column(columns, 'Session ID')
        timestamp_col = find_column(columns, 'Timestamp')
        emotion_col = find_column(columns, 'Emotion')
        confidence_col = find_column(columns, 'Confidence')
        
        missing_columns = []
        if not session_id_col:
            missing_columns.append('Session ID')
        if not timestamp_col:
            missing_columns.append('Timestamp')
        if not emotion_col:
            missing_columns.append('Emotion')
        if not confidence_col:
            missing_columns.append('Confidence')
        
        if missing_columns:
            return None, f"Missing required columns: {', '.join(missing_columns)}. Found columns: {', '.join([str(c) for c in columns])}"
        
        # Rename columns to standard names
        df = df.rename(columns={
            session_id_col: 'Session ID',
            timestamp_col: 'Timestamp',
            emotion_col: 'Emotion',
            confidence_col: 'Confidence'
        })
        
        # Convert Timestamp to datetime
        try:
            df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        except Exception as e:
            return None, f"Error parsing Timestamp: {str(e)}"
        
        # Filter out invalid rows
        df = df.dropna(subset=['Emotion', 'Confidence'])
        df = df[df['Emotion'] != 'none']
        df['Confidence'] = pd.to_numeric(df['Confidence'], errors='coerce')
        df = df.dropna(subset=['Confidence'])
        
        # Group by Emotion to get frequency, average confidence, and standard deviation
        emotion_summary = df.groupby('Emotion').agg({
            'Confidence': ['count', 'mean', 'std'],
            'Session ID': 'nunique'
        }).reset_index()
        emotion_summary.columns = ['Emotion', 'Frequency', 'Avg Confidence', 'Std Confidence', 'Unique Sessions']
        
        # Calculate proportions
        total_emotions = emotion_summary['Frequency'].sum()
        emotion_summary['Proportion'] = emotion_summary['Frequency'] / total_emotions * 100
        emotion_summary['Std Confidence'] = emotion_summary['Std Confidence'].fillna(0)
    
    # Calculate volatility score
    volatility_score = 0
    if not is_summary_format:
        df_sorted = df.sort_values(['Session ID', 'Timestamp'])
        for session_id in df_sorted['Session ID'].unique():
            session_data = df_sorted[df_sorted['Session ID'] == session_id]
            for i in range(1, len(session_data)):
                prev_emotion = session_data.iloc[i-1]['Emotion']
                curr_emotion = session_data.iloc[i]['Emotion']
                positive = ['happy', 'surprise']
                negative = ['sad', 'angry', 'fear']
                if (prev_emotion in positive and curr_emotion in negative) or \
                   (prev_emotion in negative and curr_emotion in positive):
                    volatility_score += 1
        total_timestamps = len(df)
        volatility_score = (volatility_score / total_timestamps * 100) if total_timestamps > 0 else 0
    else:
        volatility_score = emotion_summary['Std Confidence'].mean() / 100 * 10  # Scale to 0-10 range
    
    # Health predictions with suggestions
    health_predictions = []
    for _, row in emotion_summary.iterrows():
        emotion = row['Emotion'].lower()
        proportion = row['Proportion']
        avg_confidence = row['Avg Confidence']
        std_confidence = row.get('Std Confidence', 0)
        
        if emotion == 'angry' and proportion > 40:
            health_predictions.append({
                'Risk': 'Cardiovascular Issues',
                'Likelihood': min(80, 60 + proportion - 40),
                'Explanation': f"High anger ({proportion:.1f}%) with confidence {avg_confidence:.1f}% increases risk of hypertension and heart disease.",
                'Suggestions': "Practice anger management techniques (e.g., deep breathing, meditation), engage in regular physical activity (e.g., 30 min/day), and consult a healthcare provider for cardiovascular screening."
            })
            health_predictions.append({
                'Risk': 'Chronic Stress',
                'Likelihood': min(75, 55 + proportion - 40),
                'Explanation': f"Elevated anger ({proportion:.1f}%) contributes to stress-related disorders.",
                'Suggestions': "Incorporate stress-reduction practices like mindfulness or yoga, ensure adequate sleep (7-8 hours/night), and seek counseling if stress persists."
            })
        
        if emotion == 'sad' and proportion > 50:
            health_predictions.append({
                'Risk': 'Depression',
                'Likelihood': min(90, 70 + proportion - 50),
                'Explanation': f"High sadness ({proportion:.1f}%) with confidence {avg_confidence:.1f}% suggests risk of depression.",
                'Suggestions': "Seek professional help from a therapist or counselor, engage in social activities, and consider cognitive-behavioral therapy (CBT) or support groups."
            })
            health_predictions.append({
                'Risk': 'Anxiety',
                'Likelihood': min(80, 60 + proportion - 50),
                'Explanation': f"Persistent sadness ({proportion:.1f}%) may contribute to anxiety disorders.",
                'Suggestions': "Practice relaxation techniques (e.g., progressive muscle relaxation), maintain a balanced diet, and consult a mental health professional for anxiety management strategies."
            })
        
        if emotion == 'fear' and proportion > 30:
            health_predictions.append({
                'Risk': 'Anxiety Disorders',
                'Likelihood': min(80, 60 + proportion - 30),
                'Explanation': f"High fear ({proportion:.1f}%) with confidence {avg_confidence:.1f}% indicates potential anxiety disorders.",
                'Suggestions': "Try mindfulness meditation, seek therapy (e.g., exposure therapy or CBT), and build a support network to manage anxiety triggers."
            })
        
        if emotion in ['happy', 'surprise'] and proportion < 20:
            health_predictions.append({
                'Risk': 'Low Mood',
                'Likelihood': min(70, 50 + (20 - proportion)),
                'Explanation': f"Low positive emotions ({emotion}: {proportion:.1f}%) may indicate a low mood, increasing the risk of emotional instability or early depression.",
                'Suggestions': "Engage in activities that boost positive emotions (e.g., hobbies, exercise, social connections), practice gratitude journaling, and consult a mental health professional if low mood persists."
            })
        
        if emotion == 'neutral' and proportion > 50 and avg_confidence < 60:
            health_predictions.append({
                'Risk': 'Emotional Suppression',
                'Likelihood': min(60, 50 + proportion - 50),
                'Explanation': f"High neutral emotions ({proportion:.1f}%) with low confidence ({avg_confidence:.1f}%) may indicate emotional suppression.",
                'Suggestions': "Explore expressive therapies (e.g., art or music therapy), practice emotional awareness through journaling, and seek counseling to address suppressed emotions."
            })
    
    if volatility_score > 10:
        health_predictions.append({
            'Risk': 'Mood Disorders',
            'Likelihood': min(80, 60 + volatility_score),
            'Explanation': f"Emotional fluctuations (volatility score: {volatility_score:.1f}) suggest potential mood disorders.",
            'Suggestions': "Consult a psychiatrist for mood disorder evaluation, maintain a consistent daily routine, and consider mood-stabilizing activities like regular exercise and stress management."
        })
    
    health_predictions = sorted(health_predictions, key=lambda x: x['Likelihood'], reverse=True)
    
    # Prepare data for chart
    emotion_distribution = {row['Emotion']: row['Proportion'] for row in emotion_summary.to_dict('records')}
    
    return {
        'health_predictions': health_predictions,
        'emotion_summary': emotion_summary.to_dict(orient='records'),
        'emotion_distribution': emotion_distribution
    }, None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy', 'message': 'Emotion Analysis App is running'}), 200

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}_{filename}")
        file.save(file_path)
        
        try:
            # Use ExcelFile to ensure proper file handling
            with pd.ExcelFile(file_path) as xls:
                # Try original format first
                df = pd.read_excel(xls)
                results, error = analyze_emotions(df, is_summary_format=False)
                if error:
                    # Try Emotion Summary sheet
                    if 'Emotion Summary' in xls.sheet_names:
                        results, error = analyze_emotions(xls, is_summary_format=True)
                    if error:
                        return jsonify({'error': error}), 400
            
            # Attempt to remove file
            if not safe_remove(file_path):
                print(f"Warning: Could not delete file {file_path} due to persistent access issues")
            
            return render_template('results.html', results=results)
        
        except Exception as e:
            # Attempt to remove file in case of error
            safe_remove(file_path)
            return jsonify({'error': f"Error processing file: {str(e)}"}), 500
    else:
        return jsonify({'error': 'Invalid file type. Please upload an Excel file (.xlsx or .xls)'}), 400

if __name__ == '__main__':
    # For local development
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
else:
    # For production (Render)
    app.config['DEBUG'] = False