# 🧾 Uber Receipt Downloader

This app allows you to **automatically download receipt PDFs from Uber for Business** using a properly formatted CSV file. It automates login via Chrome, maintains session cookies between runs, and saves each PDF using user-friendly filenames.

---

## 🚀 Requirements

- **Google Chrome** must be installed.
- macOS or Windows with Python 3.8+
- A valid CSV file with the required structure.
- Internet access to download receipts from Uber.

---

## 📁 CSV Format Requirements

Your input `.csv` file must have the following **columns with exact header names**:

| Column Header                 | Description                              |
|------------------------------|------------------------------------------|
| `Receipt`                    | Direct URL to the PDF receipt (must work when logged into Uber Business) |
| `Last Name`                  | Used in naming the downloaded file       |
| `Transaction Timestamp (UTC)`| ISO-style timestamp used in filename     |

✅ Example:

```csv
Receipt,Last Name,Transaction Timestamp (UTC)
https://business.uber.com/receipt/abc123,Smith,2025-07-01T14:22:33Z
https://business.uber.com/receipt/def456,Brown,2025-07-02T09:33:36Z

🚫 The app will fail if:

Any of these columns are missing or renamed
Any rows have missing (blank) values in these columns

## 🧪 First Run

When launched, the app will open Google Chrome.
You'll be prompted to log into your Uber for Business account.
After login, the app will save session cookies to your local system so you won’t need to log in again for future runs.

## 🗂 Output

All receipts will be downloaded as PDFs and saved in your selected folder. Files are named using:

<Last Name>_<Timestamp>.pdf
Example:

Smith_2025-07-01_14-22-33.pdf

## 🔐 Cookie Storage

Session cookies are stored locally at:

~/.uber_receipts_cookies.pkl
To clear login and force re-authentication, simply delete that file.

## 💬 Troubleshooting

| Problem                               | Solution                                                                             |
| ------------------------------------- | ------------------------------------------------------------------------------------ |
| `No module named 'pandas'`            | Run `pip install -r requirements.txt`                                                |
| App opens Chrome but doesn’t download | Make sure you're logged into the **correct Uber account** and that cookies are valid |
| Still seeing login page               | Delete cookie file at `~/.uber_receipts_cookies.pkl` and relaunch the app            |
| Filenames not saving correctly        | Ensure the CSV file has **no blank values** and all required headers                 |

## 🧑‍💻 Author

Created by Josh Spodick
Open to contributions & feature requests!