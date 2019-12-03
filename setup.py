from setuptools import setup

setup(name='SpiderRDAP',
      version='0.1',
      description='SpiderRDAP',
      url='http://github.com/gakiwate/SpiderRDAP',
      author='Gautam Akiwate',
      author_email='gakiwate@cs.ucsd.edu',
      license='GPLv2',
      packages=['spider_rdap'],
      install_requires=[
          'requests'
      ],
      scripts=[],
      zip_safe=False)