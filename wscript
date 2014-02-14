#! /usr/bin/env python
# encoding: utf-8

import os

APPNAME = 'external-benchmarks'
VERSION = '0.1.0'

def recurse_helper(ctx, name):
    if not ctx.has_dependency_path(name):
        ctx.fatal('Load a tool to find %s as system dependency' % name)
    else:
        p = ctx.dependency_path(name)
        ctx.recurse([p])


def options(opt):

    import waflib.extras.wurf_dependency_bundle as bundle
    import waflib.extras.wurf_dependency_resolve as resolve
    import waflib.extras.wurf_configure_output

    bundle.add_dependency(opt,
        resolve.ResolveGitMajorVersion(
            name = 'waf-tools',
            git_repository = 'github.com/steinwurf/external-waf-tools.git',
            major_version = 2))

    bundle.add_dependency(opt,
        resolve.ResolveGitMajorVersion(
            name = 'boost',
            git_repository = 'github.com/steinwurf/external-boost-light.git',
            major_version = 1))

    bundle.add_dependency(opt,
        resolve.ResolveGitMajorVersion(
            name = 'gauge',
            git_repository = 'github.com/steinwurf/cxx-gauge.git',
            major_version = 7))

    bundle.add_dependency(opt,
        resolve.ResolveGitMajorVersion(
            name = 'tables',
            git_repository = 'github.com/steinwurf/tables.git',
            major_version = 4))

    opt.load('wurf_dependency_bundle')
    opt.load('wurf_tools')

def configure(conf):

    if conf.is_toplevel():

        conf.load('wurf_dependency_bundle')
        conf.load('wurf_tools')

        conf.load_external_tool('mkspec', 'wurf_cxx_mkspec_tool')
        conf.load_external_tool('runners', 'wurf_runner')
        conf.load_external_tool('install_path', 'wurf_install_path')
        conf.load_external_tool('project_gen', 'wurf_project_generator')

        recurse_helper(conf, 'boost')
        recurse_helper(conf, 'gauge')
        recurse_helper(conf, 'tables')

    set_simd_flags(conf)

def set_simd_flags(conf):
    """
    Sets flags used to compile in SIMD mode
    """
    CC = conf.env.get_flat("CC")
    flags = []
    defines = []

    if 'gcc' in CC or 'clang' in CC:
        flags += ['-O3', '-fPIC']
        flags += conf.mkspec_try_flags('cflags',
                    ['-mmmx', '-msse', '-msse2', '-msse3', '-mpclmul',
                     '-mssse3', '-msse4.1', '-msse4.2', '-mavx'])

        if '-msse' in flags: defines.append('INTEL_SSE')
        if '-msse2' in flags: defines.append('INTEL_SSE2')
        if '-msse3' in flags: defines.append('INTEL_SSE3')
        if '-mpclmul' in flags: defines.append('INTEL_SSE4_PCLMUL')
        if '-mssse3' in flags: defines.append('INTEL_SSSE3')
        if '-msse4.1' in flags: defines.append('INTEL_SSE4')
        if '-msse4.2' in flags: defines.append('INTEL_SSE4')

    elif 'CL.exe' in CC or 'cl.exe' in CC:
        pass

    else:
        conf.fatal('Unknown compiler - no SIMD flags specified')

    conf.env['CFLAGS_SIMD_SHARED'] = flags
    conf.env['CXXFLAGS_SIMD_SHARED'] = flags
    conf.env['DEFINES_SIMD_SHARED'] = defines

def build(bld):

    if '-O2' in bld.env['CFLAGS']:
        bld.env['CFLAGS'].remove('-O2')

    bld.stlib(
          features        = 'c',
          source          = bld.path.ant_glob('gf-complete/src/**/*.c'),
          target          = 'gf_complete',
          includes        = ['gf-complete/include'],
          export_includes = ['gf-complete/include'],
          use             = ['SIMD_SHARED'])

    bld.stlib(
          features        = 'c',
          source          = bld.path.ant_glob('jerasure/src/**/*.c',
                            excl = 'jerasure/src/cauchy_best_r6.c'),
          target          = 'jerasure',
          includes        = ['jerasure/include'],
          export_includes = ['jerasure/include'],
          use             = ['SIMD_SHARED', 'gf_complete'])

    if bld.is_toplevel():

        bld.load('wurf_dependency_bundle')

        recurse_helper(bld, 'boost')
        recurse_helper(bld, 'gauge')
        recurse_helper(bld, 'tables')

        # Only build test and benchmarks when executed from the
        # top-level wscript i.e. not when included as a dependency
        # in a recurse call

        bld.recurse('benchmark/jerasure_throughput')




