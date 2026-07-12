"""
Create an animation of pressure wave propagation for the `pressureWavePropagation` setup.

The script loads pressure snapshots from a selected OpenFOAM case, masks the
domain around the pressure source, re-centers the coordinates, and writes an
MP4 animation of the normalized pressure fluctuation ``p' / p0``.
"""
import torch as pt
import matplotlib.pyplot as plt

from os import makedirs
from os.path import join, exists
from matplotlib.animation import FuncAnimation, FFMpegWriter

from utils import prepare_data


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
    ani.save(join(save_dir, f"wave_animation_{case}.mp4"), writer=writer)
