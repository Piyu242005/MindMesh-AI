# 📸 Screenshot Instructions

## ✅ Quick Fix - Add Your Screenshots in 3 Steps:

### Step 1: Take Screenshots
Open your Aurora RAG application and take 2 screenshots:
1. **Main welcome screen** (with example prompt cards)
2. **Active chat conversation** (with questions and AI responses)

### Step 2: Save Screenshots
Save/copy your 2 screenshots to the `assets/` folder with these exact names:
- `aurora-dashboard.png` (or .jpg)
- `aurora-chat.png` (or .jpg)

### Step 3: Update README (if using .jpg)
If you saved as .jpg instead of .png, update the image extensions in README.md

---

## 🚀 Option: Use Your Existing Screenshots

If you already have the screenshots open:

**Windows:**
1. Right-click on each image → "Save image as..."
2. Navigate to: `C:\Users\Piyu\Downloads\RAG-Based-AI\assets\`
3. Save with the exact names:
   - `aurora-dashboard.png`
   - `aurora-chat.png`

**Or Drag & Drop:**
1. Open the `assets` folder in File Explorer
2. Drag your 2 screenshots into the folder
3. Rename them to match the required names

---

## 📁 Current Status

Your `assets/` folder structure should look like this:

```
assets/
├── README.md                 ✅ Exists
├── aurora-dashboard.png      ❌ Add this
└── aurora-chat.png          ❌ Add this
```

---

## 🔄 After Adding Images

Once you add the images, run:

```bash
# Stage the new images
git add assets/*.png

# Commit
git commit -m "📸 Add Aurora interface screenshots"

# Push to GitHub
git push origin main
```

Then your README will display the actual screenshots on GitHub! 🎉
