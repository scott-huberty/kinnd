from pathlib import Path
import sys


def lab_server_is_mounted():
    """Check if the lab server is mounted/accessible on the users computer."""
    if lab_server_path().exists():
        return True
    else:
        raise FileNotFoundError(f"Lab server not mounted at {lab_server_path}")

def lab_server_path():
    """Return the path to the lab server."""
    if sys.platform == "darwin":
        return Path("/Volumes") / "neurology_share"
    elif sys.platform == "linux":
        raise NotImplementedError(
            "Accessing the lab server from Linux is not yet implemented."
            )
    elif sys.platform == "win32":
        raise NotImplementedError(
            "Accessing the lab server from Windows is not yet implemented."
            )
    else:
        raise OSError(f"Unknown operating system: {sys.platform}")


def semantics_path():
    """Return the path to the Semantics data on the lab server."""
    return lab_server_path() / "charlotte_semantics_data"

def get_eeg_fpaths(study="semantics"):
    """Get the EEG filepaths for the specified study, from the lab server.

    Parameters
    ----------
    study : str
        The name of the study to get the EEG filepaths. Currently only "semantics" is supported.

    Returns
    -------
    list of Path
        A list of Path objects pointing to the EEG files for the specified study.
    """
    if study == "semantics":
        return list( (semantics_path() / "sem_esrp").glob("*.set") )
    else:
        raise NotImplementedError(f"Study {study} not implemented yet.")

def get_semantics_fpaths():
    """Get the EEG filepaths for the Semantics data, from the lab server.

    Returns
    -------
    dict of dict
        A dictionary of dictionaries, where the keys are the subject IDs and the
        values are dictionaries with keys 'match' and 'mismatch' that point to
        the file paths for the match and mismatch conditions, respectively.
    """
    from collections import defaultdict

    fpaths = get_eeg_fpaths(study="semantics")
    subject_dict = defaultdict(dict)

    # Iterate through the file paths
    for fpath in fpaths:
        # Extract the filename
        fname = fpath.name
        # Extract the key part before the "S"
        key = f"sub-{fname.split('s')[0].zfill(2)}"
        # Determine if the file is a match or mismatch
        if 'SnMa' in fname:
            subject_dict[key]['match'] = fpath
        elif 'SnMi' in fname:
            subject_dict[key]['mismatch'] = fpath

    # Convert defaultdict to a regular dict for easier viewing
    subject_dict = dict(subject_dict)
    return subject_dict
