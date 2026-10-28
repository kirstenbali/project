import pandas as pd
from backend_analysis import FilterSpec, apply_filters
from map_analysis import heatmap_cells, map_cell_polygons
from test_mvp import fixture


def test_map_respects_date_hour_and_area_filters_and_counts_rows():
    frame = fixture()
    frame['map_lat'] = [34.055,34.055,34.065,34.075]
    frame['map_lon'] = [-118.255]*4
    frame.loc[1,'valid_coordinates'] = True
    cells = heatmap_cells(frame)
    assert int(cells.offense_rows.sum()) == 3
    assert int(cells.offense_rows.max()) == 2  # Repeated cases remain offense rows.
    selected = apply_filters(frame, FilterSpec(areas=['Central'],start_date='2026-10-19',end_date='2026-10-19',start_hour=8,end_hour=14))
    assert int(heatmap_cells(selected).offense_rows.sum()) == 2
    assert heatmap_cells(apply_filters(frame, FilterSpec(start_date='2026-10-20'))).empty
    polygons = map_cell_polygons(cells)
    assert sum(p['offense_rows'] for p in polygons) == 3
    assert all(set(p)=={'polygon','offense_rows','color'} for p in polygons)


def test_map_missing_coordinates_and_empty_selection():
    frame=fixture()
    assert heatmap_cells(frame).empty
    frame['map_lat']=[None]*4
    frame['map_lon']=[None]*4
    assert heatmap_cells(frame).empty
    assert map_cell_polygons(heatmap_cells(frame)) == []
