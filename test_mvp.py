from pathlib import Path
from unittest.mock import patch
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest
import backend_analysis as b


def fixture():
    return b.enrich_data(pd.DataFrame({
        'CaseNo': ['A','A','B','C'], 'Date_Occurred':['2026-10-19']*4,
        'Time_Occurred':[100,800,1400,2000], 'Area_Name':['Central']*3+['West LA'],
        'Report_District_No':['0101','0101','0102','0901'],
        'Premise_Description':['STREET']*4, 'NIBR Description':['TEST']*4,
        'Transit-related Crime':['Yes','No','No','No'],
        'Domestic Violence Crime':['No']*4, 'Homeless-Victim Crime':['No']*4,
        'valid_coordinates':[True,False,True,False],
    }), 'nibrs')


def loader(path, dataset):
    x=fixture()
    if dataset=='legacy':
        x=x.rename(columns={'CaseNo':'DR_NO'})
        x['Crime_Description']='TEST'
    return x


def widget(app, kind, label):
    return next(w for w in getattr(app,kind) if w.label==label)


def number(app,label):
    return int(widget(app,'metric',label).value.replace(',',''))


def test_separated_blocks_and_coordinate_denominator():
    x=fixture()
    y=b.apply_filters(x,b.FilterSpec(time_blocks=['Morning','Evening']))
    assert y.occurrence_hour.tolist()==[8,20]
    assert b.apply_filters(x,b.FilterSpec(time_blocks=[])).empty
    y=b.apply_filters(x,b.FilterSpec(valid_coordinates_only=True))
    assert len(y)==4
    assert len(b.geographic_subset(y,True))==2
    assert b.nibrs_headline_metrics(y)['valid_coordinate_share']==0.5


def test_district_identifiers_preserve_zeros():
    x=fixture()
    y=b.apply_filters(x,b.FilterSpec(districts=['0101']))
    assert len(y)==2
    queue=b.build_review_queue(y)
    assert queue.iloc[0].Report_District_No=='0101'
    assert queue.iloc[0].offense_rows==2


def test_widgets_reset_queue_remove_and_empty():
    with patch.object(b,'load_clean_data',side_effect=loader):
        app=AppTest.from_file(str(Path(__file__).with_name('dashboard.py'))).run(timeout=30)
        assert not app.exception
        assert number(app,'Selected offense rows')==4
        widget(app,'multiselect','Area').set_value(['Central']).run()
        widget(app,'multiselect','Time-of-day block').set_value(['Morning','Evening']).run()
        assert number(app,'Selected offense rows')==1
        widget(app,'button','Reset filters').click().run()
        assert number(app,'Selected offense rows')==4
        assert widget(app,'multiselect','Area').value==['Central','West LA']
        assert len(widget(app,'multiselect','Time-of-day block').value)==4
        widget(app,'checkbox','Valid coordinates only').check().run()
        assert number(app,'Selected offense rows')==4
        assert widget(app,'metric','Valid-coordinate coverage').value=='50.0%'
        widget(app,'multiselect','Choose a district to add').set_value(['0101']).run()
        widget(app,'button','Add selected district(s)').click().run()
        assert not app.exception
        queue=app.session_state['queue']
        assert len(queue)==1 and queue[0]['Report_District_No']=='0101'
        assert queue[0]['offense_rows']==2
        assert 'LAT' not in queue[0] and 'LON' not in queue[0]
        widget(app,'button','Add selected district(s)').click().run()
        assert len(app.session_state['queue'])==1
        widget(app,'multiselect','Districts to remove').set_value(['0101']).run()
        widget(app,'button','Remove selected districts').click().run()
        assert not app.exception and not app.session_state['queue']
        widget(app,'multiselect','Area').set_value([]).run()
        assert not app.exception
        assert number(app,'Selected offense rows')==0
        assert any('No records match' in w.value for w in app.warning)
        widget(app,'button','Reset filters').click().run()
        assert number(app,'Selected offense rows')==4


def test_all_filter_defaults_reset():
    with patch.object(b,'load_clean_data',side_effect=loader):
        app=AppTest.from_file(str(Path(__file__).with_name('dashboard.py'))).run(timeout=30)
        widget(app,'multiselect','Day').set_value(['Tuesday']).run()
        widget(app,'multiselect','Offense').set_value(['TEST']).run()
        widget(app,'multiselect','Premise').set_value(['STREET']).run()
        widget(app,'multiselect','Context').set_value(['transit']).run()
        widget(app,'radio','Context logic').set_value('AND').run()
        widget(app,'checkbox','Limit occurrence dates').check().run()
        widget(app,'checkbox','Valid coordinates only').check().run()
        widget(app,'button','Reset filters').click().run()
        assert not app.exception
        assert number(app,'Selected offense rows')==4
        assert widget(app,'multiselect','Context').value==[]
        assert widget(app,'multiselect','Offense').value==[]
        assert widget(app,'multiselect','Premise').value==[]
        assert widget(app,'radio','Context logic').value=='OR'
        assert not widget(app,'checkbox','Limit occurrence dates').value
        assert not widget(app,'checkbox','Valid coordinates only').value
