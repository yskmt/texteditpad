from setuptools import setup

__version__ = '0.23'

setup(
    name='texteditpad',
    packages=['texteditpad'],
    version=__version__,
    description='Simple textbox editing widget with Emacs-like keybindings',
    long_description=open('README.rst').read(),
    url='https://github.com/yskmt/texteditpad',
    author='Yusuke Sakamoto',
    author_email='yus.sakamoto@gmail.com',
    license='MIT',
    keywords='curses terminal text edit box pad',
    entry_points={'console_scripts': ['texteditpad=src.texteditbox:main']},
    classifiers=[
        'Intended Audience :: End Users/Desktop',
        'Environment :: Console :: Curses',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX',
        'Natural Language :: English',
        'Programming Language :: Python :: 2.7',
        'Topic :: Terminals',
        'Topic :: Utilities',
        'Topic :: Text Editors'
    ],
)

