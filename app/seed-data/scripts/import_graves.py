# app\seed-data\scripts\import_graves.py
"""
One-time import script: loads the burial register Excel file
(3 sheets: Table 1, Table 2, Table 3 - one continuous ledger split
across sheets) into the `graves` table in Supabase.

WHERE TO PUT THIS FILE
-----------------------
This script auto-detects your project root by walking up from its own
location until it finds a folder containing `app/db/connection.py` -
so it works no matter how deep it's nested (scripts/, app/seed-data/
scripts/, etc.). Just make sure it's placed *somewhere inside* the
backend project that contains the `app` package.

Put the Excel file in the SAME folder as this script, or edit
EXCEL_PATH below to point elsewhere.

Run it with the path to wherever you placed it, e.g.:

    uv run app/seed-data/scripts/import_graves.py

(run from the backend project root, i.e. the folder one level above `app/`)

REQUIREMENTS
------------
Your FastAPI app already needs sqlmodel + a postgres driver (psycopg2
or psycopg) since it talks to Supabase. This script additionally needs
pandas + openpyxl to read the Excel file:

    pip install pandas openpyxl

WHAT IT DOES
------------
1. Reads all 3 sheets (Table 2 and Table 3 have no header row in the
   source file, and Table 3 has 23 blank trailing rows - both handled
   below).
2. Combines them into one dataframe: Qaber No, Date Buried,
   Name of Deceased, Village, Surname.
3. Maps -> Grave(old_grave_id, date_buried, deceased_name,
   deceased_surname, native_place). `grave_id` (the new numbering
   system) is intentionally left NULL for every row - the Excel
   Qaber No now goes into `old_grave_id` instead, per your instruction.
4. Checks which (old_grave_id, deceased_name, date_buried) combos
   already exist in your `graves` table and skips those, so re-running
   this script after a partial failure is safe. NOTE: this is just a
   crash-recovery safety net, not a uniqueness rule - old_grave_id is
   intentionally allowed to repeat (multiple burials in one grave over
   the years), so this check will never block a legitimate re-burial
   record from importing.
5. Inserts in batches, with a DRY_RUN mode to preview first.

DATA NOTES
-----------
- Qaber No 2167 appears twice in the source file for two different
  people (Osman Ebranim Monamed, buried 2021-11-22, and Salma Bibi
  Abdul Qadir, buried 2023-05-25). Both import fine as separate rows
  with old_grave_id="2167" - no uniqueness constraint blocks this,
  which matches how multiple burials can share one physical grave.
- 17 rows have no Surname in the sheet -> deceased_surname stays NULL
  for those.
- Before running this: deceased_name and deceased_surname must be wide
  enough columns (varchar(255) recommended) - see chat history for the
  ALTER TABLE statements already run for this.
"""

import sys
from pathlib import Path

import pandas as pd
from sqlmodel import Session, select


def find_project_root(start: Path) -> Path:
    """Walk upwards from `start` until a folder containing app/db/connection.py
    is found. This makes the script work no matter how deeply it's nested
    (scripts/, app/seed-data/scripts/, etc.) without editing paths by hand."""
    current = start.resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "app" / "db" / "connection.py").exists():
            return candidate
    raise RuntimeError(
        f"Could not find a folder containing 'app/db/connection.py' by walking "
        f"up from {start}. Make sure this script sits somewhere inside your "
        f"backend project (the one containing the 'app' package)."
    )


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = find_project_root(SCRIPT_DIR)
sys.path.insert(0, str(PROJECT_ROOT))

from app.db.connection import engine          # noqa: E402
from app.models.grave_model import Grave       # noqa: E402


# ======================= CONFIG =======================
# Defaults to the Excel file sitting right next to this script.
# Change this if you put the .xlsx somewhere else.
EXCEL_PATH = SCRIPT_DIR.parent / "data" / "All_2_0__1966_-_Feb_2024_with_surname.xlsx"
DRY_RUN = False     # set to False once the preview looks right
BATCH_SIZE = 200
# ========================================================


