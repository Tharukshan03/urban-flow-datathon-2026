"""Member 3 Phase 1: validate the official handover using metadata only.

Run from the repository root: python verify_member1.py
No trip records are read and no Member 1 files are modified.
"""

from pathlib import Path
import sys

import pyarrow as pa
import pyarrow.parquet as pq


def main():
    path = Path("data/processed/clean_trips.parquet")
    if not path.is_file():
        print(f"Validation: FAILED - missing {path.as_posix()}")
        return 1
    try:
        metadata = pq.read_metadata(path)
        schema = metadata.schema.to_arrow_schema()
    except Exception as exc:
        print(f"Validation: FAILED - cannot open Parquet metadata: {exc}")
        return 1

    print(f"Source: {path.as_posix()}")
    print("Parquet metadata opened successfully")
    print(f"Rows: {metadata.num_rows:,}")
    print(f"Columns: {metadata.num_columns}")
    print(f"Row groups: {metadata.num_row_groups}")
    print("Complete column list:")
    for index, field in enumerate(schema, start=1):
        print(f"  {index:2}. {field.name}: {field.type}")
    print("Location-related columns (origin/dest/zone/borough/loc):")
    for name in schema.names:
        if any(term in name.lower() for term in ("origin", "dest", "zone", "borough", "loc")):
            print(f"  {name}")

    errors = []
    if metadata.num_rows != 45_533_334:
        errors.append(f"Expected 45,533,334 rows; found {metadata.num_rows:,}")
    if metadata.num_columns != 45 or len(schema) != 45:
        errors.append(f"Expected 45 columns; found {metadata.num_columns} physical / {len(schema)} Arrow")
    fields = {
        "Pickup zone": "pickup_zone_name",
        "Dropoff zone": "dropoff_zone_name",
        "Pickup borough": "pickup_borough_name",
        "Dropoff borough": "dropoff_borough_name",
        "Timestamp": "pickup_timestamp",
    }
    for label, name in fields.items():
        print(f"{label}: {name}")
        if name not in schema.names:
            errors.append(f"Missing documented field: {name}")
            continue
        dtype = schema.field(name).type
        if name == "pickup_timestamp":
            print(f"Timestamp storage type: {dtype}")
            if not pa.types.is_timestamp(dtype):
                print("Note: timestamp parsing must be validated before analysis; metadata cannot verify values.")
        elif not (pa.types.is_string(dtype) or pa.types.is_large_string(dtype)):
            errors.append(f"Expected readable string type for {name}; found {dtype}")

    print("Scope: schema/metadata only; label values and chronological ordering are not scanned.")
    if errors:
        print("Validation: FAILED")
        for error in errors:
            print(f"  {error}")
        return 1
    print("Validation: PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
