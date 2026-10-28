"""Aggregate approximate map cells after the dashboard's shared filters."""
import pandas as pd

CELL_DEGREES = 0.01


def heatmap_cells(frame):
    """Return counts per ~1 km cell, excluding rows without usable coordinates."""
    if not {'map_lat', 'map_lon'}.issubset(frame.columns):
        return pd.DataFrame(columns=['map_lat', 'map_lon', 'offense_rows'])
    valid = frame.loc[frame['valid_coordinates'].fillna(False)].dropna(subset=['map_lat', 'map_lon'])
    return valid.groupby(['map_lat', 'map_lon'], observed=True).size().rename('offense_rows').reset_index()


def map_cell_polygons(cells):
    """Create count-colored grid polygons without exposing individual locations."""
    if cells.empty:
        return []
    maximum = int(cells.offense_rows.max())
    output = []
    for row in cells.itertuples(index=False):
        lat, lon = float(row.map_lat), float(row.map_lon)
        half = CELL_DEGREES / 2
        fraction = (int(row.offense_rows) / maximum) ** 0.5
        gold, cardinal = (255, 204, 0), (153, 0, 0)
        color = [round(a + (b-a)*fraction) for a,b in zip(gold, cardinal)] + [195]
        output.append({'polygon': [[lon-half,lat-half],[lon+half,lat-half],
                                   [lon+half,lat+half],[lon-half,lat+half]],
                       'offense_rows': int(row.offense_rows), 'color': color})
    return output
