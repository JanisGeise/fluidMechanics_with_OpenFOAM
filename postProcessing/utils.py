"""
helper functions
"""
from glob import glob
from os.path import join

import torch as pt

from typing import Tuple, Union
from flowtorch.data import FOAMDataloader, mask_box
from pandas import read_csv


def prepare_data(load_path: str, bounds : list, field_name: str = "p",
                 t_start: Union[float, int] = 0.001) -> Tuple[list, pt.Tensor, pt.Tensor]:
    """
    Load and mask OpenFOAM snapshots for the wave animation.

    :param load_path: Path to the OpenFOAM case directory.
    :type load_path: str
    :param bounds: Lower and upper ``[x, y]`` bounds used to mask the mesh.
    :type bounds: Sequence[Sequence[float | int]]
    :param field_name: Name of the scalar field to load.
    :type field_name: str
    :param t_start: Earliest write time included in the animation.
    :type t_start: float | int
    :return: Write times, masked two-dimensional coordinates, and masked field
        snapshots arranged as ``(n_points, n_times)``.
    :rtype: tuple[list[str], torch.Tensor, torch.Tensor]
    """
    # load the snapshots of the volume data
    loader = FOAMDataloader(load_path)

    # mask the coordinates
    _coord = loader.vertices[:, :2]

    # apply the mask
    mask = mask_box(_coord, lower=bounds[0], upper=bounds[1])

    # mask the vertices
    _coord = pt.stack([pt.masked_select(_coord[:, d], mask) for d in range(2)], dim=1)

    # take all available write times except zero
    _write_times = [t for t in loader.write_times if float(t) >= t_start]

    # allocate a tensor for the flow fields, for the animation we don't care about DP
    _data = pt.zeros((_coord.shape[0], len(_write_times))).to(pt.float32)

    # load the data, loop over times due to memory constraints for the DDES case
    print(f"Loading snapshots for field {field_name}. Found {len(_write_times)} snapshots.")

    for i, t in enumerate(_write_times):
        print(f"\rLoading write time {i + 1} / {len(_write_times)}.", end="", flush=True)
        _data[:, i] = pt.masked_select(loader.load_snapshot(field_name, t), mask).to(pt.float32)

    print("\nDone.")

    return _write_times, _coord, _data


def compute_norm_of_fields(load_path: str, time_boundaries: list = None,
                           field: str = "UMean") -> Tuple[pt.Tensor, list]:
    """
    Compute the L2 norm of a volume field for a given number of write times.
    The L2 norms are scaled with the L2 norm of the first field.

    :param load_path: path to the simulation
    :param time_boundaries: min. / max. write times for computing the L2 norm
    :param field: Name of the field
    :return: write times and norms of fields.
    """
    print(f"Starting with case: {load_path}.")
    loader = FOAMDataloader(load_path)

    # get the defined boundaries for start and end time to use if provided
    if time_boundaries is not None:
        idx = sorted([i for i, t in enumerate(loader.write_times) if t in time_boundaries])
        write_times = loader.write_times[idx[0]:idx[1]+1]

    # else use all times steps but zero
    else:
        write_times = loader.write_times[1:]

    # check for the time steps in which the target filed is present
    write_times = [t for t in write_times if field in loader.field_names[t]]

    # compute the norm of the field in the last time step
    norm_first_field = loader.load_snapshot(field, write_times[0]).norm()

    # now compute the difference of the norm between two consecutive time steps
    all_norms, last_snapshot = [], 0
    for i in range(len(write_times)):
        print(f"Loading time step ({i+1} / {len(write_times)}) t = {write_times[i]} s.")
        new_snapshot = loader.load_snapshot(field, write_times[i])
        all_norms.append((new_snapshot-last_snapshot).norm() / norm_first_field)
        last_snapshot = new_snapshot

    # don't return the norm of the last field, since the difference is zero
    return pt.tensor(list(map(float, write_times))), all_norms


# TODO: simplify for this case
def load_line_samples(load_path: str, loc: list, coord: str = "x", start: int = 0,
                      stop:  int = 50000, times: list[str] = None) -> Tuple[list, list]:
    """
    Load the line samples from OpenFOAM.

    The function searches for CSV files corresponding to one or more sampling locations and
    collects both the numerical data and their associated time steps.

    The order of variables in the OpenFOAM `volSymmTensorField` is assumed to be:
    ``[XX, XY, XZ, YY, YZ, ZZ]`` — this ordering is used to assign column names consistently.

    :param load_path: Path to the OpenFOAM case directory (containing ``postProcessing/sample_lines``).
    :type load_path: str
    :param loc: List of sampling location names to load, has to be characteristic to the file name
    :type loc: list[str]
    :param coord: Coordinate along which the sampling line was taken (e.g., "x" or "y").
    :type coord: str
    :param start: Start index for slicing the available time directories.
    :type start: int
    :param stop: Stop index for slicing the available time directories.
    :type stop: int
    :param times: List containing the write times to load, the order of times is preserved when loading, if given
                ``start`` and ``stop`` will be ignored
    :type times: list[str]
    :return: A tuple of two lists:
             - ``all_lines``: list of lists of pandas DataFrames, one per location and time step.
             - ``all_times``: list of lists of time values (as strings) corresponding to each DataFrame.
    :rtype: Tuple[list, list]
    """
    names = [coord, "p", "Ux", "Uy", "Uz", "Ux_mean", "Uy_mean", "Uz_mean", "Ma", "T"]
    files = [glob(join(load_path, "postProcessing", "sample_lines", t, f"*_{l}_*.csv"))[0] for t in times]

    line = [read_csv(f, names=names, header=None, sep=",", skiprows=1, usecols=range(len(names))) for f in files]

    return line

if __name__ == "__main__":
    pass
