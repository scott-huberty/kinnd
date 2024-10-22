import pytz
import datetime

import mne

from pathlib import Path
from warnings import warn

def read_raw_listen(filename):
    """Read an MFF file from the Listen study into MNE-Python.

    Parameters
    ----------
    filename : str or Path
        The path to the MFF file.

    Returns
    -------
    raw : mne.io.Raw
        The EEG data as an MNE-Python `~mne.io.Raw` object.
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
    cel_map = {"1": "match", "2": "mismatch"}
    WANT_EVENTS = ["img+", "snd+"]
    stim_map = {"img+": "image", "snd+": "word"}

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
            elif event["code"] in WANT_EVENTS:
                condition = cel_map[str(event["keys"]["cel#"])]
                description = f"{stim_map[event['code']]}_{condition}"
            else:
                description = event["code"]
            onsets.append(ts)
            durations.append(duration)
            descriptions.append(description)
    raw.set_annotations(mne.Annotations(onsets, durations, descriptions))
    return raw
