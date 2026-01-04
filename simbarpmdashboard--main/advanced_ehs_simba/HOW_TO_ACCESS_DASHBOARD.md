# 🎯 How to Access Dashboard

## ✅ Branch Status

**Current Branch:** `feature/dashboard` ✅
- All dashboard changes are on this separate branch
- Your main branch is safe and untouched

---

## 🌐 Access Dashboard

### **Option 1: Open in Browser (Easiest)**

1. **Make sure API is running:**
   ```bash
   cd /Users/apple/Downloads/perpexcu/advanced_ehs_simba
   source venv/bin/activate
   python arduino_api.py
   ```

2. **Open this URL in your browser:**
   ```
   http://localhost:5001/dashboard
   ```

3. **You should see:**
   - Beautiful dark-themed dashboard
   - Material prediction display
   - Test preset buttons
   - Detection history
   - Material database grid

---

## 🔄 Branch Management

### **Current Status:**
```bash
# You're currently on:
feature/dashboard  ← Dashboard branch
```

### **To Switch Back to Main:**
```bash
git checkout main
```

### **To Switch Back to Dashboard:**
```bash
git checkout feature/dashboard
```

### **To Delete Dashboard Branch (if you don't like it):**
```bash
git checkout main          # Switch to main first
git branch -D feature/dashboard  # Delete dashboard branch
```

---

## ✅ API is Running!

The API server is already started. Just open:
```
http://localhost:5001/dashboard
```

---

## 🎨 What You'll See

- **Header:** SmartDrill Pro logo + status
- **Prediction Card:** Current material + confidence ring
- **Sensor Readings:** RPM, Current, Vibration, Depth
- **Test Buttons:** 6 presets to simulate different rocks
- **History:** Past predictions
- **Materials Grid:** All 12 rock types

---

## 🆘 Troubleshooting

**Dashboard not loading?**
- Check API is running: `curl http://localhost:5001/`
- Check port 5001: `lsof -ti:5001`

**Want to see main branch?**
- `git checkout main` (dashboard won't be there)

**Want dashboard back?**
- `git checkout feature/dashboard`

---

**Just open `http://localhost:5001/dashboard` in your browser!** 🚀

