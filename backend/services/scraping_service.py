# services/scraping_service.py
"""
Web scraping pour alimenter la base RAG Qdrant
Sources : sites constructeurs + PDFs fiches techniques
"""

import requests
from bs4 import BeautifulSoup
import fitz  # PyMuPDF
from PIL import Image
import io
import os
import json
import time
from pathlib import Path
from loguru import logger
from typing import List, Dict, Optional
from config import settings


class ScrapingService:
    """
    Collecte des données depuis le web et les PDFs
    pour alimenter la base Qdrant
    """

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
            )
        })
        self.data_dir = Path("knowledge_base")
        self.pdf_dir  = self.data_dir / "pdfs"
        self.img_dir  = self.data_dir / "images"

        self.data_dir.mkdir(exist_ok=True)
        self.pdf_dir.mkdir(exist_ok=True)
        self.img_dir.mkdir(exist_ok=True)

        logger.info("ScrapingService initialized")

    # ─────────────────────────────────────────────────────
    # SOURCES PRÉDÉFINIES PAR CATÉGORIE D'ÉQUIPEMENT SFM
    # ─────────────────────────────────────────────────────

    SOURCES = {
        "Climatisation": [
            {
                "brand": "Daikin",
                "url": "https://www.daikin.fr/fr_fr/products/catalog.html",
                "type": "web"
            },
            {
                "brand": "LG",
                "url": "https://www.lg.com/fr/climatisation/",
                "type": "web"
            },
        ],
        "AppareilInformatique": [
            {
                "brand": "Dell",
                "url": "https://www.dell.com/fr-fr/shop/ordinateurs-portables/",
                "type": "web"
            },
            {
                "brand": "HP",
                "url": "https://www.hp.com/fr-fr/laptops.html",
                "type": "web"
            },
        ],
        "PériphériqueImpression": [
            {
                "brand": "HP",
                "url": "https://www.hp.com/fr-fr/printers.html",
                "type": "web"
            },
            {
                "brand": "Canon",
                "url": "https://www.canon.fr/printers/",
                "type": "web"
            },
        ],
        "InfrastructureIT": [
            {
                "brand": "Cisco",
                "url": "https://www.cisco.com/c/fr_fr/products/switches/",
                "type": "web"
            },
        ],
        "Réfrigération": [
            {
                "brand": "Samsung",
                "url": "https://www.samsung.com/fr/refrigerators/",
                "type": "web"
            },
        ],
    }

    # ─────────────────────────────────────────────────────
    # SCRAPING WEB
    # ─────────────────────────────────────────────────────

    def load_manual_catalog(self) -> List[Dict]:
        """Charge le catalogue manuel JSON"""
        catalog_path = self.data_dir / "equipment_catalog.json"
        
        if not catalog_path.exists():
            logger.warning("No manual catalog found at knowledge_base/equipment_catalog.json")
            return []
        
        try:
            with open(catalog_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            logger.info(f"Loaded {len(data)} items from manual catalog")
            return data
        except Exception as e:
            logger.error(f"Failed to load manual catalog: {e}")
            return []


    def scrape_product_page(self, url: str, brand: str,
                            designation: str) -> List[Dict]:
        """
        Scrape une page produit et extrait les specs
        """
        results = []

        try:
            logger.info(f"Scraping: {url}")
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            # Extraire toutes les images produit
            images = self._extract_images(soup, url, brand)

            # Extraire specs textuelles
            specs = self._extract_specs_from_html(soup, brand, designation)

            # Associer images + specs
            for spec in specs:
                spec["images"]      = images[:3]  # Max 3 images par produit
                spec["source_url"]  = url
                spec["designation"] = designation
                results.append(spec)

            logger.info(f"Scraped {len(results)} products from {brand}")

        except Exception as e:
            logger.warning(f"Scraping failed for {url}: {e}")

        return results

    def _extract_images(self, soup: BeautifulSoup,
                        base_url: str, brand: str) -> List[str]:
        """Télécharge les images produit et retourne les chemins locaux"""
        saved_paths = []

        # Sélecteurs CSS courants pour les images produit
        selectors = [
            "img.product-image",
            "img.product-img",
            "img[class*='product']",
            "img[class*='catalog']",
            ".product-gallery img",
            "img[alt*='product']",
        ]

        img_tags = []
        for selector in selectors:
            found = soup.select(selector)
            if found:
                img_tags.extend(found[:3])
                break

        # Fallback : prendre les premières images significatives
        if not img_tags:
            all_imgs = soup.find_all("img", src=True)
            img_tags = [
                img for img in all_imgs
                if img.get("width") and int(
                    img.get("width", 0)) > 100
            ][:3]

        for idx, img_tag in enumerate(img_tags[:3]):
            try:
                src = img_tag.get("src", "")
                if src.startswith("//"):
                    src = "https:" + src
                elif src.startswith("/"):
                    from urllib.parse import urlparse
                    parsed = urlparse(base_url)
                    src = f"{parsed.scheme}://{parsed.netloc}{src}"

                if not src.startswith("http"):
                    continue

                img_response = self.session.get(src, timeout=10)
                img_response.raise_for_status()

                # Sauvegarder localement
                img_name = (
                    f"{brand.lower()}_{idx}_{int(time.time())}.jpg"
                )
                img_path = self.img_dir / img_name

                # Convertir en JPEG
                image = Image.open(
                    io.BytesIO(img_response.content)
                ).convert("RGB")
                image.save(str(img_path), "JPEG", quality=85)

                saved_paths.append(str(img_path))
                logger.debug(f"Image saved: {img_path}")

            except Exception as e:
                logger.warning(f"Image download failed: {e}")
                continue

        return saved_paths

    def _extract_specs_from_html(self, soup: BeautifulSoup,
                                  brand: str,
                                  designation: str) -> List[Dict]:
        """Extrait les spécifications depuis le HTML"""
        specs_list = []

        # Chercher les tableaux de spécifications
        spec_tables = soup.find_all(
            "table", class_=lambda c: c and (
                "spec" in c.lower()
                or "technical" in c.lower()
                or "caracteristique" in c.lower()
            )
        )

        # Chercher aussi dans les divs avec data-spec
        spec_divs = soup.find_all(
            attrs={"data-spec": True}
        )

        # Noms de produits depuis les titres
        product_names = []
        for tag in soup.find_all(["h1", "h2", "h3"]):
            text = tag.get_text(strip=True)
            if brand.lower() in text.lower() and len(text) < 100:
                product_names.append(text)

        product_name = (
            product_names[0]
            if product_names
            else f"{brand} {designation}"
        )

        # Créer une fiche minimale avec ce qu'on trouve
        spec = {
            "name":        product_name,
            "brand":       brand,
            "model":       self._extract_model(soup, brand),
            "designation": designation,
            "power":       self._find_value(soup, ["power", "puissance", "watt", "W"]),
            "voltage":     self._find_value(soup, ["voltage", "tension", "volt", "V"]),
            "cooling_capacity": self._find_value(
                soup, ["BTU", "kW", "cooling", "froid"]
            ),
        }
        specs_list.append(spec)

        return specs_list

    def _extract_model(self, soup: BeautifulSoup,
                       brand: str) -> Optional[str]:
        """Extrait le numéro de modèle"""
        import re

        text = soup.get_text()
        # Patterns communs : FTXM35N, E5-571, LaserJet Pro M404
        patterns = [
            rf"{brand}[\s\-]([A-Z0-9]{{4,12}})",
            r"Modèle\s*:\s*([A-Z0-9\-]{4,15})",
            r"Model\s*:\s*([A-Z0-9\-]{4,15})",
            r"Référence\s*:\s*([A-Z0-9\-]{4,15})",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None

    def _find_value(self, soup: BeautifulSoup,
                    keywords: List[str]) -> Optional[float]:
        """Cherche une valeur numérique associée à un mot-clé"""
        import re

        text = soup.get_text()
        for keyword in keywords:
            pattern = rf"{keyword}[\s:]*(\d+[\.,]?\d*)"
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    value_str = match.group(1).replace(",", ".")
                    return float(value_str)
                except ValueError:
                    continue
        return None

    # ─────────────────────────────────────────────────────
    # PARSING PDF
    # ─────────────────────────────────────────────────────

    def parse_pdf(self, pdf_path: str) -> List[Dict]:
        """
        Extrait texte + images d'un PDF de fiche technique
        """
        results = []

        try:
            doc = fitz.open(pdf_path)
            logger.info(f"Parsing PDF: {pdf_path} ({len(doc)} pages)")

            full_text  = ""
            all_images = []

            for page_num, page in enumerate(doc):
                # Extraire le texte
                full_text += page.get_text()

                # Extraire les images
                image_list = page.get_images(full=True)
                for img_idx, img_ref in enumerate(image_list[:2]):
                    try:
                        xref    = img_ref[0]
                        base_img = doc.extract_image(xref)
                        img_bytes = base_img["image"]

                        image = Image.open(
                            io.BytesIO(img_bytes)
                        ).convert("RGB")

                        # Ignorer les icônes trop petites
                        if image.width < 100 or image.height < 100:
                            continue

                        img_name = (
                            f"pdf_{Path(pdf_path).stem}"
                            f"_p{page_num}_i{img_idx}.jpg"
                        )
                        img_path = self.img_dir / img_name
                        image.save(str(img_path), "JPEG", quality=85)
                        all_images.append(str(img_path))

                    except Exception as e:
                        logger.warning(f"Image extraction failed: {e}")

            # Extraire les specs du texte complet
            spec = self._extract_specs_from_text(
                full_text, pdf_path
            )
            spec["images"]     = all_images[:5]
            spec["source_url"] = f"file://{pdf_path}"
            results.append(spec)

            doc.close()

        except Exception as e:
            logger.error(f"PDF parsing failed for {pdf_path}: {e}")

        return results

    def _extract_specs_from_text(self, text: str,
                                  source: str) -> Dict:
        """Extrait les specs depuis le texte brut d'un PDF"""
        import re

        spec = {
            "name":             Path(source).stem,
            "brand":            self._detect_brand(text),
            "model":            self._extract_model_from_text(text),
            "designation":      self._detect_designation(text),
            "power":            None,
            "voltage":          None,
            "cooling_capacity": None,
        }

        # Puissance
        for pattern in [
            r"(\d+[\.,]?\d*)\s*[Ww](?:att)?",
            r"[Pp]uissance[\s:]*(\d+[\.,]?\d*)",
            r"[Pp]ower[\s:]*(\d+[\.,]?\d*)",
        ]:
            m = re.search(pattern, text)
            if m:
                try:
                    spec["power"] = float(m.group(1).replace(",", "."))
                    break
                except ValueError:
                    pass

        # Tension
        for pattern in [
            r"(\d+[\.,]?\d*)\s*[Vv](?:olt)?",
            r"[Tt]ension[\s:]*(\d+[\.,]?\d*)",
            r"[Vv]oltage[\s:]*(\d+[\.,]?\d*)",
        ]:
            m = re.search(pattern, text)
            if m:
                try:
                    spec["voltage"] = float(m.group(1).replace(",", "."))
                    break
                except ValueError:
                    pass

        # Capacité de refroidissement (BTU)
        for pattern in [
            r"(\d+[\.,]?\d*)\s*BTU",
            r"(\d+[\.,]?\d*)\s*kW",
            r"[Cc]apacité[\s:]*(\d+[\.,]?\d*)",
        ]:
            m = re.search(pattern, text)
            if m:
                try:
                    spec["cooling_capacity"] = float(
                        m.group(1).replace(",", ".")
                    )
                    break
                except ValueError:
                    pass

        return spec

    def _detect_brand(self, text: str) -> Optional[str]:
        """Détecte la marque depuis le texte"""
        brands = [
            "Daikin", "LG", "Samsung", "Dell", "HP",
            "Canon", "Cisco", "Schneider", "Lenovo",
            "Apple", "Epson", "Brother", "Panasonic"
        ]
        for brand in brands:
            if brand.lower() in text.lower():
                return brand
        return None

    def _extract_model_from_text(self, text: str) -> Optional[str]:
        """Extrait le modèle depuis le texte brut"""
        import re
        patterns = [
            r"[Mm]odèle\s*:?\s*([A-Z0-9][\w\-]{3,14})",
            r"[Mm]odel\s*:?\s*([A-Z0-9][\w\-]{3,14})",
            r"[Rr]éférence\s*:?\s*([A-Z0-9][\w\-]{3,14})",
        ]
        for pattern in patterns:
            m = re.search(pattern, text)
            if m:
                return m.group(1).strip()
        return None

    def _detect_designation(self, text: str) -> str:
        """Détecte la désignation SFM depuis le texte"""
        keywords = {
            "Climatisation":          ["climatiseur", "air conditionn", "split", "clim"],
            "AppareilInformatique":   ["laptop", "ordinateur", "computer", "notebook"],
            "PériphériqueImpression": ["imprimante", "printer", "laser", "jet d'encre"],
            "Réfrigération":          ["réfrigérateur", "frigo", "refrigerator"],
            "InfrastructureIT":       ["switch", "router", "serveur", "server"],
            "Éclairage":              ["luminaire", "ampoule", "led", "lighting"],
        }
        text_lower = text.lower()
        for designation, kws in keywords.items():
            if any(kw in text_lower for kw in kws):
                return designation
        return "Autres"

    # ─────────────────────────────────────────────────────
    # PIPELINE COMPLET
    # ─────────────────────────────────────────────────────

    def run_full_scraping(self) -> List[Dict]:
        """
        Pipeline complet :
        1. Catalogue manuel (JSON)
        2. PDFs locaux
        3. Web scraping (si accessible)
        """
        all_data = []

        # 1. Catalogue manuel
        logger.info("=== Phase 1: Manual catalog ===")
        manual_data = self.load_manual_catalog()
        all_data.extend(manual_data)
        logger.info(f"Manual catalog: {len(manual_data)} items")

        # 2. PDFs locaux
        logger.info("=== Phase 2: PDF parsing ===")
        pdf_files = list(self.pdf_dir.glob("*.pdf"))
        logger.info(f"Found {len(pdf_files)} PDFs to parse")
        for pdf_path in pdf_files:
            data = self.parse_pdf(str(pdf_path))
            all_data.extend(data)

        # 3. Web scraping (optionnel)
        logger.info("=== Phase 3: Web scraping ===")
        for designation, sources in self.SOURCES.items():
            for source in sources:
                if source["type"] == "web":
                    data = self.scrape_product_page(
                        source["url"],
                        source["brand"],
                        designation
                    )
                    all_data.extend(data)
                    time.sleep(2)

        # Sauvegarder
        output_path = self.data_dir / "scraped_data.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)

        logger.info(f"Total: {len(all_data)} items saved")
        return all_data