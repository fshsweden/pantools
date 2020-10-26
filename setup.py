from setuptools import find_packages, setup
setup(
    name='pantools',
    packages=find_packages(include=['pantools']),
    version='0.1.12',
    author='Peter Andersson',
    author_email='peter@fsh.se',
    description='PAN Tools library',
    url="https://github.com/fshsweden/pantools",
    license='MIT',
    install_requires=[],
    setup_requires=['pytest-runner'],
    tests_require=['pytest==4.4.1'],
    test_suite='tests',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6'
)
