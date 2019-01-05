#! /usr/bin/env python
# -*- encoding:utf-8 -*-
# FileName: archlinux.py

"This file is part of ____"
 
__author__   = "yetist"
__copyright__= "Copyright (C) 2018 Wu Xiaotian <yetist@gmail.com>"
__license__  = """
This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with this program; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""
import os
import requests
import subprocess
import io
import tarfile

def http_get(url):
    resp = requests.get(url)
    if resp.status_code == 200:
        return resp.content
    else:
        return b''

def download_file(url, filename):
    print('saving file %s' % filename)
    data = http_get(url)
    fd = open(filename, 'wb+')
    fd.write(data)
    fd.close()

def save_mate_release(basename, version='1.21', outdir='.'):
    saved_path = os.path.join(outdir, basename)
    if os.path.isfile(saved_path):
        return
    baseurl = 'http://pub.mate-desktop.org/releases'
    url = 'http://pub.mate-desktop.org/releases/%s/%s' % (version, basename)
    download_file(url, saved_path)

def get_last_release(name='SHA1SUMS'):
    packages = {}

    if not os.path.isfile(name):
        save_mate_release(name)

    content = open(name).read()
    for line in content.splitlines():
        lines = line.split('\t')
        pkgs = lines[1].rsplit('-',  1)
        sums = lines[0]
        name = pkgs[0]
        version = pkgs[1].rstrip('tar.xz')
        packages[name] = [version, sums]
    return packages

def extract(data, include, target_path):
    try:
        tar = tarfile.open(mode= "r:gz", fileobj = io.BytesIO(data))
        members = tar.getmembers()
        for m in members:
            if m.name.find(include) > 0:
                m.name=os.path.basename(m.name)
                tar.extract(m, target_path)
        tar.close()
    except Exception as e:
        print(e)

def download_srcpkg(name):
    dirname = name
    maps = {
            "caja-extensions" : "caja-extensions-common",
            }
    if name in maps:
        name = maps[name]
    cmdline = "pacman -S -p --print-format %r " + name
    try:
        pkgrepo = subprocess.check_output(cmdline.split())
    except:
        print("pkg %s error\n" % name)
        return
    repo = pkgrepo.decode("utf-8").split()[0]
    if repo == "core" or repo == "extra" or repo == "testing":
        url = "https://git.archlinux.org/svntogit/packages.git/snapshot/packages/%s.tar.gz" % name
    else:
        url = "https://git.archlinux.org/svntogit/community.git/snapshot/community-packages/%s.tar.gz" % name
    data = http_get (url)
    if len(data) > 100:
        extract(data, "/%s/trunk/" % name, dirname)

def build_pkgbuild(name, version):
    pkgfile = os.path.join("%s/PKGBUILD" % name)
    if not os.path.isfile(pkgfile):
        print("WARNING: not found %s" % pkgfile)
        return
    newlines = []
    lines = open(pkgfile).read().splitlines()
    for line in lines:
        if line.startswith("pkgver="):
            newlines.append("pkgver=%s" % version)
        elif line.startswith("pkgrel="):
            newlines.append("pkgrel=1")
        else:
            newlines.append(line)
    fp = open(pkgfile, "w+")
    fp.write("\n".join(newlines))
    fp.close()
    cwd = os.getcwd()
    os.chdir(name)
    os.system("makepkg -cirsL --skipchecksums --noconfirm")
    os.chdir(cwd)

def update_packages():
    packages = get_last_release()

    for i in packages:
        if not os.path.isdir(i):
            os.mkdir(i)
        download_srcpkg(i)
        version = packages[i][0]
        tarball = "%s-%s.tar.xz" % (i, version)
        save_mate_release(tarball, outdir = i)
        build_pkgbuild(i, version)

if __name__=="__main__":
    update_packages()
