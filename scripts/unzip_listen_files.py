from pathlib import Path
import kinnd

server_is_mounted = kinnd.utils.paths.lab_server_is_mounted(strict=False)

def unzip_listen_files():
    """Unzip the Listen study files from the lab server."""
    if not server_is_mounted:
        raise FileNotFoundError("Lab server not mounted.")
    listen_path = kinnd.utils.paths.listen_path()
    listen_files = list(listen_path.rglob("*.zip"))
    for f in listen_files:
        already_unzipped = list(f.parent.glob("*.mff"))
        if already_unzipped:
            if any([f.stem == this_file.name for this_file in already_unzipped]):
                print(f"{f.name} already unzipped.")
                continue
        print(f"Unzipping {f}")
        kinnd.utils.paths.unzip(f)


if __name__ == "__main__":
    unzip_listen_files()