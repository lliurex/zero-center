#!/usr/bin/env python3

from setuptools import setup

if __name__ == '__main__':
    setup(name='zeroinstallerhelper',
          version='0.1',
          description='Install zero-center files and generate pkexec configs for pkexec debhelper',
          long_description="""""",
          author='Raul Rodrigo Segura',
          author_email='raurodse@gmail.com',
          maintainer='Raul Rodrigo Segura',
          maintainer_email='raurodse@gmail.com',
          keywords=['software', 'debhelper'],
          url='https://github.com/edupals/zero-installer',
          license='GPL3',
          platforms='UNIX',
          packages=['edupals.zerocenter'],
          package_dir={'edupals.zerocenter':'zero-dev/src_debhelper'},
          scripts=['bin/dh_zeroinstaller'],
          data_files=[('/usr/share/perl5/Debian/Debhelper/Sequence/', ['zero-dev/Sequence/zero.pm'])]
         )
