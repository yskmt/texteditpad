from setuptools import setup

__version__ = '0.3'

setup(
    name='texteditpad',
    py_modules=['texteditpad'],
    version=__version__,
    description='Simple textbox editing widget with Emacs-like keybindings',
    long_description=open('README.rst').read(),
    url='https://github.com/yskmt/texteditpad',
    author='Yusuke Sakamoto',
    author_email='yus.sakamoto@gmail.com',
    license='MIT',
    keywords='curses terminal text edit box pad',
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
