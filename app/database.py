import os
import sqlite3
from datetime import date, datetime

import psycopg
from psycopg.rows import dict_row


def get_database_url():
    return os.environ.get("DATABASE_URL", "").strip()


def get_database_path():
    return os.environ.get(
        "DATABASE_PATH",
        os.path.join(os.path.dirname(__file__), "goshow.db"),
    )


class DatabaseConnection:
    def __init__(self, connection, backend):
        self.connection = connection
        self.backend = backend

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception, traceback):
        if exception_type is not None:
            self.connection.rollback()

        self.connection.close()

    def prepare_query(self, query):
        if self.backend == "postgres":
            return query.replace("?", "%s")

        return query

    def execute(self, query, parameters=()):
        return self.connection.execute(
            self.prepare_query(query),
            parameters,
        )

    def executemany(self, query, parameter_rows):
        cursor = self.connection.cursor()
        cursor.executemany(
            self.prepare_query(query),
            parameter_rows,
        )
        return cursor

    def insert_and_get_id(self, query, parameters):
        if self.backend == "postgres":
            returning_query = (
                query.rstrip().rstrip(";") + " RETURNING id"
            )
            row = self.execute(
                returning_query,
                parameters,
            ).fetchone()
            return row["id"]

        cursor = self.execute(query, parameters)
        return cursor.lastrowid

    def commit(self):
        self.connection.commit()

    def rollback(self):
        self.connection.rollback()


def get_connection():
    database_url = get_database_url()

    if database_url:
        connection = psycopg.connect(
            database_url,
            row_factory=dict_row,
            connect_timeout=15,
        )
        return DatabaseConnection(connection, "postgres")

    connection = sqlite3.connect(get_database_path())
    connection.row_factory = sqlite3.Row
    return DatabaseConnection(connection, "sqlite")


