from setuptools import setup, find_packages

setup(
    name="ts-resonance-core",
    version="0.1.0",
    description="Spectral anomaly detection for time-series data.",
    author="ResonanceArchitect",
    author_email="123456+ResonanceArchitect@users.noreply.github.com",
    packages=find_packages(),
    install_requires=[
        "numpy",
        "scikit-learn",
        "joblib",
        "pandas"
    ],
    extras_require={
        "neural": ["tensorflow>=2.10.0"]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Topic :: Scientific/Engineering :: Information Analysis",
    ],
    python_requires='>=3.8',
)
