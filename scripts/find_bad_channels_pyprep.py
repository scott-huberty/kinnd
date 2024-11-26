import argparse

import os
import time

from datetime import datetime
from pathlib import Path
from warnings import warn

import pandas as pd

import mne
import mne_bids

import kinnd

import pyprep

import logging

from create_listen_bids import EVENT_IDS


def process_one_subject(bpath, overwrite):
    """Process a single subject from the Listen study."""
    subject = bpath.subject
    session = bpath.session
    task = bpath.task
    broot = bpath.root

    if (broot.parent / "mne-bids-pipeline" / f"sub-{subject}").exists():
        return
    dpath = mne_bids.BIDSPath(
        subject=subject,
        session=session,
        task=task,
        suffix="eeg",
        datatype="eeg",
        root=broot.parent / "mne-bids-pipeline",
    )


    # instantiate logger
    logger = mne.utils.logger

    console_handler = logging.StreamHandler()
    log_fpath = str(Path(__file__).parent / f"./logs/find_bad_channels_pyprep/sub-{subject}_ses-{session}_task-{task}.txt")
    file_handler = logging.FileHandler(log_fpath, mode="a", encoding="utf-8")
    formatter = logging.Formatter(
        "{asctime} - {levelname} - {message}",
        style="{",
        datefmt="%Y-%m-%d %H:%M",
    )
    console_handler.setFormatter(formatter)
    console_handler.setLevel("DEBUG")
    file_handler.setFormatter(formatter)
    file_handler.setLevel("DEBUG")
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)


    # If script makes it to this point. We are processing
    logger.info(f"Processing sub-{subject}_ses-{session}_task-{task}")

    raw = mne_bids.read_raw_bids(bpath)
    raw.info["bads"].extend(["E125", "E126", "E127", "E128"])

    # Find Breaks
    break_annots = mne.preprocessing.annotate_break(raw)
    raw.set_annotations(raw.annotations + break_annots)

    # PyPrep
    all_bads = []
    for _ in range(3):
        nc = pyprep.NoisyChannels(raw=raw, random_state=42)
        nc.find_bad_by_deviation()
        nc.find_bad_by_correlation()
        nc.find_bad_by_ransac()

        bads = nc.get_bads()
        all_bads.extend(bads)
        all_bads = sorted(all_bads)
        raw.info["bads"] = all_bads

    mne_bids.write_raw_bids(
        raw=raw,
        bids_path=dpath,
        event_id=EVENT_IDS,
        allow_preload=True,
        format="EDF",
    )
    return True


def process_dataset(broot, task=None, overwrite=False):
    csv_fpath = broot.parent / "eeg_list.csv"
    df = pd.read_csv(csv_fpath, header=0)

    for tup in df.itertuples():
        subject = str(tup.subject)
        session = f"{tup.session:02d}"
        if tup.task != task:
            warn(f"SKIPPING: sub-{subject}_ses-{session}_task-{tup.task} because only the {task} task was requested")
            continue
        bpath = mne_bids.BIDSPath(subject=subject, session=session, task=tup.task, root=broot)
        process_one_subject(bpath, overwrite=overwrite)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--subject", dest="subject", type=str, default=None)
    parser.add_argument("--session", dest="session", type=str, default=None)
    parser.add_argument(
        "--task",
        dest="task",
        type=str,
        default=None,
        choices=["semantics", "phonemes", "resting"]
        )
    parser.add_argument("--bids_root", dest="bids_root", type=Path, default=None)
    parser.add_argument(
        "--overwrite",
          dest="overwrite",
          type=bool,
          choices=[True, False],
          default=False
          )
    args = parser.parse_args()

    # MNE-BIDS
    broot = args.bids_root
    if broot is None:
        broot = kinnd.paths.get_listen_path() / "data" / "bids"
    broot = Path(broot).expanduser().resolve()

    subject = args.subject
    if subject is None:
        process_dataset(broot, task=args.task, overwrite=args.overwrite)
    else:
        subject = f"{args.subject}"
        session = args.session.zfill(2)
        task = f"{args.task}"
        bpath = mne_bids.BIDSPath(subject=subject, session=session, task=task, root=broot)
        process_one_subject(bpath, overwrite=args.overwrite)
