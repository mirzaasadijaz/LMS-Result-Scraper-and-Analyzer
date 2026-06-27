# UAF Student Result Scraper & GPA Calculator

A two-stage pipeline for pulling semester results off the UAF (University of
Agriculture, Faisalabad) LMS portal and turning them into a clean
GPA / CGPA report.

1. **`scraper.py`** — logs into the UAF LMS results page once per
   registration number and saves marks/grades for a fixed list of courses.
2. **`s4_cleaning.ipynb`** — cleans that raw export, computes Semester 4 GPA
   from the raw marks, and merges it with each student's prior-semester GPAs
   to produce a final CGPA sheet.

## Project structure

```
uaf_stu_result/
├── scraper.py                  # Selenium scraper
├── s4_cleaning.ipynb           # Cleaning + GPA/CGPA notebook
├── data/
│   ├── uaf.txt                 # Input: registration numbers, one per line
│   └── result_uaf.csv          # Output of scraper.py / input to notebook
├── BSCS 1St M4.xlsx             # Prior-semester GPA records (GPA_S1-S3)
└── Final_Student_Results.csv   # Final output of the notebook
```

## Requirements

- Python 3.x
- Google Chrome + a matching ChromeDriver on PATH
- Packages:

```
pip install selenium pandas numpy openpyxl
```

## 1. Scraper — `scraper.py`

For each registration number in the input file, it opens the LMS login page
(`https://lms.uaf.edu.pk/login/index.php`), enters the reg number into the
`REG` field, waits for the results table, then saves the student's name plus
any row matching one of the target courses:

```
CS-408, BMS-402, IS-402, CS-410, STAT-402, CS-406, CS-412
```

Edit `TARGET_COURSES` to change which courses get captured.

**Before running:**
- Update `INPUT_FILE` and `OUTPUT_FILE` at the top of the script — they're
  currently hardcoded Windows paths (`D:\ana_proj\uaf_stu_result\data\...`).
- Make sure ChromeDriver matches your installed Chrome version.

**Run:**
```
python scraper.py
```

**Notes:**
- Runs with a visible Chrome window by default (the `--headless` line is
  commented out — uncomment to run headless).
- 10-second wait per page; an invalid/unrecognized reg number is skipped
  with a warning printed to the console.
- Output is one CSV row per (student, course) match, so each student
  normally appears in up to 7 rows before the notebook reshapes things.

## 2. Cleaning & GPA notebook — `s4_cleaning.ipynb`

Takes `data/result_uaf.csv` and reshapes it into one row per student, then
computes GPA and CGPA.

**Steps:**
1. Load the raw scraped CSV.
2. Spot-check teacher names against a known/excluded list (catches
   scraping mismatches).
3. Drop columns not needed for GPA (`Semester`, `Teacher Name`,
   `Course Title`, `Credit Hours`, `Mid`, `Assignment`, `Final`,
   `Practical`); drop one known-bad registration number; rename
   `Total` → `Marks`.
4. Pivot long → wide: one row per student, with `Marks_<course>` and
   `Grade_<course>` columns.
5. Fill missing `IS-402` marks with the cohort average and missing grade
   with `'P'` (IS-402 is a 0-credit course, so this doesn't affect GPA).
6. Reorder columns into `Marks_/Grade_` pairs per course.
7. **Compute GPA:**
   - `credit_hours` maps each course code to its credit value.
   - `qp_1_credit` … `qp_4_credit` are quality-point lookup tables (marks →
     quality points) for 1–4 credit-hour courses, following the standard
     marks-to-QP conversion bands.
   - A grade of `F` or `P` forces that course's quality points to `0`,
     regardless of marks.
   - `GPA = total quality points / total credit hours`, rounded to 2 dp.
8. Merge in prior-semester GPAs (`GPA_S1`, `GPA_S2`, `GPA_S3`) from
   `BSCS 1St M4.xlsx` (sheet `SEM-3`), matched on `Registration Number`.
9. Rename the newly computed GPA column to `GPA_S4`.
10. `CGPA = mean(GPA_S1, GPA_S2, GPA_S3, GPA_S4)`, and
    `%CGPA = CGPA / 4 * 100`.
11. (Optional) filter for a single student to spot-check a result.
12. Export the final table to `Final_Student_Results.csv`.

**Inputs the notebook expects:**
- `data/result_uaf.csv` (from the scraper)
- `BSCS 1St M4.xlsx` in the same folder, with a `SEM-3` sheet containing
  `Reg No.`, `GPA_S1`, `GPA_S2`, `GPA_S3` (header on the second row).

**Output:** `Final_Student_Results.csv` — Registration Number, Name,
Marks/Grade per course, GPA_S1–S4, CGPA, %CGPA.

## Things to double-check before reusing on a new batch

- The excluded-teacher list and the dropped registration number
  (`2024-ag-10851`) look like one-off fixes for this specific run's data —
  review whether they still apply to new data.
- `credit_hours` and the quality-point tables are hardcoded for this
  semester's specific course list/credit hours — update both if the course
  lineup changes.
- Paths are hardcoded (Windows-style in `scraper.py`, relative in the
  notebook) — adjust for your environment.
