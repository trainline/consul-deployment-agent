# Copyright (c) Trainline Limited, 2016-2017. All rights reserved. See LICENSE.txt in the project root for license information.

import unittest
from agent.retention_policy import get_directories_to_delete

class Fake(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

class TestRetentionPolicy(unittest.TestCase):
    def test_get_directories_to_delete_returns_empty_when_given_no_dirs(self):
        actual = get_directories_to_delete(Fake(), [])
        expected = []
        self.assertItemsEqual(actual, expected)
    def test_get_directories_to_delete_retains_the_n_most_recent_directories_when_none_protected(self):
        actual = get_directories_to_delete(Fake(), [
            ('/a/b', Fake(st_ctime=1L)),
            ('/a/c', Fake(st_ctime=3L)),
            ('/a/d', Fake(st_ctime=0L)),
            ('/a/e', Fake(st_ctime=2L))
        ], retain=2)
        expected = ['/a/b', '/a/d']
        self.assertItemsEqual(actual, expected)
    def test_get_directories_to_delete_retains_the_protected_directories_without_retention_limit(self):
        actual = get_directories_to_delete(Fake(dir='/a/d', last_dir='/a/b'), [
            ('/a/b', Fake(st_ctime=1L)),
            ('/a/c', Fake(st_ctime=3L)),
            ('/a/d', Fake(st_ctime=0L)),
            ('/a/e', Fake(st_ctime=2L))
        ])
        expected = ['/a/c', '/a/e']
        self.assertItemsEqual(actual, expected)
    def test_get_directories_to_delete_retains_the_protected_directories_and_the_latest_with_retention_limit(self):
        actual = get_directories_to_delete(Fake(dir='/a/b', last_dir='/a/c'), [
            ('/a/b', Fake(st_ctime=1L)),
            ('/a/c', Fake(st_ctime=3L)),
            ('/a/d', Fake(st_ctime=0L)),
            ('/a/e', Fake(st_ctime=2L))
        ], retain=3)
        expected = ['/a/d']
        self.assertItemsEqual(actual, expected)
    def test_get_directories_to_delete_retains_the_found_protected_directories_and_the_latest_with_retention_limit(self):
        actual = get_directories_to_delete(Fake(dir='/b/d', last_dir='/b/b'), [
            ('/a/b', Fake(st_ctime=1L)),
            ('/a/c', Fake(st_ctime=3L)),
            ('/a/d', Fake(st_ctime=0L)),
            ('/a/e', Fake(st_ctime=2L))
        ], retain=2)
        expected = ['/a/b', '/a/d']
        self.assertItemsEqual(actual, expected)