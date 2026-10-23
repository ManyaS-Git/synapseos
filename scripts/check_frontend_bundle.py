import urllib.request
import re

url = "https://synapseos-three.vercel.app"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req) as resp:
    html = resp.read().decode("utf-8")

scripts = re.findall(r'src="(/_next/static/[^"]+)"', html)
print(f"Found {len(scripts)} scripts in HTML.")

found_target = False
found_localhost = False

for s in scripts:
    s_url = url + s
    try:
        with urllib.request.urlopen(s_url) as s_resp:
            content = s_resp.read().decode("utf-8", errors="ignore")
            if "synapseos-api-2onj.onrender.com" in content:
                print(f"[VERIFIED] Frontend contains backend URL in {s}")
                found_target = True
            if "localhost:8000" in content:
                found_localhost = True
    except Exception as e:
        print(f"Error fetching {s}: {e}")

if not found_target and found_localhost:
    print("[WARNING] Frontend bundle contains 'localhost:8000' fallback! NEXT_PUBLIC_API_URL may not have been set during Vercel build.")
elif found_target:
    print("[SUCCESS] Frontend bundle is correctly configured with public backend URL!")
