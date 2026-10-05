"""Personality traits come from the model files (mindcore/model/*.mind, optional user model.mind)."""
from copy import deepcopy

from .model import get_model

TRAITS = get_model().trait_info()


def default_persona():
    return get_model().default_persona()


def normalize_persona(persona=None):
    return get_model().normalize_persona(persona)


def effective_params(base, persona):
    return get_model().effective_params(base, persona)


def apply_persona(readout, persona=None):
    """Traits act on the dynamics, so the readout is returned unchanged."""
    return deepcopy(readout)
