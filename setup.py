from setuptools import setup, find_packages

setup(
    name='carta_controle',
    version='1.0',
    packages=find_packages(),
    include_package_data=True,
    package_data={
        '': ['fonts/*'],
    },
    install_requires=[
        'streamlit',
        'pandas',
        'numpy',
        'plotly',
        'fpdf',
    ],
)