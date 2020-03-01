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
          'requests',
          'PySocks',
          'boto3'
      ],
      scripts=['scripts/spiderRDAP', 'scripts/spiderRDAPAWSTest'],
      zip_safe=False)
