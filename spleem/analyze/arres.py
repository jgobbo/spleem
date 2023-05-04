import os
import numpy as np
from time import perf_counter
from pathlib import Path
from matplotlib import pyplot as plt
from .imports import ReadUView

__all__ = ["extract_arres", "extract_all_arres"]

ARRES_FILENAME = "ARRES_data.csv"


def extract_arres(
    folder: Path, box_radius: int = 18, output_file: bool = True, n_sv: int = None
):
    files = os.listdir(folder)
    if ARRES_FILENAME in files:
        print(f"{ARRES_FILENAME} already exists for dataset in {folder}.")

        return np.loadtxt(folder / ARRES_FILENAME, delimiter=",")
    else:
        RU = ReadUView()

        files = [file for file in files if file.endswith(".dat")]
        n_files = int(files[-1].split("_")[0]) + 1
        assert n_files == len(
            files
        ), f"File indicies in {folder} don't match number of files."

        sv_start, k_start = float(files[0].split("_")[3]), float(files[0].split("_")[5])
        sv_end, k_end = float(files[-1].split("_")[3]), float(files[-1].split("_")[5])
        sv_step = round(
            float(files[1].split("_")[3]) - float(files[0].split("_")[3]), 3
        )
        if k_first := (sv_step == 0):
            sv = sv_start
            file_i = 0
            while sv == sv_start:
                sv = float(files[file_i].split("_")[3])
                file_i += 1
            n_k = file_i - 1
            n_sv = n_files // n_k
        else:
            n_sv = round((sv_end - sv_start) / sv_step) + 1
            n_k = n_files // n_sv
        print(f"{sv_start=}, {sv_end=}, {n_sv=}, {k_start=}, {k_end=}, {n_k=}")
        assert n_sv * n_k == n_files, f"Filename parsing for data in {folder} failed."

        data = np.zeros((n_sv, n_k))
        start_time = perf_counter()
        for i, file in enumerate(files):
            if k_first:
                row = i // n_k
                col = i % n_k
            else:
                row = i % n_sv
                col = i // n_sv

            image = RU.getImage(folder / file)[0]
            center_intensity: np.ndarray = np.sum(
                image[
                    512 - box_radius : 512 + box_radius,
                    512 - box_radius : 512 + box_radius,
                ],
                axis=0,
            )
            data[row, col] = (
                center_intensity.max()
                - (center_intensity[0] + center_intensity[-1]) / 2
            )

            dt = perf_counter() - start_time
            print(
                f"finished reading file {i+1}/{len(files)}, {dt:.3f} seconds elapsed",
                end="\r",
            )

        # data = np.flip(data, axis=0) dont think you want this
        if output_file:
            np.savetxt(folder / ARRES_FILENAME, data, delimiter=",")

        return data


def extract_all_arres(root: Path, plot: bool = True) -> dict[str, np.ndarray]:
    dataset = {}
    for parent, dirs, _files in os.walk(root):
        for directory in dirs:
            try:
                if "ARRES" in directory:
                    data = extract_arres(Path(parent) / directory)
                    dataset[directory] = data
                    if plot:
                        plt.imshow(data)
                        plt.show()
            except Exception as e:
                print(f"Extracting data from {directory} failed due to exception: {e}")
    return dataset
