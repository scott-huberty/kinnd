import argparse
import sys

from pathlib import Path

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

    # Find Breaks
    break_annots = mne.preprocessing.annotate_break(raw)
    raw.set_annotations(raw.annotations + break_annots)

    # PyLossless Pipeline
    pipeline = ll.LosslessPipeline(config_fpath)
    pipeline.run_with_raw(raw.load_data())
    rejection_policy = ll.RejectionPolicy()
    cleaned_raw = rejection_policy.apply(pipeline)

    # Save Outputs
    dpath = broot.parent / "derivatives" / "pylossless" / f"sub-{subject}"
    dpath.mkdir(exist_ok=False, parents=False)
    dpath = dpath / f"ses-{session}"
    dpath.mkdir(exist_ok=False, parents=False)

    basename = f"{subject}_ses-{session}_task-{task}"
    eeg_out = dpath / f"{basename}_desc-cleaned_eeg.fif"
    cleaned_raw.save(eeg_out)
    ica_out = dpath / f"{basename}_desc-ica.fif"
    pipeline.ica2.save(ica_out)
    labels_out = dpath / f"{basename}_desc-iclabels.csv"
    pipeline.flags["ic"].to_csv(labels_out)


def get_pylossless_config(broot):
    """Get the PyLossless config file"""
    broot = Path(broot)
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


def process_dataset(bpath, config_fpath):
    csv_fpath = broot.parent / "eeg_list.csv"
    df = pd.read_csv(csv_fpath, index=0)

    for tup in df.itertuples():
        subject = str(tup.subject)
        task = tup.task
        session = f"{tup.session:02d}"
        bpath = mne_bids.BIDSPath(subject=subject, session=session, task=task, root=broot)

        if task != "semantics":
            continue
        process_one_subject(bpath, config_fpath)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    # parser.add_argument("--subject", dest="subject", type=str, required=True)
    # parser.add_argument("--session", dest="session", type=str, required=True)
    """parser.add_argument(
        "--task",
        dest="task",
        type=str,
        required=True,
        choices=["semantics", "phonemes", "resting"]
        )
    parser.add_argument("--bids_root", dest="bids_root", type=Path, default=None)
    args = parser.parse_args()

    # MNE-BIDS
    broot = args.bids_root
    if broot is None:
        broot = kinnd.paths.listen_path().parent / "data" / "bids"
    broot = Path(broot).expanduser().resolve()"""
    broot = Path.home() / "data" / "bids"
    subs = list(broot.glob("sub-*"))
    no = sys.argv[1]

    config_fpath = get_pylossless_config(broot)
    subject = f"{args.subject}"
    session = args.session.zfill(2)
    task = f"{args.task}"

    bpath = mne_bids.BIDSPath(subject=subject, session=session, task=task, root=broot)
    process_one_subject(bpath)