def load_and_combine(path: str) -> pd.DataFrame:
    """Read all 3 sheets and combine into one clean dataframe."""

    # Table 1: has a real header row, 5 columns
    df1 = pd.read_excel(path, sheet_name="Table 1")
    df1.columns = ["Qaber No", "Date Buried", "Name of Deceased", "Village", "Surname"]

    # Table 2: NO header row, NO Village column, 4 columns
    df2 = pd.read_excel(path, sheet_name="Table 2", header=None)
    df2.columns = ["Qaber No", "Date Buried", "Name of Deceased", "Surname"]
    df2["Village"] = None

    # Table 3: NO header row, 6 columns - the 5th column (index 4) is always
    # empty in the source file, so it's dropped. Has 23 fully blank trailing
    # rows that need dropping too.
    df3 = pd.read_excel(path, sheet_name="Table 3", header=None)
    df3.columns = ["Qaber No", "Date Buried", "Name of Deceased", "Village", "_blank", "Surname"]
    df3 = df3.drop(columns=["_blank"])
    df3 = df3.dropna(subset=["Qaber No"])

    combined = pd.concat([df1, df2, df3], ignore_index=True)
    combined["Qaber No"] = combined["Qaber No"].astype(int)

    return combined


def to_grave_rows(df: pd.DataFrame) -> list[Grave]:
    graves = []
    for row in df.itertuples(index=False, name=None):
        qaber_no, date_buried, deceased_name, village, surname = row
        graves.append(
            Grave(
                grave_id=None,  # new numbering system - not populated from Excel
                old_grave_id=str(int(qaber_no)),
                date_buried=date_buried.date() if pd.notna(date_buried) else None,
                deceased_name=str(deceased_name).strip(),
                deceased_surname=(
                    str(surname).strip()
                    if pd.notna(surname) and str(surname).strip()
                    else None
                ),
                native_place=(
                    str(village).strip()
                    if pd.notna(village) and str(village).strip()
                    else None
                ),
            )
        )
    return graves


def main():
    print(f"Reading {EXCEL_PATH} ...")
    df = load_and_combine(EXCEL_PATH)
    print(f"Combined rows: {len(df)}")

    dupes = df[df.duplicated(subset=["Qaber No"], keep=False)]
    if len(dupes):
        print(f"\nNote: {len(dupes)} rows share a duplicate Qaber No "
              f"(expected - multiple burials can share one grave):")
        print(dupes.sort_values("Qaber No").to_string(index=False))
        print()

    with Session(engine) as session:
        existing = set(
            session.exec(
                select(Grave.old_grave_id, Grave.deceased_name, Grave.date_buried)
            ).all()
        )
        print(f"Existing (old_grave_id, name, date_buried) combos already in DB: {len(existing)}")

        def already_imported(row) -> bool:
            qaber_no, date_buried, deceased_name, village, surname = row
            key = (
                str(int(qaber_no)),
                str(deceased_name).strip(),
                date_buried.date() if pd.notna(date_buried) else None,
            )
            return key in existing

        mask = df.apply(lambda r: already_imported(tuple(r)), axis=1)
        df_to_import = df[~mask]
        skipped = len(df) - len(df_to_import)
        if skipped:
            print(f"Skipping {skipped} rows that exactly match a record already in the DB.")

        rows = to_grave_rows(df_to_import)
        print(f"\nRows to insert: {len(rows)}")

        if not rows:
            print("Nothing new to insert. Done.")
            return

        print("\nSample of first 3 rows that would be inserted:")
        for g in rows[:3]:
            print(f"  old_grave_id={g.old_grave_id!r} date_buried={g.date_buried} "
                  f"deceased_name={g.deceased_name!r} deceased_surname={g.deceased_surname!r} "
                  f"native_place={g.native_place!r}")

        if DRY_RUN:
            print("\nDRY_RUN is True — nothing was written to the database.")
            print("Review the output above, then set DRY_RUN = False and re-run.")
            return

        inserted = 0
        for i in range(0, len(rows), BATCH_SIZE):
            batch = rows[i:i + BATCH_SIZE]
            session.add_all(batch)
            session.commit()
            inserted += len(batch)
            print(f"  committed {inserted}/{len(rows)}")

        print(f"\n✅ Done. Inserted {inserted} grave records.")


if __name__ == "__main__":
    main()
