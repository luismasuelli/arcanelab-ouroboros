from setuptools import setup, find_packages

setup(
    name='arcanelab-ouroboros',
    version='0.0.1',
    namespace_packages=['arcanelab'],
    packages=find_packages(exclude=['ouroboros_proj', 'ouroboros_proj.*', 'sample', 'sample.*']),
    package_data={
        'arcanelab.ouroboros': [
            'locale/*/LC_MESSAGES/*.*'
        ]
    },
    url='https://github.com/luismasuelli/arcanelab-ouroboros',
    license='LGPL',
    author='Luis y Anita',
    author_email='luismasuelli@hotmail.com',
    description='Workflow library for Django',
    install_requires=['Django>=1.7', 'python-cantrips>=0.7.3', 'django-trackmodels-ritual>=0.0.11']
)