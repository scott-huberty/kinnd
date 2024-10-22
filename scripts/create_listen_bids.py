"""Some semantics files have typo in the filename. This script renames them."""
import argparse

from pathlib import Path
from warnings import warn

import numpy as np
import pandas as pd

import kinnd
import mne
import mne_bids

lab_server_is_mounted = kinnd.utils.paths.lab_server_is_mounted(strict=False)

EVENT_IDS = {
            "BAD_ACQ_SKIP": 0,
            # Semantics
            "image_match": 1,
            "image_mismatch": 2,
            "word_match": 3,
            "word_mismatch": 4,
            "net": 5, # user defined?
            # Stimtracker events
            "DIN6": 56,
            "DIN8": 58,
            # EGI stuff
            "bgin": 60,
            "CELL": 61,
            "SESS": 62,
            "TRSP": 63,
            }

SKIP_FILES = list((kinnd.utils.paths.listen_path().parent / "data" / "bids").glob("sub-*"))
SKIP_FILES = [f.name for f in SKIP_FILES]

def bidsify_listen_files(task=None):
    """Rename the Semantics files with typos in the filename."""
    if not lab_server_is_mounted:
        raise FileNotFoundError("Lab server not mounted.")
    broot = kinnd.utils.paths.listen_path().parent / "data" / "bids"
    fname = broot.parent / "eeg_list.csv"
    df = pd.read_csv(fname, header=0)

    for tup in df.itertuples():
        if f"sub-{tup.subject}" in SKIP_FILES:
            continue
        if pd.isnull(tup.task):
            warn(f"Skipping {tup.subject}_ses-{tup.session:02d} because it has no task.")
            continue
        if task != tup.task:
            continue
        raw = kinnd.studies.listen.io.read_raw_listen(tup.sourcefile)

        subject = str(tup.subject)
        session = f"{tup.session:02d}"

        bpath = mne_bids.BIDSPath(
            subject=subject,
            session=session,
            task=tup.task,
            suffix="eeg",
            datatype="eeg",
            root=broot,
            )

        mne_bids.write.write_raw_bids(
            raw=raw,
            bids_path=bpath,
            overwrite=False,
            event_id=EVENT_IDS,
            allow_preload=True,
            format="EDF",
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", default=None, type=str)
    args = parser.parse_args()
    bidsify_listen_files(task=args.task)