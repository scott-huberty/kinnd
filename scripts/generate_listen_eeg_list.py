import re
import sys

from warnings import warn
from pathlib import Path
import pandas as pd

# Assumes that you are mounted to the lab server and on a Mac
if sys.platform != "darwin":
    raise OSError("Currently, This script is only supported on macOS.")
fpath = Path("/Volumes/neurology_share/LISTEN/Participant Files")
if not fpath.exists():
    raise FileNotFoundError(
        f"{fpath} does not exist. Are you sure you are mounted to the lab server?")

# Get all the files in the directory
files = list(fpath.rglob("*.mff"))
df = pd.DataFrame(files, columns=["sourcefile"])
idxs_to_drop = []
# Sanitize the data
for tup in df.itertuples():
    if tup.sourcefile.name.startswith("._"):  # Hidden files
        idxs_to_drop.append(tup.Index)
df = df.drop(idxs_to_drop)

# Extract the participant number
df["subject"] = df["sourcefile"].apply(
    lambda x: re.search(r"20\d{2}", str(x)).group(0)
    )

df["session"] = None
df["task"] = None
df["bidsfile"] = None
for tup in df.itertuples():
    # Initialize Variables
    session = None
    task = None
    fname = str(tup.sourcefile).lower()
    if "resting" in fname:
        task = "resting"
    elif \
        "semantics" in fname or \
        "sematics" in fname or \
        "sematincs" in fname:
            task = "semantics"
    elif "phonemes" in fname or "auditoryoddball" in fname:
        task = "phonemes"
    else:
         warn(f"Could not determine task for {tup.sourcefile}", UserWarning)
    if task is not None:
        df.at[tup.Index, "task"] = task

    # Session
    if "day 2" in fname or "_2_" in fname:
        session = "02"
    elif tup.subject == "2023" and "20231115" in fname:
        session = "02"
    else:
        session = "01"
    df.at[tup.Index, "session"] = session

    if task is not None:
        bpath = f"sub-{tup.subject}_ses-{session}_task-{task}_eeg.edf"
        basepath = Path(f"/Volumes/neurology_share/LISTEN/data/bids/sub-{tup.subject}/ses-{session}/eeg")
        df.at[tup.Index, "bidsfile"] = basepath / bpath

df = df.sort_values(["subject", "session", "task"])
df.to_csv(fpath.parent / "data" / "eeg_list.csv", index=False)