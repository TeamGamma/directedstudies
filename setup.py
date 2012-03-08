from setuptools import setup, find_packages

setup(
    name='sps',
    version='0.0.1',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'sps_transaction_server = sps.transactions.server:main',
            'sps_web_server = sps.web.app:main',
        ],
    }
)

