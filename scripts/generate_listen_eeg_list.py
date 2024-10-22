import re
from pathlib import Path
import pandas as pd

# Assumes that you are mounted to the lab server and on a Mac
fpath = Path("/Volumes/neurology_share/LISTEN/Participant Files")
if not fpath.exists():
    raise FileNotFoundError(
        f"{fpath} does not exist. Are you sure you are mounted to the lab server?")

# Get all the files in the directory
files = list(fpath.rglob("*.mff"))
df = pd.DataFrame(files, columns=["sourcefile"])

# Extract the participant number
df["subject"] = df["sourcefile"].apply(
    lambda x: re.search(r"20\d{2}", str(x)).group(0)
    )

df["session"] = None
df["task"] = None
for tup in df.itertuples():
    fname = str(tup.sourcefile).lower()
    if "resting" in fname:
        df.at[tup.Index, "task"] = "resting"
    elif \
        "semantics" in fname or \
        "sematics" in fname or \
        "sematincs" in fname:
            df.at[tup.Index, "task"] = "semantics"
    elif "phonemes" in fname:
        df.at[tup.Index, "task"] = "phonemes"
    elif "auditoryoddbal" in fname:
        df.at[tup.Index, "task"] = "auditoryoddball"

    # Session
    if "day 2" in fname or "_2_" in fname:
        df.at[tup.Index, "session"] = "02"
    elif tup.subject == "2023" and "20231115" in fname:
        df.at[tup.Index, "session"] = "02"
    else:
        df.at[tup.Index, "session"] = "01"

df = df.sort_values(["subject", "session", "task"])
df.to_csv(fpath.parent / "data" / "eeg_list.csv", index=False)