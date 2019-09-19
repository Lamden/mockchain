from setuptools import setup

setup(
    name='mockchain',
    version='0.1',
    packages=['tests', 'mockchain', 'mockchain.contracts', 'mockchain.contracts.genesis'],
    url='https://github.com/lamden/mockchain',
    license='Creative Commons Non-Commercial',
    author='Lamden',
    author_email='team@lamden.io',
    description='A special Lamden blockchain instance that behaves like the regular network, but is self-hosted and flexible so that it can be used for development and testing.'
)
