# Deployment Checklist for Render

## Pre-Deployment Steps

### ✅ Files Created/Updated
- [x] `requirements.txt` - Python dependencies
- [x] `Procfile` - Tells Render how to start the app
- [x] `runtime.txt` - Specifies Python version
- [x] `.gitignore` - Excludes unnecessary files
- [x] `render.yaml` - Render configuration (optional)
- [x] `README.md` - Documentation
- [x] `app.py` - Updated for production hosting
- [x] `test_deployment.py` - Deployment readiness test

### ✅ Application Configuration
- [x] Production-ready Flask configuration
- [x] Health check endpoint (`/health`)
- [x] Proper file upload handling
- [x] Environment-aware port configuration
- [x] Upload folder path fixed for production

## Deployment Steps on Render

### Option 1: GitHub Integration (Recommended)

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit - ready for Render deployment"
   git branch -M main
   git remote add origin https://github.com/yourusername/your-repo-name.git
   git push -u origin main
   ```

2. **Deploy on Render**
   - Go to [Render Dashboard](https://dashboard.render.com/)
   - Click "New" → "Web Service"
   - Connect your GitHub account
   - Select your repository
   - Configure:
     - **Name**: `emotion-analysis-app`
     - **Environment**: `Python 3`
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `gunicorn app:app`
     - **Instance Type**: Free (or paid for better performance)

### Option 2: Direct Upload

1. **Create ZIP file** (exclude these folders/files):
   - `uploads/`
   - `__pycache__/`
   - `.git/`
   - `.vscode/`
   - `*.pyc`

2. **Upload to Render**
   - Go to [Render Dashboard](https://dashboard.render.com/)
   - Click "New" → "Web Service"
   - Choose "Upload from computer"
   - Upload your ZIP file
   - Use same configuration as Option 1

## Post-Deployment Verification

### Test These URLs After Deployment:
- `https://your-app-name.onrender.com/` - Main application
- `https://your-app-name.onrender.com/health` - Health check

### Expected Behavior:
1. **Home page** should load with file upload form
2. **File upload** should work with Excel files
3. **Results page** should display analysis and charts
4. **Health endpoint** should return JSON status

## Troubleshooting

### Common Issues:

1. **Build Fails**
   - Check `requirements.txt` for correct package versions
   - Ensure Python version in `runtime.txt` is supported

2. **App Won't Start**
   - Verify `Procfile` syntax: `web: gunicorn app:app`
   - Check app logs in Render dashboard

3. **File Upload Issues**
   - Render has ephemeral storage - files are automatically cleaned
   - Check file size limits (16MB max configured)

4. **Import Errors**
   - Run `python test_deployment.py` locally first
   - Ensure all dependencies are in `requirements.txt`

### Environment Variables (Optional):
Set these in Render dashboard if needed:
- `FLASK_ENV=production`
- `PYTHON_VERSION=3.11.5`

## Performance Notes

- **Free Tier**: App may sleep after 15 minutes of inactivity
- **Paid Tier**: Better performance and no sleep mode
- **File Storage**: Temporary files are automatically cleaned up
- **Memory**: Current configuration should work within free tier limits

## Security Considerations

- File type validation is implemented
- Secure filename handling
- File size limits enforced
- Automatic cleanup of uploaded files
- No sensitive data stored permanently