def init_database():
    if not get_database_url():
        database_path = get_database_path()
        database_dir = os.path.dirname(database_path)

        if database_dir:
            os.makedirs(database_dir, exist_ok=True)

    concerts = [
        (
            "Lenny Kravitz - Live 2026",
            "Lenny Kravitz",
            "Uber Arena, Berlin",
            "2026-08-21",
            89.00,
            120,
            "Lenny Kravitz brings his guitar-driven mix of rock, funk, and soul to Uber Arena for a summer night built around big hooks and a polished live band. Expect a career-spanning set that moves from swaggering riffs to warm, groove-heavy moments made for an arena crowd.",
            "https://goshowimageswingwei.blob.core.windows.net/concert-images/lenny-kravitz.jpg",
        ),
        (
            "Guns N' Roses",
            "Guns N' Roses",
            "Uber Arena, Berlin",
            "2026-08-28",
            110.00,
            90,
            "Guns N' Roses return to Berlin with a full-scale rock show shaped by iconic riffs, extended solos, and the kind of singalong choruses that fill an arena. This is a high-energy date for fans who want the band's hard-rock catalog delivered with volume, attitude, and plenty of room for live surprises.",
            "https://goshowimageswingwei.blob.core.windows.net/concert-images/guns-n-roses.jpg",
        ),
        (
            "Pet Shop Boys",
            "Pet Shop Boys",
            "Waldbuhne Berlin",
            "2026-09-05",
            75.00,
            150,
            "Pet Shop Boys bring their elegant synth-pop catalogue to the open-air setting of Waldbuhne Berlin. The show pairs sharp electronic production, theatrical staging, and decades of dance-floor favorites in a setting made for a summer evening.",
            "https://goshowimageswingwei.blob.core.windows.net/concert-images/pet-shop-boys.jpg",
        ),
        (
            "Blood Orange - OFF DAYS 2026",
            "Blood Orange",
            "Columbiahalle, Berlin",
            "2026-09-12",
            60.49,
            70,
            "Blood Orange brings Dev Hynes' distinctive blend of alternative R&B, indie pop, funk, and downtown club textures to Columbiahalle. The listing is suited for fans of a more intimate concert atmosphere, with spacious grooves and emotionally direct songwriting at the center of the night.",
            "https://goshowimageswingwei.blob.core.windows.net/concert-images/blood-orange.jpg",
        ),
        (
            "Gentleman - Gratitude Tour 2026",
            "Gentleman",
            "Columbiahalle, Berlin",
            "2026-09-19",
            47.00,
            80,
            "Gentleman returns to Columbiahalle with a reggae-focused live show rooted in warm rhythms, clear melodies, and an easy connection with the audience. The Gratitude Tour date is a relaxed but lively night for fans of roots reggae, dancehall touches, and uplifting singalong moments.",
            "https://goshowimageswingwei.blob.core.windows.net/concert-images/gentleman.jpg",
        ),
        (
            "Joji - SOLARIS",
            "Joji",
            "Velodrom, Berlin",
            "2026-09-07",
            69.00,
            100,
            "Joji's SOLARIS date at Velodrom brings his atmospheric blend of alt-R&B, melancholic pop, and understated electronic production to a large-room setting. Expect a focused live set built around vulnerable vocals, late-night textures, and fan favorites that balance quiet intensity with bigger cinematic moments.",
            "https://goshowimageswingwei.blob.core.windows.net/concert-images/joji.png",
        ),
        (
            "The National - City Lights",
            "The National",
            "Tempodrom, Berlin",
            "2026-10-03",
            64.50,
            95,
            "The National bring their brooding indie-rock sound to Tempodrom for a Berlin date centered on rich arrangements, baritone vocals, and slow-burning anthems. The show should appeal to fans who want the band's intimate lyricism presented with the scale and dynamics of a seasoned live act.",
            "https://goshowimageswingwei.blob.core.windows.net/concert-images/the-national.jpg",
        ),
        (
            "SZA - Evening Session",
            "SZA",
            "Uber Arena, Berlin",
            "2026-10-10",
            98.00,
            130,
            "SZA's Evening Session brings modern R&B, alt-soul, and confessional pop songwriting to Uber Arena. The concert listing highlights a sleek arena production with room for both stripped-back vocal moments and the bigger, beat-driven tracks that have made her catalog feel personal and communal at once.",
            "https://goshowimageswingwei.blob.core.windows.net/concert-images/sza.jpg",
        ),
        (
            "Hozier - Unreal Unearth Tour",
            "Hozier",
            "Max-Schmeling-Halle, Berlin",
            "2026-10-17",
            72.00,
            115,
            "Hozier brings the Unreal Unearth Tour to Max-Schmeling-Halle with a set that draws from blues, soul, folk, and expansive rock arrangements. Fans can expect commanding vocals, a full live band, and songs that shift naturally between quiet intensity and sweeping choruses.",
            "https://goshowimageswingwei.blob.core.windows.net/concert-images/hozier.jpg",
        ),
        (
            "Raye - My 21st Century Blues",
            "Raye",
            "Columbiahalle, Berlin",
            "2026-10-24",
            54.00,
            85,
            "Raye brings My 21st Century Blues to Columbiahalle for a show that blends pop, R&B, jazz phrasing, and sharp storytelling. The night is built for listeners who want strong vocals, candid lyrics, and a live band feel that gives the songs extra swing and bite.",
            "https://goshowimageswingwei.blob.core.windows.net/concert-images/raye.jpg",
        ),
        (
            "Khruangbin - A La Sala",
            "Khruangbin",
            "Verti Music Hall, Berlin",
            "2026-10-31",
            58.00,
            105,
            "Khruangbin's A La Sala date at Verti Music Hall offers a groove-led set shaped by psychedelic guitar lines, dubby bass, crisp drums, and global funk influences. It is a relaxed, rhythm-forward concert for fans who want atmosphere, musicianship, and space to move.",
            "https://goshowimageswingwei.blob.core.windows.net/concert-images/khruangbin.jpg",
        ),
        (
            "Fred again.. - Live",
            "Fred again..",
            "Velodrom, Berlin",
            "2026-11-07",
            83.00,
            125,
            "Fred again.. brings an immersive electronic live show to Velodrom, combining club energy with emotional vocal samples and hands-on performance. Expect a big-room set that moves between intimate diary-like moments and communal dance peaks.",
            "https://goshowimageswingwei.blob.core.windows.net/concert-images/fred-again.jpg",
        ),
        (
            "Rosalia - Motomami Night",
            "Rosalia",
            "Uber Arena, Berlin",
            "2026-11-14",
            92.00,
            140,
            "Rosalia's Motomami Night brings her fusion of flamenco roots, experimental pop, reggaeton, and precise visual style to Uber Arena. The show is positioned as a sleek arena performance with choreography, bold production choices, and songs that move confidently between tradition and the club.",
            "https://goshowimageswingwei.blob.core.windows.net/concert-images/rosalia.jpg",
        ),
        (
            "Bon Iver - Winter Songs",
            "Bon Iver",
            "Admiralspalast, Berlin",
            "2026-11-21",
            67.00,
            75,
            "Bon Iver's Winter Songs date at Admiralspalast is a seated-feeling, atmospheric concert built around layered vocals, textured guitars, and spacious folk arrangements. It is a fitting winter booking for fans who want a quieter, carefully shaped live experience rather than a standard arena spectacle.",
            "https://goshowimageswingwei.blob.core.windows.net/concert-images/bon-iver.jpg",
        ),
        (
            "Jungle - Volcano Tour",
            "Jungle",
            "Huxleys Neue Welt, Berlin",
            "2026-11-28",
            52.00,
            90,
            "Jungle bring the Volcano Tour to Huxleys Neue Welt with a tight live set of modern funk, disco, soul, and dance-pop grooves. The concert is made for a standing-room crowd, with bright vocal hooks and rhythm-section momentum carrying the night from the first track.",
            "https://goshowimageswingwei.blob.core.windows.net/concert-images/jungle.jpg",
        ),
        (
            "Arctic Monkeys - Late Night Berlin",
            "Arctic Monkeys",
            "Waldbuhne Berlin",
            "2026-09-06",
            88.00,
            160,
            "Arctic Monkeys take over Waldbuhne Berlin with a late-night rock show that balances wiry early singles, lounge-tinged newer material, and swaggering festival-sized favorites. The open-air venue gives the set room to feel both stylish and loud without losing the band's cool, tightly wound edge.",
            "https://goshowimageswingwei.blob.core.windows.net/concert-images/arctic-monkeys.jpg",
        ),
        (
            "Nina Chuba - Farben Tour",
            "Nina Chuba",
            "Max-Schmeling-Halle, Berlin",
            "2026-12-05",
            49.50,
            100,
            "Nina Chuba brings the Farben Tour to Max-Schmeling-Halle with a German-language pop set full of bright hooks, rap-influenced phrasing, and playful stage energy. The show is a strong fit for fans looking for a current, radio-ready Berlin night with an enthusiastic crowd.",
            "https://goshowimageswingwei.blob.core.windows.net/concert-images/nina-chuba.jpg",
        ),
        (
            "AnnenMayKantereit - Sommerabend",
            "AnnenMayKantereit",
            "Parkbuhne Wuhlheide, Berlin",
            "2026-09-13",
            59.00,
            135,
            "AnnenMayKantereit close the month at Parkbuhne Wuhlheide with a warm German indie-rock show shaped by raspy lead vocals, direct songwriting, and big crowd singalongs. The outdoor setting suits the band's mix of intimate lyrics and festival-ready choruses.",
            "https://goshowimageswingwei.blob.core.windows.net/concert-images/annenmaykantereit.jpg",
        ),
    ]

    with get_connection() as connection:
        if connection.backend == "postgres":
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS concerts (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    artist TEXT NOT NULL,
                    venue TEXT NOT NULL,
                    concert_date TEXT NOT NULL,
                    price DOUBLE PRECISION NOT NULL,
                    seats_available INTEGER NOT NULL,
                    description TEXT NOT NULL,
                    image_url TEXT NOT NULL DEFAULT ''
                )
                """
            )

            connection.execute(
                """
                ALTER TABLE concerts
                ADD COLUMN IF NOT EXISTS image_url
                TEXT NOT NULL DEFAULT ''
                """
            )

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS bookings (
                    id SERIAL PRIMARY KEY,
                    concert_id INTEGER NOT NULL,
                    customer_name TEXT NOT NULL,
                    customer_email TEXT NOT NULL,
                    tickets INTEGER NOT NULL,
                    created_at TIMESTAMPTZ
                        NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (concert_id)
                        REFERENCES concerts (id)
                        ON DELETE CASCADE
                )
                """
            )
        else:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS concerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    artist TEXT NOT NULL,
                    venue TEXT NOT NULL,
                    concert_date TEXT NOT NULL,
                    price REAL NOT NULL,
                    seats_available INTEGER NOT NULL,
                    description TEXT NOT NULL,
                    image_url TEXT NOT NULL DEFAULT ''
                )
                """
            )

            columns = [
                row[1]
                for row in connection.execute(
                    "PRAGMA table_info(concerts)"
                ).fetchall()
            ]

            if "image_url" not in columns:
                connection.execute(
                    """
                    ALTER TABLE concerts
                    ADD COLUMN image_url TEXT NOT NULL DEFAULT ''
                    """
                )

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS bookings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    concert_id INTEGER NOT NULL,
                    customer_name TEXT NOT NULL,
                    customer_email TEXT NOT NULL,
                    tickets INTEGER NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (concert_id)
                        REFERENCES concerts (id)
                )
                """
            )

        count_row = connection.execute(
            "SELECT COUNT(*) AS total FROM concerts"
        ).fetchone()

        if isinstance(count_row, dict):
            concert_count = count_row["total"]
        else:
            concert_count = count_row[0]

        if concert_count == 0:
            connection.executemany(
                """
                INSERT INTO concerts
                (
                    title,
                    artist,
                    venue,
                    concert_date,
                    price,
                    seats_available,
                    description,
                    image_url
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                concerts,
            )

        connection.commit()


def row_to_dict(row):
    if not row:
        return None

    result = dict(row)

    for key, value in result.items():
        if isinstance(value, (date, datetime)):
            result[key] = value.isoformat()

    return result
