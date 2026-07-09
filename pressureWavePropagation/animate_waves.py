"""
Create an animation of pressure wave propagation from OpenFOAM data.

The script loads pressure snapshots from a selected OpenFOAM case, masks the
domain around the pressure source, re-centers the coordinates, and writes an
MP4 animation of the normalized pressure fluctuation ``p' / p0``.
"""
import torch as pt
import matplotlib.pyplot as plt

from os import makedirs
from typing import Union, Tuple
from os.path import join, exists
from matplotlib.animation import FuncAnimation, FFMpegWriter

from flowtorch.data import FOAMDataloader, mask_box


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

if __name__ == "__main__":
    # path settings
    case = "Ma1.50"
    load_path = join("..", "run", "pressureWavePropagation", case)
    save_dir = join("..", "run", "pressureWavePropagation", "plots")

    # boundaries for plotting
    source_center = [100, 150]
    min_bounds = [source_center[0] - 25, source_center[1] - 25]
    max_bounds = [source_center[0] + 25, source_center[1] + 25]

    # free stream settings
    Ma = 1.50
    p0 = 101325
    p0_prime = 0.01 * p0

    # load the data
    write_times, xy, data = prepare_data(load_path, [min_bounds, max_bounds])

    # transform the bounds, so that the source is centered
    xy[:, 0] -= source_center[0]
    xy[:, 1] -= source_center[1]

    # subtract the initial pressure from the data matrix
    data -= p0

    # create plot directory
    if not exists(save_dir):
        makedirs(save_dir)

    # use latex fonts
    plt.rcParams.update({"text.usetex": True, "figure.dpi": 360})

    # make colorbar consistent with contour plot
    pressure_levels = pt.linspace(-p0_prime/p0 * 100, p0_prime/p0 * 100, 501)

    # animate flow field only
    fig, ax = plt.subplots(figsize=(6, 5))
    cf = ax.tricontourf(xy[:, 0], xy[:, 1], data[:, 0]/p0 * 100, cmap="seismic", levels=pressure_levels, extend="both")

    # colorbar settings
    cbar = fig.colorbar(cf, ax=ax, shrink=0.6)
    cbar.set_ticks(pt.linspace(-p0_prime/p0 * 100, p0_prime/p0 * 100, 9))
    cbar.set_label(r"$p^\prime \,/\,p_0~[\%]$")

    # animate
    def animate(i):
        print("\r", f"Creating frame {i + 1:03d} / {len(write_times)}", end="")
        # update flow field
        ax.clear()
        cf = ax.tricontourf(xy[:, 0], xy[:, 1], data[:, i]/p0 * 100, cmap="seismic", levels=pressure_levels, extend="both")
        ax.set_xlabel(r"$\tilde{x}$")
        ax.set_ylabel(r"$\tilde{y}$")
        ax.set_aspect("equal")
        ax.set_title(fr"$Ma_\infty = {Ma:.2f}$")

        return cf

    ax.set_xlabel(r"$\tilde{x}$")
    ax.set_ylabel(r"$\tilde{y}$")
    ax.set_aspect("equal")
    fig.tight_layout()

    ani = FuncAnimation(fig, animate, frames=data.shape[1], blit=False, repeat=True)
    writer = FFMpegWriter(fps=15)
    ani.save(join(save_dir, f"flow_field_animation_{case}.mp4"), writer=writer)
