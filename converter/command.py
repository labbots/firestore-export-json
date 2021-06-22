import argparse
import json
import os
import sys
from functools import partial
from multiprocessing import Pool, cpu_count, Value
from pathlib import Path
from typing import Dict
from threading import Lock

from google.appengine.api import datastore
from google.appengine.api.datastore_types import EmbeddedEntity
from google.appengine.datastore import entity_bytes_pb2 as entity_pb2

from converter import records
from converter.exceptions import BaseError, ValidationError
from converter.utils import embedded_entity_to_dict, get_dest_dict, serialize_json

num_files: Value = Value("i", 0)
num_files_processed: Value = Value("i", 0)

def main(args=None):
    if args is None:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser(
        prog="fs_to_json", description="Firestore DB export to JSON"
    )

    parser.add_argument(
        "source_dir",
        help="Destination directory to store generated JSON",
        type=str,
        action="store",
        default=None,
    )

    parser.add_argument(
        "dest_dir",
        help="Destination directory to store generated JSON",
        type=str,
        action="store",
        default=None,
    )

    parser.add_argument(
        "-P",
        "--processes",
        help=f"Number of processes to use to process the files. Defaults to {cpu_count() - 1}",
        default=cpu_count() - 1,
        type=int,
    )

    parser.add_argument(
        "-C",
        "--clean-dest",
        help="Remove all json files from output dir",
        default=False,
        action="store_true",
    )

    parser.add_argument(
        "-c",
        "--no-check-crc",
        help="Turn off the check/computation of CRC values for the records."
        "This will increase performance at the cost of potentially having corrupt data,"
        "mostly on systems without accelerated crc32c.",
        default=False,
        action="store_true",
    )

    args = parser.parse_args(args)
    try:
        source_dir = os.path.abspath(args.source_dir)
        if not os.path.isdir(source_dir):
            raise ValidationError("Source directory does not exist.")
        if not args.dest_dir:
            dest_dir = os.path.join(source_dir, "json")
        else:
            dest_dir = os.path.abspath(args.dest_dir)

        Path(dest_dir).mkdir(parents=True, exist_ok=True)

        if os.listdir(dest_dir) and args.clean_dest:
            print("Destination directory is not empty. Deleting json files...")
            for f in Path(dest_dir).glob("*.json"):
                try:
                    print(f"Deleting file {f.name}")
                    f.unlink()
                except OSError as e:
                    print("Error: %s : %s" % (f, e.strerror))

        process_files(
            source_dir=source_dir,
            dest_dir=dest_dir,
            num_processes=args.processes,
            no_check_crc=args.no_check_crc,
        )
    except BaseError as e:
        print(str(e))
        sys.exit(1)


def process_files(
    source_dir: str, dest_dir: str, num_processes: int, no_check_crc: bool
):
    p = Pool(num_processes)
    files = sorted(os.listdir(source_dir))
    num_files.value = len(files)
    print(f"processing {num_files.value} file(s)")


    f = partial(process_file, source_dir, dest_dir, no_check_crc)
    p.map(f, files)
    print(f"processed: {num_files_processed.value}/{num_files.value} {num_files_processed.value/num_files.value*100}%")


def process_file(source_dir: str, dest_dir: str, no_check_crc: bool, filename: str):
    if not filename.startswith("output-"):
        return
    json_tree: Dict = {}
    in_file = os.path.join(source_dir, filename)

    with open(in_file, "rb") as raw:
        reader = records.RecordsReader(raw, no_check_crc=no_check_crc)
        for record in reader:
            entity_proto = entity_pb2.EntityProto()
            entity_proto.ParseFromString(record)
            ds_entity = datastore.Entity.FromPb(entity_proto)
            data = {}
            for name, value in list(ds_entity.items()):
                if isinstance(value, EmbeddedEntity):
                    dt: Dict = {}
                    data[name] = embedded_entity_to_dict(value, dt)
                else:
                    data[name] = value

            data_dict = get_dest_dict(ds_entity.key(), json_tree)
            data_dict.update(data)

    out_file_path = os.path.join(dest_dir, filename + ".json")
    with open(out_file_path, "w", encoding="utf8") as out:
        out.write(
            json.dumps(json_tree, default=serialize_json, ensure_ascii=False, indent=2)
        )
    num_files_processed.value += 1
    print(f"progress: {num_files_processed.value}/{num_files.value} {num_files_processed.value/num_files.value*100}%")


if __name__ == "__main__":
    main()
