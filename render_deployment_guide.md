# 🚀 Deploy OrchestrAI Dashboard to Render

## 📋 Prerequisites

1. **GitHub Repository** - Push your code to GitHub
2. **Render Account** - Free account at https://render.com
3. **Environment Variables** - Configure your API keys

---

## 🗂️ Project Structure for Render

Your project should be structured like this:

```
MultiAgent_Project/
├── main.py                    # FastAPI backend
├── requirements.txt           # Python dependencies
├── .env                       # Environment variables (don't commit)
├── frontend/
│   ├── dashboard/
│   │   ├── index.html        # Dashboard HTML
│   │   ├── styles.css        # Dashboard CSS
│   │   ├── app.js           # Dashboard JavaScript
│   │   └── README.md        # Documentation
│   └── portfolio/
│       └── index.html        # Portfolio page
├── backend/                   # Backend agents
├── database/                 # Data storage
└── render.yaml              # Render configuration (optional)
```

---

## 🔧 Step 1: Update Main.py for Render

Make sure your `main.py` includes the dashboard static files:

```python
# Add this to your STATIC_DIRS list in main.py
STATIC_DIRS = [
    "database",
    "application_packages", 
    "frontend/practice",
    "frontend/portfolio",
    "frontend/portfolio/internships",
    "frontend/interview",
    "frontend/analytics",
    "frontend/dashboard",  # ← Add this line
    "optimized_resumes",
    "cover_letters",
]

# Add this mount for the dashboard
_safe_mount("/dashboard", os.path.join(DATA_DIR, "frontend/dashboard"), "dashboard", html=True)
```

---

## 🌐 Step 2: Create Render Configuration

Create `render.yaml` in your root directory:

```yaml
services:
  # Web Service for Backend API
  - type: web
    name: orchestrai-api
    runtime: python
    plan: free
    autoDeploy: true
    buildCommand: "pip install -r requirements.txt"
    startCommand: "python main.py"
    envVars:
      - key: PYTHON_VERSION
        value: "3.9"
      - key: GITHUB_TOKEN
        sync: false
      - key: GEMINI_API_KEY
        sync: false
      - key: EMAIL_USER
        sync: false
      - key: EMAIL_PASS
        sync: false
      - key: EMAIL_RECEIVER
        sync: false

  # Static Site for Dashboard
  - type: web
    name: orchestrai-dashboard
    runtime: static
    plan: free
    buildCommand: "echo 'No build required'"
    staticPublishPath: ./frontend/dashboard
    envVars:
      - key: API_URL
        value: https://orchestrai-api.onrender.com
```

---

## 🔐 Step 3: Configure Environment Variables

In Render Dashboard, set these environment variables:

### For the API Service (`orchestrai-api`):
```
GITHUB_TOKEN=your_github_token
GEMINI_API_KEY=AIzaSyDEOz_aJpaJ1CTorIlrQ4GxfwDP1S0wF3A
EMAIL_USER=your_gmail@gmail.com
EMAIL_PASS=your_gmail_app_password
EMAIL_RECEIVER=receiver@gmail.com
GITHUB_USERNAME=Swathy1209
GITHUB_REPO=Swathy1209/orchestrai-db
```

### For the Dashboard Service (`orchestrai-dashboard`):
```
API_URL=https://orchestrai-api.onrender.com
```

---

## 📤 Step 4: Push to GitHub

```bash
# Add all files
git add .

# Commit changes
git commit -m "Add OrchestrAI Dashboard for Render deployment"

# Push to GitHub
git push origin main
```

---

## 🚀 Step 5: Deploy on Render

1. **Go to Render Dashboard**: https://dashboard.render.com

2. **Create New Services**:
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Choose the branch (usually `main`)

3. **Configure API Service**:
   - Name: `orchestrai-api`
   - Runtime: `Python`
   - Plan: `Free`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python main.py`

4. **Configure Dashboard Service**:
   - Name: `orchestrai-dashboard`
   - Runtime: `Static`
   - Plan: `Free`
   - Build Command: `echo "No build required"`
   - Publish Directory: `frontend/dashboard`

5. **Add Environment Variables** for both services

6. **Deploy!** Click "Create Web Service"

---

## 🔗 Step 6: Update Dashboard API Calls

Update `frontend/dashboard/app.js` to use the Render API:

```javascript
// Update the API base URL
const API_BASE_URL = 'https://orchestrai-api.onrender.com';

// Update fetch methods
async fetchFromAPI(endpoint) {
    try {
        const response = await fetch(`${API_BASE_URL}/${endpoint}`);
        if (!response.ok) throw new Error('API request failed');
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        return null;
    }
}
```

---

## 📧 Step 7: Test Email Integration

Once deployed:

1. **Test API**: Visit `https://orchestrai-api.onrender.com/docs`
2. **Test Dashboard**: Visit `https://orchestrai-dashboard.onrender.com`
3. **Trigger Pipeline**: Call the pipeline endpoint or set up cron job

---

## 🔄 Step 8: Automated Email Reports

For daily email reports, you have two options:

### Option A: Render Cron (Recommended)
```yaml
# Add to render.yaml
cronjobs:
  - name: daily-email-report
    schedule: "0 8 * * *"  # Daily at 8 AM UTC
    command: "python -c 'from backend.agents.execution_agent import run_orchestrai_pipeline; run_orchestrai_pipeline()'"
    service: orchestrai-api
```

### Option B: External Cron Service
Use GitHub Actions, cron-job.org, or EasyCron to call:
```
https://orchestrai-api.onrender.com/trigger-pipeline
```

---

## 🎯 URL Structure After Deployment

- **API**: `https://orchestrai-api.onrender.com`
- **Dashboard**: `https://orchestrai-dashboard.onrender.com`
- **Portfolio**: `https://orchestrai-api.onrender.com/portfolio`
- **Documentation**: `https://orchestrai-api.onrender.com/docs`

---

## 📱 Email Template Update

Update your email template to include the dashboard link:

```html
<!-- Add to email_service.py -->
<div style="text-align: center; margin: 20px 0;">
  <a href="https://orchestrai-dashboard.onrender.com" 
     style="background: #0f3460; color: white; padding: 12px 24px; 
            text-decoration: none; border-radius: 8px; font-weight: 600;">
    📊 View Interactive Dashboard
  </a>
</div>
```

---

## 🔧 Troubleshooting

### Common Issues:

1. **Build Fails**: Check `requirements.txt` has all dependencies
2. **API Errors**: Verify environment variables are set correctly
3. **Dashboard 404**: Ensure static files are in correct directory
4. **Email Not Sending**: Check Gmail app password and SMTP settings

### Debug Commands:

```bash
# Check Render logs
# In Render Dashboard → Service → Logs

# Test locally
python main.py

# Check environment
python -c "import os; print(os.getenv('GEMINI_API_KEY'))"
```

---

## 🎉 Success!

Once deployed, you'll have:

- ✅ **Live API** at `https://orchestrai-api.onrender.com`
- ✅ **Interactive Dashboard** at `https://orchestrai-dashboard.onrender.com`
- ✅ **Daily Email Reports** with dashboard links
- ✅ **Mobile-responsive** design
- ✅ **Real-time data** updates

---

## 📞 Support

- **Render Docs**: https://render.com/docs
- **GitHub Issues**: Create issues in your repository
- **Status Page**: https://status.render.com

---

**🚀 Your OrchestrAI Dashboard is now live on Render!**
