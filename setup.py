import setuptools

with open("README", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name='horus',
    version='0.0.4',
    author='Anton Vattay',
    author_email='anton@cuttingedgeai.com',
    description='Process watcher.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/CuttingEdgeAI/horus',
    project_urls = {
        "Bug Tracker": "https://github.com/CuttingEdgeAI/horus/issues"
    },
    license='Private',
    packages=['horus'],
    install_requires=['wheel'],
)