"""
Management command to seed the Pinecone vector index with world
locations (capitals, major cities, and famous landmarks).

Usage:
    uv run manage.py seed_locations          # Seed locations
    uv run manage.py seed_locations --clear  # Clear index, then seed
"""

import logging
import re
import unicodedata

from django.conf import settings
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)

# ── Location dataset ─────────────────────────────────────
# Each entry: (name, lat, lon, country, type, aliases)
# The text field sent to Pinecone includes the name, country, and aliases
# to maximize semantic match quality.

LOCATIONS = [
    # ─── World Capitals ───
    ("Washington D.C.", 38.9072, -77.0369, "US", "city", ["DC", "Capitol Hill"]),
    ("London", 51.5074, -0.1278, "GB", "city", ["City of London", "Greater London"]),
    ("Paris", 48.8566, 2.3522, "FR", "city", ["City of Light", "Ville Lumière"]),
    ("Tokyo", 35.6762, 139.6503, "JP", "city", ["東京"]),
    ("Beijing", 39.9042, 116.4074, "CN", "city", ["Peking", "北京"]),
    ("Moscow", 55.7558, 37.6173, "RU", "city", ["Москва"]),
    ("Berlin", 52.5200, 13.4050, "DE", "city", ["German Capital"]),
    ("Rome", 41.9028, 12.4964, "IT", "city", ["Eternal City", "Roma"]),
    ("Madrid", 40.4168, -3.7038, "ES", "city", []),
    ("Ottawa", 45.4215, -75.6972, "CA", "city", []),
    ("Canberra", -35.2809, 149.1300, "AU", "city", []),
    ("Brasília", -15.7975, -47.8919, "BR", "city", []),
    ("New Delhi", 28.6139, 77.2090, "IN", "city", ["Delhi"]),
    ("Cairo", 30.0444, 31.2357, "EG", "city", ["Al-Qahira"]),
    ("Ankara", 39.9334, 32.8597, "TR", "city", []),
    ("Buenos Aires", -34.6037, -58.3816, "AR", "city", []),
    ("Seoul", 37.5665, 126.9780, "KR", "city", ["서울"]),
    ("Bangkok", 13.7563, 100.5018, "TH", "city", ["Krung Thep"]),
    ("Nairobi", -1.2864, 36.8172, "KE", "city", []),
    ("Lima", -12.0464, -77.0428, "PE", "city", []),
    ("Addis Ababa", 9.0192, 38.7525, "ET", "city", ["Addis", "Finfinnee"]),
    ("Jakarta", -6.2088, 106.8456, "ID", "city", []),
    ("Mexico City", 19.4326, -99.1332, "MX", "city", ["CDMX", "Ciudad de México"]),
    ("Bogotá", 4.7110, -74.0721, "CO", "city", []),
    ("Riyadh", 24.7136, 46.6753, "SA", "city", []),
    ("Lisbon", 38.7223, -9.1393, "PT", "city", ["Lisboa"]),
    ("Vienna", 48.2082, 16.3738, "AT", "city", ["Wien"]),
    ("Warsaw", 52.2297, 21.0122, "PL", "city", ["Warszawa"]),
    ("Stockholm", 59.3293, 18.0686, "SE", "city", []),
    ("Oslo", 59.9139, 10.7522, "NO", "city", []),
    ("Helsinki", 60.1699, 24.9384, "FI", "city", []),
    ("Copenhagen", 55.6761, 12.5683, "DK", "city", ["København"]),
    ("Athens", 37.9838, 23.7275, "GR", "city", ["Athina"]),
    ("Dublin", 53.3498, -6.2603, "IE", "city", []),
    ("Bern", 46.9480, 7.4474, "CH", "city", []),
    ("Amsterdam", 52.3676, 4.9041, "NL", "city", []),
    ("Brussels", 50.8503, 4.3517, "BE", "city", ["Bruxelles"]),
    ("Kyiv", 50.4501, 30.5234, "UA", "city", ["Kiev"]),
    ("Hanoi", 21.0285, 105.8542, "VN", "city", []),
    ("Manila", 14.5995, 120.9842, "PH", "city", []),
    # ─── Major Cities ───
    (
        "New York City",
        40.7128,
        -74.0060,
        "US",
        "city",
        ["NYC", "Big Apple", "Manhattan", "New York"],
    ),
    ("Los Angeles", 34.0522, -118.2437, "US", "city", ["LA", "City of Angels"]),
    ("Chicago", 41.8781, -87.6298, "US", "city", ["Windy City", "Chi-Town"]),
    ("San Francisco", 37.7749, -122.4194, "US", "city", ["SF", "Bay Area", "Frisco"]),
    ("Miami", 25.7617, -80.1918, "US", "city", ["Magic City"]),
    ("Houston", 29.7604, -95.3698, "US", "city", ["Space City"]),
    ("Las Vegas", 36.1699, -115.1398, "US", "city", ["Vegas", "Sin City"]),
    ("Seattle", 47.6062, -122.3321, "US", "city", ["Emerald City"]),
    ("Boston", 42.3601, -71.0589, "US", "city", ["Beantown"]),
    ("Toronto", 43.6532, -79.3832, "CA", "city", ["The Six"]),
    ("Vancouver", 49.2827, -123.1207, "CA", "city", []),
    ("Montreal", 45.5017, -73.5673, "CA", "city", ["Montréal"]),
    ("São Paulo", -23.5505, -46.6333, "BR", "city", ["Sampa"]),
    ("Rio de Janeiro", -22.9068, -43.1729, "BR", "city", ["Rio"]),
    ("Mumbai", 19.0760, 72.8777, "IN", "city", ["Bombay"]),
    ("Shanghai", 31.2304, 121.4737, "CN", "city", []),
    ("Hong Kong", 22.3193, 114.1694, "HK", "city", ["HK"]),
    ("Singapore", 1.3521, 103.8198, "SG", "city", ["Lion City"]),
    ("Dubai", 25.2048, 55.2708, "AE", "city", []),
    ("Istanbul", 41.0082, 28.9784, "TR", "city", ["Constantinople"]),
    ("Sydney", -33.8688, 151.2093, "AU", "city", []),
    ("Melbourne", -37.8136, 144.9631, "AU", "city", []),
    ("Johannesburg", -26.2041, 28.0473, "ZA", "city", ["Joburg"]),
    ("Cape Town", -33.9249, 18.4241, "ZA", "city", []),
    ("Lagos", 6.5244, 3.3792, "NG", "city", []),
    ("Casablanca", 33.5731, -7.5898, "MA", "city", []),
    ("Barcelona", 41.3874, 2.1686, "ES", "city", ["Barça"]),
    ("Milan", 45.4642, 9.1900, "IT", "city", ["Milano"]),
    ("Munich", 48.1351, 11.5820, "DE", "city", ["München"]),
    ("Prague", 50.0755, 14.4378, "CZ", "city", ["Praha"]),
    ("Budapest", 47.4979, 19.0402, "HU", "city", []),
    ("Zurich", 47.3769, 8.5417, "CH", "city", ["Zürich"]),
    ("Osaka", 34.6937, 135.5023, "JP", "city", []),
    ("Taipei", 25.0330, 121.5654, "TW", "city", []),
    ("Kuala Lumpur", 3.1390, 101.6869, "MY", "city", ["KL"]),
    ("Havana", 23.1136, -82.3666, "CU", "city", ["La Habana"]),
    # ─── Famous Landmarks ───
    ("Eiffel Tower", 48.8584, 2.2945, "FR", "landmark", ["Tour Eiffel", "Iron Lady"]),
    ("Statue of Liberty", 40.6892, -74.0445, "US", "landmark", ["Lady Liberty"]),
    ("Great Wall of China", 40.4319, 116.5704, "CN", "landmark", ["万里长城"]),
    ("Machu Picchu", -13.1631, -72.5450, "PE", "landmark", ["Lost City of the Incas"]),
    (
        "Colosseum",
        41.8902,
        12.4922,
        "IT",
        "landmark",
        ["Roman Colosseum", "Flavian Amphitheatre"],
    ),
    ("Taj Mahal", 27.1751, 78.0421, "IN", "landmark", []),
    (
        "Great Pyramids of Giza",
        29.9792,
        31.1342,
        "EG",
        "landmark",
        ["The Great Pyramids", "Pyramids of Egypt", "Giza Pyramids"],
    ),
    ("Christ the Redeemer", -22.9519, -43.2105, "BR", "landmark", ["Cristo Redentor"]),
    ("Big Ben", 51.5007, -0.1246, "GB", "landmark", ["Elizabeth Tower"]),
    ("Sydney Opera House", -33.8568, 151.2153, "AU", "landmark", []),
    ("Petra", 30.3285, 35.4444, "JO", "landmark", ["Rose City"]),
    ("Stonehenge", 51.1789, -1.8262, "GB", "landmark", []),
    ("Angkor Wat", 13.4125, 103.8670, "KH", "landmark", []),
    ("Mount Fuji", 35.3606, 138.7274, "JP", "landmark", ["Fuji-san", "富士山"]),
    ("Golden Gate Bridge", 37.8199, -122.4783, "US", "landmark", []),
    ("Times Square", 40.7580, -73.9855, "US", "landmark", ["Crossroads of the World"]),
    ("Niagara Falls", 43.0896, -79.0849, "CA", "landmark", []),
    ("Kremlin", 55.7520, 37.6175, "RU", "landmark", ["Moscow Kremlin"]),
    ("Burj Khalifa", 25.1972, 55.2744, "AE", "landmark", ["Tallest Building"]),
    (
        "Sagrada Família",
        41.4036,
        2.1744,
        "ES",
        "landmark",
        ["Sagrada Familia", "Gaudí's Cathedral"],
    ),
    ("Table Mountain", -33.9625, 18.4039, "ZA", "landmark", []),
    ("Hollywood Sign", 34.1341, -118.3215, "US", "landmark", ["Hollywood"]),
    ("Central Park", 40.7829, -73.9654, "US", "landmark", []),
    ("Grand Canyon", 36.1069, -112.1129, "US", "landmark", []),
    (
        "Acropolis",
        37.9715,
        23.7267,
        "GR",
        "landmark",
        ["Acropolis of Athens", "Parthenon"],
    ),
    ("Louvre Museum", 48.8606, 2.3376, "FR", "landmark", ["Louvre", "Musée du Louvre"]),
    ("Vatican City", 41.9029, 12.4534, "VA", "landmark", ["The Vatican", "Holy See"]),
    (
        "Mount Everest",
        27.9881,
        86.9250,
        "NP",
        "landmark",
        ["Sagarmatha", "Chomolungma"],
    ),
    ("Kilimanjaro", -3.0674, 37.3556, "TZ", "landmark", ["Mount Kilimanjaro"]),
    ("Victoria Falls", -17.9243, 25.8572, "ZW", "landmark", ["Mosi-oa-Tunya"]),
    ("Santorini", 36.3932, 25.4615, "GR", "landmark", ["Thera", "Thira"]),
    ("Maldives", 3.2028, 73.2207, "MV", "landmark", ["Maldive Islands"]),
    ("Bali", -8.3405, 115.0920, "ID", "landmark", ["Island of the Gods"]),
    ("Great Barrier Reef", -18.2871, 147.6992, "AU", "landmark", []),
    ("Chichen Itza", 20.6843, -88.5678, "MX", "landmark", ["El Castillo"]),
    ("Christ Church", -43.5321, 172.6362, "NZ", "city", ["Christchurch"]),
    ("Marrakech", 31.6295, -7.9811, "MA", "city", ["Marrakesh"]),
    ("Zanzibar", -6.1659, 39.1989, "TZ", "landmark", ["Spice Island"]),
    ("Maui", 20.7984, -156.3319, "US", "landmark", ["Valley Isle"]),
    ("Bermuda", 32.3078, -64.7505, "BM", "landmark", ["Bermuda Triangle"]),
    ("Galápagos Islands", -0.9538, -90.9656, "EC", "landmark", ["Galapagos"]),
    ("Easter Island", -27.1127, -109.3497, "CL", "landmark", ["Rapa Nui"]),
    ("Dead Sea", 31.5, 35.5, "IL", "landmark", []),
    ("Amazon Rainforest", -3.4653, -62.2159, "BR", "landmark", ["Amazon", "Amazonia"]),
]


