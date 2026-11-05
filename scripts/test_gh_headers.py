import requests

test_url = "https://boards.greenhouse.io/figma/jobs/5711913004"

# 1. Bare requests
r1 = requests.get(test_url)
print("1. Bare requests:", r1.status_code)

# 2. Browser standard headers
headers_browser = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "en-US,en;q=0.9",
    "Sec-Ch-Ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1"
}
r2 = requests.get(test_url, headers=headers_browser)
print("2. Browser headers:", r2.status_code)

# 3. Referer from google
headers_ref = dict(headers_browser)
headers_ref["Referer"] = "https://www.google.com/"
r3 = requests.get(test_url, headers=headers_ref)
print("3. Google referer:", r3.status_code)

# 4. Embedded mode on Figma's own domain or ?gh_jid
r4 = requests.get("https://www.figma.com/careers/?gh_jid=5711913004", headers=headers_browser)
print("4. Figma domain careers:", r4.status_code, "len:", len(r4.content))

# 5. Look at response headers of 406
print("\nHeaders of r2:")
for k, v in r2.headers.items():
    print(f"  {k}: {v}")
