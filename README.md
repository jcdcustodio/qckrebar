# QCKRebar
Current Version: 1.0.0 (2025-02-22)

[**Access Live Version Here**](https://qckrebar.streamlit.app/)

<hr>

**QCKRebar** is a web application built for optimized estimation of steel reinforcing bars. Implemented in Python using Streamlit for the web framework, the application is a rough proof of concept for conveniently automate workflows in estimating cost of construction through code. Ideas for developing the application taken from personal spreadsheet templates and [Cutting Optimization Pro](https://optimalprograms.com/cutting-optimization/). The best fit algorithm was used to return an optimized result as output.

<hr>

### Local installation/setup 

1. Fork the repository then clone locally on your machine.

2. Ensure your current working directory is the project folder itself and check if `pyproject.toml` or `requirements.txt` is present in your working directory.

3. **Installation using** `uv`
    + [Download and install uv](https://docs.astral.sh/uv/#installation). 
    + In the terminal, run `uv venv` to create a virtual environment. 
    + Activate venv using `<source path> .venv/bin/activate`.
    + Run `uv sync` to sync the dependencies of the environment according to the content of `pyproject.toml`.

    + *Optional* - From `pyproject.toml`, take note of the "optional-dependencies" that are visible at the bottom. Run `uv sync --extra <name>` to install additional packages.

4. **Installation using** `pip`
    + Create a virtual environment and activate it from your working directory.
    + Run `pip install -r requirements.txt`.

5. To launch the application, go to `main/` and run `streamlit run app.py`.