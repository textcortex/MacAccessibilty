
from setuptools import setup
import os


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name="textCortex",
    version='0.1.0',
    author="Textcortex",
    url="https://textcortex.com/",
    description="Textcortex backgroud service code",
    license="",
    packages=['textCortex','textCortex.a11y'],
    install_requires=[
        'pyobjc-core>=9.2',
        'pyobjc-framework-Cocoa>=9.2',
        'pyobjc-framework-Quartz>=9.2',
        'pyobjc-framework-ApplicationServices>=9.2',
        'pyobjc-framework-CoreText>=9.2',
        'future'
    ],
    
)



