import pytest
import tempfile
import os, sys
from astropy.utils.data import download_file
from .. import astrodb
from sqlite3 import IntegrityError
import io

filename = os.path.join(tempfile.mkdtemp(), 'empty_db.db')


def setup_module(module):
    try:
        db_path = download_file("http://github.com/BDNYC/BDNYCdb/raw/master/bdnyc_database.db")
    except:
        db_path = download_file("http://github.com/BDNYC/BDNYCdb/raw/master/BDNYCv1.0.db")
    module.bdnyc_db = astrodb.Database(db_path)
    astrodb.create_database(filename)
    module.empty_db = astrodb.Database(filename)


def test_load_bdnyc():
    print(bdnyc_db)
    assert not isinstance(bdnyc_db, type(None))


def test_load_empty():
    print(empty_db)
    assert not isinstance(empty_db, type(None))


def test_search(): 
    bdnyc_db.search('2MASS', 'sources')


def test_inventory():
    bdnyc_db.inventory(1)


def test_sqlquery():
    bdnyc_db.query("SELECT s.id, s.ra, s.dec, s.shortname, p.source_id, p.band, p.magnitude "
        "FROM sources as s JOIN photometry as p ON s.id=p.source_id "
        "WHERE s.dec<=-10 AND p.band=='W1'")


def test_schema():
    bdnyc_db.schema('sources')
    empty_db.schema('sources')


def test_table():
    columns = ['id', 'ra', 'dec', 'shortname', 'source_id']
    types = ['INTEGER', 'REAL', 'REAL', 'TEXT', 'INTEGER']
    constraints = ['NOT NULL UNIQUE', '', '', '', '']
    empty_db.table('new_sources', columns, types, constraints, new_table=True)
    t = empty_db.query("PRAGMA table_info(new_sources)", fmt='table')
    print(t)
    assert sorted(columns) == sorted(t['name'])


def test_add_data_empty():
    t1 = empty_db.query('SELECT * FROM sources', fmt='array')

    if isinstance(t1, type(None)):
        len_t1 = 0
    else:
        len_t1 = len(t1)

    data = list()
    data.append(['ra', 'dec', 'shortname', 'comments'])
    data.append([12, -12, 'fakesource', ''])
    empty_db.add_data(data, 'sources', verbose=True)

    t2 = empty_db.query('SELECT * FROM sources', fmt='array')
    assert len(t2) == len_t1 + 1


def test_new_ids():
    available = bdnyc_db._lowest_rowids('sources', 10)
    t = bdnyc_db.query('SELECT id FROM sources')
    assert available not in t


def test_add_foreign_key():
    empty_db.add_foreign_key('new_sources', ['sources'], ['source_id'], ['id'])


def test_foreign_key_support():
    data = list()
    data.append(['ra', 'dec', 'shortname', 'source_id'])
    data.append([12, -12, 'fakesource', 9999])
    with pytest.raises(IntegrityError):
        empty_db.add_data(data, 'new_sources')  # Foreign key error expected


def test_lookup():
    bdnyc_db.lookup([1, '2MASS'], 'sources')


def test_clean_up(monkeypatch):
    data = list()
    data.append(['ra', 'dec', 'shortname', 'source_id'])
    data.append([12, -12, 'fakesource', 1])
    data.append([12, -12, 'fakesource2', 1])

    # Fake user input
    inputs = ['r', 'y']
    input_generator = (i for i in inputs)
    monkeypatch.setattr('astrodbkit.astrodb.get_input', lambda prompt: next(input_generator))

    empty_db.add_data(data, 'new_sources', verbose=True)  # This internally calls clean_up

    t = empty_db.query('SELECT * FROM new_sources', fmt='table')
    assert len(t) == 1


@pytest.mark.xfail
def test_merge():
    empty_db.modify('DROP TABLE new_sources')
    bdnyc_db.merge(filename, 'sources')
    assert False

@pytest.mark.xfail
def test_output_spectrum():
    assert False

@pytest.mark.xfail
def test_plot_spectrum():
    assert False
