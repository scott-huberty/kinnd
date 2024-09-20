from pathlib import Path

import mne

from kinnd.utils.paths import get_semantics_fpaths

def fix_event_ids(ep):
    """Reduce event labels to just BAD+ and match or mismatch.

    Parameters
    ----------
    ep : mne.Epochs
        The epochs object to modify, which should have been read in from the Semantics data.

    Returns
    -------
    mne.Epochs
        The modified epochs object.
    """
    if Path(ep.filename).stem.endswith("SnMa"):
        event_id = {"match": 100}
    elif Path(ep.filename).stem.endswith("SnMi"):
        event_id = {"mismatch": 200}
    else:
        raise ValueError(f"Could not determine condition from filename: {Path(ep.filename)}")
    bad_ids = [ev for ev in ep.event_id if "BAD+" in ev]
    mne.epochs.combine_event_ids(ep, bad_ids, new_event_id={'BAD+': 999}, copy=False)
    stim_ids = [ev for ev in ep.event_id if "BAD+" not in ev]
    mne.epochs.combine_event_ids(ep, stim_ids, new_event_id=event_id, copy=False)
    return ep

def read_epochs_semantics(subject, drop_bad=True, verbose="INFO"):
    """Read data from disk for a single subject in the Semantics dataset.

    .. note::
        This function will combine the match and mismatch conditions into a single
        epochs object, with event IDs of 100 for match and 200 for mismatch. The
        "BAD+" events will be combined into a single event ID of 999.

    Parameters
    ----------
    subject : str
        The subject ID to load. Should be in the format 'sub-XX', such as 'sub-01',
        or 'sub-3027'.
    drop_bad : bool
        Whether to drop epochs that overlap with BAD+ events from the data.
        Default is True.
    verbose : str
        The verbosity level for logging output to use when loading the data. Default
        is "INFO". Can be "DEBUG", "INFO", "WARNING", "ERROR", or "CRITICAL".

    Returns
    -------
    mne.Epochs
        The epochs object for the specified subject.
    """
    fpaths = get_semantics_fpaths()
    if subject not in fpaths:
        msg = f"Subject {subject} not found in the Semantics data."
        hint = "Hint: Call get_semantics_fpaths() to see the available subjects."
        raise ValueError(f"{msg}\n{hint}")
    match_ep = mne.read_epochs_eeglab(fpaths[subject]['match'], verbose=verbose)
    fix_event_ids(match_ep)
    mismatch_ep = mne.read_epochs_eeglab(fpaths[subject]['mismatch'], verbose=verbose)
    fix_event_ids(mismatch_ep)
    ep = mne.concatenate_epochs([match_ep, mismatch_ep], verbose=verbose)
    if drop_bad:
        bad_inds = ep["BAD+"].selection
        return ep.drop(bad_inds, reason="BAD+ event", verbose="INFO")
    return ep
