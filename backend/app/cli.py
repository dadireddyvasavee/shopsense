"""Management commands.

python -m app.cli seed                     # load data/demo_catalog.json (upsert by SKU)
python -m app.cli ingest path/to/file.json # ingest your own catalog
python -m app.cli make-admin user@x.com    # grant admin role (enables POST /api/catalog/ingest)
"""
import json
import sys

from sqlalchemy import select

from app.core.db import SessionLocal
from app.models import User
from app.services import catalog


def main(argv: list[str]) -> None:
    cmd = argv[0] if argv else "help"
    with SessionLocal() as db:
        if cmd == "seed":
            print(catalog.ingest(db, json.loads(catalog.DEMO_FILE.read_text()), source="demo"))
        elif cmd == "ingest" and len(argv) > 1:
            print(catalog.ingest(db, json.loads(open(argv[1], encoding="utf-8").read()), source="import"))
        elif cmd == "make-admin" and len(argv) > 1:
            u = db.scalar(select(User).where(User.email == argv[1].lower()))
            if not u:
                sys.exit("user not found")
            u.role = "admin"
            db.commit()
            print(f"{u.email} is now admin")
        else:
            print(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
