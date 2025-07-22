# Emotion Analysis Web Application

A Flask web application that analyzes emotion data from Excel files and provides health risk predictions based on emotional patterns.

## Features

- Upload Excel files containing emotion data
- Analyze emotion patterns and distributions
- Generate health risk predictions with suggestions
- Interactive charts showing emotion distribution
- Support for multiple Excel formats

## Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python app.py
```

3. Open your browser and go to `http://localhost:5000`

## Deployment on Render

### Method 1: Using GitHub (Recommended)

1. Push your code to a GitHub repository
2. Go to [Render Dashboard](https://dashboard.render.com/)
3. Click "New" → "Web Service"
4. Connect your GitHub repository
5. Configure the service:
   - **Name**: emotion-analysis-app (or your preferred name)
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Instance Type**: Free (or paid for better performance)

### Method 2: Manual Upload

1. Create a ZIP file of your project (excluding uploads/ folder and other unnecessary files)
2. Go to [Render Dashboard](https://dashboard.render.com/)
3. Click "New" → "Web Service"
4. Choose "Deploy from Git" or upload your ZIP file
5. Follow the same configuration as Method 1

### Environment Variables (Optional)

You can set these environment variables in Render:
- `FLASK_ENV`: production
- `PYTHON_VERSION`: 3.11.5

## File Structure

```
mobile/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── Procfile              # Render deployment configuration
├── runtime.txt           # Python version specification
├── render.yaml           # Render service configuration
├── .gitignore            # Git ignore rules
├── README.md             # This file
├── templates/
│   ├── index.html        # Upload page
│   └── results.html      # Results display page
└── uploads/              # Temporary file storage (auto-created)
```

## Supported File Formats

- Excel files (.xlsx, .xls)
- Two formats supported:
  1. Raw emotion data with columns: Session ID, Timestamp, Emotion, Confidence
  2. Emotion Summary format with columns: Emotion, Average (%)

## Health Risk Analysis

The application analyzes emotional patterns to predict potential health risks including:
- Cardiovascular issues
- Depression and anxiety
- Mood disorders
- Emotional suppression

Each prediction includes:
- Risk likelihood percentage
- Detailed explanation
- Actionable suggestions for improvement

## Technical Details

- **Framework**: Flask 2.3.3
- **Data Processing**: Pandas, NumPy
- **Excel Support**: openpyxl, xlrd
- **Charts**: Chart.js
- **Styling**: Tailwind CSS
- **Production Server**: Gunicorn

## Security Features

- File type validation
- Secure filename handling
- Automatic file cleanup
- File size limits (16MB max)