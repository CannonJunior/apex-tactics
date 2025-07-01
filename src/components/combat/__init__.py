"""
Combat Components Package

Core combat-related components including damage, defense, and attack mechanics.
"""

from .damage import DamageComponent, DamageResult, AttackType
from .defense import DefenseComponent
from .attack import AttackComponent

__all__ = [
    'DamageComponent',
    'DamageResult', 
    'AttackType',
    'DefenseComponent',
    'AttackComponent'
]