import argparse

from pathlib import Path
from warnings import warn

import pandas as pd

import mne
import mne_bids

import pylossless as ll

import kinnd


def process_one_subject(bpath):
    """Process a single subject from the Listen study."""
    config_fpath = get_pylossless_config(bpath)

    subject = bpath.subject
    session = bpath.session
    task = bpath.task
    broot = bpath.root
    raw = mne_bids.read_raw_bids(bpath)
    raw.info["bads"].extend(["E125", "E126", "E127", "E128"])

    # Save Outputs
    dpath = broot.parent / "derivatives" / "pylossless" / f"sub-{subject}"
    dpath.mkdir(exist_ok=True, parents=False)
    dpath = dpath / f"ses-{session}"
    dpath.mkdir(exist_ok=True, parents=False)
    dname = f"sub-{subject}_ses-{session}_task-{task}_desc-cleaned_eeg.fif"
    if (dpath / dname).exists():
        warn(f"SKIPPING: {dname} output already exists at {dpath}.")
        return

    # Find Breaks
    break_annots = mne.preprocessing.annotate_break(raw)
    raw.set_annotations(raw.annotations + break_annots)

    # PyLossless Pipeline
    pipeline = ll.LosslessPipeline(config_fpath)
    pipeline.run_with_raw(raw.load_data())
    rejection_policy = ll.RejectionPolicy()
    cleaned_raw = rejection_policy.apply(pipeline)

    basename = f"sub-{subject}_ses-{session}_task-{task}"
    eeg_out = dpath / f"{basename}_desc-cleaned_eeg.fif"
    cleaned_raw.save(eeg_out)
    ica1_out = dpath / f"{basename}_desc-fastica_ica.fif"
    ica2_out = dpath / f"{basename}_desc-infomax_ica.fif"
    pipeline.ica1.save(ica1_out)
    pipeline.ica2.save(ica2_out)
    labels_out = dpath / f"{basename}_iclabels.csv"
    pipeline.flags["ic"].to_csv(labels_out)


def get_pylossless_config(bpath):
    """Get the PyLossless config file"""
    broot = Path(bpath.root)
    config = ll.config.Config()
    config_fpath = broot.parent / "listen_pylossless_config.yaml"
    if not config_fpath.exists():
        config.load_default()
        config["filtering"]["notch_filter_args"]["freqs"] = [60]
        config["noisy_channels"]["outliers_kwargs"]["k"] = 6
        config["noisy_channels"]["outliers_kwargs"]["lower"] = 0.25
        config["noisy_channels"]["outliers_kwargs"]["upper"] = 0.75

        config["noisy_epochs"]["outliers_kwargs"]["k"] = 6
        config["noisy_epochs"]["outliers_kwargs"]["lower"] = 0.25
        config["noisy_epochs"]["outliers_kwargs"]["upper"] = 0.75

        config["uncorrelated_channels"]["outliers_kwargs"]["k"] = 6
        config["uncorrelated_channels"]["outliers_kwargs"]["lower"] = 0.25
        config["uncorrelated_channels"]["outliers_kwargs"]["upper"] = 0.75

        config["uncorrelated_epochs"]["outliers_kwargs"]["k"] = 6
        config["uncorrelated_epochs"]["outliers_kwargs"]["lower"] = 0.25
        config["uncorrelated_epochs"]["outliers_kwargs"]["upper"] = 0.75

        config["ica"]["noisy_ic_epochs"]["outliers_kwargs"]["k"] = 6
        config["ica"]["noisy_ic_epochs"]["outliers_kwargs"]["lower"] = 0.25
        config["ica"]["noisy_ic_epochs"]["outliers_kwargs"]["upper"] = 0.75

        config.save(config_fpath)
    return config_fpath


def process_dataset(broot, task=None):
    csv_fpath = broot.parent / "eeg_list.csv"
    df = pd.read_csv(csv_fpath, header=0)

    for tup in df.itertuples():
        subject = str(tup.subject)
        session = f"{tup.session:02d}"
        if tup.task != task:
            warn(f"SKIPPING: sub-{subject}_ses-{session}_task-{tup.task} because only the {task} task was requested")
            continue
        bpath = mne_bids.BIDSPath(subject=subject, session=session, task=tup.task, root=broot)
        process_one_subject(bpath)


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
    args = parser.parse_args()

    # MNE-BIDS
    broot = args.bids_root
    if broot is None:
        broot = kinnd.paths.listen_path().parent / "data" / "bids"
    broot = Path(broot).expanduser().resolve()

    subject = args.subject
    if subject is None:
        process_dataset(broot, task=args.task)
    else:
        subject = f"{args.subject}"
        session = args.session.zfill(2)
        task = f"{args.task}"
        bpath = mne_bids.BIDSPath(subject=subject, session=session, task=task, root=broot)
        process_one_subject(bpath)
