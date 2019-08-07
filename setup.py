import setuptools

from woocommerce import __author__, __version__, __title__

setuptools.setup(
    name=__title__,
    version=__version__,
    description="WooCommerce REST API v3 (async and sync)",
    long_description="WooCommerce REST API v3 (async and sync)",
    author=__author__,
    author_email='leon@ultrafunk.nl',
    url='https://github.com/ultrafunkamsterdam/WooCommerce',
    packages=setuptools.find_packages(),
    install_required['requests'],
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
