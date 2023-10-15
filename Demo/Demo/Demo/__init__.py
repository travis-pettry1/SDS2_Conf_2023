from .Demo import Demo
from Commands import RegisterCommand
from PluginSetupTools import RegisterPluginSetup

RegisterCommand(Demo(), "Model/Parametric")
