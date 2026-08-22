"""
Comparaison avec RAG vs sans RAG
Pour le chapitre 5 du rapport PFE
"""

import time
from pathlib import Path

import requests


BASE_URL = "http://localhost:8000"
VIDEO_PATH = "test_videos/ma_video.mp4"
LOCATION = "Bureau SFM"

TEST_EMAIL = "tech1@sfm.com"
TEST_PASSWORD = "tech123"

# Pause plus longue pour limiter les erreurs Gemini 429
PAUSE_BETWEEN_TESTS = 65


def get_user_id() -> str | None:
    """Authentifie l'utilisateur et retourne son UUID."""

    print("\n🔐 Authentification...")

    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
            },
            timeout=15,
        )

        if response.status_code != 200:
            print(
                f"❌ Échec de connexion : "
                f"{response.status_code} — {response.text}"
            )
            return None

        payload = response.json()

        # Prend en charge plusieurs formats de réponse
        user = payload.get("user") or {}
        user_id = (
            user.get("id")
            or payload.get("user_id")
            or payload.get("id")
        )

        if not user_id:
            print(
                "❌ Aucun user_id trouvé dans la réponse : "
                f"{payload}"
            )
            return None

        print(f"✅ Connecté : {TEST_EMAIL}")
        print(f"   user_id : {user_id}")

        return user_id

    except requests.RequestException as error:
        print(f"❌ Login impossible : {error}")
        return None


def test_video(
    endpoint: str,
    label: str,
    user_id: str,
) -> dict:
    """Exécute une analyse vidéo avec l'utilisateur connecté."""

    print(f"\n{'=' * 50}")
    print(f"Test : {label}")
    print(f"{'=' * 50}")

    if not user_id:
        print("❌ Test annulé : user_id absent")
        return {}

    video = Path(VIDEO_PATH)

    if not video.exists():
        print(f"❌ Vidéo introuvable : {VIDEO_PATH}")
        return {}

    form_data = {
        "location": LOCATION,
        "max_keyframes": "15",
        "user_id": user_id,
    }

    try:
        with video.open("rb") as video_file:
            start = time.time()

            response = requests.post(
                f"{BASE_URL}{endpoint}",
                files={
                    "file": (
                        video.name,
                        video_file,
                        "video/mp4",
                    )
                },
                data=form_data,
                timeout=300,
            )

            elapsed = time.time() - start

    except requests.Timeout:
        print("❌ Délai maximal de 300 secondes dépassé")
        return {}

    except requests.RequestException as error:
        print(f"❌ Requête impossible : {error}")
        return {}

    if response.status_code == 401:
        print("❌ Authentification refusée")
        print(response.text)
        return {}

    if response.status_code == 429:
        print("❌ Quota journalier ou quota Gemini atteint")
        print(response.text)
        return {}

    if response.status_code != 200:
        print(
            f"❌ Erreur HTTP {response.status_code} : "
            f"{response.text}"
        )
        return {}

    result = response.json()
    equipments = result.get("equipments", [])

    print(f"\n⏱️  Temps total : {elapsed:.1f} s")
    print(f"📦 Équipements : {len(equipments)}")
    print("\nDétail des fiches :")

    for index, equipment in enumerate(equipments, 1):
        confidence = equipment.get("confidence") or {}
        designation_confidence = confidence.get(
            "designation", 0
        )

        print(
            f"\n  Fiche {index} — "
            f"{equipment.get('name', 'N/A')}"
        )
        print(
            "    designation : "
            f"{equipment.get('designation')}"
        )
        print(
            "    brand       : "
            f"{equipment.get('brand')}"
        )
        print(
            "    model       : "
            f"{equipment.get('model')}"
        )
        print(
            "    power       : "
            f"{equipment.get('power')}"
        )
        print(
            "    voltage     : "
            f"{equipment.get('voltage')}"
        )
        print(
            "    status      : "
            f"{equipment.get('equipmentStatus')}"
        )
        print(
            "    confiance   : "
            f"{designation_confidence:.0%}"
        )
        print(
            "    needsReview : "
            f"{equipment.get('needsReview', '?')}"
        )

    return {
        "equipments": equipments,
        "temps": elapsed,
    }


