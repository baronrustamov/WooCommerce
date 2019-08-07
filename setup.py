import setuptools


__title__ = "woocommerce"
__version__ = "1.0"
__author__ = "UltrafunkAmsterdam"
__license__ = "MIT"


setuptools.setup(
    name=__title__,
    version=__version__,
    description="WooCommerce REST API v3 (async and sync)",
    long_description="WooCommerce REST API v3 (async and sync)",
    author=__author__,
    author_email='leon@ultrafunk.nl',
    url='https://github.com/ultrafunkamsterdam/WooCommerce',
    packages=setuptools.find_packages(),
    install_requires=['requests'],
    include_package_data=True,
    license='MIT',
    classifiers=[
        # Trove classifiers
        # Full list: https://pypi.python.org/pypi?%3Aaction=list_classifiers
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy'
    ]
)
