import re, os
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
from numpy.typing import NDArray
from PIL import Image as Tif  # I want the name Image
from scipy.interpolate import interp1d
from dataclasses import dataclass
from statistics import mean, stdev
from .persistence.imagepers import persistence

__all__ = [
    "Frame",
    "Image",
    "SpinImage",
    "Sweep",
    "SpinSweep",
    "electron_rate",
    "test_electron_counting",
    "load_scan",
    "load_all",
]


@dataclass
class Frame:
    filepath: Path
    data: NDArray = None
    metadata: dict = None
    index: int = None
    start_voltage: float = None
    start_voltage_table: list = None

    def __post_init__(self):
        self._import_frame(self.filepath)

    def _import_frame(self, path: Path):
        self.metadata = self._read_metadata(self._find_meta_path(path))
        self.index = self.metadata.pop("index")
        self.start_voltage = self.metadata.pop("Start_Voltage")

        self.data = np.array(Tif.open(path))

    def _read_metadata(self, filename) -> dict:
        data = {}
        with open(filename, "r") as metadata:
            for line in metadata.readlines():
                string = line.strip()
                info = string.split(":")
                if len(info) > 1:
                    key = info[0].replace(" ", "")
                    if len(info) > 2:
                        val = ":".join(info[1:]).replace(" ", "")
                    else:
                        val = info[1].replace(" ", "")
                    data[key] = val
        return self._prune_metadata(data)

    def _prune_metadata(self, data: dict) -> dict:
        del data["directory"]
        del data["file"]
        if self.start_voltage_table is None:
            interp = interp1d([-10000, 10000], [-10000, 10000])
        else:
            interp = interp1d(*self.start_voltage_table)
        for key in data:
            if key != "time":
                if data[key] == "ValueNotAvailable":
                    data[key] = None
                else:
                    data[key] = float(re.sub("[^0-9.\-]", "", data[key]))
        data["Start_Voltage"] = (
            interp(data["Start_Voltage"]).tolist()
            if data["Start_Voltage"] is not None
            else None
        )
        data["index"] = int(data["index"])
        return data

    @staticmethod
    def _find_meta_path(path: Path):
        filename = path.parts[-1]
        metadata_filename = re.sub("[-].*[-]", "", filename).replace("tif", "txt")
        return path.parents[0] / Path(metadata_filename)


@dataclass
class Image:
    folder: Path
    start_voltage_table: list = None
    frames: list[Frame] = None

    def __post_init__(self):
        if not isinstance(self.folder, Path):
            self.folder = Path(self.folder)

        self._import_image()

    def _import_image(self):
        file_list = [
            Path(file) for file in os.listdir(self.folder) if self._valid_file(file)
        ]
        self.frames = np.ndarray(len(file_list), dtype=Frame)
        for file in file_list:
            frame = Frame(self.folder / file)
            self.frames[frame.index - 1] = frame

    def _valid_file(self, filename: str):
        return filename.endswith(".tif")

    def plot_image(
        self, frame_slice: slice = None, vmin=None, vmax=None, ax: plt.Axes = None
    ):
        frame_slice = (
            frame_slice if frame_slice is not None else slice(len(self.frames))
        )

        integrated_image: np.ndarray = None  # TODO clean this up
        for frame in self.frames[frame_slice]:
            integrated_image = (
                frame.data
                if integrated_image is None
                else integrated_image + frame.data
            )

        integrated_image = integrated_image - integrated_image.min()
        integrated_image = integrated_image / integrated_image.max()

        if ax == None:
            fig, ax = plt.subplots()
            ax.imshow(integrated_image, vmin=vmin, vmax=vmax)
            return fig, ax

        ax.imshow(integrated_image, vmin=vmin, vmax=vmax)
        return ax


