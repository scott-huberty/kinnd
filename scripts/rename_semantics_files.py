"""Some semantics files have typo in the filename. This script renames them."""
from pathlib import Path

import shutil
from warnings import warn

import kinnd
import mne
import mne_bids
import mne_bids.write

lab_server_is_mounted = kinnd.utils.paths.lab_server_is_mounted(strict=False)

EVENT_IDS = {
            "BAD_ACQ_SKIP": 0,
            "stm+": 1,
            "img+": 2,
            "snd+": 3,
            "rest": 4,
            "Devt": 5,
            "net": 6,
            "DIN8": 7,
            "bgin": 8,
            "CELL": 9,
            "SESS": 10,
            "TRSP": 11,
            "IEND": 12,
            }

SKIP_FILES = [
    "2001",
    "2002", # Could not determine task
    "2003",
    "2005", # Could not determine task
    "2006", # Could not determine task
    "2013",
    "2014",
    "2015",
    "2019",
    "2021",
    "2022",
    "2023",
    "2024",
    "2025",
    "2037",
    "2044",
    "2068",
    "2017",
    "2018",
    "2016",
    "2045",
    "2046",
    ]

def bidsify_listen_files():
    """Rename the Semantics files with typos in the filename."""
    if not lab_server_is_mounted:
        raise FileNotFoundError("Lab server not mounted.")
    listen_path = kinnd.utils.paths.listen_path()
    subject_dirs = list(listen_path.glob("2???"))

    for sub_dir in subject_dirs:
        if sub_dir.name in SKIP_FILES:
            continue

        eeg_dirs = [d for d in sub_dir.glob("*EEG*/") if d.is_dir()]
        if len(eeg_dirs) == 0:
            warn(f"No EEG directories found in {sub_dir}.")
            continue
        elif len(eeg_dirs) > 1:
            warn(f"Multiple EEG directories found in {sub_dir}: {eeg_dirs}.")

        if list(eeg_dirs[0].glob("Day 1")):
            warn(f"Multiple Days found in {sub_dir}.")
            eeg_dirs = [d for d in eeg_dirs[0].glob("Day*") if d.is_dir()]

        if len(eeg_dirs) == 0:
            warn(f"No EEG directories found in {sub_dir}.")
            continue
        elif len(eeg_dirs) > 1:
            warn(f"Multiple EEG directories found in {sub_dir}: {eeg_dirs}.")

        for di, eeg_dir in enumerate(eeg_dirs):
            for cache_dir in list(eeg_dir.rglob("__MACOSX/")):
                print(f"Removing __MACOSX: {cache_dir}.")
                shutil.rmtree(cache_dir)
            files = list(eeg_dir.rglob("*.mff"))
            assert not any(["__MACOSX" in f.name for f in files])

            session = f"{di+1:02d}"
            for this_file in files:
                raw = mne.io.read_raw_egi(this_file, events_as_annotations=True)
                subject = sub_dir.name
                cond_sem = "sematics" in this_file.name.lower() or "semantics" in this_file.name.lower()
                cond_phoneme = "phoneme" in this_file.name.lower()
                cond_rest = "resting" in this_file.name.lower()
                if cond_sem:
                    task = "semantics"
                elif cond_phoneme:
                    task = "phoneme"
                elif cond_rest:
                    task = "resting"
                else:
                    raise ValueError(f"Could not determine task for {this_file}.")
                bpath = mne_bids.BIDSPath(
                    subject=subject,
                    session=session,
                    task=task,
                    root=listen_path.parent / "data" / "bids",
                    )
                bpath.update(suffix="eeg", extension=".fif")
                mne_bids.write.write_raw_bids(
                    raw=raw,
                    bids_path=bpath,
                    overwrite=False,
                    event_id=EVENT_IDS,
                    )

if __name__ == "__main__":
    bidsify_listen_files()