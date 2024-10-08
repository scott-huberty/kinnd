import mne
import numpy as np

def plot_topomap(data_dict, info, ch_type="eeg", **kwargs):
    """Plot a topomap of the data.

    Parameters
    ----------
    data_dict : dict
        A dictionary with the data to plot. The keys are the channel names and
        the values are the scalar values to plot.
    info : mne.Info
        an mne.Info object thata contains information about the channel names
        and locations. The channel names in `data_dict` should match the channel
        names in `info`, and they should be the same length (i.e. if you have
        25 channels in `data_dict`, you should have 25 channels in `info`).
        Technically, `info` can be any object that can be passed to the `pos`
        argument of `mne.viz.plot_topomap`, but it is recommended to use an
        `mne.Info` object.
    ch_type : str
        The channel type of the data. Default is "eeg".
    **kwargs
        Additional keyword arguments to pass to `mne.viz.plot_topomap`. The most
        common arguments to pass is the the `axes` argument to plot the topomap
        on a specific `matplotlib` axis object.

    Returns
    -------
    mne.viz.TopoArray
        The plot object.

    Examples
    --------
    >>> import mne
    >>> import numpy as np
    >>> from kinnd.viz import plot_topomap
    >>> montage = mne.channels.make_standard_montage("biosemi64")
    >>> data = np.random.rand(len(montage.ch_names))
    >>> ch_names = montage.ch_names
    >>> data_dict = dict(zip(ch_names, data))
    >>> info = mne.create_info(ch_names, 1000, "eeg")
    >>> info.set_montage(montage)
    >>> plot_topomap(data_dict, info)
    """
    if not isinstance(data_dict, dict):
        raise ValueError(f"`data_dict` must be a dictionary. Got {type(data_dict)}")

    data = np.array(list(data_dict.values()))
    fig = mne.viz.plot_topomap(data, info, ch_type=ch_type, **kwargs)


