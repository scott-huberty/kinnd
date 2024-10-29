import pytz
import datetime

import mne

from pathlib import Path


def get_cel_map(events_eci):
    """Return a dictionary mapping from CEL codes to human readable conditions.

    For example for the semantics task, this should return a dictionary like:
    {"1": "match", "2": "mismatch"}. For the phonemes task, this should return
    {"1": "Standard", "2": "Deviant"}.
    """
    at_cell_events = False
    cel_map = {}
    for event in events_eci:
        if at_cell_events and event["code"] != "CELL":
            return cel_map
        if event["code"] == "CELL":
            at_cell_events = True
        if at_cell_events:
            cel_map[int(event["keys"]["cel#"])] = event["label"]
    return cel_map


def read_raw_listen(filename, event_mapping=None, condition_mapping=None):
    """Read an MFF file from the Listen study into MNE-Python.

    Parameters
    ----------
    filename : str or Path
        The path to the MFF file.
    event_mapping : dict
        A custom mapping of event codes to human readable descriptions. If None, no
        mapping is done, and the event codes themselves used as the `mne.Annotations`
        descriptions. For example, for the semantics task, you might use
        `{"img+": "image", "snd+": "word"}`.
    condition_mapping : dict
        A custom mapping of CEL codes to human readable condition labels. If ``None``,
        This function will try to extrac the mapping from the CEL codes at the
        beginning of the ``'EVENTS_ECI[...].xml'`` file. If this fails, you should
        provide a mapping here. For example, for the semantics task, you would pass
        ``{"1": "match", "2": "mismatch"}``. For the phonemes task, you would pass
        ``{"1": "Standard", "2": "Deviant"}``.

    Returns
    -------
    raw : mne.io.Raw
        The EEG data as an MNE-Python `~mne.io.Raw` object.

    Notes
    -----
    This function is for reading EGI source files from the Listen study, so that they
    can be BIDS standardized. It is not intended for analyses. Instead, use
    ``kinnd.io.read_raw_bids`` for that purpose.
    """
    import mffpy

    filename = Path(filename)

    mff_reader = mffpy.Reader(filename)
    mff_reader.set_unit("EEG", "V")

    # Basic Information
    meas_date = mff_reader.startdatetime
    meas_date = meas_date.replace(tzinfo=pytz.timezone("US/Pacific"))
    meas_date = meas_date.astimezone(pytz.utc)
    meas_date = meas_date.replace(tzinfo=datetime.timezone.utc)

    sfreq = mff_reader.sampling_rates["EEG"]

    # Montage
    with mff_reader.directory.filepointer("info1") as fp:
        info = mffpy.XML.from_file(fp)
    montage_map = {"HydroCel GSN 128 1.0": "GSN-HydroCel-129",}
    mon = info.generalInformation["montageName"]
    montage = mne.channels.make_standard_montage(montage_map[mon])

    # samples
    eeg, _ = mff_reader.get_physical_samples()["EEG"]

    # Events
    events_xmls = list(filename.glob("Events*.xml"))
    events_xmls = [fname.name for fname in events_xmls]
    if not events_xmls:
        raise RuntimeError(f"No events found in {filename}")

    categories_dict = {}
    for event_file in events_xmls:
        categories = mffpy.XML.from_file(filename / event_file)
        categories_dict[event_file] = categories.get_content()["event"]

    # Create MNE Objects
    ch_names = montage.ch_names
    ch_types = ["eeg"] * len(ch_names)
    info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types=ch_types)
    info.set_montage(montage)
    info.set_meas_date(meas_date)
    raw = mne.io.RawArray(eeg, info)

    # Annotations
    if condition_mapping is None:
        event_eci = [k for k in categories_dict.keys() if "ECI" in k]
        assert len(event_eci) == 1
        event_eci = categories_dict[event_eci[0]]
        condition_mapping = get_cel_map(event_eci)

    onsets = []
    durations = []
    descriptions = []
    for events in categories_dict.values():
        for event in events:
            onset = event["beginTime"].replace(tzinfo=pytz.timezone("US/Pacific"))
            onset = onset.astimezone(pytz.utc).replace(tzinfo=datetime.timezone.utc)
            ts = (onset - raw.info["meas_date"]).total_seconds()
            duration = event["duration"] / 1000
            if event["code"] in ["bgin", "TRSP", "SESS", "CELL", "Isi+"]:
                # Skip these events to keep the annotations clean
                # Isi+ is weird because the onset is outside the recording. Corrupted?
                continue
            elif event_mapping is not None and event["code"] in event_mapping:
                condition = condition_mapping[int(event["keys"]["cel#"])]
                description = f"{event_mapping[event['code']]}_{condition}"
            else:
                description = event["code"]
            onsets.append(ts)
            durations.append(duration)
            descriptions.append(description)
    raw.set_annotations(mne.Annotations(onsets, durations, descriptions))
    return raw


def read_processed_listen(subject, task, session=1, listen_fpath=None):
    """Read a processed (cleaned) derivative file from the LISTEN study.

    Parameters
    ----------
    subject : int | str
        The subject ID, for example 2001 or "2001".
    task : str
        The experimental task. Must be one of "semantics" or "phonemes".
    session : int | str
        The session (visit). Must be 1 or 2. If a string, it can be "1", "2", "01", or
        "02".
    listen_fpath : str | pathlib.Path | None
        If you are not connected to the lab server, the relative or absolute path to the
        LISTEN project directory (assuming that you have copied the folder from the lab
        server to some hard drive). The folder must be a clone of the folder on the lab
        server, with a 'bids' sub directory. If ``None`` is passed, then the code will
        attempt to access the data on the lab server, meaning that you should have the
        lab server mounted to your local hard drive.
    """
    from kinnd.utils.paths import get_listen_path

    # Sanity Checks
    _validate_type("subject", subject, str)
    _validate_type("task", task, str)
    _validate_type("session", session, (int, str))
    _validate_type("listen_fpath", listen_fpath, (str, Path, None))
    # Sanitize
    session = str(session).zfill(2)

    if not listen_fpath:
        droot = get_listen_path() / "data" / "derivatives" / "pylossless"
    else:
        droot = (listen_fpath /
                 "data" /
                 "derivatives" /
                 "pylossless").expanduser.resolve()
    if not droot.exists():
        raise FileNotFoundError(f"{droot} does not exist.")
    sub_path = (
        droot /
        f"sub-{subject}" /
        f"ses-{session}" /
        f"sub-{subject}_ses-{session}_task-{task}_desc-cleaned_eeg.fif"
    )
    return mne.io.read_raw(sub_path)



def _validate_type(parameter, argument, expected):
    """Validate that the user passed an argument that is a valid type for the parameter.

    Parameters
    ----------
    parameter : str
        The name of the parameter.
    argument : str | int | float | bool | list | tuple | dict
        The argument that the user passed
    expected : builtin type | tuple | list
        The type that the argument is expected to belong to. For
        example, str, int, or mne_bids.BIDSPath. Can also be a list or tuple of
        types, if the argument can be one of many.
    """
    from collections.abc import Iterable

    expected = (expected,) if not isinstance(expected, Iterable) else expected
    # doing a state check on None is tricky
    expected = tuple(
        [
        type(this_type)
        if this_type is None
        else this_type
        for this_type in expected
        ]
        )
    if not isinstance(argument, expected):
        # Sanitize
        raise ValueError(
            f"{parameter} must be of type"
            f" {' or '.join(str(this_type) for this_type in expected)}"
            f" but got {type(argument)}"
            )
    return True
