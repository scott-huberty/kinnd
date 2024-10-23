"""Some semantics files have typo in the filename. This script renames them."""
import argparse

import sys

from pathlib import Path
from warnings import warn

import numpy as np
import pandas as pd

import kinnd
import mne
import mne_bids

# This script assumes that the lab server is mounted on a Mac.
lab_server_is_mounted = kinnd.utils.paths.lab_server_is_mounted(strict=True)

EVENT_IDS = {
            "BAD_ACQ_SKIP": 0,
            # Semantics
            "image_match": 1,
            "image_mismatch": 2,
            "word_match": 3,
            "word_mismatch": 4,
            "net": 5, # user defined?
            # Phonemes
            "tone_Standard": 10,
            "tone_Deviant": 11,
            # Resting
            "rest": 20,
            "Devt": 21,
            # Stimtracker events
            "DIN6": 56,
            "DIN8": 58,
            # EGI stuff
            "bgin": 60,
            "CELL": 61,
            "SESS": 62,
            "TRSP": 63,
            "isi+": 64,
            }

def bidsify_listen_files(task=None):
    """BIDS Sanitize the Listen EEG files."""
    broot = kinnd.utils.paths.listen_path().parent / "data" / "bids"
    fname = broot.parent / "eeg_list.csv"
    df = pd.read_csv(fname, header=0)

    for tup in df.itertuples():
        if pd.isnull(tup.task):
            warn(
                 f"Skipping {tup.subject}_ses-{tup.session:02d} because it has no task.",
                 stacklevel=2,
                 )
            continue
        if Path(tup.bidsfile).exists():
                    warn(
                         f"Skipping {tup.subject}_ses-{tup.session:02d} because it already exists.",
                         stacklevel=2,
                         )
                    continue
        if task is not None and task != tup.task:
            warn(
                 f"Skipping {tup.subject}_ses-{tup.session:02d}_{tup.task} because it is not {task}.",
                 stacklevel=2,)
            continue
        if task == "semantics":
            event_mapping = {"img+": "image", "snd+": "word"}
        elif task == "phonemes":
            event_mapping = {"stm+": "tone"}
        else:
            event_mapping = None
        raw = kinnd.studies.listen.io.read_raw_listen(
            tup.sourcefile, event_mapping=event_mapping
            )

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