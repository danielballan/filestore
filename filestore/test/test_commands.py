from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import six
import numpy as np
import uuid
import itertools

from filestore.api import (insert_resource, insert_datum, retrieve,
                           register_handler, deregister_handler,
                           bulk_insert_datum)
from filestore.core import DatumNotFound
from filestore.utils.testing import fs_setup, fs_teardown
from numpy.testing import assert_array_equal
from nose.tools import assert_raises

from .t_utils import SynHandlerMod
import pymongo.errors


def setup():
    fs_setup()
    # register the dummy handler to use
    register_handler('syn-mod', SynHandlerMod)


def teardown():
    fs_teardown()
    deregister_handler('syn-mod')


def _insert_syn_data(f_type, shape, count):
    fb = insert_resource(f_type, None, {'shape': shape})
    ret = []
    res_map_cycle = itertools.cycle((lambda x: x,
                                     lambda x: x['id'],
                                     lambda x: str(x['id'])))
    for k, rmap in zip(range(count), res_map_cycle):
        r_id = str(uuid.uuid4())
        insert_datum(rmap(fb), r_id, {'n': k + 1})
        ret.append(r_id)
    return ret


def _insert_syn_data_bulk(f_type, shape, count):
    fb = insert_resource(f_type, None, {'shape': shape})
    d_uid = [str(uuid.uuid4()) for k in range(count)]
    d_kwargs = [{'n': k + 1} for k in range(count)]
    bulk_insert_datum(fb, d_uid, d_kwargs)

    return d_uid


def _rt_helper(func):
    shape = (25, 32)
    mod_ids = func('syn-mod', shape, 10)

    for j, r_id in enumerate(mod_ids):
        data = retrieve(r_id)
        known_data = np.mod(np.arange(np.prod(shape)), j + 1).reshape(shape)
        assert_array_equal(data, known_data)


def test_round_trip():
    yield _rt_helper, _insert_syn_data
    yield _rt_helper, _insert_syn_data_bulk


def test_non_exist():
    assert_raises(DatumNotFound, retrieve, 'aardvark')


def test_non_unique_fail():
    shape = (25, 32)
    fb = insert_resource('syn-mod', None, {'shape': shape})
    r_id = str(uuid.uuid4())
    insert_datum(str(fb['id']), r_id, {'n': 0})
    assert_raises(pymongo.errors.DuplicateKeyError,
                  insert_datum, str(fb['id']), r_id, {'n': 1})
