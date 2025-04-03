from setuptools import setup, find_packages

setup(
    name="brigade_accounting",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        'customtkinter>=5.1.3',
        'pandas>=1.5.0',
        'reportlab>=4.0.0',
        'python-dateutil>=2.8.2'
    ],
    entry_points={
        'console_scripts': [
            'brigade-accounting=app.main:main'
        ]
    }
)