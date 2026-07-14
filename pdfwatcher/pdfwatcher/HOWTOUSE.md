# HOW TO USE — PDF Watcher (Invoice Renamer)

## What this program does

You have a folder full of PDF invoices from energy companies (Avacon, Mitnetz, E.On, etc.).  
Each PDF has a messy name like `Rechnung123.pdf`.  

This program **reads the PDF**, figures out which solar park it belongs to,  
and **renames it** to a clean name like:

```
D5 AR 20260228 Avacon 215000385783 Solarpark-Musterstadt 2026.02_311140059500.pdf
```

Then you can find any invoice in 2 seconds instead of opening 50 PDFs one by one.

---

## First time setup (do this ONCE)

### 1. Install Python

If you don't have Python, download it from:  
**https://www.python.org/downloads/**  

During install, CHECK the box that says **"Add Python to PATH"**.

### 2. Open a terminal

Press **Windows key**, type `cmd`, press Enter.  
A black window opens.

### 3. Go to the program folder

Type this and press Enter:

```
cd C:\Users\redck\Downloads\pdfwatcher
```

*(If you put the folder somewhere else, change the path.)*

### 4. Install the program

Type this ONE command and press Enter:

```
pip install -r requirements.txt
```

Wait 30 seconds. It will download everything the program needs.

---

## How to start the program

Every time you want to use it:

### 1. Open terminal

**Windows key** → type `cmd` → Enter

### 2. Go to folder

```
cd C:\Users\redck\Downloads\pdfwatcher
```

### 3. Start

```
python main.py
```

The window opens. You will see a dark screen with company names on the left.

---

## Everyday use (the simple version)

### Step 1: Drop PDFs into the right folder

Put your PDFs here:

```
...\Companies\Avacon\         ← put Avacon PDFs here
...\Companies\Mitnetz\        ← put Mitnetz PDFs here
...\Companies\E-On\           ← put E.On PDFs here
```

The program watches these folders automatically.  
If you drop a PDF in the right company folder, it renames itself in a few seconds.

### Step 2: Check the new names

Click on a company name on the left (like "Avacon").  
You see a list:

| ✓ | Old Name | → | New Name | Status | % |
|---|---|---|---|---|---|
| ☐ | scan123.pdf | → | D5 AR 20260228 Avacon ... | OK | 100% |
| ☐ | doc456.pdf | → | D2 AR 20260315 Mitnetz ... | OK | 85% |

**Green** = everything looks good  
**Yellow** = some info is missing, double-check  
**Red** = something went wrong, open the PDF manually

### Step 3: Approve and move

Click the little **☐ box** next to each file you want to move.  
It turns into **✅**.

Then click the green **"Markierte verschieben"** button at the top.

All checked files move to the destination folder.

---

## The buttons (what they do)

| Button | What it does |
|---|---|
| **Markierte verschieben** | Moves all checked files to the destination folder |
| **← Rückgängig** | Undoes the last move (puts files back) |
| **Alle ✓** | Checks ALL files at once |
| **Alle X** | Unchecks ALL files at once |
| **⚡ Auto: ON** | Turns automatic renaming on/off |
| **🔵 Dry Run: OFF** | If ON: shows what WOULD happen, but doesn't actually move files |

---

## Setting up the mapping (important!)

The program needs to know **which customer number** belongs to **which solar park**.

### How to set it up

1. **Right-click** on a company name on the left (like "Avacon")
2. Click **"⚙ Einstellungen"**
3. A window opens with a table

For each entry, fill in:

| Field | What to type | Example |
|---|---|---|
| **Kundennr** | The number from the PDF | `215000385783` |
| **Standort** | Where the solar park is | `Solarpark Musterstadt` |
| **Firma** | Which DETO company | `D5` |

4. Click **"+ Hinzufügen"** to add a new row
5. Click **"💾 Speichern"** to save

Once saved, any PDF with that Kundennummer will get the right Standort and Firma in its name.

### Finding the Kundennummer

Open any PDF from that company. Look for a number next to:
- **Vertragskonto** (most common)
- **Kundennummer**
- **Lieferstelle** (Lichtblick only)

That 8-12 digit number is what you put in the mapping table.

---

## What the colors mean

| Color | Meaning |
|---|---|
| 🟢 Green | All info found, name is correct |
| 🟡 Yellow | Some info missing, check manually |
| 🔴 Red | Error reading the PDF |
| 🔵 Blue | Dry Run mode (nothing actually moves) |
| 🟠 Orange | Duplicate filename found |

---

## Dry Run mode (safe testing)

Before you trust the program with real files, use Dry Run:

1. Click **"🔵 Dry Run: OFF"** → it turns orange: **"🟠 Dry Run: ON"**
2. Click a company, check the file list
3. The new names appear with `[DRY]` in front
4. Nothing actually gets renamed or moved

When you're happy, click again to turn Dry Run OFF.

---

## How to run the tests

If something seems broken, run the tests:

```
cd C:\Users\redck\Downloads\pdfwatcher
python -m pytest tests/ -v
```

You should see **87 passed**.  
If any say FAILED, something is wrong.

---

## Common problems

### "Module not found" error

You forgot step 4 of setup. Run:

```
pip install -r requirements.txt
```

### "Watchdog nicht installiert"

Auto-rename won't work but manual scanning still does.  
Run: `pip install watchdog`

### Program window is too small

Drag the edges of the window to resize.  
The size is saved automatically for next time.

### Language changed and my layout reset

Fixed in this version. Your language, theme, and window size are saved separately —  
changing one does NOT wipe the others.

### A PDF didn't get renamed

- Is it in the correct company folder?
- Is Auto-rename ON? (check the ⚡ button at the top)
- Does the confidence show less than 75%? (yellow or red status)
- If still stuck: click the company name on the left to manually re-scan

---

## Folder structure (for IT people)

```
pdfwatcher/
├── main.py                  ← double-click or run this to start
├── requirements.txt         ← what to install
├── pyproject.toml           ← project settings
├── HOWTOUSE.md              ← this file
├── mappings.json            ← your Kundennummer→Standort data (DON'T DELETE)
├── preferences.json         ← language, theme, window size
├── moves.log                ← record of every move (for undo)
├── src/                     ← the program code
└── tests/                   ← 87 automated tests
```

---

## Questions?

If a new energy company starts sending invoices in a weird format,  
a developer needs to add a new "provider" file in `src/.../providers/`.  

That's a 30-line file with the specific patterns for that company's PDF layout.