@dataclass
class Sweep(Image):
    def extract_iv(self, voltage_range=None, x_slice=None, y_slice=None):
        x_slice = slice(0, self.frames[0].data.shape[0]) if x_slice is None else x_slice
        y_slice = slice(0, self.frames[0].data.shape[1]) if y_slice is None else y_slice

        intensity = []
        voltage = []
        for frame in self.frames:
            if voltage_range is None or (
                voltage_range[0] <= frame.start_voltage <= voltage_range[1]
            ):
                frame_intensity = frame.data[x_slice, y_slice].sum()
                if frame.start_voltage in voltage:
                    intensity[-1] += frame_intensity
                else:
                    voltage.append(frame.start_voltage)
                    intensity.append(frame_intensity)

        intensity = np.array(intensity)
        voltage = np.array(voltage)
        intensity = (intensity - np.min(intensity)) / (
            np.max(intensity) - np.min(intensity)
        )

        return voltage, intensity

    def iv_curve(
        self,
        ax: plt.Axes = None,
        voltage_range=None,
        x_slice=None,
        y_slice=None,
        offset=0,
        **kwargs,
    ):
        voltage, intensity = self.extract_iv(
            voltage_range=voltage_range, x_slice=x_slice, y_slice=y_slice
        )

        if ax == None:
            fig, ax = plt.subplots()
            ax.plot(voltage, intensity)
            ax.set_xlabel("start voltage [V]")
            ax.set_ylabel("intensity")
            return fig, ax

        ax.plot(voltage, intensity + offset, kwargs=kwargs)


@dataclass
class SpinImage(Image):
    def _valid_file(self, filename):
        return filename.endswith(".tif") and ("[SPLEEM]" in filename)


# TODO verify that this class is working
@dataclass
class SpinSweep(Sweep):
    up_frames: list[Frame] = None
    down_frames: list[Frame] = None

    def _import_image(self):
        frame_sets = {
            "[SPLEEM]": self.frames,
            "[SPINUP]": self.up_frames,
            "[SPINDN]": self.down_frames,
        }

        for spin, frame_set in frame_sets:
            file_list = [
                Path(file)
                for file in os.listdir(self.folder)
                if self._valid_file(file, spin=spin)
            ]
            frame_set = np.ndarray(len(file_list), dtype=Frame)
            for file in file_list:
                frame = Frame(self.folder / file)
                frame_set[frame.index - 1] = frame

    def _valid_file(self, filename: str, spin: str):
        return filename.endswith(".tif") and spin in filename

    # def _set_frames(self, frame_set:str="diff"):
    #     self.frames = {"up": self.up_frames,
    #                    "down": self.down_frames,
    #                    "diff": self.difference_frames,
    #                   }[frame_set]

    def extract_iv(self, frame_set=None, *args, **kwargs):
        frame_set = self.frames if frame_set is None else frame_set

        with self.frames as frame_set:
            return super().extract_iv(*args, **kwargs)

        # self._set_frames(frame_set=frame_set)
        # if x_slice == None:
        #     x_slice=(0,len(frame_set[0].x))
        # if y_slice == None:
        #     y_slice=(0,len(frame_set[0].y))

        # intensity = []
        # voltage = []
        # for frame in self.frames.values():
        #     if voltage_range==None or (voltage_range[0] <= frame.Start_Voltage <= voltage_range[1]):
        #         if frame.Start_Voltage in voltage:
        #             intensity[-1] += frame.sel(x=slice(*x_slice), y=slice(*y_slice)).sum().values
        #         else:
        #             voltage.append(frame.Start_Voltage)
        #             intensity.append(frame.sel(x=slice(*x_slice), y=slice(*y_slice)).sum().values)

        # intensity = np.array(intensity)
        # voltage = np.array(voltage)
        # intensity = intensity - min(intensity)
        # intensity = intensity / max(intensity)

        # return intensity, voltage

    # TODO fix this
    # def triple_iv_curve(self, ax=None, x_slice=None, y_slice=None):
    #     if isinstance(ax, np.ndarray):
    #         assert ax.size[1] == 3
    #     else:
    #         _, ax = plt.subplots(1, 3)
    #     frame_set = [self.up_frames, self.down_frames, self.frames]
    #     titles = ["Spin Up", "Spin Down", "Difference"]

    #     for i in range(3):
    #         intensity, voltage = self.extract_iv(x_slice=x_slice, y_slice=y_slice, frame_set=frame_set[i])
    #         ax[i].plot(voltage, intensity)
    #         ax[i].set_xlabel('start voltage [V]')
    #         ax[i].set_ylabel('intensity')
    #         ax[i].set_title(titles[i])

    #     return ax

    def iv_curve(self, frame_set=None, *args, **kwargs):
        frame_set = self.frames if frame_set is None else frame_set

        with self.frames as frame_set:
            return super().iv_curve(*args, **kwargs)

        # intensity, voltage = self.extract_iv(frame_set=frame_set, voltage_range=voltage_range, x_slice=x_slice, y_slice=y_slice)

        # if ax == None:
        #     fig, ax = plt.subplots()
        #     ax.plot(voltage, intensity)
        #     ax.set_xlabel('start voltage [V]')
        #     ax.set_ylabel('intensity')
        #     return fig, ax

        # ax.plot(voltage, intensity+y_shift, **kwargs)

    def plot_image(self, frame_set=None, *args, **kwargs):
        frame_set = self.frames if frame_set is None else frame_set

        with self.frames as frame_set:
            super().plot_image(*args, **kwargs)

        # self._set_frames(frame_set)
        # Image.plot_image(self)


