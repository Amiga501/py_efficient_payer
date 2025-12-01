# -*- coding: utf-8 -*-
"""
Created on Tue Nov 11 21:52:33 2025

@author: Brendan

The main panel app

Basic plan is to have 3x panels for initial MVP:
    - Summary comparison page of PAYE vs contractor
    - PAYE specific page
    - Contractor specific page

"""
# %% Global imports
from collections.abc import Callable
from dotenv import load_dotenv

import panel as pn
import os


# %% py_contractor imports
from py_contractor.config.config import Config
from py_contractor.config.loggers import DashLogger


# %% Module level config

pn.extension("tabulator")

LOGGER = DashLogger().logger

load_dotenv(Config().ENV_DIR)

# %% Functions

def main_app():
    """!
    **Create the app**
    
    """
    app = PanelApp(
        logger=LOGGER,
        )
    
    return app.run()


# %% Classes

# -----------------------------------------------------------------------------
class PanelApp:    
    """!
    The dashboard
    
    """

    # -------------------------------------------------------------------------
    def __init__(self, *
                 logger: Callable,
                 ):
        """!
        **Instantiate**
        
        """        
        self.logger = logger
        
        if not self.__get_env_vars():
            self.template = None
            return
        
        self.__create_template()
        
    # -------------------------------------------------------------------------
    def __create_sidebar(self):
        """!
        **Create the sidebar links**
        
        """
        
    # -------------------------------------------------------------------------
    def __create_template(self):
        """!
        **Create the template and add objects**
        
        """
        
        self.tabs = pn.Tabs()
        
        self.__create_template_summary()
        
        self.template = pn.template.FastGridTemplate(
            site="Panel", 
            title="py_efficient_payer", 
            prevent_collision=True,
            )
        
        self.template.main = self.tabs
        
    # -------------------------------------------------------------------------
    def __create_template_authorisation(self):
        """!
        **Create the authorisation template**
        """
        
    # -------------------------------------------------------------------------
    def __create_template_summary(self):
        """!
        **Create the summary tab objects**
        
        """
        layout1 = pn.Column(
            styles={"background": "green"}, 
            sizing_mode="stretch_both",
            )
        layout2 = pn.Column(
            styles={"background": "red"}, 
            sizing_mode="stretch_both",
            )
        layout3 = pn.Column(
            styles={"background": "blue"}, 
            sizing_mode="stretch_both",
            )
        
        self.tabs.append(
            pn.Column(
                pn.Row(layout1, layout2),
                layout3,
                )
            )
        
    # -------------------------------------------------------------------------
    def __get_env_vars(self) -> bool:
        """!
        **Pull env vars into the class**
        
        @return [bool] True if all necessary vars found, False otherwise
        
        """        
        vars_ = ["CLIENT_SECRET",
                 "CLIENT_ID",
                 "REDIRECT_URI",
                 "SCOPE",
                 "OAUTH_AUTHORISE_URL",
                 "OAUTH_TOKEN_URL"
                 ]
        
        for var_ in vars_:
            if not (val := os.environ.get(var_)):
                self.logger.error(
                    f"Required environmental var: {var_} not found, won't be "
                    "able to complete setup")
                return False
            setattr(self, var_.lower(), val)
        
        return True
    
    # -------------------------------------------------------------------------
    def run(self):
        """!
        **Run the webapp**
        """
        return self.template
            
        
    
    
# %% Main
if __name__ == "__main__":
    
    pn.serve(
        main_app,
        port=5006,
        threaded=True,
        )

else:
    main_app().servable()