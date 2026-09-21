import json

import ee


PROJECT_ID = "terrawatch-ai-506504"


def initialize_gee():
    """
    Initialize Google Earth Engine using Streamlit Cloud secrets
    when available, otherwise use the local Earth Engine credentials.
    """

    try:
        import streamlit as st

        if "EARTHENGINE_CREDENTIALS" in st.secrets:
            credential_data = json.loads(
                st.secrets["EARTHENGINE_CREDENTIALS"]
            )

            credential_args = {
                "token_uri": ee.oauth.TOKEN_URI,
                "refresh_token": credential_data["refresh_token"],
                "client_id": credential_data.get(
                    "client_id",
                    ee.oauth.CLIENT_ID,
                ),
                "client_secret": credential_data.get(
                    "client_secret",
                    ee.oauth.CLIENT_SECRET,
                ),
                "scopes": credential_data.get(
                    "scopes",
                    ee.oauth.SCOPES,
                ),
            }

            if credential_data.get("project"):
                credential_args["quota_project_id"] = credential_data["project"]

            credentials = ee.oauth.credentials_lib.Credentials(token=None,
                **credential_args
            )

            ee.Initialize(
                credentials=credentials,
                project=PROJECT_ID,
            )

            print("Google Earth Engine connected using Streamlit credentials")
            return True

    except Exception as error:
        print("Streamlit GEE authentication unavailable:", error)

    try:
        ee.Initialize(project=PROJECT_ID)
        print("Google Earth Engine connected using local credentials")
        return True

    except Exception as error:
        print("GEE initialization error:", error)
        return False

