from pathlib import Path

def check_directory(directory):
    """Check if a directory exists, and raise an error if it doesn't.

    Parameters
    ----------
    directory : str | Path
        The directory to check.

    Returns
    -------
    Path
        The directory as a Path object.

    Raises
    ------
    FileNotFoundError
        If the directory does not exist.
    IOError
        If the directory is not a string or Path object.
    """
    if not isinstance(directory, (str, Path)):
        raise OSError(
            f"directory must be a string or Path object, not {type(directory)}"
            )
    if not Path(directory).exists():
        raise FileNotFoundError(f"Directory {directory} does not exist.")
    return Path(directory)