def _build_text(name, country, loc_type, aliases):
    """Build a descriptive text string for embedding."""
    parts = [f"{name}, {country} — {loc_type}"]
    if aliases:
        parts.append(f"Also known as: {', '.join(aliases)}")
    return ". ".join(parts)


class Command(BaseCommand):
    help = "Seed the Pinecone vector index with world locations for fuzzy matching."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete all existing vectors before seeding.",
        )

    def handle(self, *args, **options):
        api_key = settings.PINECONE_API_KEY
        if not api_key:
            self.stderr.write(self.style.ERROR("PINECONE_API_KEY is not set."))
            return

        from pinecone import Pinecone

        pc = Pinecone(api_key=api_key)

        host = settings.PINECONE_HOST
        if host:
            index = pc.Index(
                name=settings.PINECONE_INDEX_NAME,
                host=host,
            )
        else:
            index = pc.Index(settings.PINECONE_INDEX_NAME)

        # Optionally clear
        if options["clear"]:
            self.stdout.write("Clearing all vectors from the index...")
            try:
                index.delete(delete_all=True)
                self.stdout.write(self.style.SUCCESS("Index cleared."))
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f"Clear skipped (index may be empty): {e}")
                )

        # Build texts and metadata
        texts = []
        metadata_list = []
        ids = []

        for name, lat, lon, country, loc_type, aliases in LOCATIONS:
            text = _build_text(name, country, loc_type, aliases)
            texts.append(text)
            metadata_list.append(
                {
                    "name": name,
                    "lat": lat,
                    "lon": lon,
                    "country": country,
                    "type": loc_type,
                    "aliases": ", ".join(aliases) if aliases else "",
                    "text": text,
                }
            )
            # ASCII-safe ID: normalize, strip accents, lowercase
            nfkd = unicodedata.normalize("NFKD", name)
            ascii_name = nfkd.encode("ascii", "ignore").decode("ascii")
            clean_id = re.sub(r"[^a-z0-9]+", "_", ascii_name.lower()).strip("_")
            ids.append(clean_id)

        self.stdout.write(f"Generating embeddings for {len(texts)} locations...")

        # Embed in batches of 50 (Pinecone Inference API limit)
        batch_size = 50
        all_vectors = []

        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i : i + batch_size]
            self.stdout.write(
                f"  Embedding batch {i // batch_size + 1}/"
                f"{(len(texts) + batch_size - 1) // batch_size}..."
            )

            response = pc.inference.embed(
                model="llama-text-embed-v2",
                inputs=batch_texts,
                parameters={
                    "input_type": "passage",
                    "truncate": "END",
                },
            )

            for j, embedding in enumerate(response):
                idx = i + j
                all_vectors.append(
                    {
                        "id": ids[idx],
                        "values": embedding.values,
                        "metadata": metadata_list[idx],
                    }
                )

        # Upsert in batches of 50
        self.stdout.write("Upserting vectors to Pinecone...")
        for i in range(0, len(all_vectors), batch_size):
            batch = all_vectors[i : i + batch_size]
            index.upsert(vectors=batch)
            self.stdout.write(
                f"  Upserted batch {i // batch_size + 1}/"
                f"{(len(all_vectors) + batch_size - 1) // batch_size}"
            )

        stats = index.describe_index_stats()
        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone! Seeded {len(all_vectors)} locations. "
                f"Index now has {stats.total_vector_count} vectors."
            )
        )
