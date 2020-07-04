import argparse
from itertools import takewhile
from math import degrees, pi, radians
from typing import Dict, List, Tuple

import gpxpy
import matplotlib.pyplot as plt
import numpy as np
from gpxpy import geo


def arguments():
    parser = argparse.ArgumentParser(description="Plot bearings of gpx track on radar chart")
    parser.add_argument("--gpx", "-g", help="gpx file")
    parser.add_argument(
        "--segments", "-s", help="number of segments", type=int, default="16",
    )
    parser.add_argument("--north", "-n", help="north align segment border", action="store_true")
    return parser.parse_args()


def get_distances_per_degree(gpx, segments: float) -> Dict[float, float]:
    distance_per_degree: Dict[float, float] = {}
    for track in gpx.tracks:
        for segment in track.segments:
            for prev, cur in zip(segment.points, segment.points[1:]):
                distance = geo.haversine_distance(
                    prev.latitude, prev.longitude, cur.latitude, cur.longitude
                )
                bearing_degree = geo.get_course(
                    prev.longitude, prev.latitude, cur.longitude, cur.latitude
                )
                distance_per_degree[bearing_degree] = (
                    distance_per_degree.get(bearing_degree, 0) + distance / 1000
                )
    return distance_per_degree


def get_offset(align_north: bool, segments: int) -> float:
    if align_north:
        return 180 / segments
    return 0


def get_ranges(segments: int, offset: float) -> List:
    ranges = [
        (x + offset + 360) % 360
        for x in np.linspace(start=0, stop=360, num=segments, endpoint=False)
    ]
    return list(zip(ranges, ranges[1:]))


def get_values_and_angles(
    ranges: List, distance_per_degree: dict, offset: float
) -> Tuple[List, List]:
    data: Dict[float, float] = {}
    default_y = (ranges[-1][1] + ((ranges[0][0] + ranges[0][1]) / 2) + 360 - offset) % 360
    for k, v in distance_per_degree.items():
        y = radians(
            next((((x[0] + x[1]) / 2) for x in ranges if x[0] <= k and x[1] > k), default_y,)
        )
        data[y] = data.get(y, 0.0) + v

    data = dict(sorted(data.items()))

    angles = list(data.keys())
    angles += angles[:1]

    values = list(data.values())
    values += values[:1]
    return values, angles


def plot_chart(values: List, angles: List, title: str) -> None:
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    lines, labels = plt.thetagrids(range(0, 360, 45), ("E", "NE", "N", "NW", "W", "SW", "S", "SE"))
    ax.plot(angles, values, color="violet", linewidth=2)
    ax.fill(angles, values, "b", alpha=0.1)
    plt.title(title)
    plt.show()


if __name__ == "__main__":
    args = arguments()

    with open(args.gpx, "r") as gpx_file:
        gpx = gpxpy.parse(gpx_file)

    distance_per_degree = get_distances_per_degree(gpx, args.segments)
    offset = get_offset(args.north, args.segments)
    ranges = get_ranges(args.segments, offset)
    values, angles = get_values_and_angles(ranges, distance_per_degree, offset)
    plot_chart(values, angles, f"{gpx.tracks[0].name} ({args.segments} segments)")
