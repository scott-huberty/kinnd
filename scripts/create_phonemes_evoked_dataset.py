import argparse

from pathlib import Path

from warnings import warn

import mne
import xarray as xr

import kinnd


def main(derivative="pylossless"):


    dpath = (
        kinnd.utils.paths.get_listen_path() /
        "data" /
        "derivatives" /
        derivative
    )
    subs = list(dpath.glob("sub-*"))

    ds = {}
    for sub in subs:
        pid = sub.name.split("sub-")[-1]
        try:
            inst = kinnd.studies.listen.io.read_processed_listen(
                subject=pid,
                task="phonemes",
                derivative=derivative,
                read_raw_kwargs=dict(preload=True),
                )
        except FileNotFoundError as e:
            warn(f"{e}", stacklevel=2)
            continue

        if derivative == "pylossless":
            bads = inst.info["bads"].copy() # save for later
            inst.interpolate_bads().set_eeg_reference("average").filter(1, 40)
            inst.annotations.rename(
                {"tone_Standard": "tone/standard", "tone_Deviant": "tone/deviant"}
                )

            # Bug. says that it is using net but it isn't
            epochs = mne.Epochs(
                inst,
                event_id=["tone/standard", "tone/deviant"],
                tmin=-.1,
                tmax=1,
                preload=True
                )
        elif derivative == "mne-bids-pipeline":
            epochs = inst
            bads = epochs.info["bads"].copy()
            epochs.interpolate_bads()
        da = []
        for condition in ["tone/standard", "tone/deviant"]:
            evoked = epochs[condition].average()
            da.append(
                xr.DataArray(
                evoked.data,
                dims=["channel", "time"],
                coords=dict(
                    condition=condition,
                    channel=evoked.ch_names,
                    time=evoked.times),
                )
            )
        da = xr.concat(da, dim="condition")
        da.attrs = {
            "filename": Path(_get_inst_filename(inst)).name,
            "task": "phonemes",
            "sfreq": inst.info["sfreq"],
            "filter": f"{inst.info['highpass']}-{inst.info['lowpass']} Hz",
            "reference": "average",
            "n_good_standard_trials": len(epochs['tone/standard']),
            "n_good_deviant_trials": len(epochs['tone/deviant']),
            "baseline": epochs.baseline,
            "bads": bads,
            "derivative": derivative,
                    }
        ds[sub.name] = da
    ds = xr.Dataset(ds)
    assert 1 == 0
    ds.to_zarr(dpath.parent / "xarray" / f"phonemes_evoked_{derivative}.zarr", mode="w")


def _get_inst_filename(inst):
    from mne.io import BaseRaw
    from mne import BaseEpochs

    if isinstance(inst, BaseRaw):
        return inst.filenames[0]
    elif isinstance(inst, BaseEpochs):
        return inst.filename
    else:
        raise ValueError(f"inst must be an MNE Raw or Epochs instance. got {type(inst)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--derivative",
        dest="derivative",
        type=str,
        choices=["pylossless", "mne-bids-pipeline"],
        default="pylossless"
        )
    args = parser.parse_args()
    main(derivative=args.derivative)
