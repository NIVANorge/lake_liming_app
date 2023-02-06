# Lake liming app

A web application for simulating the effectiveness of lake liming using different lime products. Developed for Miljødirektoratet during 2023.

## 1. Background

An overview of the project and main development tasks can be found on the [Wiki](https://github.com/NIVANorge/lake_liming_app/wiki).

## 2. Streamlit app for testing

A simple Streamlit app to explore user requirements is deployed [here](https://nivanorge-lake-liming-app-app-9p2c97.streamlit.app/). Note that the final application will probably not be deployed using Streamlit, but it's useful as a starting point for discussions and for quickly exploring UI options.

To deploy the app for testing via JupyterHub:

 1. Clone this repository to the Hub

 2. Open a terminal and `cd` into the `lake_liming_app` folder

 3. Run `streamlit run app.py` to start the app

 4. Open a new browser tab and navigate to https://jupyterhub.niva.no/hub/user-redirect/proxy/8501/ to view the app

## 3. Documentation

User documentation for the application is [here](https://nivanorge.github.io/lake_liming_app/).

### 3.1. Updating the documentation

The documentation is built using [Quarto](https://quarto.org/). Files are stored in the main repository within the `docs` sub-folder. To update the documentation, simply update the files in this folder and push your changes to `main`. This will trigger a GitHub "action" ([here](https://github.com/NIVANorge/lake_liming_app/blob/main/.github/workflows/quarto-publish.yml)) that will rebuild the website and publish a new version via GitHub-Pages.

## 4. Data templates

Blank data templates for use with the app are available [here](https://github.com/NIVANorge/lake_liming_app/tree/main/data). Templates containing example data for use when testing are also provided.

## 5. Contributing

Please use the [Discussions board](https://github.com/NIVANorge/lake_liming_app/discussions) for general questions & ideas, and the [Issue tracker](https://github.com/NIVANorge/lake_liming_app/issues) for specific suggestions (i.e. anything requiring a definite action or resolution). Further details about the project can be found on the [Wiki](https://github.com/NIVANorge/lake_liming_app/wiki) and in the [user-facing documentation](https://nivanorge.github.io/lake_liming_app/). All code relating to the project is [here](https://github.com/NIVANorge/lake_liming_app).


## 6. Other resources

 * **[Column test template](./data/liming_app_data_template_v1-0.xlsx)**. A proposed template for uploading column test data to the app.
 
 * **[Example dataset](./data/liming_app_test_data.xlsx)**. An example dataset from Karl-Jan transferred to the new template.
 
 * **[TPKALK](https://niva.brage.unit.no/niva-xmlui/handle/11250/208709)**. An old model developed by Atle Hindar et al. at NIVA during the 1990s. This model implements additional calculations required to estimate liming requirements for lakes with specific characteristics.
