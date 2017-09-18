# Copyright (c) Trainline Limited, 2016-2017. All rights reserved. See LICENSE.txt in the project root for license information.

import unittest
import os
import shutil
import tempfile
from os.path import join
from agent.tweaked_shutil import mergetree

def w(path, content):
    with open(path, 'w') as f:
        f.write(content)

def r(path):
    with open(path, 'r') as f:
        return f.read()

class TestCommonDeploymentStageUtils(unittest.TestCase):
    def test_it_overwrites_a_file_with_the_same_name(self):
        tmpdir = tempfile.mkdtemp()
        try:
            indir = join(tmpdir, 'input')
            outdir = join(tmpdir, 'output')
            os.makedirs(indir)
            w(join(indir, 'overwrite.txt'), 'success')
            os.makedirs(outdir)
            w(join(outdir, 'overwrite.txt'), 'should be overwritten')
            mergetree(indir, outdir)
            self.assertEqual(r(join(outdir, 'overwrite.txt')), 'success')
        finally:
            shutil.rmtree(tmpdir)
    def test_it_overwrites_a_file_with_a_dir_of_the_same_name(self):
        tmpdir = tempfile.mkdtemp()
        try:
            indir = join(tmpdir, 'input')
            outdir = join(tmpdir, 'output')
            os.makedirs(indir)
            os.makedirs(join(indir, 'overwrite'))
            os.makedirs(outdir)
            w(join(outdir, 'overwrite'), 'should be replaced by a dir')
            mergetree(indir, outdir)
            self.assertFalse(os.path.isfile(join(outdir, 'overwrite')))
            self.assertTrue(os.path.isdir(join(outdir, 'overwrite')))
        finally:
            shutil.rmtree(tmpdir)
    def test_it_does_not_modify_an_existing_file_without_a_name_collision(self):
        tmpdir = tempfile.mkdtemp()
        try:
            indir = join(tmpdir, 'input')
            outdir = join(tmpdir, 'output')
            os.makedirs(indir)
            os.makedirs(outdir)
            w(join(outdir, 'expected-file.txt'), 'success')
            mergetree(indir, outdir)
            self.assertTrue(os.path.isfile(join(outdir, 'expected-file.txt')))
        finally:
            shutil.rmtree(tmpdir)
    def test_it_appends_a_file_not_already_present(self):
        tmpdir = tempfile.mkdtemp()
        try:
            indir = join(tmpdir, 'input')
            outdir = join(tmpdir, 'output')
            os.makedirs(indir)
            w(join(indir, 'expected-file.txt'), 'success')
            os.makedirs(outdir)
            mergetree(indir, outdir)
            self.assertTrue(os.path.isfile(join(outdir, 'expected-file.txt')))
        finally:
            shutil.rmtree(tmpdir)
    def test_complex_scenario(self):
        tmpdir = tempfile.mkdtemp()
        try:
            indir = join(tmpdir, 'input')
            outdir = join(tmpdir, 'output')
            os.makedirs(join(indir, 'a'))
            os.makedirs(join(indir, 'c'))
            w(join(indir, 'a', 'a.txt'), 'a')
            w(join(indir, 'c', 'a.txt'), 'aca')
            w(join(indir, 'c', 'c.txt'), 'acc')
            os.makedirs(outdir)
            os.makedirs(join(outdir, 'b'))
            os.makedirs(join(outdir, 'c'))
            w(join(outdir, 'b', 'b.txt'), 'b')
            w(join(outdir, 'c', 'b.txt'), 'bcb')
            w(join(outdir, 'c', 'c.txt'), 'bcc')
            mergetree(indir, outdir)
            self.assertEqual(r(join(outdir, 'a', 'a.txt')), 'a')
            self.assertEqual(r(join(outdir, 'b', 'b.txt')), 'b')
            self.assertEqual(r(join(outdir, 'c', 'a.txt')), 'aca')
            self.assertEqual(r(join(outdir, 'c', 'b.txt')), 'bcb')
            self.assertEqual(r(join(outdir, 'c', 'c.txt')), 'acc')
        finally:
            shutil.rmtree(tmpdir)