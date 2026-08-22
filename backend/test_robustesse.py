import requests
import time

BASE_URL = "http://localhost:8000"
VIDEO    = "test_videos/ma_video.mp4"

resultats = {
    "reussies": 0,
    "echecs":   0,
    "quota":    0,
    "temps":    []
}

for i in range(20):
    debut = time.time()
    try:
        with open(VIDEO, "rb") as f:
            r = requests.post(
                f"{BASE_URL}/api/analyze-video",
                files={"file": ("video.mp4", f, "video/mp4")},
                data={"location": f"Test_{i}",
                      "max_keyframes": "5"},
                timeout=120
            )
        elapsed = time.time() - debut
        if r.status_code == 200:
            resultats["reussies"] += 1
            resultats["temps"].append(elapsed)
            print(f"  ✅ Req {i+1:02d}: {elapsed:.1f}s")
        else:
            resultats["echecs"] += 1
            print(f"  ❌ Req {i+1:02d}: HTTP {r.status_code}")
    except Exception as e:
        resultats["echecs"] += 1
        if "429" in str(e):
            resultats["quota"] += 1
        print(f"  ❌ Req {i+1:02d}: {e}")
    time.sleep(5)  # pause entre requêtes

# Résumé
print("\n" + "="*50)
print(f"Réussies    : {resultats['reussies']}/20")
print(f"Échecs      : {resultats['echecs']}/20")
print(f"Quota 429   : {resultats['quota']}")
if resultats["temps"]:
    moy = sum(resultats["temps"]) / len(resultats["temps"])
    print(f"Temps moyen : {moy:.1f}s")