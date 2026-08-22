# test_suite.py
"""
Suite de tests complète — Backend Vision-RAG v2.0
Teste : performance, qualité des fiches, robustesse
"""

import requests
import time
import json
import os
import csv
from pathlib import Path
from datetime import datetime
from loguru import logger


class TestSuite:

    BASE_URL   = "http://localhost:8000"
    VIDEOS_DIR = "test_videos"
    RESULTS_DIR = "test_results"

    # Seuils de validation
    MAX_TIME_SECONDS    = 120    # Max 2 minutes par vidéo
    MIN_EQUIPMENTS      = 1      # Au moins 1 équipement détecté
    MIN_CONFIDENCE      = 0.70   # Confiance minimale acceptée
    MAX_REVIEW_RATE     = 0.70   # Max 70% needsReview

    VALID_DESIGNATIONS = [
        "AppareilCuisine", "AppareilInformatique",
        "Climatisation", "Eclairage", "Robinet",
        "Refrigeration", "PeripheriqueImpression",
        "InfrastructureIT", "Autres"
    ]

    VALID_STATUTS = [
        "Toujours_en_marche",
        "En_marche_pendant_les_horaires_de_travail",
        "En_marche_selon_un_planning_specifique",
        "En_marche_selon_un_besoin",
        "Mode_saisonnier", "Mode_maintenance",
        "NonDetachable", "Inactif"
    ]

    def __init__(self):
        Path(self.RESULTS_DIR).mkdir(exist_ok=True)
        self.results    = []
        self.start_time = datetime.now().strftime("%Y%m%d_%H%M%S")

    # ─────────────────────────────────────────────
    # TEST 0 — Health check
    # ─────────────────────────────────────────────

    def test_health(self) -> bool:
        logger.info("=" * 60)
        logger.info("TEST 0 — Health check")
        logger.info("=" * 60)

        try:
            r = requests.get(f"{self.BASE_URL}/api/health", timeout=10)
            data = r.json()

            yolo   = data.get("yolo",   False)
            gemini = data.get("gemini", False)
            qdrant = data.get("qdrant", False)

            logger.info(f"  YOLO   : {'OK' if yolo   else 'FAIL'}")
            logger.info(f"  Gemini : {'OK' if gemini else 'FAIL'}")
            logger.info(f"  Qdrant : {'OK' if qdrant else 'FAIL'}")

            if all([yolo, gemini, qdrant]):
                logger.info("  Health check : PASS")
                return True
            else:
                logger.error("  Health check : FAIL — services indisponibles")
                return False

        except Exception as e:
            logger.error(f"  Health check : FAIL — {e}")
            return False

    # ─────────────────────────────────────────────
    # TEST 1 — Analyse d'une vidéo
    # ─────────────────────────────────────────────

    def test_video(self, video_path: str, location: str) -> dict:
        video_name = Path(video_path).name
        logger.info(f"\n{'─'*60}")
        logger.info(f"Vidéo : {video_name}")
        logger.info(f"Localisation : {location}")
        logger.info(f"{'─'*60}")

        result = {
            "video":            video_name,
            "location":         location,
            "timestamp":        datetime.now().isoformat(),
            # Performance
            "processing_time":  None,
            "time_ok":          False,
            # Détection
            "equipments_count": 0,
            "detection_ok":     False,
            # Qualité fiches
            "valid_count":      0,
            "review_count":     0,
            "quality_ok":       False,
            "schema_ok":        True,
            # Robustesse
            "api_ok":           False,
            "error":            None,
            # Détail équipements
            "equipments":       [],
            # Score global
            "score":            0,
            "passed":           False,
        }

        start = time.time()

        try:
            # Appel API
            with open(video_path, "rb") as vf:
                response = requests.post(
                    f"{self.BASE_URL}/api/analyze-video",
                    files={"file": (video_name, vf, "video/mp4")},
                    data={
                        "location":      location,
                        "max_keyframes": "15"
                    },
                    timeout=180
                )

            elapsed = time.time() - start
            result["processing_time"] = round(elapsed, 2)
            result["api_ok"] = True

            if response.status_code != 200:
                result["error"] = f"HTTP {response.status_code}: {response.text}"
                logger.error(f"  API error: {result['error']}")
                return result

            data = response.json()

            # ── Performance ──────────────────────────────
            result["time_ok"] = elapsed <= self.MAX_TIME_SECONDS
            logger.info(f"  Temps : {elapsed:.1f}s "
                       f"({'OK' if result['time_ok'] else 'TROP LONG'})")

            # ── Détection ────────────────────────────────
            equipments = data.get("equipments", [])
            result["equipments_count"] = len(equipments)
            result["valid_count"]      = data["metadata"]["valid_equipments"]
            result["review_count"]     = data["metadata"]["needs_review"]
            result["detection_ok"]     = len(equipments) >= self.MIN_EQUIPMENTS

            logger.info(f"  Équipements : {len(equipments)} "
                       f"({result['valid_count']} valides, "
                       f"{result['review_count']} review)")

            # ── Qualité des fiches ────────────────────────
            schema_errors  = 0
            low_confidence = 0
            detail_list    = []

            for eq in equipments:
                eq_detail = {
                    "name":        eq.get("name"),
                    "designation": eq.get("designation"),
                    "brand":       eq.get("brand"),
                    "needsReview": eq.get("needsReview"),
                    "conf_desig":  eq.get("confidence", {}).get("designation", 0),
                    "schema_ok":   True,
                    "issues":      []
                }

                # Vérification schéma
                if eq.get("designation") not in self.VALID_DESIGNATIONS:
                    eq_detail["schema_ok"] = False
                    eq_detail["issues"].append(
                        f"designation invalide: {eq.get('designation')}"
                    )
                    schema_errors += 1

                if eq.get("equipmentStatus") not in self.VALID_STATUTS:
                    eq_detail["schema_ok"] = False
                    eq_detail["issues"].append(
                        f"statut invalide: {eq.get('equipmentStatus')}"
                    )
                    schema_errors += 1

                # Règle Climatisation
                if eq.get("designation") == "Climatisation":
                    if eq.get("temperature") is None:
                        eq_detail["issues"].append("temperature manquante")
                    if eq.get("coolingCapacity") is None:
                        eq_detail["issues"].append("coolingCapacity manquante")

                # Confiance
                conf = eq.get("confidence", {}).get("designation", 0)
                if conf < self.MIN_CONFIDENCE and not eq.get("needsReview"):
                    low_confidence += 1
                    eq_detail["issues"].append(f"confiance faible: {conf:.2f}")

                detail_list.append(eq_detail)

                # Log par équipement
                status_icon = "✅" if not eq.get("needsReview") else "⚠️"
                logger.info(
                    f"  {status_icon} {eq.get('designation')} | "
                    f"{eq.get('brand') or 'N/A'} | "
                    f"conf={conf:.2f}"
                )
                if eq_detail["issues"]:
                    for issue in eq_detail["issues"]:
                        logger.warning(f"     → {issue}")

            result["equipments"]  = detail_list
            result["schema_ok"]   = schema_errors == 0

            # Taux needsReview
            review_rate = (
                result["review_count"] / len(equipments)
                if equipments else 0
            )
            result["quality_ok"] = (
                result["schema_ok"]
                and review_rate <= self.MAX_REVIEW_RATE
                and low_confidence == 0
            )

            logger.info(f"  Schéma    : {'OK' if result['schema_ok'] else 'ERREURS'} "
                       f"({schema_errors} erreurs)")
            logger.info(f"  Qualité   : {'OK' if result['quality_ok'] else 'PROBLÈME'} "
                       f"(review rate: {review_rate:.0%})")

            # ── Score global ─────────────────────────────
            score = 0
            if result["api_ok"]:        score += 25
            if result["time_ok"]:       score += 25
            if result["detection_ok"]:  score += 25
            if result["quality_ok"]:    score += 25

            result["score"]  = score
            result["passed"] = score >= 75

            logger.info(f"  Score : {score}/100 "
                       f"({'PASS' if result['passed'] else 'FAIL'})")

        except requests.exceptions.Timeout:
            result["error"] = "Timeout (>180s)"
            logger.error(f"  TIMEOUT après 180s")

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"  Erreur inattendue: {e}")

        return result

    # ─────────────────────────────────────────────
    # TESTS ROBUSTESSE
    # ─────────────────────────────────────────────

    def test_robustesse(self):
        logger.info(f"\n{'='*60}")
        logger.info("TESTS ROBUSTESSE")
        logger.info(f"{'='*60}")

        # Test 1 : Requête sans fichier
        logger.info("\n  Test R1 : Requête sans fichier vidéo")
        try:
            r = requests.post(
                f"{self.BASE_URL}/api/analyze-video",
                data={"location": "Test", "max_keyframes": "5"},
                timeout=10
            )
            if r.status_code == 422:
                logger.info("  R1 : PASS (422 Unprocessable Entity attendu)")
            else:
                logger.warning(f"  R1 : inattendu ({r.status_code})")
        except Exception as e:
            logger.warning(f"  R1 : {e}")

        # Test 2 : Location vide
        logger.info("\n  Test R2 : Location vide")
        videos = list(Path(self.VIDEOS_DIR).glob("*.mp4"))
        if videos:
            try:
                with open(videos[0], "rb") as vf:
                    r = requests.post(
                        f"{self.BASE_URL}/api/analyze-video",
                        files={"file": (videos[0].name, vf, "video/mp4")},
                        data={"location": "", "max_keyframes": "5"},
                        timeout=30
                    )
                if r.status_code in [200, 422]:
                    logger.info(f"  R2 : PASS (status {r.status_code})")
                else:
                    logger.warning(f"  R2 : status {r.status_code}")
            except Exception as e:
                logger.warning(f"  R2 : {e}")

        # Test 3 : Endpoint stats RAG
        logger.info("\n  Test R3 : Stats RAG")
        try:
            r = requests.get(f"{self.BASE_URL}/api/stats", timeout=10)
            if r.status_code == 200:
                stats = r.json()
                logger.info(f"  R3 : PASS — {stats}")
            else:
                logger.warning(f"  R3 : status {r.status_code}")
        except Exception as e:
            logger.warning(f"  R3 : {e}")

        # Test 4 : Deux requêtes simultanées
        logger.info("\n  Test R4 : Deux requêtes en parallèle")
        if len(videos) >= 1:
            import threading
            responses = []

            def call_api(vid):
                try:
                    with open(vid, "rb") as vf:
                        r = requests.post(
                            f"{self.BASE_URL}/api/analyze-video",
                            files={"file": (vid.name, vf, "video/mp4")},
                            data={"location": "Test Parallel",
                                  "max_keyframes": "5"},
                            timeout=120
                        )
                    responses.append(r.status_code)
                except Exception as e:
                    responses.append(str(e))

            t1 = threading.Thread(target=call_api, args=(videos[0],))
            t2 = threading.Thread(target=call_api, args=(videos[0],))
            t1.start(); t2.start()
            t1.join();  t2.join()

            ok = all(s == 200 for s in responses)
            logger.info(
                f"  R4 : {'PASS' if ok else 'PARTIEL'} "
                f"— réponses: {responses}"
            )

    # ─────────────────────────────────────────────
    # RAPPORT FINAL
    # ─────────────────────────────────────────────

    def generate_report(self):
        logger.info(f"\n{'='*60}")
        logger.info("RAPPORT FINAL")
        logger.info(f"{'='*60}")

        total   = len(self.results)
        passed  = sum(1 for r in self.results if r.get("passed"))
        failed  = total - passed

        if not self.results:
            logger.warning("Aucun résultat disponible")
            return

        avg_time  = sum(
            r["processing_time"] for r in self.results
            if r["processing_time"]
        ) / total

        avg_eq = sum(
            r["equipments_count"] for r in self.results
        ) / total

        total_valid  = sum(r["valid_count"]  for r in self.results)
        total_review = sum(r["review_count"] for r in self.results)

        # Affichage
        logger.info(f"\n  Vidéos testées    : {total}")
        logger.info(f"  Tests réussis     : {passed}/{total} "
                   f"({passed/total*100:.0f}%)")
        logger.info(f"  Tests échoués     : {failed}/{total}")
        logger.info(f"  Temps moyen       : {avg_time:.1f}s")
        logger.info(f"  Équipements/vidéo : {avg_eq:.1f} en moyenne")
        logger.info(f"  Total valides     : {total_valid}")
        logger.info(f"  Total needsReview : {total_review}")

        logger.info(f"\n  Détail par vidéo :")
        logger.info(f"  {'Vidéo':<25} {'Score':>6} {'Temps':>8} "
                   f"{'Équip.':>7} {'Statut':>8}")
        logger.info(f"  {'─'*55}")
        for r in self.results:
            status = "PASS" if r.get("passed") else "FAIL"
            logger.info(
                f"  {r['video']:<25} "
                f"{r.get('score', 0):>5}/100 "
                f"{r.get('processing_time', 0):>7.1f}s "
                f"{r.get('equipments_count', 0):>6} "
                f"{status:>8}"
            )

        # Verdict global
        success_rate = passed / total if total > 0 else 0
        logger.info(f"\n{'='*60}")
        if success_rate >= 0.9:
            logger.info("VERDICT : SYSTEME VALIDE POUR PRODUCTION")
        elif success_rate >= 0.7:
            logger.info("VERDICT : AMELIORATIONS NECESSAIRES")
        else:
            logger.info("VERDICT : REVISION ARCHITECTURE REQUISE")
        logger.info(f"{'='*60}")

        # Sauvegarder CSV
        csv_path = (
            f"{self.RESULTS_DIR}/results_{self.start_time}.csv"
        )
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            if self.results:
                writer = csv.DictWriter(
                    f,
                    fieldnames=[
                        k for k in self.results[0].keys()
                        if k != "equipments"
                    ]
                )
                writer.writeheader()
                for r in self.results:
                    row = {k: v for k, v in r.items()
                           if k != "equipments"}
                    writer.writerow(row)

        logger.info(f"\n  Résultats sauvegardés : {csv_path}")

        # Sauvegarder JSON détaillé
        json_path = (
            f"{self.RESULTS_DIR}/results_{self.start_time}.json"
        )
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)

        logger.info(f"  Détail JSON        : {json_path}")

    # ─────────────────────────────────────────────
    # POINT D'ENTRÉE
    # ─────────────────────────────────────────────

    def run(self):
        logger.info("\n" + "="*60)
        logger.info("  SUITE DE TESTS — Vision-RAG v2.0")
        logger.info("="*60)

        # 0. Health check
        if not self.test_health():
            logger.error("Serveur indisponible — arrêt des tests")
            return

        # 1. Trouver les vidéos
        videos = sorted(Path(self.VIDEOS_DIR).glob("*.mp4"))
        if not videos:
            logger.error(
                f"Aucune vidéo dans {self.VIDEOS_DIR}/ — "
                "copiez vos vidéos MP4 dans ce dossier"
            )
            return

        logger.info(f"\n{len(videos)} vidéo(s) trouvée(s) :")
        for v in videos:
            size_mb = v.stat().st_size / 1024 / 1024
            logger.info(f"  - {v.name} ({size_mb:.1f} MB)")

        # Noms de localisations par ordre
        locations = [
            "Bureau standard",
            "Salle technique",
            "Couloir",
            "Salle de réunion",
            "Cuisine",
            "Entrepôt",
            "Datacenter",
            "Extérieur",
            "Parking",
            "Accueil",
        ]

        # 2. Tests vidéos
        logger.info(f"\n{'='*60}")
        logger.info("TESTS VIDÉOS")
        logger.info(f"{'='*60}")

        for idx, video_path in enumerate(videos):
            location = locations[idx % len(locations)]
            result   = self.test_video(str(video_path), location)
            self.results.append(result)
            time.sleep(3)  # Pause entre les tests

        # 3. Tests robustesse
        self.test_robustesse()

        # 4. Rapport
        self.generate_report()


if __name__ == "__main__":
    suite = TestSuite()
    suite.run()