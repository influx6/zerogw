#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from waflib import Utils, Options
from waflib.Build import BuildContext
from waflib.Scripting import Dist
import subprocess
import os.path

APPNAME='zerogw'
if os.path.exists('.git'):
    VERSION=subprocess.getoutput('git describe').lstrip('v').replace('-', '_')
else:
    VERSION='0.5.20'

top = '.'
out = 'build'

def options(opt):
    opt.load('compiler_c')

def configure(conf):
    conf.load('compiler_c')

def build(bld):
    import coyaml.waf
    bld(
        features     = ['c', 'cprogram', 'coyaml'],
        source       = [
            'src/config.yaml',
            'src/main.c',
            'src/log.c',
            'src/websocket.c',
            'src/sieve.c',
            'src/zutils.c',
            'src/http.c',
            'src/resolve.c',
            'src/uidgen.c',
            'src/request.c',
            'src/polling.c',
            'src/disk.c',
            'src/commands.c',
            'src/pool.c',
            'src/msgqueue.c',
            ],
        target       = 'zerogw',
        includes     = ['src'],
        defines      = [
            'LOG_STRIP_PATH="../src/"',
            ],
        cflags      = ['-std=gnu99'],
        lib          = ['coyaml', 'yaml', 'zmq', 'ev', 'website', 'crypto'],
        )
    bld(
        features     = ['c', 'cprogram', 'coyaml'],
        source       = [
            'src/config.yaml',
            'src/zerogwctl.c',
            ],
        target       = 'zerogwctl',
        includes     = ['src'],
        cflags       = ['-std=gnu99'],
        lib          = ['coyaml', 'yaml', 'zmq'],
        )
    bld(
        features    = ['c', 'cprogram'],
        source      = 'src/openport.c',
        target      = 'openport',
        )

    if bld.env['PREFIX'] == '/usr':
        bld.install_files('/etc', ['examples/zerogw.yaml'])
    else:
        bld.install_files('${PREFIX}/etc', ['examples/zerogw.yaml'])

def dist(ctx):
    ctx.excl = [
        'doc/_build/**',
        '.waf*', '*.tar.bz2', '*.zip', 'build',
        '.git*', '.lock*', '**/*.pyc', '**/*.swp', '**/*~'
        ]
    ctx.algo = 'tar.bz2'

def make_pkgbuild(task):
    import hashlib
    task.outputs[0].write(Utils.subst_vars(task.inputs[0].read(), {
        'VERSION': VERSION,
        'DIST_MD5': hashlib.md5(task.inputs[1].read('rb')).hexdigest(),
        }))

def archpkg(ctx):
    from waflib import Options
    Options.commands = ['dist', 'makepkg'] + Options.commands

def build_package(bld):
    distfile = APPNAME + '-' + VERSION + '.tar.bz2'
    bld(rule=make_pkgbuild,
        source=['PKGBUILD.tpl', distfile, 'wscript'],
        target='PKGBUILD')
    bld(rule='cp ${SRC} ${TGT}', source=distfile, target='.')
    bld.add_group()
    bld(rule='makepkg -f', source=distfile)
    bld.add_group()
    bld(rule='makepkg -f --source', source=distfile)

class makepkg(BuildContext):
    cmd = 'makepkg'
    fun = 'build_package'
    variant = 'archpkg'

def build_tests(bld):
    build(bld)
    bld.add_group()
    bld(rule='cd ${SRC[0].parent.parent.abspath()};'
        'export BUILDDIR=${SRC[1].parent.abspath()};'
        'python -m unittest discover -s test -p "*.py" -t . -v',
        source=['test/simple.py', 'zerogw'],
        always=True)

class test(BuildContext):
    cmd = 'test'
    fun = 'build_tests'
