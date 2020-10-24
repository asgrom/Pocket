from setuptools import setup

setup(
    name='pocket_articles',
    version='0.0.1',
    packages=['pocket_articles'],
    url='',
    license='',
    author='Alexandr Gromkov',
    author_email='',
    description='',
    entry_points={
        'console_scripts': [
            'pocket-qt = pocket_articles.core:main'
        ]
    }, install_requires=['lxml', 'dateutil']
)
