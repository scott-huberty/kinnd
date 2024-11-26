import argparse

import os
import time

from datetime import datetime
from pathlib import Path
from warnings import warn

import pandas as pd

import mne
import mne_bids

import pylossless as ll

import kinnd

import logging


def process_one_subject(bpath, overwrite):
    """Process a single subject from the Listen study."""
    subject = bpath.subject
    session = bpath.session
    task = bpath.task
    broot = bpath.root

    # instantiate logger
    logger = mne.utils.logger
    # logger.setLevel("DEBUG")

    console_handler = logging.StreamHandler()
    log_fpath = str(Path(__file__).parent / f"./logs/sub-{subject}_ses-{session}_task-{task}.txt")
    file_handler = logging.FileHandler(log_fpath, mode="a", encoding="utf-8")
    formatter = logging.Formatter(
        "{asctime} - {levelname} - {message}",
        style="{",
        datefmt="%Y-%m-%d %H:%M",
    )
    console_handler.setFormatter(formatter)
    console_handler.setLevel("DEBUG")
    file_handler.setFormatter(formatter)
    file_handler.setLevel("DEBUG")
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    # Define Output paths
    dpath = broot.parent / "derivatives" / "pylossless" / f"sub-{subject}"
    dpath.mkdir(exist_ok=True, parents=False)
    dpath = dpath / f"ses-{session}"
    dpath.mkdir(exist_ok=True, parents=False)
    dname = f"sub-{subject}_ses-{session}_task-{task}_desc-cleaned_eeg.fif"

    # check when the file was last processed
    if (dpath / dname).exists():
        mtime = os.path.getmtime(dpath / dname)
        time_str = time.ctime(mtime)
        dt_processed = datetime.strptime(time_str, "%a %b %d %H:%M:%S %Y")
    else:
        dt_processed = None
    if (dpath / dname).exists() and not overwrite:
        logger.info(f"SKIPPING: {dname} output already exists at {dpath}.")
        close_logger(logger, console_handler, file_handler)
        return
    started_processing_date = datetime(2024, 11, 4)
    if dt_processed and dt_processed >= started_processing_date:
        logger.info(
            f"sub-{subject}_ses-{session}_task-{task} processed on {dt_processed}. Skipping"
            )
        close_logger(logger, console_handler, file_handler)
        return

    # If script makes it to this point. We are processing
    logger.info(f"Processing sub-{subject}_ses-{session}_task-{task}")
    config_fpath = get_pylossless_config(bpath)

    raw = mne_bids.read_raw_bids(bpath)
    raw.info["bads"].extend(["E125", "E126", "E127", "E128"])

    # Find Breaks
    break_annots = mne.preprocessing.annotate_break(raw)
    raw.set_annotations(raw.annotations + break_annots)

    # PyLossless Pipeline
    pipeline = ll.LosslessPipeline(config_fpath)
    pipeline.run_with_raw(raw.load_data())
    rejection_policy = ll.RejectionPolicy(ch_flags_to_reject=['volt_std', 'noisy', 'uncorrelated', 'bridged'])
    cleaned_raw = rejection_policy.apply(pipeline)

    basename = f"sub-{subject}_ses-{session}_task-{task}"
    eeg_out = dpath / f"{basename}_desc-cleaned_eeg.fif"
    cleaned_raw.save(eeg_out, overwrite=overwrite)
    ica1_out = dpath / f"{basename}_desc-fastica_ica.fif"
    ica2_out = dpath / f"{basename}_desc-infomax_ica.fif"
    pipeline.ica1.save(ica1_out, overwrite=overwrite)
    pipeline.ica2.save(ica2_out, overwrite=overwrite)
    labels_out = dpath / f"{basename}_iclabels.csv"
    pipeline.flags["ic"].to_csv(labels_out)
    logger.info(f"Finished sub-{subject}_ses-{session}_task-{task}")
    logger.removeHandler(file_handler)
    logger.removeHandler(console_handler)
    file_handler.close()
    console_handler.close()


def close_logger(logger, console_handler, file_handler):
    logger.removeHandler(file_handler)
    logger.removeHandler(console_handler)
    file_handler.close()
    console_handler.close()


def get_pylossless_config(bpath):
    """Get the PyLossless config file"""
    broot = Path(bpath.root)
    config = ll.config.Config()
    config_fpath = broot.parent / "listen_pylossless_config.yaml"
    if not config_fpath.exists():
        config.load_default()
        config["flag_channels_fixed_threshold"] = {}
        config["flag_channels_fixed_threshold"]["threshold"] = 0.00015

        config["flag_epochs_fixed_threshold"] = {}
        config["flag_epochs_fixed_threshold"]["threshold"] = 0.00015


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


def process_dataset(broot, task=None, overwrite=False):
    csv_fpath = broot.parent / "eeg_list.csv"
    df = pd.read_csv(csv_fpath, header=0)

    for tup in df.itertuples():
        subject = str(tup.subject)
        session = f"{tup.session:02d}"
        if tup.task != task:
            warn(f"SKIPPING: sub-{subject}_ses-{session}_task-{tup.task} because only the {task} task was requested")
            continue
        bpath = mne_bids.BIDSPath(subject=subject, session=session, task=tup.task, root=broot)
        process_one_subject(bpath, overwrite=overwrite)


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
    parser.add_argument(
        "--overwrite",
          dest="overwrite",
          type=bool,
          choices=[True, False],
          default=False
          )
    args = parser.parse_args()

    # MNE-BIDS
    broot = args.bids_root
    if broot is None:
        broot = kinnd.paths.get_listen_path() / "data" / "bids"
    broot = Path(broot).expanduser().resolve()

    subject = args.subject
    if subject is None:
        process_dataset(broot, task=args.task, overwrite=args.overwrite)
    else:
        subject = f"{args.subject}"
        session = args.session.zfill(2)
        task = f"{args.task}"
        bpath = mne_bids.BIDSPath(subject=subject, session=session, task=task, root=broot)
        process_one_subject(bpath, overwrite=args.overwrite)