def compare(
    with_rag: dict,
    without_rag: dict,
) -> None:
    """Compare les résultats obtenus dans les deux configurations."""

    print(f"\n{'=' * 62}")
    print("COMPARAISON AVEC RAG VS SANS RAG")
    print(f"{'=' * 62}")

    equipments_with = with_rag.get("equipments", [])
    equipments_without = without_rag.get("equipments", [])

    print(
        f"\n{'Champ':<20}"
        f"{'Avec RAG':>20}"
        f"{'Sans RAG':>20}"
    )
    print("-" * 62)

    print(
        f"{'Nb équipements':<20}"
        f"{len(equipments_with):>20}"
        f"{len(equipments_without):>20}"
    )
    print(
        f"{'Temps (s)':<20}"
        f"{with_rag.get('temps', 0):>20.1f}"
        f"{without_rag.get('temps', 0):>20.1f}"
    )

    compared_count = min(
        len(equipments_with),
        len(equipments_without),
    )

    if len(equipments_with) != len(equipments_without):
        print(
            "\n⚠️ Les deux configurations n'ont pas produit "
            "le même nombre de fiches."
        )

    fields = [
        "designation",
        "brand",
        "model",
        "power",
        "voltage",
        "equipmentStatus",
        "needsReview",
    ]

    for index in range(compared_count):
        equipment_with = equipments_with[index]
        equipment_without = equipments_without[index]

        print(
            f"\n  --- Fiche {index + 1} : "
            f"{equipment_with.get('name', 'N/A')} ---"
        )

        for field in fields:
            value_with = equipment_with.get(field)
            value_without = equipment_without.get(field)

            difference = (
                "✅ identique"
                if value_with == value_without
                else "⚠️ différent"
            )

            print(
                f"    {field:<18} : "
                f"[RAG] {str(value_with):<18} | "
                f"[sans RAG] {str(value_without):<18} "
                f"{difference}"
            )

    hallucinations_with = sum(
        1
        for equipment in equipments_with
        if equipment.get("brand")
        and (equipment.get("confidence") or {}).get(
            "brand", 0
        ) < 0.5
    )

    hallucinations_without = sum(
        1
        for equipment in equipments_without
        if equipment.get("brand")
        and (equipment.get("confidence") or {}).get(
            "brand", 0
        ) < 0.5
    )

    print(
        f"\n{'Marques à confiance <50 %':<30}"
        f"{hallucinations_with:>15}"
        f"{hallucinations_without:>15}"
    )


if __name__ == "__main__":
    print("🚀 Test de comparaison RAG vs sans RAG")
    print(f"   Vidéo   : {VIDEO_PATH}")
    print(f"   Serveur : {BASE_URL}")

    # Authentification obligatoire
    current_user_id = get_user_id()

    if not current_user_id:
        print("\n❌ Comparaison annulée : connexion impossible")
        raise SystemExit(1)

    result_with_rag = test_video(
        endpoint="/api/analyze-video",
        label="AVEC RAG — pipeline complet",
        user_id=current_user_id,
    )

    if result_with_rag:
        print(
            f"\n⏳ Pause de {PAUSE_BETWEEN_TESTS} secondes "
            "pour limiter les erreurs Gemini 429..."
        )
        time.sleep(PAUSE_BETWEEN_TESTS)

    result_without_rag = test_video(
        endpoint="/api/analyze-no-rag",
        label="SANS RAG — Gemini seul",
        user_id=current_user_id,
    )

    if result_with_rag and result_without_rag:
        compare(
            result_with_rag,
            result_without_rag,
        )
    else:
        print(
            "\n⚠️ Comparaison impossible : "
            "au moins un test a échoué."
        )

    print("\n✅ Script terminé")