# Troubleshooting Streamlit JavaScript Issues

## Problem
App works locally but fails on other devices with errors like:
- "SyntaxError: Unexpected identifier 'L'"
- "TypeError: Failed to fetch dynamically imported module: /static/js/PlotlyChart.*.js"

## Root Cause
These errors are NOT from your code. They're from Streamlit's internal JavaScript loading mechanism.

## Solutions Applied

### 1. Streamlit Configuration (✅ Done)
Created `.streamlit/config.toml` with:
- Headless mode enabled
- CORS disabled
- Static serving enabled
- Error details enabled

### 2. Dockerfile Updates (✅ Done)
- Added Streamlit config copy
- Added flags: `--server.enableCORS=false --server.enableStaticServing=true`

## Additional Steps to Fix the Issue

### Step 1: Clear Browser Cache
Users experiencing the issue should:
1. Clear browser cache (Ctrl+Shift+Delete)
2. Try in incognito/private mode
3. Try different browser (Chrome, Firefox, Edge)

### Step 2: Rebuild and Redeploy
```bash
# On local machine
git add .
git commit -m "Fix Streamlit static file serving"
git push origin main
```

### Step 3: Verify Deployment
```bash
# SSH into EC2
ssh -i /path/to/key.pem ubuntu@<EC2-IP>

# Check container
cd ~/construction-planner
docker-compose down
docker-compose pull
docker-compose up -d

# Check logs
docker-compose logs -f
```

### Step 4: Test from Different Devices
- Test from mobile device
- Test from different network
- Test with VPN disabled

## If Issue Persists

### Option A: Disable Plotly Interactive Features
If Plotly is still causing issues, switch to static images:

```python
# In frontend/app.py, replace st.plotly_chart with:
import plotly.io as pio

# Convert to static image
img_bytes = pio.to_image(fig, format='png')
st.image(img_bytes, use_column_width=True)
```

### Option B: Use Streamlit's Built-in Charts
Replace Plotly with Streamlit's native charts:
```python
# Instead of st.plotly_chart, use:
st.bar_chart(df)
st.line_chart(df)
st.area_chart(df)
```

### Option C: Check Streamlit Version
Ensure same Streamlit version locally and in deployment:
```bash
# Local
streamlit --version

# In Dockerfile, pin version:
# streamlit==1.28.0
```

## Monitoring

### Check for Static File Errors
```bash
# On EC2, check Streamlit logs for static file errors
docker-compose logs | grep -i "static"
docker-compose logs | grep -i "js"
```

### Enable Debug Mode
In `.streamlit/config.toml`, set:
```toml
[logger]
level = "debug"
```

## Prevention

### Regular Maintenance
1. Keep Streamlit version updated
2. Clear Docker cache periodically:
   ```bash
   docker system prune -a
   ```
3. Monitor logs for static file errors

### Best Practices
1. Always test deployment from multiple devices
2. Use version pinning in requirements.txt
3. Keep browser cache clearing instructions handy for users

## Contact Support
If issue persists after all steps:
1. Check Streamlit GitHub issues for similar problems
2. Report to Streamlit with error logs
3. Consider using Streamlit Cloud for deployment (handles static files automatically)
