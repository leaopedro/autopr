from setuptools import setup, find_packages

setup(
    name='autopr_cli',
    version='0.2.4',
    py_modules=['run_cli'],
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'autopr=run_cli:main',
        ],
    },
    install_requires=[],
    author='Pedro Leao',
    author_email='leaop54@gmail.com',
    description='A CLI tool to automate PR creation and listing.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/leaopedro/autopr',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)