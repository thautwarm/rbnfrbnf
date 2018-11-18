from setuptools import setup, find_packages
import rbnfrbnf
readme = ""

setup(
    name='rbnfrbnf',
    version=rbnfrbnf.__version__,
    keywords='parser generation, LR parser, efficient, JIT',
    description='A best LR parser generator',
    long_description=readme,
    long_description_content_type='text/markdown',
    license='MIT',
    python_requires='>=3.6.0',
    url='https://github.com/thautwarm/rbnfrbnf',
    author='thautwarm, lfkdsk',
    author_email='twshere@outlook.com',
    packages=find_packages(),
    # entry_points={'console_scripts': ['yapypy=yapypy.cmd.cli:python_ex_cli']},
    install_requires=['rbnf'],
    package_data={'rbnfrbnf': ['bootstrap/*.rbnf']},
    platforms='any',
    classifiers=[
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: Implementation :: CPython'
    ],
    zip_safe=False)
