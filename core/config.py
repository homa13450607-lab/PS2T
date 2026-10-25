###############################################################
# PS2T - Persian Speech To Text
#
# Configuration Manager
#
# Version: 2.1.0
#
# Responsibility:
#
#   - Load settings.yaml
#   - Provide configuration access
#   - Manage project paths
#   - Offline model configuration
#
###############################################################


import yaml

from pathlib import Path
from typing import Dict, Any





class Settings:



    def __init__(
        self,
        config_path: str = "config/settings.yaml"
    ):


        #######################################################
        # Project Root
        #######################################################

        #
        # Structure:
        #
        # Speech To Text
        #
        # ├── app
        # ├── config
        # │    └── settings.yaml
        # ├── models
        #
        #######################################################


        self.base_dir = (
            Path(__file__)
            .resolve()
            .parent
            .parent
            .parent
        )



        self.config_file = (
            self.base_dir /
            config_path
        )



        self._config: Dict[str, Any] = (
            self._load_config()
        )





    ###########################################################
    # Load YAML
    ###########################################################


    def _load_config(self):


        if not self.config_file.exists():

            raise FileNotFoundError(
                f"Config file not found: {self.config_file}"
            )



        with open(
            self.config_file,
            "r",
            encoding="utf-8"
        ) as file:


            config = yaml.safe_load(file)



        if config is None:

            raise ValueError(
                "Configuration file is empty"
            )



        return config





    ###########################################################
    # Generic Getter
    ###########################################################


    def get(
        self,
        section: str,
        key: str,
        default=None
    ):


        return (

            self._config
            .get(section, {})
            .get(key, default)

        )





    ###########################################################
    # Application
    ###########################################################


    @property
    def app_name(self):

        return self.get(
            "app",
            "name",
            "PS2T"
        )



    @property
    def version(self):

        return self.get(
            "app",
            "version",
            "1.0.0"
        )



    @property
    def host(self):

        return self.get(
            "app",
            "host",
            "127.0.0.1"
        )



    @property
    def port(self):

        return self.get(
            "app",
            "port",
            8000
        )





    ###########################################################
    # Engine
    ###########################################################


    @property
    def default_engine(self):

        return self.get(
            "engine",
            "default_engine",
            "whisper"
        )



    @property
    def default_model(self):

        return self.get(
            "engine",
            "default_model",
            "medium"
        )



    @property
    def default_language(self):

        return self.get(
            "engine",
            "default_language",
            "fa"
        )



    #
    # Local Offline Model Path
    #

    @property
    def model_path(self):


        relative_path = self.get(
            "engine",
            "model_path",
            "models/faster-whisper-medium"
        )


        return (
            self.base_dir /
            relative_path
        )





    ###########################################################
    # Hardware
    ###########################################################


    @property
    def device(self):

        return self.get(
            "engine",
            "device",
            "auto"
        )





    ###########################################################
    # Whisper Configuration
    ###########################################################


    @property
    def whisper_config(self):


        return (

            self._config
            .get(
                "engine",
                {}
            )
            .get(
                "whisper",
                {}
            )

        )





    @property
    def whisper_beam_size(self):


        return self.whisper_config.get(
            "beam_size",
            5
        )





    @property
    def whisper_vad_filter(self):


        return self.whisper_config.get(
            "vad_filter",
            True
        )





    @property
    def cpu_compute_type(self):


        return self.whisper_config.get(
            "cpu_compute_type",
            "int8"
        )





    @property
    def gpu_compute_type(self):


        return self.whisper_config.get(
            "gpu_compute_type",
            "float16"
        )





    ###########################################################
    # Paths
    ###########################################################


    def get_path(
        self,
        key: str
    ) -> Path:



        relative_path = (

            self._config
            .get(
                "paths",
                {}
            )
            .get(
                key,
                key
            )

        )



        path = (

            self.base_dir /
            relative_path

        )



        path.mkdir(
            parents=True,
            exist_ok=True
        )



        return path





    @property
    def models_dir(self):

        return self.get_path(
            "models_dir"
        )



    @property
    def uploads_dir(self):

        return self.get_path(
            "uploads_dir"
        )



    @property
    def outputs_dir(self):

        return self.get_path(
            "outputs_dir"
        )



    @property
    def logs_dir(self):

        return self.get_path(
            "logs_dir"
        )



    @property
    def temp_dir(self):

        return self.get_path(
            "temp_dir"
        )





    ###########################################################
    # Upload
    ###########################################################


    @property
    def max_file_size_mb(self):


        return (

            self._config
            .get(
                "upload",
                {}
            )
            .get(
                "max_file_size_mb",
                2048
            )

        )





    ###########################################################
    # Processing
    ###########################################################


    @property
    def max_parallel_jobs(self):


        return (

            self._config
            .get(
                "processing",
                {}
            )
            .get(
                "max_parallel_jobs",
                1
            )

        )





    @property
    def cleanup_temp_files(self):


        return (

            self._config
            .get(
                "processing",
                {}
            )
            .get(
                "cleanup_temp_files",
                True
            )

        )





    ###########################################################
    # Dictionary
    ###########################################################


    @property
    def dictionary_enabled(self):


        return (

            self._config
            .get(
                "dictionary",
                {}
            )
            .get(
                "enabled",
                True
            )

        )





    @property
    def dictionary_path(self):


        return (

            self.base_dir /
            self._config
            .get(
                "dictionary",
                {}
            )
            .get(
                "path",
                "app/dictionary/custom_dict.json"
            )

        )





###############################################################
# Singleton
###############################################################


settings = Settings()