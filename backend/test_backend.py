# test_backend.py
"""
Suite de tests complète basée sur les recommandations de l'encadrante
Tests les 10 vidéos du jeu de test proposé
"""

import requests
import time
import json
from pathlib import Path
from typing import Dict, List
import pandas as pd
from loguru import logger


class BackendTester:
    """Testeur pour le backend Vision-RAG recommandé"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = []
    
    def test_health(self) -> bool:
        """Test 1 : Health check"""
        logger.info("🔍 Test 1/10: Health check...")
        
        try:
            response = requests.get(f"{self.base_url}/api/health")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"   ✅ API healthy: {data}")
                return True
            else:
                logger.error(f"   ❌ API unhealthy: {response.status_code}")
                return False
        
        except Exception as e:
            logger.error(f"   ❌ Health check failed: {e}")
            return False
    
    def test_video_analysis(
        self, 
        video_path: str, 
        location: str,
        expected_min: int = 0,
        expected_max: int = 20
    ) -> Dict:
        """
        Test d'analyse vidéo
        
        Args:
            video_path: Chemin vers la vidéo
            location: Localisation
            expected_min: Nombre minimum d'équipements attendus
            expected_max: Nombre maximum d'équipements attendus
        
        Returns:
            Résultats du test
        """
        
        logger.info(f"🎬 Testing video: {Path(video_path).name}")
        logger.info(f"   Location: {location}")
        logger.info(f"   Expected: {expected_min}-{expected_max} equipments")
        
        start_time = time.time()
        
        try:
            # Préparer la requête
            with open(video_path, 'rb') as video_file:
                files = {'file': video_file}
                data = {'location': location, 'max_keyframes': 20}
                
                response = requests.post(
                    f"{self.base_url}/api/analyze-video",
                    files=files,
                    data=data,
                    timeout=300  # 5 minutes max
                )
            
            processing_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                
                # Métriques
                equipments_count = result['equipments_count']
                valid_count = result['metadata']['valid_equipments']
                review_count = result['metadata']['needs_review']
                
                # Validation
                success = expected_min <= equipments_count <= expected_max
                
                test_result = {
                    'video': Path(video_path).name,
                    'location': location,
                    'success': success,
                    'equipments_count': equipments_count,
                    'valid_count': valid_count,
                    'review_count': review_count,
                    'processing_time': processing_time,
                    'backend_time': result['processing_time'],
                    'keyframes': result['metadata']['keyframes_extracted'],
                    'detections': result['metadata']['detections_total'],
                    'unique_crops': result['metadata']['unique_crops']
                }
                
                # Log résultat
                status = "✅" if success else "❌"
                logger.info(f"   {status} Analysis complete:")
                logger.info(f"      - Equipments: {equipments_count} (valid: {valid_count}, review: {review_count})")
                logger.info(f"      - Time: {processing_time:.2f}s (backend: {result['processing_time']:.2f}s)")
                logger.info(f"      - Pipeline: {result['metadata']['keyframes']} keyframes → "
                           f"{result['metadata']['detections']} detections → "
                           f"{result['metadata']['unique_crops']} crops → "
                           f"{equipments_count} equipments")
                
                # Afficher quelques équipements
                for idx, eq in enumerate(result['equipments'][:3], 1):
                    logger.info(f"      - Equipment {idx}: {eq['designation']} - {eq['brand'] or 'Unknown'}")
                
                return test_result
            
            else:
                logger.error(f"   ❌ Request failed: {response.status_code}")
                logger.error(f"      Response: {response.text}")
                
                return {
                    'video': Path(video_path).name,
                    'location': location,
                    'success': False,
                    'error': response.text,
                    'processing_time': processing_time
                }
        
        except Exception as e:
            logger.error(f"   ❌ Test failed: {e}")
            
            return {
                'video': Path(video_path).name,
                'location': location,
                'success': False,
                'error': str(e),
                'processing_time': time.time() - start_time
            }
    
    def run_full_test_suite(self, test_videos_dir: str = "test_videos"):
        """
        Exécute la suite complète de tests (10 vidéos recommandées)
        
        Jeu de test proposé par l'encadrante (Section 9 du rapport) :
        1. bureau_standard.mp4 - Bureau classique (5-10 équipements)
        2. salle_technique.mp4 - Salle serveurs (10-15 équipements)
        3. cuisine.mp4 - Cuisine professionnelle (8-12 équipements)
        4. atelier.mp4 - Atelier fabrication (12-20 équipements)
        5. entrepot.mp4 - Entrepôt stockage (3-8 équipements)
        6. salle_reunion.mp4 - Salle de réunion (3-6 équipements)
        7. datacenter.mp4 - Datacenter (15-25 équipements)
        8. magasin.mp4 - Magasin retail (10-18 équipements)
        9. parking.mp4 - Parking souterrain (5-10 équipements)
        10. exterieur.mp4 - Façade bâtiment (8-15 équipements)
        """
        
        test_cases = [
            # (fichier, location, min_expected, max_expected)
            ("bureau_standard.mp4", "Bureau RDC", 5, 10),
            ("salle_technique.mp4", "Salle technique Étage 2", 10, 15),
            ("cuisine.mp4", "Cuisine professionnelle", 8, 12),
            ("atelier.mp4", "Atelier fabrication", 12, 20),
            ("entrepot.mp4", "Entrepôt stockage", 3, 8),
            ("salle_reunion.mp4", "Salle réunion A", 3, 6),
            ("datacenter.mp4", "Datacenter principal", 15, 25),
            ("magasin.mp4", "Magasin retail", 10, 18),
            ("parking.mp4", "Parking souterrain P1", 5, 10),
            ("exterieur.mp4", "Façade bâtiment principal", 8, 15)
        ]
        
        logger.info("=" * 80)
        logger.info("🧪 SUITE DE TESTS COMPLÈTE - 10 VIDÉOS")
        logger.info("   Basée sur les recommandations de l'encadrante (Section 9)")
        logger.info("=" * 80)
        
        # Test 1 : Health check
        if not self.test_health():
            logger.error("❌ Health check échoué, arrêt des tests")
            return
        
        # Tests 2-11 : Vidéos
        for idx, (video_file, location, min_exp, max_exp) in enumerate(test_cases, 2):
            logger.info("")
            logger.info(f"📹 Test {idx}/11: {video_file}")
            logger.info("-" * 80)
            
            video_path = Path(test_videos_dir) / video_file
            
            if not video_path.exists():
                logger.warning(f"   ⚠️  Vidéo introuvable: {video_path}")
                logger.warning(f"      Créez des vidéos de test ou utilisez vos propres vidéos")
                
                self.results.append({
                    'video': video_file,
                    'location': location,
                    'success': False,
                    'error': 'File not found'
                })
                continue
            
            result = self.test_video_analysis(
                str(video_path),
                location,
                expected_min=min_exp,
                expected_max=max_exp
            )
            
            self.results.append(result)
            
            # Pause entre tests
            time.sleep(2)
        
        # Génération du rapport
        self._generate_report()
    
    def _generate_report(self):
        """Génère un rapport détaillé des tests"""
        
        logger.info("")
        logger.info("=" * 80)
        logger.info("📊 RAPPORT DE TESTS")
        logger.info("=" * 80)
        
        # Statistiques globales
        total_tests = len(self.results)
        successful_tests = len([r for r in self.results if r.get('success', False)])
        
        total_time = sum([r.get('processing_time', 0) for r in self.results])
        avg_time = total_time / total_tests if total_tests > 0 else 0
        
        total_equipments = sum([r.get('equipments_count', 0) for r in self.results])
        
        logger.info(f"\n📈 STATISTIQUES GLOBALES")
        logger.info(f"   Total tests: {total_tests}")
        logger.info(f"   Succès: {successful_tests}/{total_tests} ({successful_tests/total_tests*100:.1f}%)")
        logger.info(f"   Temps total: {total_time:.2f}s")
        logger.info(f"   Temps moyen: {avg_time:.2f}s/vidéo")
        logger.info(f"   Équipements détectés: {total_equipments} total")
        
        # Métriques détaillées
        if successful_tests > 0:
            valid_results = [r for r in self.results if r.get('success', False)]
            
            avg_equipments = sum([r['equipments_count'] for r in valid_results]) / len(valid_results)
            avg_valid = sum([r.get('valid_count', 0) for r in valid_results]) / len(valid_results)
            avg_review = sum([r.get('review_count', 0) for r in valid_results]) / len(valid_results)
            
            logger.info(f"\n🎯 QUALITÉ")
            logger.info(f"   Équipements/vidéo: {avg_equipments:.1f} moyenne")
            logger.info(f"   Équipements valides: {avg_valid:.1f} moyenne")
            logger.info(f"   Nécessitent révision: {avg_review:.1f} moyenne")
        
        # Tableau récapitulatif
        logger.info(f"\n📋 DÉTAILS PAR VIDÉO")
        logger.info("-" * 80)
        logger.info(f"{'Vidéo':<25} {'Statut':<10} {'Équip.':<8} {'Valide':<8} {'Temps':<10}")
        logger.info("-" * 80)
        
        for result in self.results:
            status = "✅ OK" if result.get('success', False) else "❌ FAIL"
            equipments = result.get('equipments_count', 'N/A')
            valid = result.get('valid_count', 'N/A')
            time_taken = f"{result.get('processing_time', 0):.1f}s"
            
            logger.info(f"{result['video']:<25} {status:<10} {equipments:<8} {valid:<8} {time_taken:<10}")
        
        logger.info("-" * 80)
        
        # Sauvegarder en CSV
        self._save_to_csv()
        
        # Verdict final
        logger.info(f"\n{'='*80}")
        if successful_tests / total_tests >= 0.9:  # 90% de succès
            logger.info("✅ TESTS RÉUSSIS - Système validé pour production")
        elif successful_tests / total_tests >= 0.7:  # 70-90%
            logger.info("⚠️  TESTS PARTIELS - Améliorations nécessaires")
        else:
            logger.info("❌ TESTS ÉCHOUÉS - Révision architecture requise")
        
        logger.info(f"{'='*80}\n")
    
    def _save_to_csv(self):
        """Sauvegarde les résultats en CSV"""
        
        try:
            df = pd.DataFrame(self.results)
            csv_path = f"test_results_{int(time.time())}.csv"
            df.to_csv(csv_path, index=False)
            
            logger.info(f"\n💾 Résultats sauvegardés: {csv_path}")
        
        except Exception as e:
            logger.warning(f"⚠️  Échec sauvegarde CSV: {e}")


def main():
    """Point d'entrée principal"""
    
    logger.info("🚀 Démarrage de la suite de tests Vision-RAG v2.0")
    logger.info("   Architecture: YOLO-World + ByteTrack + Gemini 2.5 Flash\n")
    
    # Créer testeur
    tester = BackendTester(base_url="http://localhost:8000")
    
    # Exécuter tests
    tester.run_full_test_suite(test_videos_dir="test_videos")
    
    logger.info("✅ Suite de tests terminée\n")


if __name__ == "__main__":
    main()
