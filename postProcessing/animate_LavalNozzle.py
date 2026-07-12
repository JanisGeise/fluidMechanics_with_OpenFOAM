"""
Create an animation of pressure wave propagation for the `LavalNozzle` setup.

The script loads pressure snapshots from a selected OpenFOAM case, masks the
domain around the pressure source, re-centers the coordinates, and writes an
MP4 animation of the normalized pressure fluctuation ``p' / p0``.
"""
import torch as pt
import matplotlib.pyplot as plt

from os import makedirs
from os.path import join, exists
from matplotlib.animation import FuncAnimation, FFMpegWriter
from matplotlib.patches import Polygon
from numpy import interp

from utils import prepare_data

def create_nozzle(points, n=100):
    """
    Create a nozzle polygon from five points.
    The first three points define a circular arc, the last two are appended.
    """
    p0, pm, p1, *rest = map(lambda p: pt.as_tensor(p, dtype=pt.float32), points)

    A = 2 * pt.stack((pm - p0, p1 - p0))
    b = pt.tensor([pm @ pm - p0 @ p0, p1 @ p1 - p0 @ p0])
    c = pt.linalg.solve(A, b)
    r = pt.linalg.norm(p0 - c)

    t0 = pt.atan2(p0[1] - c[1], p0[0] - c[0])
    tm = pt.atan2(pm[1] - c[1], pm[0] - c[0])
    t1 = pt.atan2(p1[1] - c[1], p1[0] - c[0])

    while tm < t0:
        tm += 2 * pt.pi
    while t1 < tm:
        t1 += 2 * pt.pi

    t = pt.linspace(t0, t1, n)
    arc = pt.stack((c[0] + r * pt.cos(t), c[1] + r * pt.sin(t)), dim=1)

    return pt.cat((arc, pt.stack(rest)))


if __name__ == "__main__":
    # path settings, adjust if necessary
    case = "LavalNozzle_rhoCentralFoam"
    load_path = join("..", "run", "LavalNozzle", case)
    save_dir = join("..", "run", "LavalNozzle", "plots")

    # boundaries for plotting
    len_nozzle = 10
    min_bounds = [0, 0]
    max_bounds = [2*len_nozzle, len_nozzle / 2]

    # pressure at inlet
    p0 = 1e5

    # pressure at outlet
    p_out = {"0.00": 8e4, "0.50": 8e4, "1.80": 1e4, "2.00": 1e4, "4.25": 1e3, "4.5": 1e3}

    # load the data
    write_times, xy, data = prepare_data(load_path, [min_bounds, max_bounds], field_name="Ma")
    write_times = pt.tensor(list(map(float, write_times)))

    # compress the data for GitHub
    # write_times = write_times[::2]
    # data = data[:, ::2]

    # define the nozzle geometry, interpolate the arc of the nozzle
    points = [(0, 0.85), (5, 0.5), (10, 0.85), (10, 0.9), (0, 0.9)]
    nozzle = create_nozzle(points) / len_nozzle

    # scale and mirror the nozzle
    nozzle_mirror = nozzle.clone()
    nozzle_mirror[:, 1] *= -1

    # merge at symmetry plane to avoid plotting artifacts at symmetry plane
    xy_mirror = xy.clone()
    xy_mirror[:, -1] *= -1
    xy = pt.cat([xy, xy_mirror], dim=0)
    data = pt.cat([data, data], dim=0)

    # interpolate outlet pressure to the write times
    times = pt.tensor([float(t) for t in p_out.keys()])
    pressures = pt.tensor(list(p_out.values()))
    idx = pt.argsort(times)
    p = interp(write_times.numpy(), times[idx].numpy(), pressures[idx].numpy())

    # create plot directory
    if not exists(save_dir):
        makedirs(save_dir)

    # use latex fonts
    plt.rcParams.update({"text.usetex": True, "figure.dpi": 360})

    # make colorbar consistent with contour plot
    vmin, vmax = 0, 3
    ma_levels = pt.linspace(vmin, vmax, 501)

    # animate flow field only
    fig, ax = plt.subplots(figsize=(6, 4))
    cf = ax.tricontourf(xy[:, 0] / len_nozzle, xy[:, 1] / len_nozzle, data[:, 0], cmap="plasma", levels=ma_levels,
                        extend="both", vmin=vmin, vmax=vmax)

    # add the nozzle patch
    ax.add_patch(Polygon(nozzle, facecolor="white"))
    ax.add_patch(Polygon(nozzle_mirror, facecolor="white"))

    # colorbar settings
    cbar = fig.colorbar(cf, ax=ax, shrink=0.6, orientation="horizontal", location="bottom")
    cbar.set_ticks(pt.linspace(vmin, vmax, 5))
    cbar.set_label(r"$Ma~[-]$")

    # animate
    def animate(i):
        print("\r", f"Creating frame {i + 1:03d} / {len(write_times)}", end="")
        # update flow field
        ax.clear()
        cf = ax.tricontourf(xy[:, 0] / len_nozzle, xy[:, 1] / len_nozzle, data[:, i], cmap="plasma", levels=ma_levels,
                            extend="both", vmin=vmin, vmax=vmax)
        ax.add_patch(Polygon(nozzle, facecolor="white"))
        ax.add_patch(Polygon(nozzle_mirror, facecolor="white"))

        ax.set_xlabel(r"$x / L$")
        ax.set_ylabel(r"$y / L$")
        ax.set_xlim(0, 2)
        ax.set_ylim(-0.4, 0.4)
        ax.set_aspect("equal")
        ax.set_title(r"$p_\mathrm{out} / p_0 = $" + f"${(p[i] / p0):.2f}$")

        return cf

    ax.set_xlabel(r"$x / L$")
    ax.set_ylabel(r"$y / L$")
    ax.set_xlim(0, 2)
    ax.set_ylim(-0.4, 0.4)
    ax.set_aspect("equal")
    fig.tight_layout()

    ani = FuncAnimation(fig, animate, frames=data.shape[1], blit=False, repeat=True)
    writer = FFMpegWriter(fps=15)
    ani.save(join(save_dir, f"LavalNozzle_animation_{case}.mp4"), writer=writer)
