# Initialisation
import requests, json
import sys, traceback, pdb, os


def excepthook(exc_type, exc_value, exc_traceback):
    traceback.print_exception(exc_type, exc_value, exc_traceback)
    print("\nEntering debugger...")
    pdb.post_mortem(exc_traceback)


sys.excepthook = excepthook

token = os.environ["NOTION_API_TOKEN"]
databaseID = os.environ["NOTION_DATABASE_ID"]
headers = {
    "Authorization": "Bearer " + token,
    "Content-Type": "application/json",
    "Notion-Version": "2022-02-22",
}


def readDatabase(databaseID, headers):
    readUrl = f"https://api.notion.com/v1/databases/{databaseID}/query"
    res = requests.request("POST", readUrl, headers=headers)
    data = res.json()
    print(res.status_code)
    # print(res.text)

    with open("./full-properties.json", "w", encoding="utf8") as f:
        json.dump(data, f, ensure_ascii=False)
    return data


def download_pdf(url, filename):
    """Downloads a PDF from a URL and saves it with the specified filename.

    Args:
      url: The URL of the PDF to download.
      filename: The filename to save the PDF as.
    """
    response = requests.get(url, stream=True)

    if response.status_code == 200:
        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))
        with open(filename, "wb") as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)

    return response.status_code


def sanitize_name(filename):
    """Sanitizes a filename by removing invalid characters.

    Args:
      filename: The filename to sanitize.

    Returns:
      The sanitized filename with only valid characters.
    """
    valid_chars = "-_abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    return "".join(c for c in filename if c in valid_chars)


response = readDatabase(databaseID, headers)["results"]

not_downloaded = []
for idx, paper in enumerate(response):
    if len(paper["properties"]["Name"]["title"]) == 0:
        continue
    else:
        name = sanitize_name(paper["properties"]["Name"]["title"][0]["text"]["content"])

    if (
        paper["properties"]["Link"]["url"] == ""
        or paper["properties"]["Link"]["url"] is None
    ):
        print(f"No link found for paper {name}")
        continue

    if len(paper["properties"]["Category"]["rich_text"]) == 0:
        category = "Uncategorized"
    else:
        category = paper["properties"]["Category"]["rich_text"][0]["text"][
            "content"
        ].split(",")[0]

    link = paper["properties"]["Link"]["url"]
    if "arxiv" in link:
        pdf_url = (
            "https://arxiv.org/pdf/" + link.split("/")[-1].replace(".pdf", "") + ".pdf"
        )
    elif "openreview" in link:
        pdf_url = link.replace("forum", "pdf")
    elif "ieee" in link or "acm" in link:
        print(f"Skipping {name} as it requires IEEE or ACM login")
        not_downloaded.append(name)
        continue
    else:
        print(f"Skipping {name} as it is from an unrecognized source")
        not_downloaded.append(name)
        continue

    path = f"./pdfs/{category}/{name}.pdf"

    rcode = download_pdf(pdf_url, path)
    if rcode != 200:
        print(f"Failed to download paper: {name} with link {pdf_url}")

print(f"Failed to download {len(not_downloaded)} papers.")
