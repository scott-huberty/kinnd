from pathlib import Path
import sys

from kinnd.utils.check import check_directory

def lab_server_is_mounted(strict=True):
    """Check if the lab server is mounted/accessible on the users computer.

    Parameters
    ----------
    strict : bool
        If True, raise an error if the lab server is not mounted. If False, return
        False if the lab server is not mounted.

    Returns
    -------
    bool
        True is returned if the lab server is mounted. If strict is False and the
        lab server is not mounted, then False is returned. If strict is True and the
        lab server is not mounted, then a ``FileNotFoundError`` is raised.
    """
    if lab_server_path().exists():
        return True
    if strict:
            raise FileNotFoundError(f"Lab server not mounted at {lab_server_path()}")
    return False


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


def listen_path():
    """Return the path to the Listen data on the lab server."""
    return lab_server_path() / "LISTEN" / "Participant Files"


def get_eeg_fpaths(study="semantics", directory=None):
    """Get the EEG filepaths for the specified study, from the lab server.

    Parameters
    ----------
    study : str
        The name of the study to get the EEG filepaths. Currently only "semantics" is
        supported.
    directory : Path | str
        The absolute or relative filepath of the directory that contains the
        EEG files to load. If ``None``, then the code will attempt to read the files
        from the lab server.

    Returns
    -------
    list of Path
        A list of Path objects pointing to the EEG files for the specified study.
    """
    if study == "semantics":
        return list(directory.glob("*.set"))
    elif study == "listen":
        return list(directory.rglob("*.mff"))
    else:
        raise NotImplementedError(f"Study {study} not implemented yet.")

def get_semantics_fpaths(directory=None):
    """Get the EEG filepaths for the Semantics data, from the lab server.

    Parameters
    ----------
    directory : Path | str
        The absolute or relative filepath of the directory that contains the
        semantics epoched eeglab files (e.g. 1s17snma.set). If None, then the
        code willattempt to read the files from the lab server, from
        `charlotte_semantics_data/sem_esrp`.

    Returns
    -------
    dict of dict
        A dictionary of dictionaries, where the keys are the subject IDs and the
        values are dictionaries with keys 'match' and 'mismatch' that point to
        the file paths for the match and mismatch conditions, respectively.
    """
    from collections import defaultdict

    if directory is None:
        directory = semantics_path() / "sem_esrp"
    directory = check_directory(directory)

    fpaths = get_eeg_fpaths(study="semantics", directory=directory)
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


def get_listen_fpaths(directory=None):
    """Get the filepaths for Listen EEG data."""
    from collections import defaultdict

    if directory is None:
        directory = listen_path()
    directory = check_directory(directory)
    fpaths = get_eeg_fpaths(study="listen", directory=directory)
    subject_dict = defaultdict(dict)

    for fpath in fpaths:
        fname = fpath.name.lower()
        key = f"sub-{fname.split('_')[1]}"
        if "phonemes" in fname:
            subject_dict[key]["phonemes"] = fpath
        elif "resting" in fname:
            subject_dict[key]["resting"] = fpath
        elif "semantics" in fname:
            subject_dict[key]["semantics"] = fpath
        else:
            raise ValueError(
                f"File {fpath} does not match appear to belong to a Listen task."
                "Expected 'phonemes', 'resting', or 'semantics' in the filename."
                )
    return dict(subject_dict)


def unzip(fpath):
    """Unzip a zipped MFF file."""
    from shutil import unpack_archive

    target_dir = fpath.parent
    unpack_archive(fpath, target_dir)