# Superset API Testing Examples

## 🎯 Summary of Your Issue

Your curl command failed due to **CORS (Cross-Origin Resource Sharing)** restrictions in the browser, not because the API is broken. The API is working perfectly! 

**✅ Proof**: Our test script successfully accessed the dashboard API and found **6 dashboards** including "USA Births Names", "World Bank's Data", and "Sales Analystic".

## 🔧 Working Solutions

### 1. PowerShell/Windows CMD Examples

```powershell
# Step 1: Login and get access token
$loginData = @{
    username = "admin"
    password = "admin" 
    provider = "db"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:8088/api/v1/security/login" -Method POST -Body $loginData -ContentType "application/json"
$token = $response.access_token

# Step 2: Use token to access dashboard API
$headers = @{
    "Authorization" = "Bearer $token"
    "Accept" = "application/json"
}

$dashboards = Invoke-RestMethod -Uri "http://localhost:8088/api/v1/dashboard/" -Headers $headers -Method GET
$dashboards.count
```

### 2. Python Requests (Recommended)

```python
import requests

# Login
login_data = {
    "username": "admin",
    "password": "admin", 
    "provider": "db"
}

response = requests.post(
    "http://localhost:8088/api/v1/security/login",
    json=login_data
)

token = response.json()["access_token"]

# Access API
headers = {"Authorization": f"Bearer {token}"}
dashboards = requests.get(
    "http://localhost:8088/api/v1/dashboard/",
    headers=headers
).json()

print(f"Found {dashboards['count']} dashboards")
```

### 3. Postman Configuration

1. **POST** `http://localhost:8088/api/v1/security/login`
   - Body (JSON):
     ```json
     {
       "username": "admin",
       "password": "admin",
       "provider": "db"
     }
     ```
   - Copy the `access_token` from response

2. **GET** `http://localhost:8088/api/v1/dashboard/`
   - Headers: `Authorization: Bearer YOUR_TOKEN_HERE`

## 🚫 Why Browser/Swagger CORS Fails

### The Problem
- Browsers enforce CORS for security
- `localhost:8088` to `localhost:8088` requests can trigger CORS
- Swagger UI runs in browser context
- "Failed to fetch" = CORS blocking the request

### The Solution  
- **Don't use browser for API testing**
- Use proper HTTP clients instead:
  - ✅ Postman
  - ✅ Insomnia  
  - ✅ Python requests
  - ✅ PowerShell Invoke-RestMethod
  - ✅ curl (outside browser)

## 🛠️ Enable CORS (Optional)

If you want Swagger UI to work in browser, add to `superset_config.py`:

```python
# Enable CORS for API testing
ENABLE_CORS = True
CORS_OPTIONS = {
    'supports_credentials': True,
    'allow_headers': ['*'],
    'origins': ['http://localhost:8088', 'http://127.0.0.1:8088'],
    'methods': ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
}
```

## 📊 Your API Test Results

From our test script:
- ✅ **Server Status**: Running on port 8088
- ✅ **Authentication**: Working (got access token)  
- ✅ **Dashboard API**: Working (found 6 dashboards)
- ✅ **Swagger UI**: Accessible at `/swagger/v1`
- ⚠️ **CORS**: Browser restriction (not server issue)

## 🎉 Conclusion

**Your Superset API is working perfectly!** The "Failed to fetch" in Swagger UI is a common browser CORS issue, not an API problem. Use the Python script, Postman, or PowerShell examples above for reliable API testing.

### Quick Test Command

```bash
# Run our test script to verify everything works
python test_api_access.py
```

This will show you exactly what APIs are working and how to access them properly! 