def electron_rate(image: Image, exposure=1, min_persistence=20) -> tuple[float, float]:
    n_peaks = []
    for frame in image.frames:
        peak_data = persistence(frame.data)

        peak_count = 0
        for homology_class in peak_data:
            _birth_point, _birth_level, pers, _death_point = homology_class
            if pers > min_persistence:
                peak_count += 1
        n_peaks.append(peak_count / exposure)

    return (mean(n_peaks), stdev(n_peaks))


def test_electron_counting(
    image: Image, min_persistence=20, test_frame: int = 0, **kwargs
):
    fig, ax = plt.subplots(1, 2, figsize=(14, 7))
    ax[0].imshow(image.frames[test_frame].data, **kwargs)

    peak_data = persistence(image.frames[test_frame].data)
    for homology_class in peak_data:
        birth_point, _birth_level, pers, _death_point = homology_class
        y, x = birth_point
        if pers > min_persistence:
            ax[1].plot(x, y, "k.")

    ax[1].set_title(f"Peak Locations with Persistence>{min_persistence}")
    ax[1].set_xlim(0, image.frames[test_frame].data.shape[1])
    ax[1].set_ylim(0, image.frames[test_frame].data.shape[0])
    ax[1].invert_yaxis()
    ax[1].set_aspect("equal")

    return fig, ax


def load_scan(folder, desired_index: int):
    for root, dirs, _files in os.walk(folder):
        for directory in dirs:
            index: str = directory[:2]
            if index.isdigit():
                index = int(index)
                if index == desired_index:
                    if "IM" in directory:
                        return Image(Path(root) / Path(directory))
                    elif "SW" in directory:
                        return Sweep(Path(root) / Path(directory))
                    elif "SRSW" in directory:
                        return SpinSweep(Path(root) / Path(directory))
                    elif "SR" in directory:
                        return SpinImage(Path(root) / Path(directory))


def load_all(folder, inclusions: tuple[int, ...] = None) -> dict:
    if inclusions is not None:
        inclusions = set(inclusions)  # probably isnt meaningful but its fun

    scans = {}
    for root, dirs, _files in os.walk(folder):
        for directory in dirs:
            index: str = directory[:2]
            if index.isdigit():
                index = int(index)
                if (inclusions == None) or (index in inclusions):
                    if "IM" in directory:
                        scans[index] = Image(Path(root) / Path(directory))
                    elif "SW" in directory:
                        scans[index] = Sweep(Path(root) / Path(directory))
                    elif "SRSW" in directory:
                        scans[index] = SpinSweep(Path(root) / Path(directory))
                    elif "SR" in directory:
                        scans[index] = SpinImage(Path(root) / Path(directory))
    return scans
