import csv
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# --- Configuration ---
INPUT_FILE  = r"D:\ana_proj\uaf_stu_result\data\uaf.txt"
OUTPUT_FILE = r"D:\ana_proj\uaf_stu_result\data\result_uaf.csv"
URL = 'https://lms.uaf.edu.pk/login/index.php'

# The courses we want to find
TARGET_COURSES = ['CS-408','BMS-402','IS-402','CS-410','STAT-402','CS-406','CS-412']

# CSV Header  — Sr removed, Name added after Registration Number
CSV_HEADER = [
    "Registration Number", "Name",
    "Semester", "Teacher Name", "Course Code",
    "Course Title", "Credit Hours",
    "Mid", "Assignment", "Final", "Practical", "Total", "Grade"
]

# Expected column positions in the HTML table (0-based, AFTER stripping Sr)
# Original table order: Sr | Semester | Teacher Name | Course Code | Course Title
#                       | Credit Hours | Mid | Assignment | Final | Practical | Total | Grade
# We skip index 0 (Sr) → use indices 1..12
DATA_SLICE = slice(1, 13)   # grab cols 1-12 (12 values)


def setup_driver():
    """Initialises Chrome WebDriver."""
    options = webdriver.ChromeOptions()
    # options.add_argument('--headless')  # uncomment for headless mode
    driver = webdriver.Chrome(options=options)
    return driver


def get_student_name(driver, wait) -> str:
    """
    Reads the student name from the info table at the top of the result page.
    The table cell containing 'Student Full Name' is followed by the name cell.

    HTML structure (from the snippet provided):
        <table class="table tab-content" ...>
          <tr>
            <td>Registration #</td>
            <td>2024-ag-10745</td>
          </tr>
          <tr>
            <td>Student Full Name</td>
            <td> HAFIZ MUHAMMAD ASAD IJAZ </td>
          </tr>
        </table>
    """
    try:
        # Find the <td> that contains "Student Full Name", then grab its sibling
        label_cells = driver.find_elements(By.XPATH, "//td[normalize-space()='Student Full Name']")
        if label_cells:
            # The name is in the next sibling <td>
            name_cell = label_cells[0].find_element(By.XPATH, "following-sibling::td[1]")
            return name_cell.text.strip()
    except NoSuchElementException:
        pass
    return "N/A"


def scrape_data():
    driver = setup_driver()

    with open(OUTPUT_FILE, mode='w', newline='', encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(CSV_HEADER)

        # Load registration numbers
        try:
            with open(INPUT_FILE, 'r') as txt_file:
                reg_numbers = [line.strip() for line in txt_file if line.strip()]
        except FileNotFoundError:
            print(f"[ERROR] Input file not found: {INPUT_FILE}")
            driver.quit()
            return

        print(f"[INFO] {len(reg_numbers)} registration number(s) to process.\n")

        for reg_num in reg_numbers:
            print(f"[→] Processing: {reg_num}")

            try:
                driver.get(URL)
                wait = WebDriverWait(driver, 10)

                # Enter registration number
                input_el = wait.until(EC.presence_of_element_located((By.ID, "REG")))
                input_el.clear()
                input_el.send_keys(reg_num)
                input_el.send_keys(Keys.RETURN)
                
                try:
                    # Wait for the results table
                    wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))

                    # Grab student name from the info table
                    student_name = get_student_name(driver, wait)

                    rows = driver.find_elements(By.TAG_NAME, "tr")
                    found = False

                    for row in rows:
                        cols = row.find_elements(By.TAG_NAME, "td")

                        if not cols:
                            continue  # skip header / empty rows

                        row_text = row.text

                        for course_code in TARGET_COURSES:
                            if course_code.lower() in row_text.lower():
                                found = True

                                # Extract all cell texts
                                all_cols = [c.text.strip() for c in cols]

                                # Drop Sr (index 0) → take the rest
                                data_cols = all_cols[1:]   # Semester … Grade

                                # Build the final CSV row
                                csv_row = [reg_num, student_name] + data_cols

                                writer.writerow(csv_row)
                                print(f"   [✓] Saved — {course_code} | {student_name}")
                                break  # one match per row is enough

                    if not found:
                        print(f"   [!] No matching course found for {reg_num}.")

                except TimeoutException:
                    print(f"   [!] Timed out waiting for results (invalid reg no?).")

            except Exception as exc:
                print(f"   [✗] Error processing {reg_num}: {exc}")

    driver.quit()
    print(f"\n[DONE] Results saved to:\n      {OUTPUT_FILE}")


if __name__ == "__main__":
    scrape_data()